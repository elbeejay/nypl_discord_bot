import asyncio
import json
import logging
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings
from app.tools.socrata import query_nyc_311, query_restaurant_inspections, query_tree_census

logger = logging.getLogger(__name__)

NYC_DATA_SYSTEM_INSTRUCTION = """
You are the NYC Open Data Specialist Agent.
Your job is to answer questions about New York City's public municipal datasets by calling available tools.

Available tools:
1. query_nyc_311: Search 311 service complaints (noise, parking, heating, sanitation). Use SoQL WHERE filters like:
   - "complaint_type = 'Noise - Residential' AND borough = 'BROOKLYN'"
   - "incident_zip = '10001'"
   - "descriptor like '%Loud Music%'"
   Note: borough names in SoQL must be uppercase ('MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND').
2. query_restaurant_inspections: Look up NYC DOHMH restaurant health inspection grades and violation details by restaurant name.
3. query_tree_census: Look up street trees in the 5 boroughs (e.g., Queens, Brooklyn).

Instructions:
- When a user asks about NYC civic issues, municipal data, 311 complaints, or restaurant health grades, select and execute the right tool.
- Provide a clear, concise, and structured answer with relevant statistics, addresses, dates, and key findings.
"""


class NYCDataAgent:
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
        Runs the NYC Open Data expert agent loop with function calling.
        """
        try:
            client = self._get_client()
            tools = [query_nyc_311, query_restaurant_inspections, query_tree_census]
            
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
                    system_instruction=NYC_DATA_SYSTEM_INSTRUCTION,
                    tools=tools,
                    temperature=0.2,
                    thinking_config=thinking_config,
                ),
            )
            response = await chat.send_message(user_query)
            
            return response.text or "Unable to retrieve NYC Open Data records."
        except Exception as e:
            logger.error(f"Error in NYCDataAgent: {e}", exc_info=True)
            return f"NYC Data Expert Error: {str(e)}"


nyc_data_agent = NYCDataAgent()
