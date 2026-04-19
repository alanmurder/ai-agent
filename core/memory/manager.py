"""Memory Manager - Manage agent memory systems."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.memory.types import MemoryContext, MemoryEntry, MemoryType, ExtractedItem
from core.logging import get_logger
from core.metrics import get_metrics, MetricNames
from config import get_settings

logger = get_logger("memory.manager")
metrics = get_metrics()


class MemoryManager:
    """Manage agent memory across different types."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._file_store: Optional[FileMemoryStore] = None
        self._ready = False

    def initialize(self) -> None:
        """Initialize memory storage."""
        file_path = self.settings.memory.file_store.path
        self._file_store = FileMemoryStore(file_path)
        self._ready = True
        logger.info("memory_manager_initialized", path=file_path)

    def is_ready(self) -> bool:
        """Check if memory manager is ready."""
        return self._ready

    async def retrieve_context(
        self,
        query: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Retrieve relevant context from memory."""
        metrics.increment(MetricNames.MEMORY_READ_COUNT)

        context: dict[str, Any] = {}

        if not self._ready:
            self.initialize()

        # Load core memory from MEMORY.md
        context["core_memory"] = self._file_store.read_memory_md(user_id)

        # Load user preferences from SOUL.md
        context["user_preferences"] = self._file_store.read_soul_md(user_id)

        # Load current session context (placeholder for MVP)
        context["current_session"] = []

        metrics.record(MetricNames.MEMORY_RETRIEVE_TIME_MS, 0)

        return context

    async def persist_session(
        self,
        user_id: str,
        session_id: str,
        conversation: list[dict[str, str]],
    ) -> None:
        """Persist session conversation."""
        metrics.increment(MetricNames.MEMORY_WRITE_COUNT)

        if not self._ready:
            self.initialize()

        # Write to daily log
        self._file_store.write_daily_log(
            user_id=user_id,
            session_id=session_id,
            content=conversation,
        )

        logger.info(
            "session_persisted",
            user_id=user_id,
            session_id=session_id,
            messages=len(conversation),
        )

    async def update_memory(
        self,
        user_id: str,
        key: str,
        value: Any,
        type: MemoryType = MemoryType.LONG_TERM,
    ) -> None:
        """Update a specific memory entry."""
        if type == MemoryType.LONG_TERM:
            self._file_store.update_memory_md(user_id, key, value)
        elif type == MemoryType.SHORT_TERM:
            # Store in session context (placeholder)
            pass

        metrics.increment(MetricNames.MEMORY_WRITE_COUNT)

    async def analyze_for_extraction(
        self,
        conversation: list[dict[str, str]],
    ) -> list[ExtractedItem]:
        """Analyze conversation for memory extraction (Level 1 evolution)."""
        # Placeholder for MVP - use simple heuristics
        extracted: list[ExtractedItem] = []

        for message in conversation:
            content = message.get("content", "")

            # Simple pattern matching for preferences
            if "我喜欢" in content or "I prefer" in content or "I like" in content:
                extracted.append(ExtractedItem(
                    type="preference",
                    content=content,
                    confidence=0.8,
                ))

            elif "我的名字" in content or "my name is" in content.lower():
                extracted.append(ExtractedItem(
                    type="fact",
                    content=content,
                    confidence=0.9,
                ))

        return extracted


class FileMemoryStore:
    """File-based memory storage (Markdown format)."""

    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path).expanduser()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure memory directories exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "memory").mkdir(exist_ok=True)
        (self.base_path / "memory" / "sessions").mkdir(exist_ok=True)

    def _get_user_path(self, user_id: str) -> Path:
        """Get path for user workspace."""
        user_path = self.base_path / "users" / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path

    def read_soul_md(self, user_id: str) -> str:
        """Read SOUL.md for user."""
        user_path = self._get_user_path(user_id)
        soul_path = user_path / "SOUL.md"

        if not soul_path.exists():
            # Create default SOUL.md
            self._create_default_soul_md(soul_path)

        return soul_path.read_text(encoding="utf-8")

    def read_memory_md(self, user_id: str) -> str:
        """Read MEMORY.md for user."""
        user_path = self._get_user_path(user_id)
        memory_path = user_path / "MEMORY.md"

        if not memory_path.exists():
            # Create default MEMORY.md
            self._create_default_memory_md(memory_path)

        return memory_path.read_text(encoding="utf-8")

    def update_memory_md(
        self,
        user_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Update MEMORY.md with new entry."""
        user_path = self._get_user_path(user_id)
        memory_path = user_path / "MEMORY.md"

        content = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

        # Add new entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_entry = f"\n- [{timestamp}] {key}: {value}\n"

        content += new_entry
        memory_path.write_text(content, encoding="utf-8")

    def write_daily_log(
        self,
        user_id: str,
        session_id: str,
        content: list[dict[str, str]],
    ) -> None:
        """Write daily log file."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = self.base_path / "memory" / f"{today}.md"

        # Append to daily log
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Session {session_id}\n\n")

            for msg in content:
                role = msg.get("role", "unknown")
                text = msg.get("content", "")
                f.write(f"**{role}**: {text}\n\n")

    def _create_default_soul_md(self, path: Path) -> None:
        """Create default SOUL.md template."""
        content = """# SOUL.md

## Personality
- Friendly and helpful assistant
- Concise and clear responses
- Patient and understanding

## Preferences
- Format responses with clear structure
- Use code blocks for technical content
- Summarize long explanations

## Tone
- Professional yet approachable
- Avoid unnecessary jargon
- Be proactive in offering suggestions

---
Last updated: {datetime.now().strftime("%Y-%m-%d")}
"""
        path.write_text(content, encoding="utf-8")

    def _create_default_memory_md(self, path: Path) -> None:
        """Create default MEMORY.md template."""
        content = """# MEMORY.md

## User Information
- Name: Unknown
- Language: zh-CN

## Important Facts
- (No facts recorded yet)

## Interaction History
- (First interaction on {datetime.now().strftime("%Y-%m-%d")})

---
Last updated: {datetime.now().strftime("%Y-%m-%d")}
"""
        path.write_text(content, encoding="utf-8")