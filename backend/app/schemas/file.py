"""app/schemas/file.py — 文件资产 Pydantic Schema"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FileAssetOut(BaseModel):
    id: int
    filename: str
    filepath: str
    filesize: int
    mimetype: str
    kb_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
