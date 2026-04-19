"""Integration tests for AI Agent."""

import pytest
import asyncio

from core.agent.engine import AgentEngine, AgentConfig
from core.agent.types import AgentInput


@pytest.mark.asyncio
async def test_agent_engine_creation():
    """Test Agent engine can be created."""
    config = AgentConfig(
        model_provider="deepseek",
        max_iterations=5,
    )

    engine = AgentEngine(config)

    assert engine.config.model_provider == "deepseek"
    assert engine.model_router is not None


@pytest.mark.asyncio
async def test_skill_manager_init():
    """Test skill manager initialization."""
    from skills.manager import SkillManager

    manager = SkillManager()

    # Initialize without actual skills directory
    # This tests the structure, not the actual loading
    assert manager._tool_registry is not None


@pytest.mark.asyncio
async def test_memory_manager_init():
    """Test memory manager initialization."""
    from core.memory.manager import MemoryManager

    manager = MemoryManager()
    manager.initialize()

    assert manager.is_ready()


@pytest.mark.asyncio
async def test_gateway_router_init():
    """Test gateway router initialization."""
    from gateway.router import GatewayRouter

    router = GatewayRouter()

    # Test initialization
    await router.initialize()

    assert router._initialized
    assert router.agent_engine is not None

    # Test health check
    health = await router.health_check()

    assert health["status"] == "healthy"


@pytest.mark.asyncio
async def test_session_manager():
    """Test session manager."""
    from gateway.session import SessionManager
    from gateway.types import ChannelType

    manager = SessionManager()

    # Create session
    session = await manager.get_or_create(
        user_id="test_user",
        channel=ChannelType.WEB,
    )

    assert session.user_id == "test_user"
    assert session.channel == ChannelType.WEB

    # Add messages
    session.add_message("user", "Hello")
    session.add_message("assistant", "Hi there!")

    assert len(session.conversation_history) == 2

    # Persist
    await manager.persist(session)

    # Get again
    retrieved = await manager.get(session.id)
    assert retrieved is not None
    assert len(retrieved.conversation_history) == 2