"""Base message adapter."""

from abc import ABC, abstractmethod
from typing import Any, List

from gateway.types import Message, ChannelType


class MessageAdapter(ABC):
    """Abstract base class for message adapters."""

    channel: ChannelType

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to message channel."""
        pass

    @abstractmethod
    async def receive(self) -> List[Message]:
        """Receive messages from channel."""
        pass

    @abstractmethod
    async def send(self, message: Message) -> bool:
        """Send message to channel."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from channel."""
        pass

    def normalize(self, raw_message: Any) -> Message:
        """Normalize raw message to standard format."""
        return Message(
            id=self._extract_id(raw_message),
            user_id=self._extract_user_id(raw_message),
            content=self._extract_content(raw_message),
            channel=self.channel,
            metadata=self._extract_metadata(raw_message),
        )

    @abstractmethod
    def _extract_id(self, raw_message: Any) -> str:
        """Extract message ID."""
        pass

    @abstractmethod
    def _extract_user_id(self, raw_message: Any) -> str:
        """Extract user ID."""
        pass

    @abstractmethod
    def _extract_content(self, raw_message: Any) -> str:
        """Extract message content."""
        pass

    @abstractmethod
    def _extract_metadata(self, raw_message: Any) -> dict[str, Any]:
        """Extract metadata."""
        pass