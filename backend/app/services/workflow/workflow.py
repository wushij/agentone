"""app/services/workflow.py — 工作流服务"""

from typing import Any

from app.workflows.chat import ChatWorkflow
from app.workflows.rag import RagWorkflow
from app.workflows.coding import CodingWorkflow
from app.workflows.research import ResearchWorkflow

_WORKFLOWS = {
    "chat": ChatWorkflow(),
    "rag": RagWorkflow(),
    "coding": CodingWorkflow(),
    "research": ResearchWorkflow(),
}


class WorkflowService:
    def list_workflows(self) -> list[dict[str, str]]:
        return [
            {"name": w.name, "description": w.description}
            for w in _WORKFLOWS.values()
        ]

    def get_workflow(self, name: str):
        return _WORKFLOWS.get(name)

    async def execute(self, name: str, user_input: str, **kwargs: Any):
        workflow = self.get_workflow(name)
        if workflow is None:
            raise ValueError(f"Workflow not found: {name}")
        return workflow.run(user_input, **kwargs)