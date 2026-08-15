import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
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

is_production = settings.ENVIRONMENT.lower() == "production"

# In production: disable OpenAPI / Swagger documentation endpoints for security
app = FastAPI(
    title="NYC & NYPL Multi-Channel Agent Backend",
    version="0.2.0",
    description="Multi-channel AI Agent Backend supporting Discord bots, Web & Mobile Frontends, and A2UI dynamic visual data widgets.",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

# ----------------------------------------------------
# Security Layer 1: In-Memory IP Rate Limiting
# ----------------------------------------------------
app.add_middleware(RateLimitMiddleware)

# ----------------------------------------------------
# Security Layer 2: CORS Configuration
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Route Inclusions
# ----------------------------------------------------
# 1. API v1 for Frontend Clients (Protected via FRONTEND_API_KEY when configured)
app.include_router(api_v1_router)

# 2. Discord Interaction Router (Protected via Ed25519 Cryptographic Signatures)
app.include_router(discord_router)
app.include_router(discord_router, prefix="/discord")


# ----------------------------------------------------
# Root & Health Endpoints
# ----------------------------------------------------

class LegacyChatRequest(BaseModel):
    query: str
    command: Optional[str] = "ask"


@app.get("/")
async def root():
    # In production, redact internal architecture details
    if is_production:
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


@app.get("/health")
async def health_check():
    """
    Bare-minimum static health check endpoint required by GCP Cloud Run load balancers.
    Touches zero AI models and consumes zero tokens.
    """
    return {"status": "ok"}


@app.post("/chat")
async def legacy_local_chat_test(request: LegacyChatRequest):
    """
    Direct /chat testing endpoint (development only).
    Disabled in production in favor of secured /api/v1/chat.
    """
    if is_production:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legacy /chat endpoint is disabled in production. Use /api/v1/chat.",
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
