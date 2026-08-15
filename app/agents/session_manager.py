"""
Multi-turn Conversation & Session State Manager for Frontend Clients.
Supports in-memory tracking with automatic TTL expiration.
Can be easily swapped with Redis or Google Cloud Firestore for horizontal scale.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # 'user' | 'model' | 'system'
    content: str
    a2ui: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=time.time)


class Session(BaseModel):
    session_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    last_active: float = Field(default_factory=time.time)

    def add_message(self, role: str, content: str, a2ui: Optional[Dict[str, Any]] = None):
        self.messages.append(ChatMessage(role=role, content=content, a2ui=a2ui))
        self.last_active = time.time()


class SessionManager:
    def __init__(self, ttl_seconds: int = 86400):  # Default 24h TTL
        self._sessions: Dict[str, Session] = {}
        self.ttl_seconds = ttl_seconds

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        self._cleanup_expired()
        if not session_id or session_id not in self._sessions:
            new_id = session_id or str(uuid.uuid4())
            session = Session(session_id=new_id)
            self._sessions[new_id] = session
            return session

        session = self._sessions[session_id]
        session.last_active = time.time()
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        self._cleanup_expired()
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _cleanup_expired(self):
        now = time.time()
        expired_ids = [
            sid for sid, sess in self._sessions.items()
            if (now - sess.last_active) > self.ttl_seconds
        ]
        for sid in expired_ids:
            self._sessions.pop(sid, None)


session_manager = SessionManager()
