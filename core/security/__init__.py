"""Security module."""

from core.security.auth import (
    AuthMiddleware,
    TokenManager,
    JWTManager,
    APIToken,
    JWTPayload,
    get_auth_middleware,
)
from core.security.audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    get_audit_logger,
)
from core.security.isolation import (
    DataScope,
    DataIsolationManager,
    DataIsolationMiddleware,
    get_isolation_manager,
    get_isolation_middleware,
)
from core.security.sandbox import (
    SandboxConfig,
    SandboxResult,
    SandboxValidator,
    SandboxExecutor,
    DangerousOperationApproval,
    get_sandbox_executor,
    get_approval_manager,
)
from core.security.concurrent import (
    ConcurrentTokenManager,
    ConcurrentJWTManager,
    ConcurrentAuthMiddleware,
    ConcurrentDataIsolationManager,
    get_concurrent_auth,
    get_concurrent_isolation,
)

__all__ = [
    # Basic security
    "AuthMiddleware",
    "TokenManager",
    "JWTManager",
    "APIToken",
    "JWTPayload",
    "get_auth_middleware",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "get_audit_logger",
    "DataScope",
    "DataIsolationManager",
    "DataIsolationMiddleware",
    "get_isolation_manager",
    "get_isolation_middleware",
    "SandboxConfig",
    "SandboxResult",
    "SandboxValidator",
    "SandboxExecutor",
    "DangerousOperationApproval",
    "get_sandbox_executor",
    "get_approval_manager",
    # Concurrent-safe security
    "ConcurrentTokenManager",
    "ConcurrentJWTManager",
    "ConcurrentAuthMiddleware",
    "ConcurrentDataIsolationManager",
    "get_concurrent_auth",
    "get_concurrent_isolation",
]