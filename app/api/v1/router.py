"""
Aggregation Router for API Version 1 (Frontend & External Clients).
"""

from fastapi import APIRouter, Depends
from app.api.v1.auth import auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.a2ui import router as a2ui_router
from app.security.api_auth import verify_frontend_api_key

api_v1_router = APIRouter(prefix="/api/v1")

# Unprotected / self-contained auth endpoints (login, logout, verify)
api_v1_router.include_router(auth_router)

# Protected API subrouters requiring valid session cookie or API key
api_v1_router.include_router(
    chat_router,
    tags=["Chat"],
    dependencies=[Depends(verify_frontend_api_key)],
)
api_v1_router.include_router(
    sessions_router,
    tags=["Sessions"],
    dependencies=[Depends(verify_frontend_api_key)],
)
api_v1_router.include_router(
    a2ui_router,
    tags=["A2UI"],
    dependencies=[Depends(verify_frontend_api_key)],
)

