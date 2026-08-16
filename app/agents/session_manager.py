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


import re

VALID_SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
MAX_SESSIONS = 5000


class SessionManager:
    def __init__(self, ttl_seconds: int = 86400, max_sessions: int = MAX_SESSIONS):  # Default 24h TTL
        self._sessions: Dict[str, Session] = {}
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        self._cleanup_expired()

        # Validate provided session ID format; if invalid or missing, generate a safe UUID
        if session_id and not VALID_SESSION_ID_PATTERN.match(session_id):
            session_id = None

        if not session_id or session_id not in self._sessions:
            # Enforce max sessions bound before inserting new session
            if len(self._sessions) >= self.max_sessions:
                # Evict the oldest active session
                oldest_sid = min(self._sessions.keys(), key=lambda k: self._sessions[k].last_active)
                self._sessions.pop(oldest_sid, None)

            new_id = session_id or str(uuid.uuid4())
            session = Session(session_id=new_id)
            self._sessions[new_id] = session
            return session

        session = self._sessions[session_id]
        session.last_active = time.time()
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        if not session_id or not VALID_SESSION_ID_PATTERN.match(session_id):
            return None
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
