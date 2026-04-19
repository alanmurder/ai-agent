"""WeChat Enterprise Adapter."""

import httpx
from datetime import datetime
from typing import Any, List, Optional

from gateway.adapters.base import MessageAdapter
from gateway.types import Message, ChannelType
from core.logging import get_logger
from config import get_settings

logger = get_logger("adapter.wechat")


class WeChatAdapter(MessageAdapter):
    """WeChat Enterprise message adapter."""

    channel = ChannelType.WECHAT

    def __init__(self) -> None:
        self.settings = get_settings()
        self.corp_id: Optional[str] = None
        self.agent_id: Optional[str] = None
        self.secret: Optional[str] None
        self.access_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """Connect to WeChat Enterprise API."""
        adapter_config = self.settings.gateway.adapters.get("wechat", {})

        self.corp_id = adapter_config.get("corp_id")
        self.agent_id = adapter_config.get("agent_id")
        self.secret = adapter_config.get("secret")

        if not all([self.corp_id, self.agent_id, self.secret]):
            logger.warning("wechat_config_missing")
            return False

        # Get access token
        await self._refresh_access_token()

        self._client = httpx.AsyncClient(timeout=30)

        logger.info(
            "wechat_connected",
            corp_id=self.corp_id,
            agent_id=self.agent_id,
        )

        return True

    async def _refresh_access_token(self) -> None:
        """Refresh WeChat access token."""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"

        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            data = response.json()

            if data.get("errcode") == 0:
                self.access_token = data.get("access_token")
                logger.info("wechat_token_refreshed")
            else:
                logger.error(
                    "wechat_token_failed",
                    error=data.get("errmsg"),
                )

    async def receive(self) -> List[Message]:
        """Receive messages from WeChat."""
        # WeChat uses webhook/callback for receiving messages
        # This method would be called by the webhook handler
        messages = []

        return messages

    async def send(self, message: Message) -> bool:
        """Send message to WeChat."""
        if not self.access_token or not self._client:
            return False

        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send"

        payload = {
            "touser": message.user_id,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {
                "content": message.content,
            },
            "safe": 0,
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            response = await self._client.post(
                url,
                json=payload,
                headers=headers,
            )

            data = response.json()

            if data.get("errcode") == 0:
                logger.info(
                    "wechat_message_sent",
                    user_id=message.user_id,
                )
                return True

            else:
                logger.error(
                    "wechat_send_failed",
                    error=data.get("errmsg"),
                )

                # Token might be expired
                if data.get("errcode") == 40014:
                    await self._refresh_access_token()

                return False

        except Exception as e:
            logger.error("wechat_send_error", error=str(e))
            return False

    async def disconnect(self) -> bool:
        """Disconnect from WeChat."""
        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("wechat_disconnected")
        return True

    def _extract_id(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("MsgId", "")
        return ""

    def _extract_user_id(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("FromUserName", "")
        return ""

    def _extract_content(self, raw_message: Any) -> str:
        if isinstance(raw_message, dict):
            return raw_message.get("Content", "")
        return ""

    def _extract_metadata(self, raw_message: Any) -> dict[str, Any]:
        if isinstance(raw_message, dict):
            return {
                "msg_type": raw_message.get("MsgType", ""),
                "agent_id": raw_message.get("AgentID", ""),
            }
        return {}

    async def handle_webhook(self, data: dict[str, Any]) -> List[Message]:
        """Handle incoming webhook data."""
        messages = []

        # Parse WeChat callback data
        if " messages" in data:
            for msg_data in data.get("messages", []):
                message = self.normalize(msg_data)
                messages.append(message)

        return messages