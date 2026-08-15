import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings
from app.agents.nyc_data_agent import nyc_data_agent
from app.agents.nypl_agent import nypl_agent

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_INSTRUCTION = """
You are the Gateway Orchestrator Agent for the NYC & NYPL Discord Assistant.
Your job is to triage incoming user requests and delegate domain-specific tasks to specialized expert agents.

You have access to two expert delegation tools:
1. `delegate_to_nyc_data_agent`: Call this when the query relates to NYC Open Data, 311 complaints, restaurant health inspection grades/violations, street trees, or municipal city data.
2. `delegate_to_nypl_agent`: Call this when the query relates to the New York Public Library (NYPL), historical digital archives/photos/prints, library locations, or research collections.

Instructions:
- If a query requires both domains (e.g. "Tell me about the historic Schwarzman library building and find 311 noise issues around 42nd St"), you can call both tools.
- Once you receive the response from the expert agent(s), format a polished, engaging Discord-ready answer with markdown, emojis, and bullet points.
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

    async def handle_user_query(self, user_query: str, command_name: str = "ask") -> str:
        """
        Processes user query through Gateway router and delegates to expert agents.
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
            
            thinking_config = None
            if settings.THINKING_BUDGET is not None:
                thinking_config = types.ThinkingConfig(
                    thinking_budget=settings.THINKING_BUDGET,
                    include_thoughts=False,
                )
            elif settings.THINKING_LEVEL is not None:
                thinking_config = types.ThinkingConfig(
                    thinking_level=settings.THINKING_LEVEL,
                    include_thoughts=False,
                )

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


orchestrator_agent = OrchestratorAgent()
