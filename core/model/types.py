"""Model routing types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    api_base: str
    model_id: str
    context_window: int = 4096
    supports_tools: bool = True
    cost_tier: str = "medium"  # low, medium, high
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    extra_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Response from model call."""
    content: str
    model_used: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tokens_used: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelCallStats:
    """Statistics for model calls."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_latency_ms: int = 0
    model_usage: dict[str, int] = field(default_factory=dict)  # model -> count
    failure_by_model: dict[str, int] = field(default_factory=dict)


# Predefined model configurations (Chinese models first)
PREDEFINED_MODELS = {
    "deepseek": ModelConfig(
        name="DeepSeek-V3",
        api_base="https://api.deepseek.com",
        model_id="deepseek-chat",
        context_window=64000,
        supports_tools=True,
        cost_tier="low",
    ),
    "zhipu": ModelConfig(
        name="GLM-4",
        api_base="https://open.bigmodel.cn",
        model_id="glm-4",
        context_window=128000,
        supports_tools=True,
        cost_tier="medium",
    ),
    "qwen": ModelConfig(
        name="Qwen-Max",
        api_base="https://dashscope.aliyuncs.com",
        model_id="qwen-max",
        context_window=32000,
        supports_tools=True,
        cost_tier="medium",
    ),
    "baidu": ModelConfig(
        name="ERNIE-4.0",
        api_base="https://aip.baidubce.com",
        model_id="ernie-4.0-8k",
        context_window=8000,
        supports_tools=True,
        cost_tier="medium",
    ),
    "openai": ModelConfig(
        name="GPT-4",
        api_base="https://api.openai.com",
        model_id="gpt-4-turbo",
        context_window=128000,
        supports_tools=True,
        cost_tier="high",
    ),
    "anthropic": ModelConfig(
        name="Claude-3",
        api_base="https://api.anthropic.com",
        model_id="claude-3-opus",
        context_window=200000,
        supports_tools=True,
        cost_tier="high",
    ),
}