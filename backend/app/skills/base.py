"""app/skills/base.py — 技能基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillResult:
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> SkillResult:
        ...