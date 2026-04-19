"""Multi-Agent Collaboration Framework."""

import asyncio
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, field
import uuid

from core.agent.types import AgentInput, AgentOutput, ExecutionContext
from core.agent.engine import AgentEngine, AgentConfig
from core.logging import get_logger
from core.metrics import get_metrics

logger = get_logger("multi_agent")
metrics = get_metrics()


@dataclass
class AgentRole:
    """Role definition for an agent."""
    name: str
    description: str
    skills: list[str] = field(default_factory=list)
    priority: int = 100
    max_concurrent_tasks: int = 5


@dataclass
class AgentTask:
    """Task for multi-agent execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assigned_agent: Optional[str] = None
    status: str = "pending"  # pending, assigned, running, completed, failed
    result: Any = None
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationResult:
    """Result from multi-agent collaboration."""
    task_id: str
    success: bool
    results: dict[str, AgentOutput] = field(default_factory=dict)
    summary: str = ""
    execution_time_ms: int = 0
    agents_used: list[str] = field(default_factory=list)


class AgentPool:
    """Pool of specialized agents."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentEngine] = {}
        self._roles: dict[str, AgentRole] = {}
        self._busy_agents: set[str] = set()

    def register_agent(
        self,
        role: AgentRole,
        config: AgentConfig,
    ) -> str:
        """Register an agent with a specific role."""
        agent_id = str(uuid.uuid4())

        engine = AgentEngine(config)

        self._agents[agent_id] = engine
        self._roles[agent_id] = role

        logger.info(
            "agent_registered",
            agent_id=agent_id,
            role=role.name,
        )

        return agent_id

    def get_available_agent(
        self,
        required_skills: Optional[list[str]] = None,
    ) -> Optional[str]:
        """Get an available agent matching requirements."""
        for agent_id, role in self._roles.items():
            if agent_id in self._busy_agents:
                continue

            if required_skills:
                if not all(s in role.skills for s in required_skills):
                    continue

            return agent_id

        return None

    def get_agent(self, agent_id: str) -> Optional[AgentEngine]:
        """Get agent engine by ID."""
        return self._agents.get(agent_id)

    def get_role(self, agent_id: str) -> Optional[AgentRole]:
        """Get agent role by ID."""
        return self._roles.get(agent_id)

    def mark_busy(self, agent_id: str) -> None:
        """Mark agent as busy."""
        self._busy_agents.add(agent_id)

    def mark_available(self, agent_id: str) -> None:
        """Mark agent as available."""
        self._busy_agents.discard(agent_id)

    def get_agent_count(self) -> int:
        """Get total agent count."""
        return len(self._agents)

    def get_available_count(self) -> int:
        """Get available agent count."""
        return len(self._agents) - len(self._busy_agents)


class TaskCoordinator:
    """Coordinate task execution across agents."""

    def __init__(self, agent_pool: AgentPool) -> None:
        self.agent_pool = agent_pool
        self._tasks: dict[str, AgentTask] = {}
        self._pending_tasks: list[str] = []
        self._completed_tasks: list[str] = []

    def create_task(
        self,
        description: str,
        required_skills: Optional[list[str]] = None,
        dependencies: Optional[list[str]] = None,
    ) -> AgentTask:
        """Create a new task."""
        task = AgentTask(
            description=description,
            dependencies=dependencies or [],
            metadata={"required_skills": required_skills or []},
        )

        self._tasks[task.id] = task
        self._pending_tasks.append(task.id)

        logger.info("task_created", task_id=task.id)

        return task

    async def assign_task(self, task_id: str) -> bool:
        """Assign task to an available agent."""
        task = self._tasks.get(task_id)

        if not task:
            return False

        if task.status != "pending":
            return False

        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)

            if not dep_task or dep_task.status != "completed":
                return False

        # Find available agent
        required_skills = task.metadata.get("required_skills", [])
        agent_id = self.agent_pool.get_available_agent(required_skills)

        if not agent_id:
            return False

        # Assign task
        task.assigned_agent = agent_id
        task.status = "assigned"

        self.agent_pool.mark_busy(agent_id)

        logger.info(
            "task_assigned",
            task_id=task_id,
            agent_id=agent_id,
        )

        return True

    async def execute_task(self, task_id: str) -> AgentOutput:
        """Execute assigned task."""
        task = self._tasks.get(task_id)

        if not task or task.status != "assigned":
            raise ValueError(f"Task {task_id} not ready for execution")

        agent_id = task.assigned_agent
        engine = self.agent_pool.get_agent(agent_id)

        if not engine:
            raise ValueError(f"Agent {agent_id} not found")

        task.status = "running"

        input = AgentInput(
            content=task.description,
            metadata={"task_id": task_id},
        )

        try:
            output = await engine.run(input)

            task.result = output
            task.status = "completed"
            task.completed_at = datetime.now()

            self._completed_tasks.append(task_id)
            self._pending_tasks.remove(task_id)

            logger.info(
                "task_completed",
                task_id=task_id,
                agent_id=agent_id,
            )

            metrics.increment("multi_agent_task_completed")

        except Exception as e:
            task.status = "failed"
            task.result = {"error": str(e)}

            logger.error(
                "task_failed",
                task_id=task_id,
                error=str(e),
            )

        finally:
            self.agent_pool.mark_available(agent_id)

        return task.result

    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get task status."""
        task = self._tasks.get(task_id)
        return task.status if task else None

    def get_pending_tasks(self) -> list[AgentTask]:
        """Get all pending tasks."""
        return [self._tasks[tid] for tid in self._pending_tasks]


class MultiAgentOrchestrator:
    """Orchestrator for multi-agent collaboration."""

    def __init__(self) -> None:
        self.agent_pool = AgentPool()
        self.coordinator = TaskCoordinator(self.agent_pool)

        # Predefined agent roles
        self._setup_default_roles()

    def _setup_default_roles(self) -> None:
        """Setup default agent roles."""
        default_roles = [
            AgentRole(
                name="researcher",
                description="Research and gather information",
                skills=["search", "analyze", "web_browse"],
                priority=100,
            ),
            AgentRole(
                name="executor",
                description="Execute actions and tools",
                skills=["file_manager", "code_helper", "task_executor"],
                priority=90,
            ),
            AgentRole(
                name="analyst",
                description="Analyze data and generate reports",
                skills=["data_analysis", "report_generator", "visualization"],
                priority=95,
            ),
            AgentRole(
                name="coordinator",
                description="Coordinate between agents and summarize results",
                skills=["planning", "communication", "synthesis"],
                priority=80,
            ),
        ]

        self._default_roles = {r.name: r for r in default_roles}

    async def initialize_pool(
        self,
        roles: Optional[list[AgentRole]] = None,
        config: Optional[AgentConfig] = None,
    ) -> None:
        """Initialize agent pool with roles."""
        roles_to_create = roles or list(self._default_roles.values())
        agent_config = config or AgentConfig()

        for role in roles_to_create:
            # Customize config for role
            role_config = AgentConfig(
                model_provider=agent_config.model_provider,
                max_iterations=agent_config.max_iterations,
            )

            self.agent_pool.register_agent(role, role_config)

        logger.info(
            "agent_pool_initialized",
            agents_count=self.agent_pool.get_agent_count(),
        )

    async def execute_parallel(
        self,
        tasks: list[str],
        user_id: str = "default",
    ) -> CollaborationResult:
        """Execute multiple tasks in parallel."""
        task_id = str(uuid.uuid4())
        start_time = datetime.now()

        results: dict[str, AgentOutput] = {}
        agents_used: list[str] = []

        # Create task objects
        created_tasks = []

        for task_desc in tasks:
            task = self.coordinator.create_task(task_desc)
            created_tasks.append(task)

        # Assign and execute tasks
        execution_tasks = []

        for task in created_tasks:
            # Try to assign
            assigned = await self.coordinator.assign_task(task.id)

            if assigned:
                agents_used.append(task.assigned_agent)

                # Create execution coroutine
                execution_tasks.append(
                    self.coordinator.execute_task(task.id)
                )

        # Execute in parallel
        if execution_tasks:
            outputs = await asyncio.gather(*execution_tasks, return_exceptions=True)

            for i, output in enumerate(outputs):
                task = created_tasks[i]

                if isinstance(output, Exception):
                    results[task.id] = AgentOutput(
                        content=f"Error: {output}",
                        session_id=task.id,
                        user_id=user_id,
                    )
                else:
                    results[task.id] = output

        # Generate summary
        summary = self._generate_summary(results)

        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return CollaborationResult(
            task_id=task_id,
            success=all(r.content != "" for r in results.values()),
            results=results,
            summary=summary,
            execution_time_ms=execution_time,
            agents_used=agents_used,
        )

    async def execute_sequential(
        self,
        tasks: list[str],
        dependencies: Optional[dict[str, list[str]]] = None,
        user_id: str = "default",
    ) -> CollaborationResult:
        """Execute tasks sequentially with dependencies."""
        task_id = str(uuid.uuid4())
        start_time = datetime.now()

        results: dict[str, AgentOutput] = {}
        agents_used: list[str] = []

        # Create tasks with dependencies
        created_tasks = []
        dependency_map = dependencies or {}

        for i, task_desc in enumerate(tasks):
            task_name = f"task_{i}"
            task_deps = dependency_map.get(task_name, [])

            # Convert dependency names to task IDs
            dep_ids = []

            for dep_name in task_deps:
                dep_idx = int(dep_name.split("_")[1])
                if dep_idx < len(created_tasks):
                    dep_ids.append(created_tasks[dep_idx].id)

            task = self.coordinator.create_task(
                task_desc,
                dependencies=dep_ids,
            )

            created_tasks.append(task)

        # Execute tasks respecting dependencies
        for task in created_tasks:
            # Wait for dependencies
            while True:
                deps_complete = all(
                    self.coordinator.get_task_status(dep_id) == "completed"
                    for dep_id in task.dependencies
                )

                if deps_complete:
                    break

                await asyncio.sleep(0.5)

            # Assign and execute
            assigned = await self.coordinator.assign_task(task.id)

            if assigned:
                agents_used.append(task.assigned_agent)

                try:
                    output = await self.coordinator.execute_task(task.id)
                    results[task.id] = output
                except Exception as e:
                    results[task.id] = AgentOutput(
                        content=f"Error: {e}",
                        session_id=task.id,
                        user_id=user_id,
                    )

        summary = self._generate_summary(results)

        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return CollaborationResult(
            task_id=task_id,
            success=all(r.content != "" for r in results.values()),
            results=results,
            summary=summary,
            execution_time_ms=execution_time,
            agents_used=agents_used,
        )

    def _generate_summary(
        self,
        results: dict[str, AgentOutput],
    ) -> str:
        """Generate summary of results."""
        if not results:
            return "No tasks completed"

        total_tasks = len(results)
        successful = sum(1 for r in results.values() if "Error" not in r.content)

        summary_parts = [
            f"完成 {successful}/{total_tasks} 个任务",
        ]

        # Add brief results
        for task_id, output in results.items():
            content_preview = output.content[:100] if len(output.content) > 100 else output.content
            summary_parts.append(f"- {task_id}: {content_preview}")

        return "\n".join(summary_parts)

    async def delegate_to_specialist(
        self,
        task_description: str,
        required_skills: list[str],
    ) -> AgentOutput:
        """Delegate task to specialist agent."""
        # Find specialist
        agent_id = self.agent_pool.get_available_agent(required_skills)

        if not agent_id:
            return AgentOutput(
                content="No specialist agent available for this task",
                session_id="delegation",
                user_id="system",
            )

        engine = self.agent_pool.get_agent(agent_id)
        role = self.agent_pool.get_role(agent_id)

        self.agent_pool.mark_busy(agent_id)

        try:
            input = AgentInput(
                content=task_description,
                metadata={"delegated_to": role.name},
            )

            output = await engine.run(input)

            logger.info(
                "task_delegated",
                agent_id=agent_id,
                role=role.name,
            )

            return output

        finally:
            self.agent_pool.mark_available(agent_id)