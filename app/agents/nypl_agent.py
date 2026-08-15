import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings
from app.tools.nypl_api import search_nypl_digital_collections, find_nypl_branch

logger = logging.getLogger(__name__)

NYPL_SYSTEM_INSTRUCTION = """
You are the NYPL (New York Public Library) Expert Agent.
Your role is to help users explore public domain archives, historical photographs, manuscripts, rare books, and NYPL branch library services across the Bronx, Manhattan, and Staten Island.

Available tools:
1. search_nypl_digital_collections: Search the NYPL Digital Collections for public domain historical artifacts, photos, maps, and documents.
2. find_nypl_branch: Find NYPL research centers, flagship buildings (Schwarzman, Schomburg, Library for the Performing Arts, SNFL), and neighborhood branches.

Instructions:
- When a user asks about historical NYC imagery, archives, library research collections, or library locations/services, invoke the appropriate tool.
- Present your findings with fascinating historical context, catalog details, and direct links where available.
"""


class NYPLAgent:
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

    async def run(self, user_query: str) -> str:
        """
        Runs the NYPL expert agent loop.
        """
        try:
            client = self._get_client()
            tools = [search_nypl_digital_collections, find_nypl_branch]
            
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
                model=settings.EXPERT_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=NYPL_SYSTEM_INSTRUCTION,
                    tools=tools,
                    temperature=0.3,
                    thinking_config=thinking_config,
                ),
            )
            response = await chat.send_message(user_query)
            
            return response.text or "Unable to retrieve NYPL collection records."
        except Exception as e:
            logger.error(f"Error in NYPLAgent: {e}", exc_info=True)
            return f"NYPL Expert Error: {str(e)}"


nypl_agent = NYPLAgent()
