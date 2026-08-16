"""
Session Cookie & API Key Authentication for Frontend API (/api/v1).
Supports HttpOnly signed session cookies, X-API-Key headers, and Bearer tokens.
"""

import hmac
import hashlib
import time
import secrets
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "nypl_session"
SESSION_TTL_SECONDS = 86400  # 24 Hours


_EPHEMERAL_SECRET: str = secrets.token_hex(32)


def _get_signing_secret() -> str:
    """Returns secret key used for HMAC session token signing."""
    secret = settings.FRONTEND_ACCESS_PASSCODE or settings.FRONTEND_API_KEY
    if not secret:
        return _EPHEMERAL_SECRET
    return secret


def create_signed_session_token(ttl_seconds: int = SESSION_TTL_SECONDS) -> str:
    """
    Creates a tamper-proof HMAC-SHA256 signed session token.
    Format: timestamp.nonce.signature
    """
    timestamp = int(time.time())
    nonce = secrets.token_hex(16)
    payload = f"{timestamp}:{nonce}"
    secret = _get_signing_secret().encode("utf-8")
    signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{timestamp}.{nonce}.{signature}"


def verify_signed_session_token(token: str, ttl_seconds: int = SESSION_TTL_SECONDS) -> bool:
    """
    Validates token format, expiration, and HMAC signature in constant time.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        timestamp_str, nonce, signature = parts
        timestamp = int(timestamp_str)
        now = int(time.time())

        # Check expiration
        if (now - timestamp) > ttl_seconds or timestamp > (now + 60):
            return False

        payload = f"{timestamp}:{nonce}"
        secret = _get_signing_secret().encode("utf-8")
        expected_sig = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature, expected_sig)
    except Exception:
        return False


async def verify_frontend_api_key(request: Request) -> None:
    """
    Validates that incoming requests to /api/v1 have an active HttpOnly session cookie,
    or a valid X-API-Key / Bearer token when FRONTEND_ACCESS_PASSCODE is configured.
    """
    configured_key = settings.FRONTEND_ACCESS_PASSCODE or settings.FRONTEND_API_KEY
    if not configured_key or not configured_key.strip():
        # If no passcode/key is set in configuration, authentication is bypassed
        return

    # 1. Check HttpOnly Session Cookie
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie and verify_signed_session_token(session_cookie):
        return

    # 2. Check X-API-Key header (for automated scripts or legacy callers)
    provided_key = request.headers.get("X-API-Key")

    # 3. Check Authorization Bearer header
    if not provided_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()

    # 4. Check query parameters (for browser EventSource)
    if not provided_key:
        provided_key = request.query_params.get("api_key")

    if not provided_key:
        logger.warning(f"Unauthorized /api/v1 access attempt from {request.client.host if request.client else 'unknown'}: missing session cookie or passcode")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please unlock the console with your passcode.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison for raw key header
    if not hmac.compare_digest(provided_key.encode("utf-8"), configured_key.encode("utf-8")):
        logger.warning("Unauthorized /api/v1 access attempt: invalid passcode")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Passcode.",
            headers={"WWW-Authenticate": "Bearer"},
        )

