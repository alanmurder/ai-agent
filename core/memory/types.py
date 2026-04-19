"""Memory system types."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


class MemoryType(Enum):
    """Memory type classification."""
    LONG_TERM = "long_term"      # Permanent: preferences, habits
    MEDIUM_TERM = "medium_term"  # 30 days: summaries, history
    SHORT_TERM = "short_term"    # Session: context
    WORKING = "working"          # Task: current execution


@dataclass
class MemoryEntry:
    """Single memory entry."""
    id: str
    content: str
    type: MemoryType
    user_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    embedding: Optional[list[float]] = None


@dataclass
class MemoryContext:
    """Context from memory retrieval."""
    core_memory: str = ""           # From MEMORY.md
    relevant_history: list[MemoryEntry] = field(default_factory=list)
    current_session: list[dict[str, str]] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedItem:
    """Item extracted from conversation for memory."""
    type: str  # preference, fact, pattern
    content: str
    confidence: float = 0.8
    metadata: dict[str, Any] = field(default_factory=dict)