import json
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.config import settings
from app.schemas.a2ui import FrontendChatRequest, FrontendChatResponse
from app.agents.orchestrator import orchestrator_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=FrontendChatResponse, summary="Send chat query (REST)")
async def chat_endpoint(request: FrontendChatRequest):
    """
    Standard REST endpoint for frontend clients.
    Returns agent text response, multi-turn session ID, and optional A2UI visual components.
    """
    try:
        return await orchestrator_agent.handle_frontend_query(request)
    except Exception as e:
        logger.error(f"Error executing agent query: {e}", exc_info=True)
        safe_detail = (
            "An error occurred while executing the query. Please try again."
            if settings.ENVIRONMENT.lower() == "production"
            else f"Error executing agent query: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=safe_detail
        )


@router.post("/chat/stream", summary="Stream chat query via Server-Sent Events (SSE)")
async def chat_stream_endpoint(request: FrontendChatRequest):
    """
    SSE Streaming endpoint for real-time frontend user interfaces.
    Emits events:
      - 'status': Agent task / delegation progress
      - 'token': Incremental text chunks
      - 'a2ui': Dynamic data visualization components (charts, maps, photo galleries)
      - 'done': Stream completion with session ID
    """
    async def sse_event_generator():
        async for event in orchestrator_agent.stream_frontend_query(request):
            event_name = event.get("event", "message")
            event_data = json.dumps(event.get("data", {}))
            yield f"event: {event_name}\ndata: {event_data}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
