"""
Script to register Discord Slash Commands using Discord HTTP REST API.

Usage:
    # Register commands globally (propagates across all servers within ~1 hour):
    python scripts/register_commands.py

    # Register commands to a specific guild/server (INSTANT propagation for development):
    python scripts/register_commands.py --guild 123456789012345678
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path when script is executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from app.config import settings

COMMANDS = [
    {
        "name": "ask",
        "description": "Ask questions about NYC Open Data, 311, restaurant grades, or NYPL digital collections",
        "options": [
            {
                "name": "query",
                "description": "Your question (e.g. '311 noise issues in Bushwick' or 'NYPL photos of Flatiron Building')",
                "type": 3,  # STRING
                "required": True,
            }
        ],
    },
    {
        "name": "nypl",
        "description": "Search NYPL Digital Collections archives, photos, prints, or find library branches",
        "options": [
            {
                "name": "query",
                "description": "Search term or branch name (e.g. '1930s subway maps', 'Schwarzman building')",
                "type": 3,  # STRING
                "required": True,
            }
        ],
    },
    {
        "name": "nycdata",
        "description": "Query NYC municipal open datasets: 311 complaints, restaurant health grades, street trees",
        "options": [
            {
                "name": "query",
                "description": "Query or restaurant name (e.g. 'Katz Delicatessen', 'noise complaints in Astoria')",
                "type": 3,  # STRING
                "required": True,
            }
        ],
    },
]


def register_commands(guild_id: Optional[str] = None):
    app_id = settings.DISCORD_APP_ID
    bot_token = settings.DISCORD_BOT_TOKEN
    target_guild = guild_id or settings.DISCORD_GUILD_ID

    if not app_id or not bot_token:
        print("❌ Error: DISCORD_APP_ID and DISCORD_BOT_TOKEN must be set in your .env or environment")
        sys.exit(1)

    if target_guild:
        url = f"https://discord.com/api/v10/applications/{app_id}/guilds/{target_guild}/commands"
        scope_str = f"Guild/Server ID: {target_guild} (Instant Update)"
    else:
        url = f"https://discord.com/api/v10/applications/{app_id}/commands"
        scope_str = "Global (May take up to 1 hour to propagate)"

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    }

    print(f"🚀 Registering commands for Discord Application ID: {app_id}")
    print(f"📍 Target Scope: {scope_str}")

    success_count = 0
    for cmd in COMMANDS:
        try:
            response = httpx.post(url, headers=headers, json=cmd, timeout=10.0)
            if response.status_code in (200, 201):
                print(f"  ✅ Successfully registered /{cmd['name']}")
                success_count += 1
            else:
                print(f"  ❌ Failed to register /{cmd['name']}: HTTP {response.status_code} - {response.text}")
        except Exception as e:
            print(f"  ❌ Error registering /{cmd['name']}: {e}")

    print(f"\nFinished: {success_count}/{len(COMMANDS)} commands registered successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register Discord Slash Commands for NYC/NYPL Bot")
    parser.add_argument(
        "--guild",
        "-g",
        type=str,
        default=None,
        help="Specific Discord Server/Guild ID for instant command registration (bypasses 1hr global caching)",
    )
    args = parser.parse_args()
    register_commands(guild_id=args.guild)
