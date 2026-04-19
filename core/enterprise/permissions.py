"""Enterprise Permission Management - Multi-user and role-based access control."""

from datetime import datetime
from typing import Any, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid


class UserRole(Enum):
    """User role levels."""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Permission(Enum):
    """Permission types."""
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    MANAGE_SKILLS = "manage_skills"

    # Manager permissions
    MANAGE_PRODUCTS = "manage_products"
    MANAGE_ORDERS = "manage_orders"
    MANAGE_REPORTS = "manage_reports"
    VIEW_ANALYTICS = "view_analytics"

    # Operator permissions
    PROCESS_ORDERS = "process_orders"
    HANDLE_CUSTOMER = "handle_customer"
    VIEW_ORDERS = "view_orders"
    CREATE_CONTENT = "create_content"

    # Viewer permissions
    VIEW_DATA = "view_data"
    VIEW_REPORTS = "view_reports"


# Role permission mappings
ROLE_PERMISSIONS: dict[UserRole, list[Permission]] = {
    UserRole.ADMIN: [
        Permission.MANAGE_USERS,
        Permission.MANAGE_SETTINGS,
        Permission.MANAGE_SKILLS,
        Permission.MANAGE_PRODUCTS,
        Permission.MANAGE_ORDERS,
        Permission.MANAGE_REPORTS,
        Permission.VIEW_ANALYTICS,
        Permission.PROCESS_ORDERS,
        Permission.HANDLE_CUSTOMER,
        Permission.VIEW_ORDERS,
        Permission.CREATE_CONTENT,
        Permission.VIEW_DATA,
        Permission.VIEW_REPORTS,
    ],
    UserRole.MANAGER: [
        Permission.MANAGE_PRODUCTS,
        Permission.MANAGE_ORDERS,
        Permission.MANAGE_REPORTS,
        Permission.VIEW_ANALYTICS,
        Permission.PROCESS_ORDERS,
        Permission.HANDLE_CUSTOMER,
        Permission.VIEW_ORDERS,
        Permission.CREATE_CONTENT,
        Permission.VIEW_DATA,
        Permission.VIEW_REPORTS,
    ],
    UserRole.OPERATOR: [
        Permission.PROCESS_ORDERS,
        Permission.HANDLE_CUSTOMER,
        Permission.VIEW_ORDERS,
        Permission.CREATE_CONTENT,
        Permission.VIEW_DATA,
        Permission.VIEW_REPORTS,
    ],
    UserRole.VIEWER: [
        Permission.VIEW_DATA,
        Permission.VIEW_REPORTS,
    ],
}


@dataclass
class EnterpriseUser:
    """Enterprise user profile."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    name: str = ""
    role: UserRole = UserRole.VIEWER
    department: str = ""
    permissions: list[Permission] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        # Admin always has all permissions
        if self.role == UserRole.ADMIN:
            return True

        # Check role-based permissions
        role_perms = ROLE_PERMISSIONS.get(self.role, [])
        if permission in role_perms:
            return True

        # Check custom permissions
        return permission in self.permissions

    def add_permission(self, permission: Permission) -> None:
        """Add custom permission."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now()

    def remove_permission(self, permission: Permission) -> None:
        """Remove custom permission."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now()


class PermissionManager:
    """Manage enterprise permissions."""

    def __init__(self) -> None:
        self._users: dict[str, EnterpriseUser] = {}
        self._teams: dict[str, list[str]] = {}  # team_id -> list of user_ids

    def create_user(
        self,
        email: str,
        name: str,
        role: UserRole,
        department: str = "",
    ) -> EnterpriseUser:
        """Create a new enterprise user."""
        user = EnterpriseUser(
            email=email,
            name=name,
            role=role,
            department=department,
            permissions=ROLE_PERMISSIONS.get(role, []).copy(),
        )

        self._users[user.id] = user

        return user

    def get_user(self, user_id: str) -> Optional[EnterpriseUser]:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[EnterpriseUser]:
        """Get user by email."""
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def update_user_role(
        self,
        user_id: str,
        new_role: UserRole,
    ) -> bool:
        """Update user role."""
        user = self._users.get(user_id)

        if not user:
            return False

        user.role = new_role
        user.permissions = ROLE_PERMISSIONS.get(new_role, []).copy()
        user.updated_at = datetime.now()

        return True

    def check_permission(
        self,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """Check if user has permission."""
        user = self._users.get(user_id)

        if not user:
            return False

        if not user.is_active:
            return False

        return user.has_permission(permission)

    def create_team(
        self,
        team_name: str,
        user_ids: list[str],
    ) -> str:
        """Create a team."""
        team_id = str(uuid.uuid4())
        self._teams[team_id] = user_ids

        return team_id

    def get_team_members(self, team_id: str) -> list[EnterpriseUser]:
        """Get team members."""
        user_ids = self._teams.get(team_id, [])
        members = []

        for uid in user_ids:
            user = self._users.get(uid)
            if user:
                members.append(user)

        return members

    def list_users(
        self,
        role: Optional[UserRole] = None,
        department: Optional[str] = None,
    ) -> list[EnterpriseUser]:
        """List users with optional filters."""
        users = list(self._users.values())

        if role:
            users = [u for u in users if u.role == role]

        if department:
            users = [u for u in users if u.department == department]

        return users

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        user = self._users.get(user_id)

        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.now()

        return True

    def activate_user(self, user_id: str) -> bool:
        """Activate user account."""
        user = self._users.get(user_id)

        if not user:
            return False

        user.is_active = True
        user.updated_at = datetime.now()

        return True


class DataIsolationManager:
    """Manage data isolation between users."""

    def __init__(self) -> None:
        self._user_data: dict[str, dict[str, Any]] = {}

    def get_user_data_scope(self, user_id: str) -> dict[str, Any]:
        """Get data scope for user."""
        user = self._users.get(user_id) if hasattr(self, '_users') else None

        # Default scope
        scope = {
            "user_id": user_id,
            "can_access_all": False,
            "accessible_users": [user_id],
        }

        if user:
            if user.role == UserRole.ADMIN:
                scope["can_access_all"] = True
                scope["accessible_users"] = list(self._users.keys()) if hasattr(self, '_users') else []

            elif user.role == UserRole.MANAGER:
                # Manager can access team data
                scope["accessible_users"] = self._get_team_members(user_id)

        return scope

    def _get_team_members(self, user_id: str) -> list[str]:
        """Get team members for user."""
        # Find teams where user is member
        members = [user_id]

        if hasattr(self, '_teams'):
            for team_id, team_members in self._teams.items():
                if user_id in team_members:
                    members.extend(team_members)

        return list(set(members))

    def filter_data_by_scope(
        self,
        data: list[dict[str, Any]],
        user_id: str,
        data_key: str = "user_id",
    ) -> list[dict[str, Any]]:
        """Filter data based on user scope."""
        scope = self.get_user_data_scope(user_id)

        if scope["can_access_all"]:
            return data

        accessible = scope["accessible_users"]

        filtered = [
            item for item in data
            if item.get(data_key) in accessible
        ]

        return filtered


# Global permission manager
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """Get global permission manager."""
    global _permission_manager

    if _permission_manager is None:
        _permission_manager = PermissionManager()

    return _permission_manager