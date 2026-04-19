"""Concurrent-Safe Security Components - Distributed locks and Redis-backed storage."""

import asyncio
from typing import Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import hashlib
import time

from core.concurrency import (
    RedisConnectionPool,
    DistributedLock,
    DistributedRateLimiter,
    SessionStore,
    CacheManager,
    get_redis_pool,
    get_cache_manager,
    get_session_store,
)
from core.enterprise.permissions import EnterpriseUser, UserRole, Permission
from core.logging import get_logger
from core.metrics import get_metrics

logger = get_logger("security.concurrent")
metrics = get_metrics()


class ConcurrentTokenManager:
    """Token manager with Redis-backed storage for multi-instance deployment."""

    def __init__(self, redis_pool: Optional[RedisConnectionPool] = None) -> None:
        self.redis_pool = redis_pool or get_redis_pool()
        self._token_prefix = "token:"
        self._user_tokens_prefix = "user_tokens:"
        self._token_expiry_hours = 24

    async def generate_token(
        self,
        user_id: str,
        scopes: Optional[list[str]] = None,
        expires_hours: int = 24,
    ) -> str:
        """Generate a new API token."""
        import secrets
        import uuid

        # Use distributed lock for token generation
        lock = DistributedLock(
            self.redis_pool,
            f"token_gen:{user_id}",
            timeout=10,
        )

        async with lock.locked():
            # Generate random token
            raw_token = secrets.token_urlsafe(32)
            token_id = str(uuid.uuid4())
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

            # Create token record
            token_data = {
                "token_id": token_id,
                "user_id": user_id,
                "token_hash": token_hash,
                "created_at": datetime.now().isoformat(),
                "expires_at": (
                    datetime.now() + timedelta(hours=expires_hours)
                ).isoformat(),
                "is_active": True,
                "scopes": scopes or ["read", "write"],
                "rate_limit": 60,
            }

            # Store token
            await self.redis_pool.set(
                f"{self._token_prefix}{token_id}",
                token_data,
                expire=expires_hours * 3600,
            )

            # Add to user's token list
            user_tokens_key = f"{self._user_tokens_prefix}{user_id}"
            user_tokens = await self.redis_pool.get(user_tokens_key) or []
            user_tokens.append(token_id)
            await self.redis_pool.set(
                user_tokens_key,
                user_tokens,
                expire=expires_hours * 3600 + 3600,  # Extra buffer
            )

            logger.info(
                "token_generated_concurrent",
                user_id=user_id,
                token_id=token_id,
            )

            metrics.increment("tokens_generated")

            return f"sk-{raw_token}"

    async def verify_token(self, raw_token: str) -> Optional[dict[str, Any]]:
        """Verify and return token info."""
        if not raw_token.startswith("sk-"):
            return None

        # Hash the token
        token_key = raw_token[3:]
        token_hash = hashlib.sha256(token_key.encode()).hexdigest()

        # Find token by hash (scan all tokens for this hash)
        # In production, use a hash -> token_id mapping
        # For now, we check user's tokens

        # Get all token IDs (this is inefficient, optimize in production)
        # Alternative: store hash -> token_id mapping
        hash_key = f"token_hash:{token_hash}"
        token_id = await self.redis_pool.get(hash_key)

        if not token_id:
            return None

        # Get token data
        token_data = await self.redis_pool.get(f"{self._token_prefix}{token_id}")

        if not token_data:
            return None

        # Check if active and not expired
        if not token_data.get("is_active", True):
            return None

        expires_at_str = token_data.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                await self.revoke_token(token_id)
                return None

        return token_data

    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a token."""
        lock = DistributedLock(
            self.redis_pool,
            f"token_revoke:{token_id}",
            timeout=5,
        )

        async with lock.locked():
            token_data = await self.redis_pool.get(
                f"{self._token_prefix}{token_id}"
            )

            if not token_data:
                return False

            token_data["is_active"] = False
            await self.redis_pool.set(
                f"{self._token_prefix}{token_id}",
                token_data,
                expire=60,  # Keep briefly for audit
            )

            logger.info("token_revoked_concurrent", token_id=token_id)
            metrics.increment("tokens_revoked")

            return True

    async def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        lock = DistributedLock(
            self.redis_pool,
            f"user_tokens:{user_id}",
            timeout=10,
        )

        async with lock.locked():
            user_tokens_key = f"{self._user_tokens_prefix}{user_id}"
            user_tokens = await self.redis_pool.get(user_tokens_key) or []

            count = 0
            for token_id in user_tokens:
                if await self.revoke_token(token_id):
                    count += 1

            await self.redis_pool.delete(user_tokens_key)

            return count


class ConcurrentJWTManager:
    """JWT manager with Redis-backed session storage."""

    def __init__(self, redis_pool: Optional[RedisConnectionPool] = None) -> None:
        self.redis_pool = redis_pool or get_redis_pool()
        self._session_prefix = "jwt_session:"
        self._secret_key = hashlib.sha256(
            f"jwt-secret-{time.time()}".encode()
        ).hexdigest()
        self._expiry_hours = 8

    async def generate_jwt(
        self,
        user: EnterpriseUser,
        session_id: Optional[str] = None,
    ) -> str:
        """Generate JWT token."""
        import uuid

        session_id = session_id or str(uuid.uuid4())

        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "issued_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.now() + timedelta(hours=self._expiry_hours)
            ).isoformat(),
            "session_id": session_id,
        }

        # Store payload in Redis
        await self.redis_pool.set(
            f"{self._session_prefix}{session_id}",
            payload,
            expire=self._expiry_hours * 3600,
        )

        # Generate signature
        token_data = f"{payload['user_id']}:{session_id}:{payload['expires_at']}"
        signature = hashlib.sha256(
            f"{token_data}:{self._secret_key}".encode()
        ).hexdigest()

        jwt_token = f"jwt-{session_id}.{signature}"

        logger.info(
            "jwt_generated_concurrent",
            user_id=user.id,
            session_id=session_id,
        )

        metrics.increment("jwt_tokens_generated")

        return jwt_token

    async def verify_jwt(self, jwt_token: str) -> Optional[dict[str, Any]]:
        """Verify JWT token."""
        if not jwt_token.startswith("jwt-"):
            return None

        try:
            parts = jwt_token[4:].split(".")
            if len(parts) != 2:
                return None

            session_id, signature = parts

            # Get payload from Redis
            payload = await self.redis_pool.get(
                f"{self._session_prefix}{session_id}"
            )

            if not payload:
                return None

            # Verify signature
            token_data = f"{payload['user_id']}:{session_id}:{payload['expires_at']}"
            expected_sig = hashlib.sha256(
                f"{token_data}:{self._secret_key}".encode()
            ).hexdigest()

            if signature != expected_sig:
                return None

            # Check expiry
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.now() > expires_at:
                await self.redis_pool.delete(
                    f"{self._session_prefix}{session_id}"
                )
                return None

            return payload

        except Exception as e:
            logger.error("jwt_verify_error", error=str(e))
            return None

    async def refresh_jwt(self, jwt_token: str) -> Optional[str]:
        """Refresh JWT token."""
        payload = await self.verify_jwt(jwt_token)

        if not payload:
            return None

        # Delete old session
        await self.redis_pool.delete(
            f"{self._session_prefix}{payload['session_id']}"
        )

        # Get user and generate new token
        from core.enterprise.permissions import get_permission_manager

        perm_manager = get_permission_manager()
        user = perm_manager.get_user(payload["user_id"])

        if not user:
            return None

        return await self.generate_jwt(user)


class ConcurrentAuthMiddleware:
    """Authentication middleware with distributed rate limiting."""

    def __init__(
        self,
        redis_pool: Optional[RedisConnectionPool] = None,
    ) -> None:
        self.redis_pool = redis_pool or get_redis_pool()
        self.token_manager = ConcurrentTokenManager(self.redis_pool)
        self.jwt_manager = ConcurrentJWTManager(self.redis_pool)

    async def authenticate(
        self,
        auth_header: Optional[str],
        api_key: Optional[str] = None,
    ) -> Optional[EnterpriseUser]:
        """Authenticate request."""
        from core.enterprise.permissions import get_permission_manager

        perm_manager = get_permission_manager()

        # Try API token first
        if api_key:
            token_data = await self.token_manager.verify_token(api_key)

            if token_data:
                user = perm_manager.get_user(token_data["user_id"])

                if user and user.is_active:
                    return user

        # Try JWT from header
        if auth_header:
            if auth_header.startswith("Bearer "):
                jwt_token = auth_header[7:]

                payload = await self.jwt_manager.verify_jwt(jwt_token)

                if payload:
                    user = perm_manager.get_user(payload["user_id"])

                    if user and user.is_active:
                        return user

        return None

    async def check_rate_limit(
        self,
        user_id: str,
        limit: int = 60,
    ) -> tuple[bool, int]:
        """Check distributed rate limit."""
        rate_limiter = DistributedRateLimiter(
            self.redis_pool,
            key=user_id,
            limit=limit,
            window=60,
        )

        allowed, current, remaining = await rate_limiter.check()

        return allowed, remaining

    async def create_user_session(
        self,
        email: str,
        password: str,
    ) -> Optional[dict[str, Any]]:
        """Create user session (login)."""
        from core.enterprise.permissions import get_permission_manager

        perm_manager = get_permission_manager()
        user = perm_manager.get_user_by_email(email)

        if not user:
            return None

        # Generate tokens
        api_token = await self.token_manager.generate_token(user.id)
        jwt_token = await self.jwt_manager.generate_jwt(user)

        # Store session
        session_store = get_session_store()
        session_id = jwt_token.split(".")[0].replace("jwt-", "")
        await session_store.create_session(
            session_id,
            user.id,
            {
                "email": user.email,
                "role": user.role.value,
            },
        )

        logger.info(
            "user_login_concurrent",
            user_id=user.id,
            email=email,
        )

        metrics.increment("user_logins")

        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "api_token": api_token,
            "jwt_token": jwt_token,
            "expires_at": (
                datetime.now() + timedelta(hours=8)
            ).isoformat(),
        }

    async def logout(self, jwt_token: str) -> bool:
        """Logout user."""
        payload = await self.jwt_manager.verify_jwt(jwt_token)

        if payload:
            # Delete session
            await self.redis_pool.delete(
                f"{self._session_prefix}{payload['session_id']}"
            )

            # Delete session store
            session_store = get_session_store()
            await session_store.delete_session(payload["session_id"])

            logger.info("user_logout_concurrent", user_id=payload["user_id"])

            metrics.increment("user_logouts")

            return True

        return False


class ConcurrentDataIsolationManager:
    """Data isolation manager with Redis-backed scope storage."""

    def __init__(self, redis_pool: Optional[RedisConnectionPool] = None) -> None:
        self.redis_pool = redis_pool or get_redis_pool()
        self._scope_prefix = "scope:"
        self._team_members_prefix = "team_members:"
        self._dept_teams_prefix = "dept_teams:"
        self._lock_prefix = "isolation_lock:"

    async def set_user_scope(
        self,
        user_id: str,
        team_id: Optional[str] = None,
        department_id: Optional[str] = None,
        organization_id: str = "",
    ) -> dict[str, Any]:
        """Set data scope for a user."""
        from core.enterprise.permissions import UserRole, get_permission_manager

        perm_manager = get_permission_manager()
        user = perm_manager.get_user(user_id)

        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Determine scope type based on role
        scope_type = "user"

        if user.role == UserRole.ADMIN:
            scope_type = "organization"
        elif user.role == UserRole.MANAGER:
            if department_id:
                scope_type = "department"
            elif team_id:
                scope_type = "team"

        scope_data = {
            "user_id": user_id,
            "team_id": team_id or "",
            "department_id": department_id or "",
            "organization_id": organization_id,
            "scope_type": scope_type,
            "allowed_resources": [],
            "denied_resources": [],
        }

        # Store scope with lock
        lock = DistributedLock(
            self.redis_pool,
            f"{self._lock_prefix}{user_id}",
            timeout=5,
        )

        async with lock.locked():
            await self.redis_pool.set(
                f"{self._scope_prefix}{user_id}",
                scope_data,
                expire=86400,  # 24 hours
            )

        logger.info(
            "scope_set_concurrent",
            user_id=user_id,
            scope_type=scope_type,
        )

        return scope_data

    async def get_user_scope(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get data scope for a user."""
        return await self.redis_pool.get(f"{self._scope_prefix}{user_id}")

    async def filter_data(
        self,
        user_id: str,
        data: list[dict[str, Any]],
        resource_type: str,
    ) -> list[dict[str, Any]]:
        """Filter data based on user scope."""
        scope = await self.get_user_scope(user_id)

        if not scope:
            logger.warning("no_scope_for_user_concurrent", user_id=user_id)
            return []

        filtered = []

        for item in data:
            if self._check_access(scope, item, resource_type):
                filtered.append(item)

        logger.info(
            "data_filtered_concurrent",
            user_id=user_id,
            resource_type=resource_type,
            original_count=len(data),
            filtered_count=len(filtered),
        )

        return filtered

    def _check_access(
        self,
        scope: dict[str, Any],
        item: dict[str, Any],
        resource_type: str,
    ) -> bool:
        """Check if item is accessible within scope."""
        resource_id = item.get("id", item.get("resource_id", ""))

        # Check denied resources
        denied = scope.get("denied_resources", [])
        if resource_id in denied:
            return False

        # Check allowed resources
        allowed = scope.get("allowed_resources", [])
        if resource_id in allowed:
            return True

        # Check ownership based on scope type
        return self._check_ownership(scope, item, resource_type)

    def _check_ownership(
        self,
        scope: dict[str, Any],
        item: dict[str, Any],
        resource_type: str,
    ) -> bool:
        """Check if item belongs to user's scope."""
        scope_type = scope.get("scope_type", "user")

        if scope_type == "organization":
            return item.get("organization_id") == scope.get("organization_id")

        if scope_type == "department":
            return item.get("department_id") == scope.get("department_id")

        if scope_type == "team":
            return item.get("team_id") == scope.get("team_id")

        return item.get("user_id") == scope.get("user_id") or \
               item.get("owner_id") == scope.get("user_id")

    async def grant_resource_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
    ) -> bool:
        """Grant explicit access to a resource."""
        lock = DistributedLock(
            self.redis_pool,
            f"{self._lock_prefix}{user_id}",
            timeout=5,
        )

        async with lock.locked():
            scope = await self.get_user_scope(user_id)

            if not scope:
                return False

            allowed = scope.get("allowed_resources", [])
            denied = scope.get("denied_resources", [])

            if resource_id not in allowed:
                allowed.append(resource_id)
                scope["allowed_resources"] = allowed

            if resource_id in denied:
                denied.remove(resource_id)
                scope["denied_resources"] = denied

            await self.redis_pool.set(
                f"{self._scope_prefix}{user_id}",
                scope,
                expire=86400,
            )

        logger.info(
            "resource_access_granted_concurrent",
            user_id=user_id,
            resource_id=resource_id,
        )

        return True


# Global concurrent instances
_concurrent_auth: Optional[ConcurrentAuthMiddleware] = None
_concurrent_isolation: Optional[ConcurrentDataIsolationManager] = None


def get_concurrent_auth() -> ConcurrentAuthMiddleware:
    """Get global concurrent auth middleware."""
    if _concurrent_auth is None:
        _concurrent_auth = ConcurrentAuthMiddleware()
    return _concurrent_auth


def get_concurrent_isolation() -> ConcurrentDataIsolationManager:
    """Get global concurrent data isolation manager."""
    if _concurrent_isolation is None:
        _concurrent_isolation = ConcurrentDataIsolationManager()
    return _concurrent_isolation