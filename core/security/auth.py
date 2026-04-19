"""Security Module - Authentication, Authorization, Audit."""

from datetime import datetime, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field
import hashlib
import secrets
import uuid

from core.enterprise.permissions import (
    PermissionManager,
    EnterpriseUser,
    UserRole,
    Permission,
    get_permission_manager,
)
from core.logging import get_logger
from config import get_settings

logger = get_logger("security.auth")


@dataclass
class APIToken:
    """API Token for authentication."""
    token_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    token_hash: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    scopes: list[str] = field(default_factory=list)
    rate_limit: int = 60  # requests per minute


@dataclass
class JWTPayload:
    """JWT token payload."""
    user_id: str
    email: str
    role: str
    permissions: list[str]
    issued_at: datetime
    expires_at: datetime
    session_id: str = ""


class TokenManager:
    """Manage API tokens."""

    def __init__(self) -> None:
        self._tokens: dict[str, APIToken] = {}
        self._user_tokens: dict[str, list[str]] = {}
        self._token_expiry_hours = 24

    def generate_token(
        self,
        user_id: str,
        scopes: Optional[list[str]] = None,
        expires_hours: int = 24,
    ) -> str:
        """Generate a new API token."""
        # Generate random token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # Create token record
        api_token = APIToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now() + timedelta(hours=expires_hours),
            scopes=scopes or ["read", "write"],
        )

        self._tokens[api_token.token_id] = api_token

        # Track user tokens
        if user_id not in self._user_tokens:
            self._user_tokens[user_id] = []

        self._user_tokens[user_id].append(api_token.token_id)

        logger.info(
            "token_generated",
            user_id=user_id,
            token_id=api_token.token_id,
            expires_hours=expires_hours,
        )

        # Return raw token (user keeps this)
        return f"sk-{raw_token}"

    def verify_token(self, raw_token: str) -> Optional[APIToken]:
        """Verify and return token info."""
        if not raw_token.startswith("sk-"):
            return None

        # Hash the token
        token_key = raw_token[3:]  # Remove "sk-" prefix
        token_hash = hashlib.sha256(token_key.encode()).hexdigest()

        # Find token by hash
        for token_id, api_token in self._tokens.items():
            if api_token.token_hash == token_hash:
                # Check if active and not expired
                if not api_token.is_active:
                    return None

                if api_token.expires_at and datetime.now() > api_token.expires_at:
                    api_token.is_active = False
                    return None

                return api_token

        return None

    def revoke_token(self, token_id: str) -> bool:
        """Revoke a token."""
        if token_id in self._tokens:
            self._tokens[token_id].is_active = False

            logger.info(
                "token_revoked",
                token_id=token_id,
            )

            return True

        return False

    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        count = 0

        if user_id in self._user_tokens:
            for token_id in self._user_tokens[user_id]:
                if self.revoke_token(token_id):
                    count += 1

            self._user_tokens[user_id] = []

        return count

    def cleanup_expired(self) -> int:
        """Clean up expired tokens."""
        count = 0
        now = datetime.now()

        for token_id, api_token in list(self._tokens.items()):
            if api_token.expires_at and now > api_token.expires_at:
                self._tokens[token_id].is_active = False
                count += 1

        return count


class JWTManager:
    """Manage JWT tokens."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._secret_key = secrets.token_urlsafe(32)  # Should be from config in production
        self._tokens: dict[str, JWTPayload] = {}
        self._expiry_hours = 8

    def generate_jwt(
        self,
        user: EnterpriseUser,
        session_id: Optional[str] = None,
    ) -> str:
        """Generate JWT token."""
        payload = JWTPayload(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            permissions=[p.value for p in user.permissions],
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self._expiry_hours),
            session_id=session_id or str(uuid.uuid4()),
        )

        # Store payload
        self._tokens[payload.session_id] = payload

        # In production, use proper JWT library like pyjwt
        # Here we use a simplified approach for MVP
        token_data = f"{payload.user_id}:{payload.session_id}:{payload.expires_at.isoformat()}"
        signature = hashlib.sha256(
            f"{token_data}:{self._secret_key}".encode()
        ).hexdigest()

        jwt_token = f"jwt-{payload.session_id}.{signature}"

        logger.info(
            "jwt_generated",
            user_id=user.id,
            session_id=payload.session_id,
        )

        return jwt_token

    def verify_jwt(self, jwt_token: str) -> Optional[JWTPayload]:
        """Verify JWT token."""
        if not jwt_token.startswith("jwt-"):
            return None

        try:
            parts = jwt_token[4:].split(".")
            if len(parts) != 2:
                return None

            session_id, signature = parts

            # Get payload
            payload = self._tokens.get(session_id)

            if not payload:
                return None

            # Verify signature
            token_data = f"{payload.user_id}:{payload.session_id}:{payload.expires_at.isoformat()}"
            expected_sig = hashlib.sha256(
                f"{token_data}:{self._secret_key}".encode()
            ).hexdigest()

            if signature != expected_sig:
                return None

            # Check expiry
            if datetime.now() > payload.expires_at:
                del self._tokens[session_id]
                return None

            return payload

        except Exception as e:
            logger.error("jwt_verify_error", error=str(e))
            return None

    def refresh_jwt(self, jwt_token: str) -> Optional[str]:
        """Refresh JWT token."""
        payload = self.verify_jwt(jwt_token)

        if not payload:
            return None

        # Get user and generate new token
        perm_manager = get_permission_manager()
        user = perm_manager.get_user(payload.user_id)

        if not user:
            return None

        # Delete old
        del self._tokens[payload.session_id]

        # Generate new
        return self.generate_jwt(user)


class AuthMiddleware:
    """Authentication middleware for API."""

    def __init__(self) -> None:
        self.token_manager = TokenManager()
        self.jwt_manager = JWTManager()
        self.permission_manager = get_permission_manager()
        self._rate_limits: dict[str, list[datetime]] = {}

    async def authenticate(
        self,
        auth_header: Optional[str],
        api_key: Optional[str] = None,
    ) -> Optional[EnterpriseUser]:
        """Authenticate request."""
        # Try API token first
        if api_key:
            token = self.token_manager.verify_token(api_key)

            if token:
                user = self.permission_manager.get_user(token.user_id)

                if user and user.is_active:
                    return user

        # Try JWT from header
        if auth_header:
            if auth_header.startswith("Bearer "):
                jwt_token = auth_header[7:]

                payload = self.jwt_manager.verify_jwt(jwt_token)

                if payload:
                    user = self.permission_manager.get_user(payload.user_id)

                    if user and user.is_active:
                        return user

        return None

    async def check_permission(
        self,
        user: EnterpriseUser,
        permission: Permission,
    ) -> bool:
        """Check user permission."""
        return user.has_permission(permission)

    async def check_rate_limit(
        self,
        user_id: str,
        limit: int = 60,
    ) -> bool:
        """Check rate limit for user."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Get user requests
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []

        requests = self._rate_limits[user_id]

        # Remove old requests
        requests = [r for r in requests if r > minute_ago]
        self._rate_limits[user_id] = requests

        # Check limit
        if len(requests) >= limit:
            logger.warning(
                "rate_limit_exceeded",
                user_id=user_id,
                requests=len(requests),
                limit=limit,
            )
            return False

        # Record request
        requests.append(now)

        return True

    async def create_user_session(
        self,
        email: str,
        password: str,
    ) -> Optional[dict[str, Any]]:
        """Create user session (login)."""
        # Verify password (simplified for MVP)
        user = self.permission_manager.get_user_by_email(email)

        if not user:
            return None

        # In production, verify password hash
        # For MVP, we assume valid

        # Generate tokens
        api_token = self.token_manager.generate_token(user.id)
        jwt_token = self.jwt_manager.generate_jwt(user)

        logger.info(
            "user_login",
            user_id=user.id,
            email=email,
        )

        return {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "api_token": api_token,
            "jwt_token": jwt_token,
            "expires_at": (datetime.now() + timedelta(hours=8)).isoformat(),
        }

    async def logout(self, jwt_token: str) -> bool:
        """Logout user."""
        payload = self.jwt_manager.verify_jwt(jwt_token)

        if payload:
            # Revoke session
            if payload.session_id in self.jwt_manager._tokens:
                del self.jwt_manager._tokens[payload.session_id]

            logger.info(
                "user_logout",
                user_id=payload.user_id,
            )

            return True

        return False


# Global auth middleware
_auth_middleware: Optional[AuthMiddleware] = None


def get_auth_middleware() -> AuthMiddleware:
    """Get global auth middleware."""
    global _auth_middleware

    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()

    return _auth_middleware