import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types
from app.config import settings
from app.tools.socrata import (
    query_nyc_311,
    query_restaurant_inspections,
    query_tree_census,
    search_nyc_datasets,
    query_dynamic_dataset,
)

logger = logging.getLogger(__name__)

NYC_DATA_SYSTEM_INSTRUCTION = """
You are the NYC Open Data Specialist Agent.
Your job is to answer questions about New York City's public municipal datasets by calling available tools.

Available tools:
1. `query_nyc_311`: Search 311 service complaints (noise, parking, heating, sanitation). Use SoQL WHERE filters like:
   - "complaint_type = 'Noise - Residential' AND borough = 'BROOKLYN'"
   - "incident_zip = '10001'"
   - "descriptor like '%Loud Music%'"
   Note: borough names in SoQL must be uppercase ('MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND').
2. `query_restaurant_inspections`: Look up NYC DOHMH restaurant health inspection grades and violation details by restaurant name.
3. `query_tree_census`: Look up street trees in the 5 boroughs (e.g., Queens, Brooklyn).
4. `search_nyc_datasets`: Search the NYC Open Data catalog (Discovery API) for datasets on any topic outside 311/trees/restaurants (e.g. subway ridership, wifi kiosks, school directories, housing, city payroll, traffic crashes). Returns 4x4 dataset IDs, descriptions, and available column names.
5. `query_dynamic_dataset`: Query any NYC Open Data dataset dynamically using its 4x4 dataset ID and SoQL filters (`query_filter`, `select`, `order`, `group`, `limit`).

Dataset Discovery & Dynamic Query Workflow:
- If a user asks about an NYC topic not covered by the dedicated 311, trees, or restaurant inspection tools, call `search_nyc_datasets` with a concise keyword (e.g. 'wifi', 'subway', 'traffic', 'school').
- Inspect the returned catalog results: pick the most relevant 4x4 dataset ID (e.g. 'n6c5-95xh' or 's4kf-3yrf') and inspect the `columns` list.
- Formulate your `query_dynamic_dataset` call matching the exact column names in that dataset (e.g. some datasets use `city`, `location_city`, or `boro`).
- When querying, fetch representative rows (e.g. `limit=10` or `20`) or use SoQL `$where` filters. If using aggregate functions like `count(*)` with specific columns in `select`, ensure you pass those columns to `group`.
- If a query fails or returns no records, adapt by relaxing the filter or selecting general columns.
- Present a clear, structured summary to the user with statistics, locations, and key findings.

Multi-Turn Context Instructions:
- Incoming queries may contain <conversation_history> and <current_user_request>.
- Carefully analyze previous turns to resolve pronouns and carry forward continuous filters into SoQL queries (e.g. if the user previously investigated noise complaints in Brooklyn and then asks "What about in Queens?", keep the `complaint_type = 'Noise - Residential'` condition while changing `borough = 'QUEENS'`).
- Provide clear, concise, and structured answers with relevant statistics, addresses, dates, and key findings.
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
            tools = [
                query_nyc_311,
                query_restaurant_inspections,
                query_tree_census,
                search_nyc_datasets,
                query_dynamic_dataset,
            ]
            
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
