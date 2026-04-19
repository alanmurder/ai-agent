"""Model Router - Multi-model routing with failover."""

import asyncio
import time
from typing import Any, Optional, AsyncIterator
import uuid

from core.model.types import ModelConfig, ModelResponse, PREDEFINED_MODELS
from core.agent.types import ExecutionContext
from core.logging import get_logger, log_model_call
from core.metrics import get_metrics, MetricNames
from config import get_settings

logger = get_logger("model.router")
metrics = get_metrics()


class ModelRouter:
    """Route calls to multiple AI models with failover."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._model_configs: dict[str, ModelConfig] = {}
        self._failure_counts: dict[str, int] = {}
        self._load_model_configs()

    def _load_model_configs(self) -> None:
        """Load model configurations."""
        # Load predefined models
        for name, config in PREDEFINED_MODELS.items():
            self._model_configs[name] = config

    def get_model_priority(self, preferred: Optional[str] = None) -> list[str]:
        """Get model priority list for failover."""
        # Use primary from settings if not specified
        primary = preferred or self.settings.model.primary

        # Start with primary model
        priority = [primary]

        # Add fallback models from settings
        for model in self.settings.model.fallback:
            if model != primary:
                priority.append(model)

        return priority

    async def call(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Call model with failover."""
        models_to_try = self.get_model_priority(model)

        for model_name in models_to_try:
            # Check if model is available
            api_key = self.settings.get_model_api_key(model_name)
            if not api_key:
                logger.warning(f"no_api_key_for_model", model=model_name)
                continue

            try:
                response = await self._call_single_model(
                    model_name=model_name,
                    api_key=api_key,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # Reset failure count on success
                self._failure_counts[model_name] = 0

                metrics.increment(MetricNames.MODEL_CALL_COUNT)
                metrics.record(MetricNames.MODEL_TOKENS_USED, response.tokens_used.get("total", 0))

                return response

            except Exception as e:
                # Record failure
                self._failure_counts[model_name] = self._failure_counts.get(model_name, 0) + 1
                metrics.increment(MetricNames.MODEL_FAILURE_COUNT)

                logger.error(
                    "model_call_failed",
                    model=model_name,
                    error=str(e),
                    failure_count=self._failure_counts[model_name],
                )

                # Try next model
                continue

        # All models failed
        raise RuntimeError("All models failed to respond")

    async def stream(
        self,
        prompt: str,
        context: ExecutionContext,
        model: Optional[str] = None,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Stream response from model."""
        models_to_try = self.get_model_priority(model)

        for model_name in models_to_try:
            api_key = self.settings.get_model_api_key(model_name)
            if not api_key:
                continue

            try:
                # Stream from model (implementation depends on provider)
                async for chunk in self._stream_single_model(
                    model_name=model_name,
                    api_key=api_key,
                    prompt=prompt,
                    tools=tools,
                ):
                    yield chunk

                return

            except Exception as e:
                logger.error("model_stream_failed", model=model_name, error=str(e))
                continue

        raise RuntimeError("All models failed to stream")

    async def _call_single_model(
        self,
        model_name: str,
        api_key: str,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Call a single model provider."""
        config = self._model_configs.get(model_name, PREDEFINED_MODELS.get("openai"))

        start_time = time.time()

        # Build request based on model provider
        if model_name in ["deepseek", "openai"]:
            response = await self._call_openai_compatible(
                config=config,
                api_key=api_key,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        elif model_name == "zhipu":
            response = await self._call_zhipu(
                config=config,
                api_key=api_key,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        elif model_name == "qwen":
            response = await self._call_qwen(
                config=config,
                api_key=api_key,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        else:
            # Default to OpenAI-compatible API
            response = await self._call_openai_compatible(
                config=config,
                api_key=api_key,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        latency_ms = int((time.time() - start_time) * 1000)
        metrics.record(MetricNames.MODEL_LATENCY_MS, latency_ms)

        # Log the call
        log_model_call(
            logger,
            model=model_name,
            prompt_tokens=response.tokens_used.get("prompt", 0),
            completion_tokens=response.tokens_used.get("completion", 0),
            latency_ms=latency_ms,
            success=True,
        )

        response.model_used = model_name
        response.latency_ms = latency_ms

        return response

    async def _call_openai_compatible(
        self,
        config: ModelConfig,
        api_key: str,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Call OpenAI-compatible API (DeepSeek, OpenAI, etc.)."""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.api_base}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

        # Parse response
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        # Extract tool calls if present
        tool_calls = []
        if message.get("tool_calls"):
            tool_calls = message["tool_calls"]

        # Extract token usage
        usage = data.get("usage", {})
        tokens_used = {
            "prompt": usage.get("prompt_tokens", 0),
            "completion": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0),
        }

        return ModelResponse(
            content=message.get("content", ""),
            model_used=config.name,
            tool_calls=tool_calls,
            tokens_used=tokens_used,
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def _call_zhipu(
        self,
        config: ModelConfig,
        api_key: str,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Call Zhipu GLM API."""
        # Zhipu API is similar to OpenAI but with different auth
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.api_base}/api/paas/v4/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

        # Parse response (similar to OpenAI format)
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        usage = data.get("usage", {})
        tokens_used = {
            "prompt": usage.get("prompt_tokens", 0),
            "completion": usage.get("completion_tokens", 0),
            "total": usage.get("total_tokens", 0),
        }

        return ModelResponse(
            content=message.get("content", ""),
            model_used=config.name,
            tool_calls=message.get("tool_calls", []),
            tokens_used=tokens_used,
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def _call_qwen(
        self,
        config: ModelConfig,
        api_key: str,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ModelResponse:
        """Call Alibaba Qwen API via DashScope."""
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Qwen uses different request format
        payload = {
            "model": config.model_id,
            "input": {
                "messages": messages,
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        }

        if tools:
            payload["input"]["tools"] = tools

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                f"{config.api_base}/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

        # Parse Qwen response format
        output = data.get("output", {})
        usage = data.get("usage", {})

        tokens_used = {
            "prompt": usage.get("input_tokens", 0),
            "completion": usage.get("output_tokens", 0),
            "total": usage.get("total_tokens", 0),
        }

        return ModelResponse(
            content=output.get("text", ""),
            model_used=config.name,
            tool_calls=output.get("tool_calls", []),
            tokens_used=tokens_used,
            finish_reason=output.get("finish_reason", "stop"),
        )

    async def _stream_single_model(
        self,
        model_name: str,
        api_key: str,
        prompt: str,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """Stream from a single model."""
        config = self._model_configs.get(model_name, PREDEFINED_MODELS.get("openai"))

        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            async with client.stream(
                "POST",
                f"{config.api_base}/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]

                        if data_str == "[DONE]":
                            break

                        import json
                        data = json.loads(data_str)

                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")

                        if content:
                            yield content

    async def health_check(self) -> dict[str, Any]:
        """Check model router health."""
        return {
            "status": "healthy",
            "primary_model": self.settings.model.primary,
            "configured_models": list(self._model_configs.keys()),
            "failure_counts": self._failure_counts,
        }