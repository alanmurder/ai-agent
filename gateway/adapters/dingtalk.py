"""DingTalk Adapter."""

import httpx
from datetime import datetime
from typing import Any, List, Optional
import time
import hmac
import hashlib
import base64

from gateway.adapters.base import MessageAdapter
from gateway.types import Message, ChannelType
from core.logging import get_logger
from config import get_settings

logger = get_logger("adapter.dingtalk")


class DingTalkAdapter(MessageAdapter):
    """DingTalk message adapter."""

    channel = ChannelType.DINGTALK

    def __init__(self) -> None:
        self.settings = get_settings()
        self.app_key: Optional[str] = None
        self.app_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """Connect to DingTalk API."""
        adapter_config = self.settings.gateway.adapters.get("dingtalk", {})

        self.app_key = adapter_config.get("app_key")
        self.app_secret = adapter_config.get("app_secret")

        if not all([self.app_key, self.app_secret]):
            logger.warning("dingtalk_config_missing")
            return False

        # Get access token
        await self._refresh_access_token()

        self._client = httpx.AsyncClient(timeout=30)

        logger.info("dingtalk_connected", app_key=self.app_key)

        return True

    async def _refresh_access_token(self) -> None:
        """Refresh DingTalk access token."""
        url = "https://api.dingtalk.com/v1.0/oauth2 accessToken"

        payload = {
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            data = response.json()

            if "accessToken" in data:
                self.access_token = data["accessToken"]
                logger.info("dingtalk_token_refreshed")
            else:
                logger.error(
                    "dingtalk_token_failed",
                    error=data.get("message"),
                )

    async def receive(self) -> List[Message]:
        """Receive messages from DingTalk."""
        # DingTalk uses webhook/callback
        messages = []

        return messages

    async def send(self, message: Message) -> bool:
        """Send message to DingTalk."""
        if not self.access_token or not self._client:
            return False

        url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"

        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json",
        }

        payload = {
            "robotCode": self.app_key,
            "userIds": [message.user_id],
            "msgKey": "sampleText",
            "msgParam": {
                "content": message.content,
            },
        }

        try:
            response = await self._client.post(
                url,
                json=payload,
                headers=headers,
            )

            data = response.json()

            if data.get("success"):
                logger.info(
                    "dingtalk_message_sent",
                    user_id=message.user_id,
                )
                return True

            else:
                logger.error(
                    "dingtalk_send_failed",
                    error=data.get("message"),
                )
                return False

        except Exception as e:
            logger.error("dingtalk_send_error", error=str(e))
            return False

    async def disconnect(self) -> bool:
        """Disconnect from DingTalk."""
        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("dingtalk_disconnected")
        return True

    def _extract_id(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("msgId", "")
        return ""

    def _extract_user_id(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("senderStaffId", "")
        return ""

    def _extract_content(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("content", {}).get("content", "")
        return ""

    def _extract_metadata(self, raw_message: Any) -> dict[str, Any]:
        if isinstance(raw_message, dict):
            return {
                "msg_type": raw_message.get("msgType", ""),
                "conversation_type": raw_message.get("conversationType", ""),
            }
        return {}

    def generate_signature(self, timestamp: int, secret: str) -> str:
        """Generate signature for DingTalk webhook."""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        return base64.b64encode(hmac_code).decode("utf-8")

    async def handle_webhook(self, data: dict[str, Any]) -> List[Message]:
        """Handle incoming webhook data."""
        messages = []

        # Parse DingTalk callback data
        text_content = data.get("text", {})
        if text_content:
            message = Message(
                id=f"dingtalk-{datetime.now().isoformat()}",
                user_id=data.get("senderStaffId", ""),
                content=text_content.get("content", ""),
                channel=ChannelType.DINGTALK,
                metadata={
                    "msg_type": data.get("msgType", ""),
                    "conversation_id": data.get("conversationId", ""),
                },
            )
            messages.append(message)

        return messages