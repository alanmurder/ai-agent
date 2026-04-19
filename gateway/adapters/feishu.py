"""Feishu (Lark) Adapter."""

import httpx
from datetime import datetime
from typing import Any, List, Optional
import time

from gateway.adapters.base import MessageAdapter
from gateway.types import Message, ChannelType
from core.logging import get_logger
from config import get_settings

logger = get_logger("adapter.feishu")


class FeishuAdapter(MessageAdapter):
    """Feishu (Lark) message adapter."""

    channel = ChannelType.FEISHU

    def __init__(self) -> None:
        self.settings = get_settings()
        self.app_id: Optional[str] = None
        self.app_secret: Optional[str] = None
        self.tenant_access_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """Connect to Feishu API."""
        adapter_config = self.settings.gateway.adapters.get("feishu", {})

        self.app_id = adapter_config.get("app_id")
        self.app_secret = adapter_config.get("app_secret")

        if not all([self.app_id, self.app_secret]):
            logger.warning("feishu_config_missing")
            return False

        # Get tenant access token
        await self._refresh_access_token()

        self._client = httpx.AsyncClient(timeout=30)

        logger.info("feishu_connected", app_id=self.app_id)

        return True

    async def _refresh_access_token(self) -> None:
        """Refresh Feishu tenant access token."""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            data = response.json()

            if data.get("code") == 0:
                self.tenant_access_token = data.get("tenant_access_token")
                logger.info("feishu_token_refreshed")
            else:
                logger.error(
                    "feishu_token_failed",
                    error=data.get("msg"),
                )

    async def receive(self) -> List[Message]:
        """Receive messages from Feishu."""
        # Feishu uses webhook/callback
        messages = []

        return messages

    async def send(self, message: Message) -> bool:
        """Send message to Feishu."""
        if not self.tenant_access_token or not self._client:
            return False

        url = "https://open.feishu.cn/open-apis/im/v1/messages"

        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json",
        }

        # Get receive_id_type from metadata or default to user
        receive_id_type = message.metadata.get("receive_id_type", "open_id")

        payload = {
            "receive_id_type": receive_id_type,
            "receive_id": message.user_id,
            "msg_type": "text",
            "content": {
                "text": message.content,
            },
        }

        try:
            response = await self._client.post(
                url,
                json=payload,
                headers=headers,
            )

            data = response.json()

            if data.get("code") == 0:
                logger.info(
                    "feishu_message_sent",
                    user_id=message.user_id,
                )
                return True

            else:
                logger.error(
                    "feishu_send_failed",
                    error=data.get("msg"),
                )

                # Token might be expired
                if data.get("code") == 99991663:
                    await self._refresh_access_token()

                return False

        except Exception as e:
            logger.error("feishu_send_error", error=str(e))
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Feishu."""
        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("feishu_disconnected")
        return True

    def _extract_id(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("message_id", "")
        return ""

    def _extract_user_id(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("sender", {}).get("sender_id", {}).get("open_id", "")
        return ""

    def _extract_content(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            content = raw_message.get("content", "")
            if isinstance(content, str):
                import json
                try:
                    content_dict = json.loads(content)
                    return content_dict.get("text", "")
                except json.JSONDecodeError:
                    return content
        return ""

    def _extract_metadata(self, raw_message: Any) -> dict[str, Any]:
        if isinstance(raw_message, dict):
            return {
                "msg_type": raw_message.get("msg_type", ""),
                "chat_id": raw_message.get("chat_id", ""),
                "create_time": raw_message.get("create_time", ""),
            }
        return {}

    async def handle_webhook(self, data: dict[str, Any]) -> List[Message]:
        """Handle incoming webhook data."""
        messages = []

        # Parse Feishu callback data
        event = data.get("event", {})

        if event.get("type") == "im.message.receive_v1":
            message_data = event.get("message", {})

            message = Message(
                id=message_data.get("message_id", ""),
                user_id=event.get("sender", {}).get("sender_id", {}).get("open_id", ""),
                content=self._extract_content(message_data),
                channel=ChannelType.FEISHU,
                metadata={
                    "msg_type": message_data.get("msg_type", ""),
                    "chat_id": message_data.get("chat_id", ""),
                },
            )
            messages.append(message)

        return messages