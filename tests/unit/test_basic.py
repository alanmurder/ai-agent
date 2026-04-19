"""Basic tests for AI Agent."""

import pytest
import asyncio

from core.agent.types import AgentInput, AgentOutput
from core.memory.types import MemoryType
from core.model.types import PREDEFINED_MODELS
from core.tools.types import Tool, ToolCall, ToolResult, ToolStatus
from skills.types import SkillCategory, SkillVersion
from gateway.types import ChannelType, MessageType


def test_agent_input_creation():
    """Test AgentInput creation."""
    input = AgentInput(
        content="Hello",
        user_id="test_user",
        session_id="test_session",
    )

    assert input.content == "Hello"
    assert input.user_id == "test_user"
    assert input.session_id == "test_session"


def test_agent_output_creation():
    """Test AgentOutput creation."""
    output = AgentOutput(
        content="Hi there!",
        session_id="test_session",
        user_id="test_user",
        model_used="deepseek",
        tokens_used=100,
    )

    assert output.content == "Hi there!"
    assert output.model_used == "deepseek"


def test_memory_types():
    """Test memory type values."""
    assert MemoryType.LONG_TERM.value == "long_term"
    assert MemoryType.SHORT_TERM.value == "short_term"
    assert MemoryType.WORKING.value == "working"


def test_model_configs():
    """Test predefined model configs."""
    assert "deepseek" in PREDEFINED_MODELS
    assert "zhipu" in PREDEFINED_MODELS
    assert "qwen" in PREDEFINED_MODELS

    deepseek = PREDEFINED_MODELS["deepseek"]
    assert deepseek.name == "DeepSeek-V3"
    assert deepseek.context_window == 64000


def test_tool_types():
    """Test tool types."""
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object"},
    )

    assert tool.name == "test_tool"
    assert tool.timeout == 30

    result = ToolResult.success("call-123", {"output": "done"})
    assert result.status == ToolStatus.SUCCESS

    error_result = ToolResult.error("call-123", "something failed")
    assert error_result.status == ToolStatus.ERROR


def test_skill_types():
    """Test skill types."""
    assert SkillCategory.CODING.value == "coding"
    assert SkillCategory.ECOMMERCE.value == "ecommerce"
    assert SkillVersion.PERSONAL.value == "personal"


def test_gateway_types():
    """Test gateway types."""
    assert ChannelType.WEB.value == "web"
    assert ChannelType.WECHAT.value == "wechat"
    assert MessageType.TEXT.value == "text"

    from gateway.types import Message

    msg = Message.from_web("user-123", "Hello")
    assert msg.user_id == "user-123"
    assert msg.content == "Hello"
    assert msg.channel == ChannelType.WEB


def test_config_loading():
    """Test configuration loading."""
    from config import Settings

    # Create default settings
    settings = Settings()

    assert settings.deploy_mode == "local"
    assert settings.model.primary == "deepseek"


@pytest.mark.asyncio
async def test_tool_executor():
    """Test tool executor."""
    from core.tools.executor import ToolExecutor
    from core.tools.registry import get_registry
    from core.agent.types import ExecutionContext

    registry = get_registry()
    executor = ToolExecutor(registry)

    context = ExecutionContext(
        session_id="test",
        user_id="test_user",
        input=AgentInput(content="test"),
    )

    # Test unknown tool
    call = ToolCall(name="unknown_tool")
    result = await executor.execute(call, context)

    assert result.status == ToolStatus.ERROR
    assert "Unknown tool" in result.error