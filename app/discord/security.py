from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from app.config import settings


def verify_discord_signature(signature: str | None, timestamp: str | None, body: bytes) -> bool:
    """
    Verifies the Ed25519 signature sent by Discord on incoming interaction webhooks.
    """
    if not signature or not timestamp or not settings.DISCORD_PUBLIC_KEY:
        return False

    try:
        verify_key = VerifyKey(bytes.fromhex(settings.DISCORD_PUBLIC_KEY))
        verify_key.verify(f"{timestamp}".encode() + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError, TypeError, Exception):
        return False
