import logging
import httpx
from typing import Any, Dict, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class DiscordClient:
    def __init__(self):
        self.base_url = "https://discord.com/api/v10"

    @property
    def app_id(self) -> str:
        return settings.DISCORD_APP_ID

    async def patch_original_response(
        self,
        interaction_token: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Updates the original deferred interaction response ("Bot is thinking...").
        """
        if not self.app_id:
            logger.error("DISCORD_APP_ID is not configured. Cannot patch interaction response.")
            return False

        if not interaction_token:
            logger.error("No interaction token provided for response patch.")
            return False

        url = f"{self.base_url}/webhooks/{self.app_id}/{interaction_token}/messages/@original"
        
        payload: Dict[str, Any] = {}
        if content is not None:
            if len(content) > 2000:
                payload["content"] = content[:1980] + "\n\n*(Truncated)*"
            else:
                payload["content"] = content
        elif not embeds:
            payload["content"] = "*(No response generated)*"

        if embeds:
            payload["embeds"] = embeds[:10]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=payload, timeout=15.0)
                if response.status_code in (200, 204):
                    logger.debug("Successfully patched original Discord interaction message.")
                    return True
                else:
                    logger.error(
                        f"Discord API PATCH failed with status {response.status_code}: {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error sending PATCH request to Discord webhook: {e}", exc_info=True)
            return False


discord_client = DiscordClient()
