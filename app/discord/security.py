"""
Ed25519 Cryptographic Signature Verification for Discord Webhooks.
Enforces constant-time verification, public key validation, and timestamp replay windows.
"""

import time
from typing import Optional
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from app.config import settings

# Max replay age window (5 minutes / 300 seconds)
TIMESTAMP_REPLAY_WINDOW_SECONDS = 300


def verify_discord_signature(signature: Optional[str], timestamp: Optional[str], body: bytes) -> bool:
    """
    Verifies the Ed25519 signature sent by Discord on incoming interaction webhooks.
    Enforces non-empty public key, signature presence, and replay attack timestamp validation.
    """
    if not signature or not timestamp or not settings.DISCORD_PUBLIC_KEY:
        return False

    # 1. Enforce timestamp freshness to prevent replay attacks
    try:
        req_timestamp = int(timestamp)
        now = int(time.time())
        if abs(now - req_timestamp) > TIMESTAMP_REPLAY_WINDOW_SECONDS:
            return False
    except (ValueError, TypeError):
        return False

    # 2. Cryptographic signature check
    try:
        verify_key = VerifyKey(bytes.fromhex(settings.DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{timestamp}".encode("utf-8") + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError, TypeError, Exception):
        return False
