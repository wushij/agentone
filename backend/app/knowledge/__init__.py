"""app/knowledge/__init__.py — RAG 知识库模块根导出"""

from app.knowledge.embedder import Embedder
from app.knowledge.loader import load_document
from app.knowledge.manager import KnowledgeManager, knowledge_manager
from app.knowledge.splitter import TextSplitter

__all__ = [
    "Embedder",
    "KnowledgeManager",
    "TextSplitter",
    "knowledge_manager",
    "load_document",
]
