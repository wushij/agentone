"""tests/test_rag.py — RAG 测试"""

import pytest

from app.knowledge.loader import load_document
from app.knowledge.splitter import TextSplitter
from app.knowledge.embedder import Embedder


class TestLoader:
    def test_text_loader(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("Hello World", encoding="utf-8")
        docs = load_document(str(file))
        assert len(docs) == 1
        assert docs[0]["text"] == "Hello World"

    def test_markdown_loader(self, tmp_path):
        file = tmp_path / "test.md"
        file.write_text("# Title\nContent", encoding="utf-8")
        docs = load_document(str(file))
        assert len(docs) == 1
        assert "Title" in docs[0]["text"]


class TestSplitter:
    def test_split_small_text(self):
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        docs = [{"text": "Hello World", "metadata": {}}]
        chunks = splitter.split(docs)
        assert len(chunks) == 1

    def test_split_large_text(self):
        splitter = TextSplitter(chunk_size=10, chunk_overlap=2)
        docs = [{"text": "Hello World This is a test", "metadata": {}}]
        chunks = splitter.split(docs)
        assert len(chunks) >= 2


class TestEmbedder:
    @pytest.mark.asyncio
    async def test_embed_query(self):
        embedder = Embedder()
        result = await embedder.embed_query("test")
        assert len(result) == 1536


class TestBM25:
    def test_chinese_word_bm25_ranking(self):
        from app.services.rag.rag_service import bm25_scores
        query = "AgentOne 是什么系统？技术架构是什么？"
        docs = [
            "什么情况下会收到系统通知？系统通知通过 WebSocket 实时推送...",
            "AgentOne 是企业级 AI 智能体平台。前端采用 Vue 3，后端采用 FastAPI + LangGraph，技术架构完善...",
            "Prompt 模板的内容是什么格式？Markdown 格式...",
        ]
        scores = bm25_scores(query, docs)
        assert len(scores) == 3
        # doc[1] (AgentOne 技术架构) 应该得分远高于 doc[0] (系统通知) 和 doc[2] (Prompt 格式)
        assert scores[1] > scores[0]
        assert scores[1] > scores[2]