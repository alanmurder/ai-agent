"""Session Manager - Manage user sessions."""

from datetime import datetime, timedelta
from typing import Any, Optional
import uuid

from gateway.types import Session, ChannelType
from core.logging import get_logger

logger = get_logger("gateway.session")


class SessionManager:
    """Manage user sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._session_expire: dict[str, datetime] = {}

    async def get_or_create(
        self,
        user_id: str,
        channel: ChannelType,
        session_id: Optional[str] = None,
    ) -> Session:
        """Get existing session or create new one."""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.last_activity = datetime.now()
            return session

        # Check for active session by user
        for session in self._sessions.values():
            if session.user_id == user_id and session.is_active:
                if datetime.now() - session.last_activity < timedelta(minutes=30):
                    session.last_activity = datetime.now()
                    return session

        # Create new session
        new_session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            channel=channel,
            created_at=datetime.now(),
            last_activity=datetime.now(),
        )

        self._sessions[new_session.id] = new_session
        self._session_expire[new_session.id] = datetime.now() + timedelta(hours=1)

        logger.info(
            "session_created",
            session_id=new_session.id,
            user_id=user_id,
            channel=channel.value,
        )

        return new_session

    async def get(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    async def persist(self, session: Session) -> None:
        """Persist session state."""
        self._sessions[session.id] = session
        self._session_expire[session.id] = datetime.now() + timedelta(hours=1)

        logger.info(
            "session_persisted",
            session_id=session.id,
            user_id=session.user_id,
            messages=len(session.conversation_history),
        )

    async def end(self, session_id: str) -> bool:
        """End a session."""
        if session_id in self._sessions:
            self._sessions[session_id].is_active = False
            del self._session_expire[session_id]

            logger.info("session_ended", session_id=session_id)

            return True

        return False

    def get_active_count(self) -> int:
        """Get count of active sessions."""
        active = 0

        for session_id, expire in self._session_expire.items():
            if datetime.now() < expire:
                active += 1

        return active

    def cleanup_expired(self) -> int:
        """Clean up expired sessions."""
        expired_count = 0
        now = datetime.now()

        for session_id, expire in list(self._session_expire.items()):
            if now >= expire:
                if session_id in self._sessions:
                    self._sessions[session_id].is_active = False
                    del self._sessions[session_id]

                del self._session_expire[session_id]
                expired_count += 1

        if expired_count > 0:
            logger.info("sessions_cleaned", count=expired_count)

        return expired_count