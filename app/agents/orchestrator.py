import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from google import genai
from google.genai import types
from app.config import settings
from app.agents.nyc_data_agent import nyc_data_agent
from app.agents.nypl_agent import nypl_agent
from app.agents.session_manager import session_manager
from app.schemas.a2ui import (
    FrontendChatRequest,
    FrontendChatResponse,
    A2UIPayload,
)
from app.tools.a2ui_generator import extract_a2ui_from_text_response

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_INSTRUCTION = """
You are the Gateway Orchestrator Agent for the NYC & NYPL AI Assistant.
Your job is to triage incoming user requests and delegate domain-specific tasks to specialized expert agents.

You have access to two expert delegation tools:
1. `delegate_to_nyc_data_agent`: Call this when the query relates to NYC Open Data, 311 complaints, restaurant health inspection grades/violations, street trees, or municipal city data.
2. `delegate_to_nypl_agent`: Call this when the query relates to the New York Public Library (NYPL), historical digital archives/photos/prints, library locations, or research collections.

Instructions:
- If a query requires both domains (e.g. "Tell me about the historic Schwarzman library building and find 311 noise issues around 42nd St"), you can call both tools.
- Once you receive the response from the expert agent(s), format a polished, engaging answer with markdown, emojis, structured lists, and links.
- If the user asks a simple greeting or general question about what you can do, explain your capabilities without needing to call tools.
"""


async def delegate_to_nyc_data_agent(query: str) -> str:
    """
    Delegates an urban or NYC open data question to the NYC Data Expert Agent.
    """
    logger.info(f"Delegating to NYC Data Agent: {query}")
    return await nyc_data_agent.run(query)


async def delegate_to_nypl_agent(query: str) -> str:
    """
    Delegates a library, historical archive, or digital collections query to the NYPL Expert Agent.
    """
    logger.info(f"Delegating to NYPL Agent: {query}")
    return await nypl_agent.run(query)


class OrchestratorAgent:
    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._loop = None

    def _get_client(self) -> genai.Client:
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self._client is None or self._loop != current_loop:
            self._loop = current_loop
            if settings.GEMINI_API_KEY:
                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            elif settings.GOOGLE_CLOUD_PROJECT:
                self._client = genai.Client(
                    vertexai=True,
                    project=settings.GOOGLE_CLOUD_PROJECT,
                    location=settings.GOOGLE_CLOUD_LOCATION,
                )
            else:
                raise ValueError(
                    "Missing Gemini credentials. Please set GEMINI_API_KEY in your .env file "
                    "or configure GOOGLE_CLOUD_PROJECT on GCP."
                )
        return self._client

    def _get_thinking_config(self) -> Optional[types.ThinkingConfig]:
        if settings.THINKING_BUDGET is not None:
            return types.ThinkingConfig(
                thinking_budget=settings.THINKING_BUDGET,
                include_thoughts=False,
            )
        elif settings.THINKING_LEVEL is not None:
            return types.ThinkingConfig(
                thinking_level=settings.THINKING_LEVEL,
                include_thoughts=False,
            )
        return None

    async def handle_user_query(self, user_query: str, command_name: str = "ask") -> str:
        """
        Processes user query through Gateway router and delegates to expert agents.
        Maintains complete compatibility with Discord webhook bot and CLI scripts.
        """
        try:
            # Fast-path direct routing for domain-specific slash commands
            if command_name == "nypl":
                logger.info(f"Direct routing command /nypl to NYPL Agent: {user_query}")
                return await nypl_agent.run(user_query)
            elif command_name == "nycdata":
                logger.info(f"Direct routing command /nycdata to NYC Data Agent: {user_query}")
                return await nyc_data_agent.run(user_query)

            client = self._get_client()
            tools = [delegate_to_nyc_data_agent, delegate_to_nypl_agent]
            thinking_config = self._get_thinking_config()

            chat = client.aio.chats.create(
                model=settings.ORCHESTRATOR_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=ORCHESTRATOR_SYSTEM_INSTRUCTION,
                    tools=tools,
                    temperature=0.2,
                    thinking_config=thinking_config,
                ),
            )
            response = await chat.send_message(user_query)
            return response.text or "I processed your request, but could not generate a summary."
        except Exception as e:
            logger.error(f"Error in OrchestratorAgent: {e}", exc_info=True)
            return f"⚠️ Error processing your request: {str(e)}"

    def _build_query_context(self, session, query: str) -> str:
        """Constructs multi-turn conversational context with strict XML boundary demarcations."""
        if len(session.messages) > 1:
            recent_turns = session.messages[-5:-1]
            turns_xml = "\n".join([
                f'<turn role="{m.role}">\n{m.content[:300]}\n</turn>'
                for m in recent_turns
            ])
            return (
                f"<conversation_history>\n{turns_xml}\n</conversation_history>\n\n"
                f"<current_user_request>\n{query}\n</current_user_request>"
            )
        return query

    async def handle_frontend_query(self, request: FrontendChatRequest) -> FrontendChatResponse:
        """
        Processes query from a custom Web / Mobile frontend, managing multi-turn sessions
        and synthesizing A2UI interactive UI components.
        """
        session = session_manager.get_or_create_session(request.session_id)
        session.add_message(role="user", content=request.query)

        query_context = self._build_query_context(session, request.query)
        response_text = await self.handle_user_query(query_context, command_name=request.command or "ask")

        # Synthesize A2UI visual components if enabled
        a2ui_payload: Optional[A2UIPayload] = None
        if request.enable_a2ui:
            a2ui_payload = extract_a2ui_from_text_response(response_text, command_name=request.command or "ask")

        session.add_message(
            role="model",
            content=response_text,
            a2ui=a2ui_payload.model_dump() if a2ui_payload else None,
        )

        return FrontendChatResponse(
            query=request.query,
            command=request.command or "ask",
            session_id=session.session_id,
            response=response_text,
            a2ui=a2ui_payload,
        )

    async def stream_frontend_query(self, request: FrontendChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronous generator yielding real-time SSE events for custom frontends:
        - status: Background tool invocation / reasoning updates
        - token: Word / token stream for real-time text rendering
        - a2ui: Structured UI component event for data viz widgets
        - done: Stream completion
        """
        session = session_manager.get_or_create_session(request.session_id)
        session.add_message(role="user", content=request.query)

        yield {"event": "status", "data": {"message": f"Analyzing query and selecting expert agent ({request.command or 'ask'})..."}}

        try:
            query_context = self._build_query_context(session, request.query)
            response_text = await self.handle_user_query(query_context, command_name=request.command or "ask")

            # Stream words/tokens in progressive chunks for smooth frontend typography
            words = response_text.split(" ")
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size]) + (" " if i + chunk_size < len(words) else "")
                yield {"event": "token", "data": {"token": chunk}}
                await asyncio.sleep(0.01)

            # Generate A2UI if enabled
            if request.enable_a2ui:
                a2ui_payload = extract_a2ui_from_text_response(response_text, command_name=request.command or "ask")
                if a2ui_payload and a2ui_payload.components:
                    yield {
                        "event": "a2ui",
                        "data": a2ui_payload.model_dump(),
                    }
                    session.add_message(
                        role="model",
                        content=response_text,
                        a2ui=a2ui_payload.model_dump(),
                    )
                else:
                    session.add_message(role="model", content=response_text)
            else:
                session.add_message(role="model", content=response_text)

            yield {"event": "done", "data": {"session_id": session.session_id}}
        except Exception as e:
            logger.error(f"Error in stream_frontend_query: {e}", exc_info=True)
            yield {"event": "error", "data": {"error": str(e)}}


orchestrator_agent = OrchestratorAgent()
