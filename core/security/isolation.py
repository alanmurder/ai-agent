"""Data Isolation - Scope-based data filtering for enterprise multi-user environment."""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from core.enterprise.permissions import (
    EnterpriseUser,
    UserRole,
    get_permission_manager,
)
from core.logging import get_logger
from core.security.audit import AuditEventType, get_audit_logger

logger = get_logger("security.isolation")


@dataclass
class DataScope:
    """Data access scope definition."""
    user_id: str
    team_id: Optional[str] = None
    department_id: Optional[str] = None
    organization_id: str = ""
    scope_type: str = "user"  # user, team, department, organization
    allowed_resources: list[str] = field(default_factory=list)
    denied_resources: list[str] = field(default_factory=list)


class DataIsolationManager:
    """Manage data isolation for multi-user environment."""

    def __init__(self) -> None:
        self.permission_manager = get_permission_manager()
        self.audit_logger = get_audit_logger()
        self._scopes: dict[str, DataScope] = {}
        self._team_members: dict[str, list[str]] = {}
        self._department_teams: dict[str, list[str]] = {}

    def set_user_scope(
        self,
        user_id: str,
        team_id: Optional[str] = None,
        department_id: Optional[str] = None,
        organization_id: str = "",
    ) -> DataScope:
        """Set data scope for a user."""
        user = self.permission_manager.get_user(user_id)

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

        scope = DataScope(
            user_id=user_id,
            team_id=team_id,
            department_id=department_id,
            organization_id=organization_id,
            scope_type=scope_type,
        )

        self._scopes[user_id] = scope

        logger.info(
            "scope_set",
            user_id=user_id,
            scope_type=scope_type,
            team_id=team_id,
        )

        return scope

    def get_user_scope(self, user_id: str) -> Optional[DataScope]:
        """Get data scope for a user."""
        return self._scopes.get(user_id)

    def filter_data(
        self,
        user_id: str,
        data: list[dict[str, Any]],
        resource_type: str,
    ) -> list[dict[str, Any]]:
        """Filter data based on user scope."""
        scope = self.get_user_scope(user_id)

        if not scope:
            logger.warning("no_scope_for_user", user_id=user_id)
            return []

        filtered = []

        for item in data:
            if self._check_access(scope, item, resource_type):
                filtered.append(item)

        # Audit data access
        self.audit_logger.log_data_access(
            user_id=user_id,
            access_type=AuditEventType.DATA_READ,
            resource_type=resource_type,
            resource_id=f"{len(filtered)}_items",
        )

        logger.info(
            "data_filtered",
            user_id=user_id,
            resource_type=resource_type,
            original_count=len(data),
            filtered_count=len(filtered),
        )

        return filtered

    def check_write_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        resource_data: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Check if user can write to resource."""
        scope = self.get_user_scope(user_id)

        if not scope:
            return False

        # Check denied resources first
        if resource_id in scope.denied_resources:
            self._log_access_denied(user_id, resource_type, resource_id, "explicit_deny")
            return False

        # Check allowed resources
        if resource_id in scope.allowed_resources:
            return True

        # Check scope ownership
        if resource_data:
            if not self._check_ownership(scope, resource_data, resource_type):
                self._log_access_denied(user_id, resource_type, resource_id, "ownership")
                return False

        # Default: scope_type determines access
        access_allowed = self._scope_allows_write(scope, resource_type)

        if not access_allowed:
            self._log_access_denied(user_id, resource_type, resource_id, "scope_limit")

        return access_allowed

    def _check_access(
        self,
        scope: DataScope,
        item: dict[str, Any],
        resource_type: str,
    ) -> bool:
        """Check if item is accessible within scope."""
        # Check denied resources
        resource_id = item.get("id", item.get("resource_id", ""))

        if resource_id in scope.denied_resources:
            return False

        # Check allowed resources
        if resource_id in scope.allowed_resources:
            return True

        # Check ownership based on scope type
        return self._check_ownership(scope, item, resource_type)

    def _check_ownership(
        self,
        scope: DataScope,
        item: dict[str, Any],
        resource_type: str,
    ) -> bool:
        """Check if item belongs to user's scope."""
        if scope.scope_type == "organization":
            # Admin can see all
            return item.get("organization_id") == scope.organization_id

        if scope.scope_type == "department":
            # Manager can see department data
            return item.get("department_id") == scope.department_id

        if scope.scope_type == "team":
            # Manager can see team data
            return item.get("team_id") == scope.team_id

        # Regular user sees only their own data
        return item.get("user_id") == scope.user_id or item.get("owner_id") == scope.user_id

    def _scope_allows_write(self, scope: DataScope, resource_type: str) -> bool:
        """Check if scope allows write access."""
        if scope.scope_type == "organization":
            return True

        # Restricted resource types
        restricted_resources = {
            "organization_settings": "organization",
            "department_settings": "department",
            "team_settings": "team",
        }

        required_scope = restricted_resources.get(resource_type)

        if required_scope:
            scope_levels = {"user": 0, "team": 1, "department": 2, "organization": 3}
            return scope_levels.get(scope.scope_type, 0) >= scope_levels.get(required_scope, 3)

        return True

    def _log_access_denied(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        reason: str,
    ) -> None:
        """Log access denied event."""
        self.audit_logger.log_event(
            event_type=AuditEventType.TOOL_DENIED,
            user_id=user_id,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "reason": reason,
            },
            success=False,
            error_message=f"Data access denied: {reason}",
        )

        logger.warning(
            "data_access_denied",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
        )

    def add_team_member(self, team_id: str, user_id: str) -> None:
        """Add user to team."""
        if team_id not in self._team_members:
            self._team_members[team_id] = []

        if user_id not in self._team_members[team_id]:
            self._team_members[team_id].append(user_id)

        # Update user scope
        scope = self.get_user_scope(user_id)

        if scope:
            scope.team_id = team_id

    def get_team_members(self, team_id: str) -> list[str]:
        """Get all members of a team."""
        return self._team_members.get(team_id, [])

    def add_team_to_department(self, department_id: str, team_id: str) -> None:
        """Add team to department."""
        if department_id not in self._department_teams:
            self._department_teams[department_id] = []

        if team_id not in self._department_teams[department_id]:
            self._department_teams[department_id].append(team_id)

    def get_department_teams(self, department_id: str) -> list[str]:
        """Get all teams in department."""
        return self._department_teams.get(department_id, [])

    def grant_resource_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
    ) -> bool:
        """Grant explicit access to a resource."""
        scope = self.get_user_scope(user_id)

        if not scope:
            return False

        if resource_id not in scope.allowed_resources:
            scope.allowed_resources.append(resource_id)

        # Remove from denied if present
        if resource_id in scope.denied_resources:
            scope.denied_resources.remove(resource_id)

        logger.info(
            "resource_access_granted",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        return True

    def deny_resource_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
    ) -> bool:
        """Deny explicit access to a resource."""
        scope = self.get_user_scope(user_id)

        if not scope:
            return False

        if resource_id not in scope.denied_resources:
            scope.denied_resources.append(resource_id)

        # Remove from allowed if present
        if resource_id in scope.allowed_resources:
            scope.allowed_resources.remove(resource_id)

        logger.info(
            "resource_access_denied",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        return True


class DataIsolationMiddleware:
    """Middleware for data isolation in API responses."""

    def __init__(self) -> None:
        self.isolation_manager = DataIsolationManager()

    def filter_response(
        self,
        user_id: str,
        response: dict[str, Any],
        resource_type: str,
    ) -> dict[str, Any]:
        """Filter API response data for user scope."""
        # Get user scope
        scope = self.isolation_manager.get_user_scope(user_id)

        if not scope:
            return {"error": "No scope defined for user", "data": []}

        # Filter data arrays
        if "data" in response and isinstance(response["data"], list):
            response["data"] = self.isolation_manager.filter_data(
                user_id=user_id,
                data=response["data"],
                resource_type=resource_type,
            )

        if "items" in response and isinstance(response["items"], list):
            response["items"] = self.isolation_manager.filter_data(
                user_id=user_id,
                data=response["items"],
                resource_type=resource_type,
            )

        if "results" in response and isinstance(response["results"], list):
            response["results"] = self.isolation_manager.filter_data(
                user_id=user_id,
                data=response["results"],
                resource_type=resource_type,
            )

        # Filter nested data
        for key in ["orders", "products", "customers", "reports", "sessions"]:
            if key in response and isinstance(response[key], list):
                response[key] = self.isolation_manager.filter_data(
                    user_id=user_id,
                    data=response[key],
                    resource_type=key,
                )

        return response

    def check_operation_allowed(
        self,
        user_id: str,
        operation: str,
        resource_type: str,
        resource_id: str,
        resource_data: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str]]:
        """Check if operation is allowed for user."""
        if operation in ("read", "view", "list"):
            return True, None

        if operation in ("write", "update", "create"):
            allowed = self.isolation_manager.check_write_access(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_data=resource_data,
            )
            return allowed, None if allowed else "Write access denied"

        if operation in ("delete", "remove"):
            # Delete requires stricter check
            scope = self.isolation_manager.get_user_scope(user_id)

            if not scope:
                return False, "No scope defined"

            if scope.scope_type in ("organization", "department"):
                allowed = self.isolation_manager.check_write_access(
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_data=resource_data,
                )
                return allowed, None if allowed else "Delete access denied"

            return False, "Delete requires manager or admin role"

        return False, f"Unknown operation: {operation}"


# Global isolation manager
_isolation_manager: Optional[DataIsolationManager] = None
_isolation_middleware: Optional[DataIsolationMiddleware] = None


def get_isolation_manager() -> DataIsolationManager:
    """Get global data isolation manager."""
    global _isolation_manager

    if _isolation_manager is None:
        _isolation_manager = DataIsolationManager()

    return _isolation_manager


def get_isolation_middleware() -> DataIsolationMiddleware:
    """Get global data isolation middleware."""
    global _isolation_middleware

    if _isolation_middleware is None:
        _isolation_middleware = DataIsolationMiddleware()

    return _isolation_middleware