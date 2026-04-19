"""Agent Engine - Core execution loop."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, AsyncIterator
import uuid

from core.agent.types import AgentInput, AgentOutput, ExecutionContext, Conversation
from core.memory.types import MemoryContext
from core.model.router import ModelRouter
from core.memory.manager import MemoryManager
from core.tools.executor import ToolExecutor
from core.tools.types import ToolCall, ToolResult
from skills.manager import SkillManager
from core.logging import get_logger, LogContext, log_agent_event
from core.metrics import get_metrics, MetricNames

logger = get_logger("agent.engine")
metrics = get_metrics()


@dataclass
class AgentConfig:
    """Configuration for Agent engine."""
    max_iterations: int = 10
    timeout_seconds: int = 60
    enable_memory: bool = True
    enable_tools: bool = True
    enable_skills: bool = True
    model_provider: str = "deepseek"


class AgentEngine:
    """Core Agent execution engine."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.model_router = ModelRouter()
        self.memory_manager = MemoryManager()
        self.tool_executor = ToolExecutor()
        self.skill_manager = SkillManager()

    async def run(self, input: AgentInput) -> AgentOutput:
        """Execute Agent loop for a single request."""
        # Create or restore session
        session_id = input.session_id or str(uuid.uuid4())
        user_id = input.user_id or "default"

        # Create execution context
        context = ExecutionContext(
            session_id=session_id,
            user_id=user_id,
            input=input,
            iteration=0,
            max_iterations=self.config.max_iterations,
        )

        # Load memory context
        if self.config.enable_memory:
            context.memory_context = await self.memory_manager.retrieve_context(
                query=input.content,
                user_id=user_id,
            )

        # Load available tools and skills
        if self.config.enable_skills:
            context.available_skills = await self.skill_manager.get_active_skills(user_id)

        if self.config.enable_tools:
            context.available_tools = self.skill_manager.get_tool_names(context.available_skills)

        # Start timing
        end_timing = metrics.timing(MetricNames.AGENT_RESPONSE_TIME_MS)

        # Execute the loop
        try:
            output = await self._execute_loop(context)

            # Update memory after execution
            if self.config.enable_memory:
                await self.memory_manager.persist_session(
                    user_id=user_id,
                    session_id=session_id,
                    conversation=context.memory_context.get("current_session", []),
                )

            # Log success
            with LogContext(user_id=user_id, session_id=session_id):
                log_agent_event(
                    logger,
                    "agent_run_complete",
                    user_id=user_id,
                    session_id=session_id,
                    model=output.model_used,
                    iterations=context.iteration,
                )

            metrics.increment(MetricNames.AGENT_ITERATION_COUNT, context.iteration)

            return output

        except Exception as e:
            metrics.increment(MetricNames.AGENT_ERROR_COUNT)
            logger.error("agent_run_error", error=str(e), user_id=user_id)

            raise

        finally:
            end_timing()

    async def stream(self, input: AgentInput) -> AsyncIterator[str]:
        """Stream Agent response token by token."""
        session_id = input.session_id or str(uuid.uuid4())
        user_id = input.user_id or "default"

        context = ExecutionContext(
            session_id=session_id,
            user_id=user_id,
            input=input,
            iteration=0,
            max_iterations=self.config.max_iterations,
        )

        # Load context
        if self.config.enable_memory:
            context.memory_context = await self.memory_manager.retrieve_context(
                query=input.content,
                user_id=user_id,
            )

        # Stream from model
        async for chunk in self.model_router.stream(
            prompt=input.content,
            context=context,
            model=self.config.model_provider,
        ):
            yield chunk

    async def _execute_loop(self, context: ExecutionContext) -> AgentOutput:
        """Execute the Agent reasoning loop."""
        conversation = Conversation(
            user_id=context.user_id,
            session_id=context.session_id,
        )

        # Add initial user message
        conversation.add_message("user", context.input.content)

        while context.iteration < context.max_iterations:
            context.iteration += 1

            # Build prompt from conversation and context
            prompt_messages = self._build_prompt(conversation, context)

            # Call model
            response = await self.model_router.call(
                messages=prompt_messages,
                model=self.config.model_provider,
                tools=self._get_tool_definitions(context) if self.config.enable_tools else None,
            )

            # Check if response is text or tool call
            if response.tool_calls:
                # Add assistant message with tool calls
                conversation.add_message("assistant", response.content or "")

                # Execute tools
                tool_results = await self._execute_tools(response.tool_calls, context)

                # Add tool results to conversation
                for result in tool_results:
                    conversation.add_message("tool", str(result.output) if result.output else result.error or "")

                metrics.increment(MetricNames.TOOL_EXECUTION_COUNT, len(tool_results))

            else:
                # Text response - add to conversation and return
                conversation.add_message("assistant", response.content)

                return AgentOutput(
                    content=response.content,
                    session_id=context.session_id,
                    user_id=context.user_id,
                    model_used=response.model_used,
                    tokens_used=response.tokens_used.get("total", 0),
                    tool_calls=[],
                )

        # Max iterations reached
        return AgentOutput(
            content="Maximum iterations reached. Task may require more steps.",
            session_id=context.session_id,
            user_id=context.user_id,
            model_used=response.model_used,
            tokens_used=0,
            metadata={"max_iterations_reached": True},
        )

    def _build_prompt(
        self,
        conversation: Conversation,
        context: ExecutionContext,
    ) -> list[dict[str, str]]:
        """Build prompt messages from conversation and context."""
        messages = []

        # Add system message with context
        system_prompt = self._build_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        messages.extend(conversation.to_prompt_messages())

        return messages

    def _build_system_prompt(self, context: ExecutionContext) -> str:
        """Build system prompt with memory and skill context."""
        parts = []

        # Base system prompt
        parts.append("You are an AI assistant helping the user accomplish their tasks.")

        # Add memory context
        if context.memory_context:
            memory_ctx = context.memory_context
            if memory_ctx.get("core_memory"):
                parts.append(f"\n## User Information\n{memory_ctx['core_memory']}")

            if memory_ctx.get("user_preferences"):
                prefs = memory_ctx["user_preferences"]
                parts.append(f"\n## User Preferences\n{prefs}")

        # Add available skills
        if context.available_skills:
            parts.append(f"\n## Available Skills\n{', '.join(context.available_skills)}")

        return "\n".join(parts)

    def _get_tool_definitions(self, context: ExecutionContext) -> list[dict[str, Any]]:
        """Get tool definitions for the model."""
        tools = []

        for skill_name in context.available_skills:
            skill_tools = self.skill_manager.get_skill_tools(skill_name)
            for tool in skill_tools:
                tools.append(tool.to_openai_format())

        return tools

    async def _execute_tools(
        self,
        tool_calls: list[dict[str, Any]],
        context: ExecutionContext,
    ) -> list[ToolResult]:
        """Execute multiple tool calls."""
        results = []

        for call_data in tool_calls:
            tool_call = ToolCall(
                name=call_data.get("function", {}).get("name", ""),
                params=call_data.get("function", {}).get("arguments", {}),
                call_id=call_data.get("id", str(uuid.uuid4())),
            )

            result = await self.tool_executor.execute(tool_call, context)
            results.append(result)

        return results

    async def health_check(self) -> dict[str, Any]:
        """Check Agent engine health."""
        return {
            "status": "healthy",
            "model_router": await self.model_router.health_check(),
            "memory_manager": self.memory_manager.is_ready(),
            "skill_manager": len(await self.skill_manager.discover_skills()) > 0,
            "timestamp": datetime.now().isoformat(),
        }