"""Multi-agent module."""

from core.multi_agent.orchestrator import (
    MultiAgentOrchestrator,
    AgentPool,
    TaskCoordinator,
    AgentRole,
    AgentTask,
    CollaborationResult,
)

__all__ = [
    "MultiAgentOrchestrator",
    "AgentPool",
    "TaskCoordinator",
    "AgentRole",
    "AgentTask",
    "CollaborationResult",
]