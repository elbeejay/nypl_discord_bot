"""
Frontend Chat & Streaming Endpoints.
Supports REST responses and Server-Sent Events (SSE) streaming with A2UI dynamic components.
"""

import json
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.schemas.a2ui import FrontendChatRequest, FrontendChatResponse
from app.agents.orchestrator import orchestrator_agent

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing agent query: {str(e)}"
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
