"""backend/app/services/role_service.py"""

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": ["*"],
    "admin": [
        "chat:read",
        "chat:write",
        "session:manage",
        "prompt:manage",
        "model:manage",
        "tool:manage",
        "log:read",
        "config:manage",
        "user:manage",
    ],
    "user": [
        "chat:read",
        "chat:write",
        "session:manage",
    ],
}


class RoleService:
    def get_permissions(self, role: str) -> list[str]:
        return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["user"])

    def has_full_access(self, role: str) -> bool:
        return role == "super_admin"
