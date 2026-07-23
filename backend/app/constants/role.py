"""app/constants/role.py — 角色枚举"""

from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"
    PLANNER = "planner"
    WRITER = "writer"
    REVIEWER = "reviewer"
    ANALYST = "analyst"
    CODER = "coder"
