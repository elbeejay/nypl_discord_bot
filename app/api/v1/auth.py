"""
Authentication Router for Frontend Console.
Manages HttpOnly session login, logout, and session verification.
"""

import hmac
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Response, Request, status, Depends
from app.config import settings
from app.security.api_auth import (
    create_signed_session_token,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    verify_frontend_api_key,
)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    passcode: str


@auth_router.post("/login", summary="Exchange access passcode for HttpOnly session cookie")
async def login_endpoint(payload: LoginRequest, response: Response):
    """
    Verifies user-provided passcode once and issues a signed HttpOnly session cookie.
    The raw passcode is never stored or transmitted in subsequent requests.
    """
    configured_key = settings.FRONTEND_ACCESS_PASSCODE or settings.FRONTEND_API_KEY
    if not configured_key or not configured_key.strip():
        # No passcode configured on backend; issue session freely
        token = create_signed_session_token()
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            max_age=SESSION_TTL_SECONDS,
            httponly=True,
            samesite="lax",
            secure=settings.ENVIRONMENT.lower() == "production",
            path="/",
        )
        return {"status": "authenticated", "authenticated": True}

    if not hmac.compare_digest(payload.passcode.encode("utf-8"), configured_key.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Passcode. Please check and try again.",
        )

    token = create_signed_session_token()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT.lower() == "production",
        path="/",
    )
    return {"status": "authenticated", "authenticated": True}


@auth_router.post("/logout", summary="Clear session cookie")
async def logout_endpoint(response: Response):
    """Clears the HttpOnly session cookie."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "logged_out"}


@auth_router.get("/verify", dependencies=[Depends(verify_frontend_api_key)], summary="Verify session validity")
async def verify_endpoint():
    """Returns 200 OK if the current session or header is valid."""
    return {"status": "authenticated", "valid": True}
