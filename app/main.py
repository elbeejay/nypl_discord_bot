import os
import logging
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.agents.orchestrator import orchestrator_agent
from app.api.v1.router import api_v1_router
from app.discord.router import router as discord_router, extract_query_from_options
from app.security.rate_limiter import RateLimitMiddleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def is_production() -> bool:
    return settings.ENVIRONMENT.lower() == "production"


# In production: disable OpenAPI / Swagger documentation endpoints for security
app = FastAPI(
    title="NYC & NYPL Multi-Channel Agent Backend",
    version="0.2.0",
    description="Multi-channel AI Agent Backend supporting Discord bots, Web & Mobile Frontends, and A2UI dynamic visual data widgets.",
    docs_url=None if is_production() else "/docs",
    redoc_url=None if is_production() else "/redoc",
    openapi_url=None if is_production() else "/openapi.json",
)

# ----------------------------------------------------
# Security Layer 1: In-Memory IP Rate Limiting
# ----------------------------------------------------
app.add_middleware(RateLimitMiddleware)

# ----------------------------------------------------
# Security Layer 2: CORS Configuration
# In production, the SPA is served same-origin and Discord uses server-to-server
# webhooks (not browser requests), so wildcard CORS is never needed.
# ----------------------------------------------------
cors_origins = settings.CORS_ORIGINS
if is_production() and "*" in cors_origins:
    logger.warning(
        "Wildcard CORS origin ('*') is not allowed in production. "
        "Restricting to same-origin only. Set CORS_ORIGINS explicitly to allow specific external origins."
    )
    cors_origins = []

has_wildcard_cors = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not has_wildcard_cors,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# ----------------------------------------------------
# Route Inclusions: APIs & Webhooks
# ----------------------------------------------------
# 1. API v1 for Frontend Clients (Protected via FRONTEND_API_KEY when configured)
app.include_router(api_v1_router)

# 2. Discord Interaction Router (Protected via Ed25519 Cryptographic Signatures)
app.include_router(discord_router)
app.include_router(discord_router, prefix="/discord")


# ----------------------------------------------------
# Health & Diagnostic Endpoints
# ----------------------------------------------------

@app.get("/health")
async def health_check():
    """
    Bare-minimum static health check endpoint required by GCP Cloud Run load balancers.
    Touches zero AI models and consumes zero tokens.
    """
    return {"status": "ok"}


@app.get("/api/config")
async def get_frontend_config():
    """
    Provides public client bootstrap configuration.
    Sensitive keys are managed strictly server-side.
    """
    return {
        "environment": settings.ENVIRONMENT,
        "features": {
            "a2ui_visualizations": True,
            "sse_streaming": True,
        },
    }


@app.get("/api/status")
async def api_status():
    """Returns backend status and feature capabilities."""
    if is_production():
        return {
            "status": "healthy",
            "service": "nypl_discord_bot",
        }

    return {
        "status": "healthy",
        "service": "nypl_discord_bot",
        "version": "0.2.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "discord_bot": True,
            "frontend_api_v1": True,
            "a2ui_visualizations": True,
            "sse_streaming": True,
            "api_key_auth": bool(settings.FRONTEND_API_KEY),
            "rate_limiting": True,
        },
        "models": {
            "orchestrator": settings.ORCHESTRATOR_MODEL,
            "expert": settings.EXPERT_MODEL,
        }
    }


class LegacyChatRequest(BaseModel):
    query: str
    command: Optional[str] = "ask"


@app.post("/chat")
async def legacy_local_chat_test(request: Optional[LegacyChatRequest] = None):
    """
    Direct /chat testing endpoint (development only).
    Disabled in production in favor of secured /api/v1/chat.
    """
    if is_production():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )

    if not request or not request.query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'query' field in request body",
        )

    logger.info(f"Direct /chat query: '{request.query}' (command: {request.command})")
    response_text = await orchestrator_agent.handle_user_query(
        request.query,
        command_name=request.command or "ask"
    )
    return {
        "query": request.query,
        "command": request.command,
        "response": response_text
    }


# ----------------------------------------------------
# Static Frontend Serving (SPA & A2UI Web App)
# ----------------------------------------------------
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    logger.info(f"Mounting compiled frontend SPA from {FRONTEND_DIST}")
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(request: Request, full_path: str = ""):
        accept_header = request.headers.get("accept", "")
        
        # Root path handling:
        # If browser navigation (text/html) -> serve frontend index.html
        # If API diagnostic / programmatic call without text/html -> return JSON status
        if full_path in ("", "/"):
            if "text/html" in accept_header:
                index_file = FRONTEND_DIST / "index.html"
                if index_file.is_file():
                    return FileResponse(str(index_file))
            return await api_status()

        if full_path:
            potential_file = (FRONTEND_DIST / full_path).resolve()
            # Ensure resolved path does not escape the frontend/dist directory
            try:
                if potential_file.is_file() and potential_file.is_relative_to(FRONTEND_DIST.resolve()):
                    return FileResponse(str(potential_file))
            except (ValueError, RuntimeError):
                pass
        
        index_file = FRONTEND_DIST / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file))
            
        return await api_status()
else:
    @app.get("/")
    async def root_fallback():
        return await api_status()
