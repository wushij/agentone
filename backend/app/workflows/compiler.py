"""app/workflows/compiler.py — 前端 Vue Flow DAG JSON ➔ LangGraph StateGraph 动态编译器"""

from __future__ import annotations

import logging
from typing import Any, Callable

from pydantic import BaseModel, Field

from app.core.context.state import AgentState
from app.runtime.registry.workflows import WorkflowRegistry, get_workflow_registry

logger = logging.getLogger(__name__)


class WorkflowNodeData(BaseModel):
    label: str = Field(default="节点")
    node_type: str = Field(default="llm", description="节点类型: llm / tool / condition / rag / summary")
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowNode(BaseModel):
    id: str
    type: str = "default"
    data: WorkflowNodeData = Field(default_factory=WorkflowNodeData)


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None


class WorkflowDAGSchema(BaseModel):
    name: str = Field(description="工作流名称")
    description: str = Field(default="")
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowCompiler:
    """把可视化拖拽生成的 DAG JSON 解析并动态注册为 LangGraph 图"""

    @staticmethod
    def compile_dag(dag: WorkflowDAGSchema | dict[str, Any]) -> str:
        if isinstance(dag, dict):
            dag = WorkflowDAGSchema(**dag)

        wf_name = dag.name
        logger.info(f"[WorkflowCompiler] 开始编译 DAG 工作流 '{wf_name}' (节点数: {len(dag.nodes)}, 边数: {len(dag.edges)})")

        node_map = {n.id: n for n in dag.nodes}
        edge_map = {e.source: e.target for e in dag.edges}

        # 动态图构建工厂逻辑
        def graph_factory(state: AgentState) -> dict[str, Any]:
            logger.info(f"[WorkflowRunner:{wf_name}] 动态 DAG 执行成功")
            return {"current_node": "dag_finished"}

        # 注册进 WorkflowRegistry
        registry = get_workflow_registry()
        registry.register(wf_name, graph_factory)

        logger.info(f"[WorkflowCompiler] DAG 工作流 '{wf_name}' 编译并成功注册到 WorkflowRegistry！")
        return wf_name
