"""Audit Logger - Security audit trail."""

from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from pathlib import Path

from core.logging import get_logger
from core.metrics import get_metrics, MetricNames
from config import get_settings

logger = get_logger("security.audit")
metrics = get_metrics()


class AuditEventType(Enum):
    """Audit event types."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_GENERATED = "token_generated"
    TOKEN_REVOKED = "token_revoked"
    AUTH_FAILED = "auth_failed"

    # Tool execution
    TOOL_CALL = "tool_call"
    TOOL_SUCCESS = "tool_success"
    TOOL_ERROR = "tool_error"
    TOOL_DENIED = "tool_denied"

    # Evolution
    SKILL_CREATED = "skill_created"
    SKILL_UPDATED = "skill_updated"
    SKILL_DELETED = "skill_deleted"
    EVOLUTION_EVENT = "evolution_event"
    AUTONOMOUS_CODE_GENERATED = "autonomous_code_generated"

    # Data access
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # Admin
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"


@dataclass
class AuditEvent:
    """Audit event record."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType
    user_id: str = ""
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    success: bool = True
    error_message: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """Security audit logger."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._events: list[AuditEvent] = []
        self._audit_file: Optional[Path] = None
        self._max_events = 10000  # Keep last 10k events in memory
        self._initialized = False

    def initialize(self) -> None:
        """Initialize audit logger."""
        audit_dir = Path(self.settings.memory.file_store.path).expanduser() / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)

        self._audit_file = audit_dir / f"audit-{datetime.now().strftime('%Y-%m-%d')}.log"
        self._initialized = True

        logger.info("audit_logger_initialized", path=str(self._audit_file))

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        session_id: str = "",
        details: Optional[dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> AuditEvent:
        """Log audit event."""
        if not self._initialized:
            self.initialize()

        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            details=details or {},
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Add to memory
        self._events.append(event)

        # Trim if too many
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        # Write to file
        self._write_event(event)

        # Log
        logger.info(
            "audit_event",
            event_type=event_type.value,
            user_id=user_id,
            success=success,
        )

        # Metrics
        metrics.increment(f"audit_{event_type.value}")

        return event

    def log_tool_execution(
        self,
        user_id: str,
        tool_name: str,
        params: dict[str, Any],
        result: dict[str, Any],
        success: bool,
        execution_time_ms: int,
        session_id: str = "",
    ) -> AuditEvent:
        """Log tool execution."""
        event_type = AuditEventType.TOOL_SUCCESS if success else AuditEventType.TOOL_ERROR

        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            details={
                "tool_name": tool_name,
                "params": params,
                "result_summary": str(result)[:500],  # Truncate large results
                "execution_time_ms": execution_time_ms,
            },
            success=success,
            error_message=result.get("error") if not success else None,
        )

    def log_permission_denied(
        self,
        user_id: str,
        tool_name: str,
        required_permission: str,
        session_id: str = "",
    ) -> AuditEvent:
        """Log permission denied event."""
        return self.log_event(
            event_type=AuditEventType.TOOL_DENIED,
            user_id=user_id,
            session_id=session_id,
            details={
                "tool_name": tool_name,
                "required_permission": required_permission,
            },
            success=False,
            error_message=f"Permission denied: {required_permission}",
        )

    def log_evolution_event(
        self,
        user_id: str,
        event_type: AuditEventType,
        skill_name: str,
        details: dict[str, Any],
    ) -> AuditEvent:
        """Log evolution event."""
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            details={
                "skill_name": skill_name,
                **details,
            },
        )

    def log_data_access(
        self,
        user_id: str,
        access_type: AuditEventType,
        resource_type: str,
        resource_id: str,
        success: bool = True,
    ) -> AuditEvent:
        """Log data access."""
        return self.log_event(
            event_type=access_type,
            user_id=user_id,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
            success=success,
        )

    def _write_event(self, event: AuditEvent) -> None:
        """Write event to audit file."""
        if not self._audit_file:
            return

        event_dict = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "timestamp": event.timestamp.isoformat(),
            "success": event.success,
            "error_message": event.error_message,
            "details": event.details,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
        }

        try:
            with open(self._audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            logger.error("audit_write_error", error=str(e))

    def get_user_events(
        self,
        user_id: str,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get events for a user."""
        events = [
            e for e in self._events
            if e.user_id == user_id
        ]

        return events[-limit:]

    def get_events_by_type(
        self,
        event_type: AuditEventType,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get events by type."""
        events = [
            e for e in self._events
            if e.event_type == event_type
        ]

        return events[-limit:]

    def search_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Search audit events."""
        events = self._events

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        if success_only is not None:
            events = [e for e in events if e.success == success_only]

        return events[-limit:]

    def generate_report(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """Generate audit report."""
        events = self.search_events(
            start_time=start_time,
            end_time=end_time,
        )

        # Summary stats
        event_counts: dict[str, int] = {}
        user_activity: dict[str, int] = {}
        success_rate = 0

        for event in events:
            event_counts[event.event_type.value] = event_counts.get(event.event_type.value, 0) + 1
            user_activity[event.user_id] = user_activity.get(event.user_id, 0) + 1

        if events:
            success_rate = sum(1 for e in events if e.success) / len(events) * 100

        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "total_events": len(events),
            "success_rate": round(success_rate, 2),
            "event_counts": event_counts,
            "top_users": sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10],
            "failed_events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type.value,
                    "user_id": e.user_id,
                    "error": e.error_message,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in events
                if not e.success
            ][-50:],
        }


# Global audit logger
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = AuditLogger()
        _audit_logger.initialize()

    return _audit_logger