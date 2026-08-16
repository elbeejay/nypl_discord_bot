"""
Interactive & CLI Test Script for NYC & NYPL Agents.

Test the AI reasoning and tool-calling loops directly in your terminal
without needing Discord webhooks or signatures.

Usage:
    # 1. Interactive Chat Loop:
    python scripts/test_agent.py

    # 2. Single Query:
    python scripts/test_agent.py "Show 311 noise complaints in Astoria"

    # 3. Target Specific Agent:
    python scripts/test_agent.py --command nypl "Historical photos of Brooklyn Bridge"
    python scripts/test_agent.py --command nycdata "Health inspection grade for Katz Delicatessen"
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.agents.orchestrator import orchestrator_agent


SAMPLE_PROMPTS = [
    "What are recent 311 noise complaints in Williamsburg?",
    "Find health inspection grades and violations for Shake Shack in Manhattan.",
    "Search the NYC Open Data catalog for LinkNYC Wi-Fi kiosks and check their status in Queens.",
    "Search NYPL digital archives for 1930s subway construction photos.",
    "Where is the Schomburg Center and what collections does it hold?",
    "Tell me about the historic Schwarzman building and find 311 complaints near 42nd St.",
]


async def run_query(query: str, command: str = "ask"):
    print(f"\n💬 Query: {query}")
    print(f"⚙️  Routing: /{command}")
    print("⏳ Agent reasoning & querying tools...\n" + "-" * 50)
    
    try:
        response = await orchestrator_agent.handle_user_query(query, command_name=command)
        print(response)
    except Exception as e:
        print(f"❌ Error: {e}")
    print("-" * 50)


async def interactive_mode():
    print("=" * 60)
    print("🗽 NYC & NYPL Agent Interactive Terminal Tester")
    print(f"🧠 Models: Orchestrator={settings.ORCHESTRATOR_MODEL} | Expert={settings.EXPERT_MODEL}")
    if settings.THINKING_BUDGET or settings.THINKING_LEVEL:
        print(f"🤔 Thinking: Budget={settings.THINKING_BUDGET} | Level={settings.THINKING_LEVEL}")
    print("=" * 60)
    print("Type your question below (or type 'sample' for ideas, 'exit' to quit):\n")

    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            if user_input.lower() == "sample":
                print("\n💡 Sample queries to try:")
                for i, sample in enumerate(SAMPLE_PROMPTS, 1):
                    print(f"  {i}. {sample}")
                print()
                continue

            command = "ask"
            query = user_input
            if user_input.startswith("/nypl "):
                command = "nypl"
                query = user_input[6:].strip()
            elif user_input.startswith("/nycdata "):
                command = "nycdata"
                query = user_input[9:].strip()
            elif user_input.startswith("/ask "):
                command = "ask"
                query = user_input[5:].strip()

            await run_query(query, command=command)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


def main():
    parser = argparse.ArgumentParser(description="Test NYC & NYPL AI Agent Locally")
    parser.add_argument("query", nargs="?", type=str, help="Query string to test")
    parser.add_argument(
        "--command",
        "-c",
        choices=["ask", "nypl", "nycdata"],
        default="ask",
        help="Command routing mode (default: ask)",
    )
    args = parser.parse_args()

    if args.query:
        asyncio.run(run_query(args.query, command=args.command))
    else:
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
