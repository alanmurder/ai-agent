"""Health Check - Comprehensive health endpoints for Kubernetes."""

import asyncio
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from core.logging import get_logger
from core.metrics import get_metrics
from core.concurrency import (
    get_redis_pool,
    get_postgres_pool,
    get_task_queue,
)

logger = get_logger("health")
metrics = get_metrics()


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: HealthStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class SystemHealth:
    """Overall system health."""
    status: HealthStatus
    components: list[ComponentHealth] = field(default_factory=list)
    version: str = "0.1.0"
    uptime_seconds: int = 0
    instance_id: str = ""
    cluster_info: dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """Comprehensive health checker for Kubernetes deployment."""

    def __init__(self) -> None:
        self._start_time = datetime.now()
        self._instance_id: Optional[str] = None
        self._cluster_name: Optional[str] = None
        self._checks: dict[str, callable] = {}

    def set_instance_info(
        self,
        instance_id: str,
        cluster_name: str = "default",
    ) -> None:
        """Set instance identification."""
        self._instance_id = instance_id
        self._cluster_name = cluster_name

    async def check_all(self) -> SystemHealth:
        """Run all health checks."""
        components = []

        # Check Redis
        redis_health = await self._check_redis()
        components.append(redis_health)

        # Check PostgreSQL
        postgres_health = await self._check_postgres()
        components.append(postgres_health)

        # Check Task Queue
        queue_health = await self._check_task_queue()
        components.append(queue_health)

        # Check Model Router
        model_health = await self._check_model_router()
        components.append(model_health)

        # Check Memory System
        memory_health = await self._check_memory()
        components.append(memory_health)

        # Determine overall status
        overall_status = self._determine_overall_status(components)

        uptime = int((datetime.now() - self._start_time).total_seconds())

        return SystemHealth(
            status=overall_status,
            components=components,
            uptime_seconds=uptime,
            instance_id=self._instance_id or "unknown",
            cluster_info={
                "cluster_name": self._cluster_name or "default",
                "pod_name": self._instance_id,
                "namespace": "production",
            },
        )

    async def check_live(self) -> bool:
        """Liveness probe - is the process running."""
        # Basic liveness - just check if we can respond
        return True

    async def check_ready(self) -> tuple[bool, list[str]]:
        """Readiness probe - is the service ready to accept traffic."""
        issues = []

        # Check critical dependencies
        redis_pool = get_redis_pool()
        if redis_pool._pool is None:
            # Redis not required for readiness in single-instance mode
            pass

        # Check if model router is initialized
        try:
            from core.model.router import get_model_router
            router = get_model_router()
            if not router._initialized:
                issues.append("model_router_not_initialized")
        except Exception as e:
            issues.append(f"model_router_error: {str(e)}")

        return len(issues) == 0, issues

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis connection."""
        start_time = datetime.now()

        try:
            redis_pool = get_redis_pool()

            if redis_pool._pool is None:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    message="Redis not configured (single-instance mode)",
                    latency_ms=0,
                )

            # Ping Redis
            await redis_pool.execute("PING")

            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Connected",
                latency_ms=latency_ms,
                details={
                    "pool_size": redis_pool._pool.size if redis_pool._pool else 0,
                },
            )

        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)}",
                latency_ms=latency_ms,
            )

    async def _check_postgres(self) -> ComponentHealth:
        """Check PostgreSQL connection."""
        start_time = datetime.now()

        try:
            postgres_pool = get_postgres_pool()

            if postgres_pool._pool is None:
                return ComponentHealth(
                    name="postgres",
                    status=HealthStatus.DEGRADED,
                    message="PostgreSQL not configured",
                    latency_ms=0,
                )

            # Simple query
            async with postgres_pool.connection() as conn:
                if conn:
                    await conn.execute("SELECT 1")

            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return ComponentHealth(
                name="postgres",
                status=HealthStatus.HEALTHY,
                message="Connected",
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return ComponentHealth(
                name="postgres",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)}",
                latency_ms=latency_ms,
            )

    async def _check_task_queue(self) -> ComponentHealth:
        """Check async task queue."""
        try:
            task_queue = get_task_queue()

            worker_count = len(task_queue._workers)

            return ComponentHealth(
                name="task_queue",
                status=HealthStatus.HEALTHY if worker_count > 0 else HealthStatus.DEGRADED,
                message=f"{worker_count} workers running",
                details={
                    "workers": worker_count,
                    "running": task_queue._running,
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="task_queue",
                status=HealthStatus.UNHEALTHY,
                message=f"Queue error: {str(e)}",
            )

    async def _check_model_router(self) -> ComponentHealth:
        """Check model router status."""
        try:
            from core.model.router import get_model_router

            router = get_model_router()

            # Get available models
            models = router.get_available_models()
            primary_model = router._primary_model

            status = HealthStatus.HEALTHY if len(models) > 0 else HealthStatus.UNHEALTHY

            return ComponentHealth(
                name="model_router",
                status=status,
                message=f"Primary: {primary_model}, Available: {len(models)}",
                details={
                    "primary_model": primary_model,
                    "available_models": models,
                    "initialized": router._initialized,
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="model_router",
                status=HealthStatus.UNHEALTHY,
                message=f"Router error: {str(e)}",
            )

    async def _check_memory(self) -> ComponentHealth:
        """Check memory system status."""
        try:
            from core.memory.manager import get_memory_manager

            memory_manager = get_memory_manager()

            return ComponentHealth(
                name="memory",
                status=HealthStatus.HEALTHY,
                message="Memory system initialized",
                details={
                    "initialized": True,
                },
            )

        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Memory error: {str(e)}",
            )

    def _determine_overall_status(
        self,
        components: list[ComponentHealth],
    ) -> HealthStatus:
        """Determine overall system status from components."""
        unhealthy_count = sum(
            1 for c in components if c.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for c in components if c.status == HealthStatus.DEGRADED
        )

        # Critical components: redis (if configured), model_router
        critical_unhealthy = any(
            c.name in ("model_router") and c.status == HealthStatus.UNHEALTHY
            for c in components
        )

        if critical_unhealthy or unhealthy_count >= 2:
            return HealthStatus.UNHEALTHY

        if unhealthy_count == 1 or degraded_count >= 2:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY


# Global health checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker."""
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def set_instance_info(instance_id: str, cluster_name: str) -> None:
    """Set instance info for health checker."""
    checker = get_health_checker()
    checker.set_instance_info(instance_id, cluster_name)