"""Agent input/output types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class AgentInput:
    """Input for the Agent engine."""
    content: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentOutput:
    """Output from the Agent engine."""
    content: str
    session_id: str
    user_id: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    model_used: Optional[str] = None
    tokens_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionContext:
    """Context for executing agent tasks."""
    session_id: str
    user_id: str
    input: AgentInput
    memory_context: dict[str, Any] = field(default_factory=dict)
    available_tools: list[str] = field(default_factory=list)
    available_skills: list[str] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 10


@dataclass
class Conversation:
    """Conversation history."""
    messages: list[dict[str, str]] = field(default_factory=list)
    user_id: str = ""
    session_id: str = ""

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def to_prompt_messages(self) -> list[dict[str, str]]:
        return self.messages.copy()