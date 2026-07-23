"""app/schemas/model.py — 模型配置 Pydantic Schema"""

from pydantic import BaseModel, ConfigDict


class ModelConfigOut(BaseModel):
    id: int
    provider: str
    model_name: str
    is_active: bool
    api_key_masked: str | None = None

    model_config = ConfigDict(from_attributes=True)
