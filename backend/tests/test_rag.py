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