"""app/runtime/registry/workflows.py — 工作流注册表"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    def __init__(self) -> None:
        self._workflows: dict[str, Callable] = {}

    def register(self, name: str, factory: Callable) -> None:
        self._workflows[name] = factory
        logger.info(f"[WorkflowRegistry] 已注册工作流: '{name}'")

    def get(self, name: str) -> Callable | None:
        return self._workflows.get(name)

    def list_all(self) -> list[str]:
        return list(self._workflows.keys())


_workflow_registry: WorkflowRegistry | None = None


def get_workflow_registry() -> WorkflowRegistry:
    global _workflow_registry
    if _workflow_registry is None:
        _workflow_registry = WorkflowRegistry()
    return _workflow_registry
