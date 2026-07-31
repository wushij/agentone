"""backend/app/tools/base.py"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError


@dataclass
class ToolResult:
    output: str
    duration_ms: int
    error: str = ""


class BaseTool(ABC):
    name: str
    description: str
    # Pydantic 参数 Schema（§4.4）：定义后 ToolManager 会在运行前校验，
    # 并用于生成 Function Calling 的 JSON Schema。None 表示自由 kwargs。
    args_schema: type[BaseModel] | None = None
    timeout_s: float = 30.0

    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError

    def validate_args(self, kwargs: dict[str, Any]) -> tuple[dict[str, Any], str]:
        """按 args_schema 校验并归一化参数；返回 (校验后参数, 错误信息)。"""
        if self.args_schema is None:
            return kwargs, ""
        internal = {k: v for k, v in kwargs.items() if k.startswith("_")}
        public = {k: v for k, v in kwargs.items() if not k.startswith("_")}
        try:
            validated = self.args_schema(**public)
        except ValidationError as exc:
            return kwargs, f"参数校验失败: {exc.errors()[0].get('msg', str(exc))}"
        return {**validated.model_dump(exclude_none=True), **internal}, ""

    def to_function_schema(self) -> dict[str, Any]:
        """导出 OpenAI Function Calling JSON Schema（供 bind_tools）。"""
        if self.args_schema is not None:
            schema = self.args_schema.model_json_schema()
            parameters = {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            }
        else:
            parameters = {"type": "object", "properties": {}, "required": []}
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
            },
        }
