 # RAG 示例

## 知识库检索示例

用户问题：「AgentOne 支持哪些数据库？」

检索结果：
1. MySQL - 主数据库，存储用户、会话、消息等核心数据
2. Redis - 缓存和会话管理
3. FAISS - 向量存储，用于知识库检索
4. Chroma - 可选的向量数据库
5. Milvus - 可选的向量数据库

## 检索策略

- 默认使用向量检索（cosine similarity）
- 支持混合检索（向量 + BM25）
- 支持重排序（Cross-Encoder Reranker）