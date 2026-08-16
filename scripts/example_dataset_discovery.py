"""
NYC Open Data Catalog Discovery Example.

This script demonstrates how the NYC Data Agent dynamically discovers,
inspects, and queries un-indexed NYC Open Data catalogs (such as LinkNYC Wi-Fi Kiosks,
Subway Ridership, Traffic Incidents, City Payroll, and School Directories) using
the Socrata Discovery API and dynamic SODA queries.

Usage:
    python scripts/example_dataset_discovery.py
    python scripts/example_dataset_discovery.py "Find datasets on NYC public Wi-Fi kiosks"
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools.socrata import search_nyc_datasets, query_dynamic_dataset
from app.agents.nyc_data_agent import nyc_data_agent
from app.agents.orchestrator import orchestrator_agent


async def demo_direct_discovery_tools():
    """Demonstrates low-level discovery tool calls directly."""
    print("\n" + "=" * 65)
    print("STEP 1: Direct Tool Execution — Catalog Discovery API")
    print("=" * 65)
    print("🔍 Searching NYC Open Data catalog for keyword: 'LinkNYC'...")
    catalog_results = await search_nyc_datasets("LinkNYC", limit=2)
    print("📋 Catalog Results (4x4 IDs and available columns):")
    print(catalog_results)

    print("\n" + "=" * 65)
    print("STEP 2: Direct Tool Execution — Dynamic SoQL Query")
    print("=" * 65)
    print("📊 Querying dataset 'n6c5-95xh' (LinkNYC Kiosk Status) dynamically...")
    query_results = await query_dynamic_dataset(
        four_by_four_id="n6c5-95xh",
        query_filter="status = 'Activation'",
        limit=2,
    )
    print("📄 Dynamic Records Returned:")
    print(query_results)


async def demo_agent_discovery(user_query: str):
    """Demonstrates how the agent autonomous loop uses discovery tools."""
    print("\n" + "=" * 65)
    print("STEP 3: Full Agent Autonomous Reasoning Loop")
    print("=" * 65)
    print(f"💬 User Prompt: '{user_query}'")
    print("🤖 Invoking NYC Data Agent with Discovery Tools...\n")

    response = await orchestrator_agent.handle_user_query(user_query, command_name="nycdata")
    print("✨ Agent Final Synthesis:")
    print("-" * 65)
    print(response)
    print("-" * 65)


async def main():
    parser = argparse.ArgumentParser(description="NYC Open Data Discovery Example")
    parser.add_argument(
        "query",
        nargs="?",
        type=str,
        default="Search the NYC Open Data catalog for LinkNYC Wi-Fi kiosks and summarize their status in Queens.",
        help="Query to test with discovery agent",
    )
    parser.add_argument(
        "--tools-only",
        action="store_true",
        help="Only run direct low-level tool calls without invoking Gemini LLM",
    )
    args = parser.parse_args()

    if args.tools_only:
        await demo_direct_discovery_tools()
    else:
        await demo_direct_discovery_tools()
        await demo_agent_discovery(args.query)


if __name__ == "__main__":
    asyncio.run(main())
