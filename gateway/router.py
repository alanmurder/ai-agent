"""Gateway Router - Route messages to Agent."""

import asyncio
from datetime import datetime
from typing import Any, Optional
import uuid

from gateway.types import Message, Session, ChannelType
from core.agent.engine import AgentEngine, AgentConfig
from core.agent.types import AgentInput, AgentOutput
from gateway.session import SessionManager
from core.logging import get_logger, LogContext
from config import get_settings

logger = get_logger("gateway.router")


class GatewayRouter:
    """Route messages from channels to Agent engine."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session_manager = SessionManager()
        self.agent_engine: Optional[AgentEngine] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize gateway router."""
        # Initialize agent engine
        config = AgentConfig(
            model_provider=self.settings.model.primary,
            max_iterations=10,
        )
        self.agent_engine = AgentEngine(config)

        self._initialized = True

        logger.info("gateway_router_initialized")

    async def route_message(self, message: Message) -> AgentOutput:
        """Route a message to the Agent."""
        if not self._initialized:
            await self.initialize()

        # Get or create session
        session = await self.session_manager.get_or_create(
            user_id=message.user_id,
            channel=message.channel,
        )

        # Add message to session history
        session.add_message("user", message.content)

        # Create Agent input
        input = AgentInput(
            content=message.content,
            session_id=session.id,
            user_id=message.user_id,
            metadata={
                "channel": message.channel.value,
                "message_id": message.id,
            },
        )

        # Run Agent
        with LogContext(
            user_id=message.user_id,
            session_id=session.id,
            channel=message.channel.value,
        ):
            output = await self.agent_engine.run(input)

        # Add response to session
        session.add_message("assistant", output.content)

        # Persist session
        await self.session_manager.persist(session)

        logger.info(
            "message_routed",
            user_id=message.user_id,
            session_id=session.id,
            input_length=len(message.content),
            output_length=len(output.content),
        )

        return output

    async def stream_message(
        self,
        message: Message,
    ) -> Any:
        """Stream message response."""
        if not self._initialized:
            await self.initialize()

        session = await self.session_manager.get_or_create(
            user_id=message.user_id,
            channel=message.channel,
        )

        input = AgentInput(
            content=message.content,
            session_id=session.id,
            user_id=message.user_id,
        )

        return self.agent_engine.stream(input)

    async def health_check(self) -> dict[str, Any]:
        """Check gateway health."""
        return {
            "status": "healthy" if self._initialized else "initializing",
            "agent_engine": await self.agent_engine.health_check() if self.agent_engine else None,
            "active_sessions": self.session_manager.get_active_count(),
            "timestamp": datetime.now().isoformat(),
        }