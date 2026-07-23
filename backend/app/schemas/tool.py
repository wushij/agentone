"""app/schemas/tool.py — 工具配置 Pydantic Schema"""

from pydantic import BaseModel, ConfigDict


class ToolConfigOut(BaseModel):
    id: int
    name: str
    description: str
    enabled: bool
    config_json: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: dict
