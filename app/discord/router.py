"""
Discord Webhook & Interactions Router.
Handles Ed25519 signature verification, Discord PING (Type 1), and slash commands (Type 2).
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.discord.security import verify_discord_signature
from app.discord.client import discord_client
from app.agents.orchestrator import orchestrator_agent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Discord"])


def extract_query_from_options(options: Optional[List[dict]]) -> str:
    """
    Safely extract user query string from Discord slash command options or nested subcommands.
    """
    if not options:
        return "Hello!"

    for opt in options:
        if opt.get("name") == "query" and opt.get("value") is not None:
            return str(opt["value"]).strip()

    for opt in options:
        nested_options = opt.get("options")
        if nested_options and isinstance(nested_options, list):
            nested_result = extract_query_from_options(nested_options)
            if nested_result:
                return nested_result

    for opt in options:
        if opt.get("value") is not None:
            return str(opt["value"]).strip()

    return "Hello!"


async def process_agent_interaction(interaction_token: str, user_query: str, command_name: str = "ask"):
    """
    Background worker that runs the agent loop and patches Discord's deferred interaction.
    """
    logger.info(f"Processing command /{command_name} query: '{user_query}'")
    try:
        response_text = await orchestrator_agent.handle_user_query(user_query, command_name=command_name)
        success = await discord_client.patch_original_response(
            interaction_token=interaction_token,
            content=response_text,
        )
        if not success:
            logger.error("Failed to patch Discord response webhook.")
    except Exception as e:
        logger.error(f"Error executing agent task: {e}", exc_info=True)
        safe_error = (
            "❌ An error occurred while processing your request. Please try again later."
            if settings.ENVIRONMENT.lower() == "production"
            else f"❌ An error occurred while processing your request: {str(e)}"
        )
        try:
            await discord_client.patch_original_response(
                interaction_token=interaction_token,
                content=safe_error,
            )
        except Exception as fallback_error:
            logger.error(f"Failed to deliver error response to Discord: {fallback_error}", exc_info=True)


@router.post("/interactions")
async def handle_discord_interaction(request: Request, background_tasks: BackgroundTasks):
    """
    Discord HTTP Interaction endpoint.
    Handles PING (Type 1) for endpoint verification, and APPLICATION_COMMAND (Type 2) slash commands.
    """
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    body = await request.body()

    # Enforce Ed25519 signature verification on all incoming requests
    if not verify_discord_signature(signature, timestamp, body):
        logger.warning("Rejected request due to invalid or missing Ed25519 signature.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid request signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")

    interaction_type = payload.get("type")

    # 1. Handle Discord Ping Validation (Type 1)
    if interaction_type == 1:
        logger.info("Discord PING (Type 1) acknowledged.")
        return JSONResponse(content={"type": 1})

    # 2. Handle Slash Commands (Type 2)
    if interaction_type == 2:
        interaction_token = payload.get("token")
        if not interaction_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing interaction token")

        data = payload.get("data", {})
        command_name = data.get("name", "ask")
        options = data.get("options", [])
        user_query = extract_query_from_options(options)

        logger.info(f"Received slash command /{command_name} with query: '{user_query}'")

        # Defer execution to background task to avoid Discord 3s timeout
        background_tasks.add_task(process_agent_interaction, interaction_token, user_query, command_name)

        # Immediate DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE response (Type 5)
        return JSONResponse(content={"type": 5})

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"type": 4, "data": {"content": "Unsupported interaction type"}},
    )
