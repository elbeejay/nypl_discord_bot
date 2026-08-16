import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings
from app.tools.discovery import search_nyc_datasets, query_dynamic_dataset

logger = logging.getLogger(__name__)

DISCOVERY_SYSTEM_INSTRUCTION = """
You are the NYC Open Data Catalog Explorer. Your job is to help users find datasets that aren't covered by the core tools (311, trees, restaurants).
Workflow:
1. If a user asks about a topic you don't have a direct tool for (e.g., "subway turnstiles", "linknyc kiosks", "affordable housing allotments"), use `search_nyc_datasets` with keywords.
2. Review the search results. Identify the best `four_by_four_id` and look at its available `columns`.
3. Use `query_dynamic_dataset` providing that `four_by_four_id` and a valid SoQL code snippet filtering by columns you found.
4. Present the final answer clearly with descriptions of the columns and the values returned.
"""


class NYCDiscoveryAgent:
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

        if self._client is None:
            raise ValueError("Client initialization failed unexpectedly.")

        return self._client

    async def run(self, user_query: str) -> str:
        try:
            client = self._get_client()
            tools = [search_nyc_datasets, query_dynamic_dataset]

            chat = client.aio.chats.create(
                model=settings.EXPERT_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=DISCOVERY_SYSTEM_INSTRUCTION,
                    tools=tools,
                    temperature=0.2,
                ),
            )
            response = await chat.send_message(user_query)
            return response.text or "Could not find a relevant dataset catalog entry."
        except Exception as e:
            logger.error(f"Error in NYCDiscoveryAgent: {e}", exc_info=True)
            return f"Discovery Error: {str(e)}"


# Instantiated at the bottom so your import statements find it correctly
nyc_discovery_agent = NYCDiscoveryAgent()
