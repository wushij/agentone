"""app/constants/status.py — 状态枚举"""

from enum import Enum, IntEnum


class StatusEnum(IntEnum):
    INACTIVE = 0
    ACTIVE = 1
    PENDING = 2
    DELETED = -1


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
