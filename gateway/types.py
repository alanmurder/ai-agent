"""Gateway types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum


class ChannelType(Enum):
    """Message channel types."""
    WEB = "web"
    WECHAT = "wechat"
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    TELEGRAM = "telegram"
    SLACK = "slack"


class MessageType(Enum):
    """Message type classification."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    COMMAND = "command"
    EVENT = "event"


@dataclass
class Message:
    """Standardized message format."""
    id: str
    user_id: str
    content: str
    channel: ChannelType
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None

    @classmethod
    def from_web(cls, user_id: str, content: str) -> "Message":
        return cls(
            id=f"web-{datetime.now().isoformat()}",
            user_id=user_id,
            content=content,
            channel=ChannelType.WEB,
        )


@dataclass
class Session:
    """User session."""
    id: str
    user_id: str
    channel: ChannelType
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append({"role": role, "content": content})
        self.last_activity = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "channel": self.channel.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "conversation_history": self.conversation_history,
            "context": self.context,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            channel=ChannelType(data["channel"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            conversation_history=data.get("conversation_history", []),
            context=data.get("context", {}),
            is_active=data.get("is_active", True),
        )