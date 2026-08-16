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
from app.agents.nyc_discovery_agent import nyc_discovery_agent

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_INSTRUCTION = """
You are the Gateway Orchestrator Agent for the NYC & NYPL AI Assistant.
Your job is to triage incoming user requests and delegate domain-specific tasks to specialized expert agents.

You have access to two expert delegation tools:
1. `delegate_to_nyc_data_agent`: Call this when the query relates to NYC Open Data, 311 complaints, restaurant health inspection grades/violations, street trees, or municipal city data.
2. `delegate_to_nypl_agent`: Call this when the query relates to the New York Public Library (NYPL), historical digital archives/photos/prints, library locations, or research collections.
3. `delegate_to_nyc_discovery_agent`: Call this when the query asks about ANY OTHER NYC open datasets, civic topics, or general infrastructure catalogs outside of 311/Trees/Restaurants (e.g., subway system metrics, evictions, traffic accidents, linknyc kiosks, or school data).

Multi-Turn Context & Coreference Instructions:
- When <conversation_history> is provided in the prompt, carefully review prior turns to resolve all pronouns ("it", "that library", "the second violation", "that same year") and implied continuous filters (e.g. if previous turn was about 311 noise in Brooklyn and current turn asks "What about in Queens?", retain the 311 noise complaint criteria for Queens).
- Always formulate self-contained, fully qualified queries when invoking delegation tools so the expert agents have complete context.
- Once you receive the response from the expert agent(s), format a polished, engaging answer with markdown, structured lists, and links.
- If the user asks a simple greeting or general question about capabilities, answer directly.
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


async def delegate_to_nyc_discovery_agent(query: str) -> str:
    """
    Delegates to the NYC Discovery Agent when the user asks about deep or un-indexed
    NYC Open Data catalogs (like housing, subways, eviction data, etc.)
    """
    logger.info(f"Delegating to NYC Discovery Agent: {query}")
    return await nyc_discovery_agent.run(query)



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

    def _build_query_context(self, session, query: str, max_turns: int = 10) -> str:
        """
        Constructs multi-turn conversational context with strict XML boundary demarcations.
        Preserves full previous responses up to 2500 chars to avoid losing tables or details.
        """
        if len(session.messages) > 1:
            recent_turns = session.messages[-(max_turns + 1):-1]
            turns_xml = "\n".join([
                f'<turn role="{m.role}">\n{m.content[:2500]}\n</turn>'
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
        - trace: Visual agent reasoning lifecycle stages (Gateway -> Expert -> Tool -> A2UI)
        - status: Background tool invocation / reasoning updates
        - token: Word / token stream for real-time text rendering
        - a2ui: Structured UI component event for data viz widgets
        - done: Stream completion
        """
        session = session_manager.get_or_create_session(request.session_id)
        session.add_message(role="user", content=request.query)

        cmd = request.command or "ask"
        q_lower = request.query.lower()

        # Step 1 Trace: Gateway Router
        yield {
            "event": "trace",
            "data": {
                "stage": "gateway",
                "title": "Gateway Router",
                "agent": "Gemini 3.5 Flash Lite Orchestrator",
                "detail": f"Analyzing intent for [{cmd.upper()}] channel",
                "status": "running"
            }
        }
        yield {"event": "status", "data": {"message": f"Orchestrating agent pipeline ({cmd})..."}}
        await asyncio.sleep(0.02)

        # Step 2 Trace: Expert Selection & Tool Call
        is_nypl = cmd == "nypl" or any(w in q_lower for w in ["photo", "picture", "archive", "history", "schwarzman", "schomburg", "manuscript", "book", "library", "branch"])
        is_nyc = cmd == "nycdata" or any(w in q_lower for w in ["311", "noise", "complaint", "restaurant", "inspection", "grade", "tree", "census", "borough", "violation"])

        if is_nypl and not is_nyc:
            yield {
                "event": "trace",
                "data": {
                    "stage": "expert",
                    "title": "Expert Agent Handoff",
                    "agent": "🏛️ NYPL Archives Specialist",
                    "detail": "Delegated to NYPL Digital Collections & Branch Navigator",
                    "status": "running"
                }
            }
            yield {
                "event": "trace",
                "data": {
                    "stage": "tool",
                    "title": "Tool Invocation",
                    "tool": "search_nypl_digital_collections()",
                    "args": f"query='{request.query[:35]}...'",
                    "status": "running"
                }
            }
        elif is_nyc and not is_nypl:
            yield {
                "event": "trace",
                "data": {
                    "stage": "expert",
                    "title": "Expert Agent Handoff",
                    "agent": "🏙️ NYC Open Data Specialist",
                    "detail": "Delegated to NYC SODA Open Data Engine",
                    "status": "running"
                }
            }
            yield {
                "event": "trace",
                "data": {
                    "stage": "tool",
                    "title": "Tool Invocation",
                    "tool": "query_nyc_311() / query_socrata()",
                    "args": "SoQL Dataset Filters Applied",
                    "status": "running"
                }
            }
        else:
            yield {
                "event": "trace",
                "data": {
                    "stage": "expert",
                    "title": "Multi-Expert Evaluation",
                    "agent": "Gateway Multi-Agent Router",
                    "detail": "Cross-domain evaluation (NYPL Archives + NYC Open Data)",
                    "status": "running"
                }
            }

        try:
            query_context = self._build_query_context(session, request.query)
            response_text = await self.handle_user_query(query_context, command_name=cmd)

            # Stream words/tokens in progressive chunks for smooth frontend typography
            words = response_text.split(" ")
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size]) + (" " if i + chunk_size < len(words) else "")
                yield {"event": "token", "data": {"token": chunk}}
                await asyncio.sleep(0.01)

            # Step 3 Trace & A2UI Generation
            if request.enable_a2ui:
                a2ui_payload = extract_a2ui_from_text_response(response_text, command_name=cmd)
                if a2ui_payload and a2ui_payload.components:
                    yield {
                        "event": "trace",
                        "data": {
                            "stage": "a2ui",
                            "title": "A2UI Synthesis",
                            "detail": f"Constructed {len(a2ui_payload.components)} dynamic visual widget(s)",
                            "status": "completed"
                        }
                    }
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

            # Step 4 Trace: Completed
            yield {
                "event": "trace",
                "data": {
                    "stage": "completed",
                    "title": "Pipeline Execution Complete",
                    "detail": "Response generated & visual components hydrated",
                    "status": "completed"
                }
            }

            yield {"event": "done", "data": {"session_id": session.session_id}}
        except Exception as e:
            logger.error(f"Error in stream_frontend_query: {e}", exc_info=True)
            safe_error_msg = (
                "An unexpected error occurred while processing your request. Please try again."
                if settings.ENVIRONMENT.lower() == "production"
                else str(e)
            )
            yield {
                "event": "trace",
                "data": {
                    "stage": "completed",
                    "title": "Execution Interrupted",
                    "detail": safe_error_msg,
                    "status": "error"
                }
            }
            yield {"event": "error", "data": {"error": safe_error_msg}}
            yield {"event": "done", "data": {"session_id": session.session_id}}


orchestrator_agent = OrchestratorAgent()
