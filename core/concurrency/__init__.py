"""Concurrency Infrastructure - Enterprise-grade concurrent execution support.

Provides:
- Connection pools (PostgreSQL, Redis)
- Distributed locks
- Async task queues
- Rate limiting with Redis
- Session storage with Redis
"""

import asyncio
from typing import Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json
import hashlib
import time

try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from core.logging import get_logger
from core.metrics import get_metrics, MetricNames
from config import get_settings

logger = get_logger("concurrency")
metrics = get_metrics()


@dataclass
class PoolConfig:
    """Connection pool configuration."""
    min_size: int = 5
    max_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    connection_timeout: float = 10.0
    command_timeout: float = 30.0


class RedisConnectionPool:
    """Redis connection pool for distributed operations."""

    def __init__(self, config: Optional[PoolConfig] = None) -> None:
        self.config = config or PoolConfig()
        self.settings = get_settings()
        self._pool: Optional[Any] = None
        self._url: str = ""

    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        if not REDIS_AVAILABLE:
            logger.warning("aioredis not installed, using mock implementation")
            return

        # Get Redis URL from settings
        redis_url = getattr(self.settings, 'redis_url', 'redis://localhost:6379/0')

        self._url = redis_url

        try:
            # Create connection pool
            self._pool = await aioredis.create_redis_pool(
                redis_url,
                minsize=self.config.min_size,
                maxsize=self.config.max_size,
                timeout=self.config.connection_timeout,
            )

            logger.info(
                "redis_pool_initialized",
                url=redis_url,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
            )

            metrics.increment("redis_pool_initialized")

        except Exception as e:
            logger.error("redis_pool_init_error", error=str(e))
            self._pool = None

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

            logger.info("redis_pool_closed")

    async def get_connection(self) -> Any:
        """Get a connection from the pool."""
        if not self._pool:
            return None

        return self._pool

    @asynccontextmanager
    async def connection(self):
        """Context manager for Redis connection."""
        conn = await self.get_connection()
        try:
            yield conn
        finally:
            # Connection automatically returned to pool
            pass

    async def execute(self, command: str, *args) -> Any:
        """Execute a Redis command."""
        if not self._pool:
            return None

        try:
            start_time = time.time()
            result = await self._pool.execute_command(command, *args)
            execution_time_ms = int((time.time() - start_time) * 1000)

            metrics.record("redis_command_time_ms", execution_time_ms)
            metrics.increment("redis_commands_total")

            return result

        except Exception as e:
            logger.error("redis_command_error", command=command, error=str(e))
            metrics.increment("redis_errors_total")
            raise

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        if expire:
            return await self.execute("SET", key, value, "EX", expire)

        return await self.execute("SET", key, value)

    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        value = await self.execute("GET", key)

        if value is None:
            return None

        # Try to parse JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        result = await self.execute("DEL", key)
        return result > 0

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        return await self.execute("INCR", key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        return await self.execute("EXPIRE", key, seconds)


class PostgresConnectionPool:
    """PostgreSQL connection pool for async database operations."""

    def __init__(self, config: Optional[PoolConfig] = None) -> None:
        self.config = config or PoolConfig()
        self.settings = get_settings()
        self._pool: Optional[Any] = None

    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool."""
        if not POSTGRES_AVAILABLE:
            logger.warning("asyncpg not installed, using mock implementation")
            return

        # Get database URL from settings
        db_url = getattr(self.settings, 'database_url', '')

        if not db_url:
            db_config = getattr(self.settings, 'database', {})
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = db_config.get('database', 'aiagent')
            user = db_config.get('user', 'postgres')
            password = db_config.get('password', '')

            db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        try:
            self._pool = await asyncpg.create_pool(
                db_url,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                command_timeout=self.config.command_timeout,
            )

            logger.info(
                "postgres_pool_initialized",
                min_size=self.config.min_size,
                max_size=self.config.max_size,
            )

            metrics.increment("postgres_pool_initialized")

        except Exception as e:
            logger.error("postgres_pool_init_error", error=str(e))
            self._pool = None

    async def close(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

            logger.info("postgres_pool_closed")

    @asynccontextmanager
    async def connection(self):
        """Context manager for database connection."""
        if not self._pool:
            yield None
            return

        async with self._pool.acquire() as conn:
            try:
                yield conn
            finally:
                pass

    async def execute(self, query: str, *args) -> Any:
        """Execute a query."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            start_time = time.time()
            result = await conn.execute(query, *args)
            execution_time_ms = int((time.time() - start_time) * 1000)

            metrics.record("postgres_query_time_ms", execution_time_ms)
            metrics.increment("postgres_queries_total")

            return result

    async def fetch(self, query: str, *args) -> list:
        """Fetch rows from query."""
        if not self._pool:
            return []

        async with self._pool.acquire() as conn:
            start_time = time.time()
            rows = await conn.fetch(query, *args)
            execution_time_ms = int((time.time() - start_time) * 1000)

            metrics.record("postgres_query_time_ms", execution_time_ms)

            return rows

    async def fetchrow(self, query: str, *args) -> Optional[Any]:
        """Fetch a single row."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value."""
        if not self._pool:
            return None

        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)


class DistributedLock:
    """Redis-based distributed lock for multi-instance coordination."""

    def __init__(
        self,
        redis_pool: RedisConnectionPool,
        lock_name: str,
        timeout: int = 30,
        retry_interval: float = 0.1,
    ) -> None:
        self.redis_pool = redis_pool
        self.lock_name = f"lock:{lock_name}"
        self.timeout = timeout
        self.retry_interval = retry_interval
        self._lock_value: Optional[str] = None

    async def acquire(self) -> bool:
        """Acquire the distributed lock."""
        if not self.redis_pool._pool:
            # No Redis, allow operation (single instance mode)
            return True

        # Generate unique lock value
        self._lock_value = hashlib.sha256(
            f"{time.time()}-{asyncio.get_running_loop().time()}".encode()
        ).hexdigest()[:16]

        # Try to acquire lock with SET NX EX
        acquired = await self.redis_pool.execute(
            "SET",
            self.lock_name,
            self._lock_value,
            "NX",
            "EX",
            self.timeout,
        )

        if acquired:
            logger.debug("lock_acquired", lock_name=self.lock_name)
            metrics.increment("locks_acquired")
            return True

        # Retry acquisition
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            await asyncio.sleep(self.retry_interval)

            acquired = await self.redis_pool.execute(
                "SET",
                self.lock_name,
                self._lock_value,
                "NX",
                "EX",
                self.timeout,
            )

            if acquired:
                logger.debug("lock_acquired_retry", lock_name=self.lock_name)
                return True

        logger.warning("lock_acquire_failed", lock_name=self.lock_name)
        metrics.increment("locks_failed")
        return False

    async def release(self) -> bool:
        """Release the distributed lock."""
        if not self.redis_pool._pool or not self._lock_value:
            return True

        # Use Lua script to safely release lock (only if we own it)
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """

        released = await self.redis_pool.execute(
            "EVAL",
            lua_script,
            1,
            self.lock_name,
            self._lock_value,
        )

        if released:
            logger.debug("lock_released", lock_name=self.lock_name)
            self._lock_value = None
            return True

        logger.warning("lock_release_failed", lock_name=self.lock_name)
        return False

    @asynccontextmanager
    async def locked(self):
        """Context manager for distributed lock."""
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError(f"Failed to acquire lock: {self.lock_name}")

        try:
            yield
        finally:
            await self.release()


class DistributedRateLimiter:
    """Redis-based distributed rate limiter."""

    def __init__(
        self,
        redis_pool: RedisConnectionPool,
        key: str,
        limit: int = 60,
        window: int = 60,
    ) -> None:
        self.redis_pool = redis_pool
        self.key = f"rate_limit:{key}"
        self.limit = limit
        self.window = window

    async def check(self) -> tuple[bool, int, int]:
        """Check if request is allowed within rate limit."""
        if not self.redis_pool._pool:
            # No Redis, allow (single instance mode)
            return True, 0, self.limit

        # Use sliding window algorithm
        now = time.time()
        window_start = now - self.window

        # Lua script for atomic rate limiting
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        -- Remove old entries
        redis.call("ZREMRANGEBYSCORE", key, 0, now - window)

        -- Count current entries
        local count = redis.call("ZCARD", key)

        if count < limit then
            -- Add new entry
            redis.call("ZADD", key, now, now .. "-" .. math.random())
            redis.call("EXPIRE", key, window)
            return {1, count + 1, limit}
        else
            return {0, count, limit}
        end
        """

        result = await self.redis_pool.execute(
            "EVAL",
            lua_script,
            1,
            self.key,
            self.limit,
            self.window,
            now,
        )

        allowed = result[0] == 1
        current = result[1]
        remaining = self.limit - current

        if not allowed:
            logger.warning("rate_limit_exceeded", key=self.key, current=current)
            metrics.increment("rate_limit_exceeded")

        return allowed, current, remaining

    async def reset(self) -> None:
        """Reset rate limit counter."""
        if self.redis_pool._pool:
            await self.redis_pool.delete(self.key)


class AsyncTaskQueue:
    """Async task queue for background processing."""

    def __init__(
        self,
        redis_pool: RedisConnectionPool,
        queue_name: str = "tasks",
        max_workers: int = 10,
    ) -> None:
        self.redis_pool = redis_pool
        self.queue_name = f"queue:{queue_name}"
        self.max_workers = max_workers
        self._workers: list[asyncio.Task] = []
        self._handlers: dict[str, Callable] = {}
        self._running = False

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """Register a handler for a task type."""
        self._handlers[task_type] = handler

    async def enqueue(
        self,
        task_type: str,
        payload: dict[str, Any],
        priority: int = 0,
    ) -> str:
        """Enqueue a task for processing."""
        import uuid

        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "type": task_type,
            "payload": payload,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
        }

        if self.redis_pool._pool:
            # Push to Redis queue
            await self.redis_pool.execute(
                "LPUSH",
                self.queue_name,
                json.dumps(task_data),
            )
        else:
            # Local queue (single instance)
            task_data["_local"] = True

        logger.info("task_enqueued", task_id=task_id, task_type=task_type)
        metrics.increment("tasks_enqueued")

        return task_id

    async def dequeue(self) -> Optional[dict[str, Any]]:
        """Dequeue a task from the queue."""
        if self.redis_pool._pool:
            # Pop from Redis queue (blocking with timeout)
            result = await self.redis_pool.execute(
                "BRPOP",
                self.queue_name,
                1,  # 1 second timeout
            )

            if result:
                task_json = result[1]
                return json.loads(task_json)
        else:
            # Local processing - not implemented for single instance
            pass

        return None

    async def start_workers(self) -> None:
        """Start worker tasks."""
        self._running = True

        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)

        logger.info("task_workers_started", count=self.max_workers)

    async def stop_workers(self) -> None:
        """Stop all workers."""
        self._running = False

        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info("task_workers_stopped")

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop for processing tasks."""
        logger.info("worker_started", worker_id=worker_id)

        while self._running:
            try:
                task = await self.dequeue()

                if not task:
                    await asyncio.sleep(0.1)
                    continue

                await self._process_task(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("worker_error", worker_id=worker_id, error=str(e))
                await asyncio.sleep(1)

        logger.info("worker_stopped", worker_id=worker_id)

    async def _process_task(self, task: dict[str, Any]) -> None:
        """Process a single task."""
        task_type = task.get("type", "")
        task_id = task.get("id", "")
        payload = task.get("payload", {})

        handler = self._handlers.get(task_type)

        if not handler:
            logger.warning("no_handler_for_task", task_type=task_type)
            metrics.increment("tasks_no_handler")
            return

        try:
            start_time = time.time()

            if asyncio.iscoroutinefunction(handler):
                await handler(payload)
            else:
                handler(payload)

            execution_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "task_completed",
                task_id=task_id,
                task_type=task_type,
                execution_time_ms=execution_time_ms,
            )

            metrics.record("task_execution_time_ms", execution_time_ms)
            metrics.increment("tasks_completed")

        except Exception as e:
            logger.error(
                "task_failed",
                task_id=task_id,
                task_type=task_type,
                error=str(e),
            )
            metrics.increment("tasks_failed")


class SessionStore:
    """Redis-based session store for distributed session management."""

    def __init__(self, redis_pool: RedisConnectionPool) -> None:
        self.redis_pool = redis_pool
        self._local_sessions: dict[str, Any] = {}  # Fallback for no Redis
        self._session_ttl = 3600  # 1 hour

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        data: dict[str, Any],
    ) -> bool:
        """Create a new session."""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "data": data,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }

        if self.redis_pool._pool:
            key = f"session:{session_id}"
            return await self.redis_pool.set(key, session_data, expire=self._session_ttl)
        else:
            self._local_sessions[session_id] = session_data
            return True

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get session data."""
        if self.redis_pool._pool:
            key = f"session:{session_id}"
            return await self.redis_pool.get(key)
        else:
            return self._local_sessions.get(session_id)

    async def update_session(
        self,
        session_id: str,
        data: dict[str, Any],
    ) -> bool:
        """Update session data."""
        session = await self.get_session(session_id)

        if not session:
            return False

        session["data"] = data
        session["last_activity"] = datetime.now().isoformat()

        if self.redis_pool._pool:
            key = f"session:{session_id}"
            return await self.redis_pool.set(key, session, expire=self._session_ttl)
        else:
            self._local_sessions[session_id] = session
            return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if self.redis_pool._pool:
            key = f"session:{session_id}"
            return await self.redis_pool.delete(key)
        else:
            if session_id in self._local_sessions:
                del self._local_sessions[session_id]
                return True
            return False

    async def extend_session(self, session_id: str) -> bool:
        """Extend session TTL."""
        if self.redis_pool._pool:
            key = f"session:{session_id}"
            return await self.redis_pool.expire(key, self._session_ttl)
        return True


class CacheManager:
    """Redis-based cache manager."""

    def __init__(self, redis_pool: RedisConnectionPool) -> None:
        self.redis_pool = redis_pool
        self._local_cache: dict[str, Any] = {}  # Fallback

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        if self.redis_pool._pool:
            cache_key = f"cache:{key}"
            return await self.redis_pool.get(cache_key)
        else:
            return self._local_cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
    ) -> bool:
        """Set cached value."""
        if self.redis_pool._pool:
            cache_key = f"cache:{key}"
            return await self.redis_pool.set(cache_key, value, expire=ttl)
        else:
            self._local_cache[key] = value
            return True

    async def delete(self, key: str) -> bool:
        """Delete cached value."""
        if self.redis_pool._pool:
            cache_key = f"cache:{key}"
            return await self.redis_pool.delete(cache_key)
        else:
            if key in self._local_cache:
                del self._local_cache[key]
                return True
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        if not self.redis_pool._pool:
            return 0

        # Find keys matching pattern
        keys = await self.redis_pool.execute("KEYS", f"cache:{pattern}")

        if keys:
            count = 0
            for key in keys:
                if await self.redis_pool.delete(key):
                    count += 1
            return count

        return 0


# Global connection pools
_redis_pool: Optional[RedisConnectionPool] = None
_postgres_pool: Optional[PostgresConnectionPool] = None
_task_queue: Optional[AsyncTaskQueue] = None
_cache_manager: Optional[CacheManager] = None
_session_store: Optional[SessionStore] = None


async def init_concurrency_infrastructure() -> None:
    """Initialize all concurrency infrastructure."""
    global _redis_pool, _postgres_pool, _task_queue, _cache_manager, _session_store

    # Initialize Redis pool
    _redis_pool = RedisConnectionPool()
    await _redis_pool.initialize()

    # Initialize Postgres pool
    _postgres_pool = PostgresConnectionPool()
    await _postgres_pool.initialize()

    # Initialize task queue
    _task_queue = AsyncTaskQueue(_redis_pool)
    await _task_queue.start_workers()

    # Initialize cache manager
    _cache_manager = CacheManager(_redis_pool)

    # Initialize session store
    _session_store = SessionStore(_redis_pool)

    logger.info("concurrency_infrastructure_initialized")


async def close_concurrency_infrastructure() -> None:
    """Close all concurrency infrastructure."""
    global _redis_pool, _postgres_pool, _task_queue

    if _task_queue:
        await _task_queue.stop_workers()

    if _redis_pool:
        await _redis_pool.close()

    if _postgres_pool:
        await _postgres_pool.close()

    logger.info("concurrency_infrastructure_closed")


def get_redis_pool() -> RedisConnectionPool:
    """Get global Redis pool."""
    if _redis_pool is None:
        _redis_pool = RedisConnectionPool()
    return _redis_pool


def get_postgres_pool() -> PostgresConnectionPool:
    """Get global Postgres pool."""
    if _postgres_pool is None:
        _postgres_pool = PostgresConnectionPool()
    return _postgres_pool


def get_task_queue() -> AsyncTaskQueue:
    """Get global task queue."""
    if _task_queue is None:
        _task_queue = AsyncTaskQueue(get_redis_pool())
    return _task_queue


def get_cache_manager() -> CacheManager:
    """Get global cache manager."""
    if _cache_manager is None:
        _cache_manager = CacheManager(get_redis_pool())
    return _cache_manager


def get_session_store() -> SessionStore:
    """Get global session store."""
    if _session_store is None:
        _session_store = SessionStore(get_redis_pool())
    return _session_store