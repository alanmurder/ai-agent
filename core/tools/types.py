"""Tool execution types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class ToolStatus(Enum):
    """Tool execution status."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"


@dataclass
class Tool:
    """Tool definition."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for parameters
    handler: Optional[str] = None  # Handler function path
    permissions: list[str] = field(default_factory=list)
    timeout: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Tool call request."""
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    """Tool execution result."""
    call_id: str
    status: ToolStatus
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def success(cls, call_id: str, output: Any, execution_time_ms: int = 0) -> "ToolResult":
        return cls(
            call_id=call_id,
            status=ToolStatus.SUCCESS,
            output=output,
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def error(cls, call_id: str, error: str, execution_time_ms: int = 0) -> "ToolResult":
        return cls(
            call_id=call_id,
            status=ToolStatus.ERROR,
            error=error,
            execution_time_ms=execution_time_ms,
        )


@dataclass
class ToolDefinition:
    """Full tool definition for model."""
    type: str = "function"
    function: dict[str, Any] = field(default_factory=dict)

    def to_openai_format(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "function": self.function,
        }