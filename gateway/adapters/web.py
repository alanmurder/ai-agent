"""Web message adapter."""

from typing import Any, List
from datetime import datetime

from gateway.adapters.base import MessageAdapter
from gateway.types import Message, ChannelType


class WebAdapter(MessageAdapter):
    """Web message adapter."""

    channel = ChannelType.WEB

    async def connect(self) -> bool:
        """Web adapter always ready."""
        return True

    async def receive(self) -> List[Message]:
        """Web receives via HTTP/WebSocket, not polling."""
        return []

    async def send(self, message: Message) -> bool:
        """Web sends via HTTP response."""
        return True

    async def disconnect(self) -> bool:
        """Web adapter disconnect."""
        return True

    def _extract_id(self, raw_message: Any) -> str:
        return f"web-{datetime.now().isoformat()}"

    def _extract_user_id(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("user_id", "default")
        return "default"

    def _extract_content(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("content", "")
        return str(raw_message)

    def _extract_metadata(self, raw_message: Any) -> dict[str, Any]:
        return {}