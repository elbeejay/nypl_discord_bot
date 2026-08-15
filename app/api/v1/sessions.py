"""
Frontend Conversation Session Management Endpoints.
"""

from fastapi import APIRouter, HTTPException, status
from app.agents.session_manager import session_manager

router = APIRouter()


@router.get("/sessions/{session_id}", summary="Get conversation history for session")
async def get_session_history(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )
    return session


@router.delete("/sessions/{session_id}", summary="Delete / reset conversation session")
async def delete_session(session_id: str):
    deleted = session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already deleted",
        )
    return {"status": "success", "message": f"Session {session_id} deleted."}
