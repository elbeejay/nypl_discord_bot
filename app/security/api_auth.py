"""
API Key & Bearer Token Authentication Dependency for Frontend API (/api/v1).
Supports X-API-Key header, Authorization: Bearer token, and ?api_key= query parameter.
"""

import hmac
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)


async def verify_frontend_api_key(request: Request) -> None:
    """
    Validates that incoming requests to /api/v1 have a valid API Key when FRONTEND_API_KEY is configured.
    Supports:
      1. Header: 'X-API-Key: <key>'
      2. Header: 'Authorization: Bearer <key>'
      3. Query Param: '?api_key=<key>' (required for browser EventSource SSE connections)
    """
    configured_key = settings.FRONTEND_API_KEY
    if not configured_key:
        # If no key is set in configuration, authentication is bypassed (development mode)
        return

    # 1. Check X-API-Key header
    provided_key = request.headers.get("X-API-Key")

    # 2. Check Authorization Bearer header
    if not provided_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            provided_key = auth_header[7:].strip()

    # 3. Check query parameters (for browser EventSource)
    if not provided_key:
        provided_key = request.query_params.get("api_key")

    if not provided_key:
        logger.warning(f"Unauthorized /api/v1 access attempt from {request.client.host if request.client else 'unknown'}: missing API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Provide via 'X-API-Key' header, 'Authorization: Bearer <key>', or '?api_key=<key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided_key.encode("utf-8"), configured_key.encode("utf-8")):
        logger.warning(f"Unauthorized /api/v1 access attempt: invalid API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
