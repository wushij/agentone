"""app/schemas/knowledge.py — 知识库 Pydantic Schema"""

from pydantic import BaseModel


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str = "text-embedding-3-small"


class KnowledgeQueryRequest(BaseModel):
    query: str
    kb_id: str | None = None
    top_k: int = 4
