# AgentOne 🚀

**AgentOne** 是一个企业级 AI 智能体平台，以统一的 **Agent Runtime（运行时内核）** 为中心：基于 **LangGraph** 的 **Function Calling + ReAct 多步推理循环**，配合分层持久记忆、生产级 RAG、成本治理与在线评测；后端 **FastAPI**，前端 **Vue3 + Element Plus**。

---

## 🌟 核心能力

* **🧠 自治推理内核 (Agent Runtime)**：Function Calling 让模型自主选工具带参，**ReAct 多步循环**可并行调多工具，**结构化反思闭环**（reviewer 产出 `verdict` 驱动 retry/replan）；不支持 FC 的模型自动回退规则意图。
* **🗃️ 分层持久记忆 (Memory)**：会话/情节/语义三层记忆落库 MySQL，**真向量检索 + `importance×recency×relevance` 融合排序**，会话后自动提取用户偏好、定时遗忘衰减；个人中心「AI 记忆」页可查看/删除/置顶。
* **📚 生产级 RAG**：Qdrant 向量库（嵌入式免 Docker / 服务端 HNSW 二选一，未配置自动回退 JSON）+ **真 BM25×向量 RRF 混合检索** + Cross-Encoder 重排（可选）+ 查询变换（Rewrite/MultiQuery）+ 三级检索缓存（命中率入 `/metrics`）+ 引用溯源可点击展开。
* **🛠️ 工具框架与插件**：Pydantic `args_schema` 参数校验、并行执行、单工具超时与连续失败熔断；统一 Plugin 抽象已接入 **MCP** 生态（挂任意 MCP server 即用）。
* **💰 成本治理 (Cost Manager)**：每次 LLM/向量化调用落 `cost_records`，按用户/天/模型/Agent 角色多维出账 + 日限额，管理后台「成本中心」可视化。
* **🧭 模型路由 (Model Router)**：按角色路由不同模型 + fallback + 指数退避重试；真实 token 透传（LangChain `usage_metadata`）。
* **🧪 在线评测 (Evals)**：工具选择数据集 + RAG 三元组 LLM-as-Judge（faithfulness/relevancy/precision），CI 门禁防质量回退。
* **📊 实时可观测**：工作流节点状态经 WebSocket 实时推送；`trace_id` 贯穿领域事件与成本；Prometheus `/metrics` 端点。
* **🛡️ 事件驱动解耦**：EventBus 镜像 Redis Stream（跨进程/重放），工具日志与审计改为事件订阅；SettingsStore 三级优先级求值（MySQL > `.env` > 默认）。
* **📜 多维日志中心**：用户行为、Agent 执行、Tool 状态、系统心跳全维度审计。
* **💎 Premium 视觉设计**：靛蓝（Indigo）高阶毛玻璃设计系统，支持主题预设与深浅色模式。

---

## 🛠️ 技术栈

* **前端**：Vue 3 + Vite + TypeScript + Pinia + Element Plus + Vanilla CSS + Web Workers
* **后端**：FastAPI + LangGraph + LangChain + SQLAlchemy + **Alembic（数据库迁移）** + Redis（Stream 领域事件 / Pub-Sub 心跳 / SSE 锁）
* **向量与检索**：Qdrant（嵌入式 `path` / 服务端 HTTP，未配置回退 JSON）+ 内置 BM25/RRF 混合 + tiktoken 预算 + （可选）sentence-transformers 重排
* **工具生态**：MCP（Model Context Protocol）客户端接入
* **模型提供商**：DeepSeek / OpenAI / Qwen / Gemini / Ollama + Mock
* **数据库**：MySQL（业务与对话持久化）+ Redis（缓存、限流与实时推送）

---

## 📁 架构与项目结构

```text
AgentOne/
├── backend/                             # FastAPI 后端服务根目录
│   ├── main.py                          # FastAPI 主程序入口（路由挂载、中间件与 CORS）
│   ├── data/                            # 唯一运行时物理落盘根目录（gitignore 忽略）
│   │   ├── uploads/                     # 用户上传文件
│   │   ├── knowledge/                   # 知识库原始文件
│   │   └── exports/                     # 导出数据存储
│   ├── app/                             # 后端核心业务代码
│       ├── runtime/                     # ★ Agent Runtime：平台核心（API 层唯一入口）
│       │   ├── runtime.py               # 统一门面（组件总装配）
│       │   ├── executor/                # Function Calling 绑定 + loops/react 多步循环
│       │   ├── context/                 # Context Builder（唯一 Prompt 拼装）+ tiktoken 预算
│       │   ├── state/                   # 分域 State + reducer + 版本化
│       │   ├── tools/                   # Tool Manager + Plugin 抽象 + MCP 来源
│       │   ├── router/                  # Model Router（角色路由/fallback）
│       │   ├── cost/                    # Cost Manager（多维计量/聚合/限额）
│       │   ├── evals/                   # LLM-as-Judge 评测器
│       │   └── schema.py                # 统一 AgentOutput / SourceRef
│       ├── agents/                      # Agent 节点（planner/reviewer 结构化/writer）
│       ├── api/                         # RESTful API（v1/ 含 memories、cost、metrics）
│       ├── cache/                       # 多级缓存（Embedding/RAG/LLM，含命中率）
│       ├── config/                      # Pydantic 环境变量配置（含 QDRANT_URL）
│       ├── constants/                   # 全局常量与枚举
│       ├── core/                        # 图执行引擎 GraphRunner（由 Runtime 调度）
│       ├── db/                          # SQLAlchemy Engine & Redis 连接池
│       ├── events/                      # EventBus + Redis Stream 消费组 + 领域订阅方
│       ├── knowledge/                   # RAG：stores/qdrant、transform 查询变换、reranker、retrievers
│       ├── llm/                         # LLM 模型工厂与 Mock 模型
│       ├── memory/                      # 分层持久记忆（persistent 落库 + scheduler 遗忘）
│       ├── middleware/                  # 全局异常拦截、请求审计与限流
│       ├── models/                      # SQLAlchemy ORM（含 memories/cost_records/knowledge_bases）
│       ├── monitor/                     # 指标/Token/Cost 估算与 Prometheus 导出
│       ├── prompts/                     # 系统级与模板级 Prompt 仓库 (.md)
│       ├── providers/                   # 大模型厂商适配 (DeepSeek/OpenAI/Qwen/Gemini/Ollama)
│       ├── repositories/                # 数据持久化仓储层
│       ├── schemas/                     # Pydantic 数据契约校验层
│       ├── services/                    # 业务领域服务（含 rag/kb_store、prompt/prompt_ab）
│       ├── skills/                      # Agent Skill 扩展能力集
│       ├── storage/                     # 唯一磁盘 Path 访问控制层 (paths.py)
│       ├── tools/                       # Agent 内置工具（BaseTool + args_schema）
│       ├── utils/                       # 通用基础工具
│       └── workflows/                   # 场景工作流 (Chat, RAG, Coding, Research)
│   └── alembic/                         # ★ 数据库迁移 (alembic.ini + versions/，baseline + 阶段2 新表)
├── frontend/                            # Vue 3 前端工程
│   └── src/                             # 前端源码
│       ├── api/                         # API 请求封装（axios 解包、静默刷新；含 memory、cost）
│       ├── components/                  # UI 组件包 (common/admin/auth/chat/dashboard/layout/profile)
│       ├── composables/                 # Vue 3 组合式逻辑复用函数 (useChatView, useDashboard...)
│       ├── constants/                   # 前端全局常量 (storage key 单一来源)
│       ├── directives/                  # Vue 自定义指令集 (v-permission, v-copy, v-debounce)
│       ├── enums/                       # 前端业务枚举 (ChatStatus, MessageRole...)
│       ├── layouts/                     # 系统 Shell 整体布局 (AppLayout.vue)
│       ├── plugins/                     # 插件集中注册器 (Pinia, Router, Directives...)
│       ├── router/                      # Vue Router 路由配置与全局守卫
│       ├── stores/                      # Pinia 状态集中管理 (User, Chat, Agent, Theme)
│       ├── styles/                      # 样式系统与主题令牌 (theme/ tokens/ presets/ dark-vars)
│       ├── types/                       # TypeScript 类型声明库
│       ├── utils/                       # 前端实用工具函数
│       ├── views/                       # 页面视图（ChatView、Dashboard、MemoryView、admin/CostView、agent/）
│       └── workers/                     # Web Worker 后台计算线程 (markdown.worker.ts)
├── sql/                                 # 数据库结构与初始化脚本
│   ├── init.sql                         # 一键建库建表与演示账号初始化 SQL
│   └── migrations/                      # 增量版本数据库迁移脚本
├── deploy/                              # Docker Compose 与 Nginx 部署模板
└── docs/                                # 架构设计与知识库文档
```

---

## ⚡ 快速开始

### 1. 启动基础设施（MySQL + Redis + Qdrant）
```bash
cd deploy
docker compose -f docker-compose.infra.yml up -d
```
> 不想用 Docker？Qdrant 可改用**嵌入式本地模式**（见第 3 步 `QDRANT_URL=./qdrant_db`），无需单独起服务。

### 2. 初始化数据库（Alembic 迁移）
```bash
cd backend
pip install -r requirements.txt
python -m alembic upgrade head   # baseline + 阶段2 新表 (memories/cost_records/knowledge_bases)
```
> 已有旧库（手工导入过 `sql/init.sql`）首次接入：`python -m alembic stamp head` 收编为基线后再 `upgrade head`。

### 3. 配置并运行后端
```bash
cd backend
cp .env.example .env
uvicorn main:app --reload --port 8000   # 嵌入式 Qdrant 仅单 worker
```
**最小 `.env`（本地无 Docker 最优）**：
```env
QDRANT_URL=./qdrant_db     # 嵌入式向量库，免 Docker、数据持久化；置空=回退 JSON
# DATABASE_URL / REDIS_URL 本地默认即可
# API Key 无需写入 .env：启动后在管理后台「模型管理」页填写并设为默认（对话与向量化均取默认模型的 Key）
```
> 说明：嵌入式 Qdrant 是纯 Python 本地模式（持久化 + 免 Docker），同一目录同时只允许一个进程占用（故单 worker）；追求 HNSW 高性能请用服务端模式 `QDRANT_URL=http://127.0.0.1:6333`。本地 cross-encoder 重排为可选：`pip install sentence-transformers`（依赖 torch，不装则降级启发式重排）。

### 4. 运行前端
```bash
cd frontend
npm install
npm run dev
```
访问本地开发页面：`http://localhost:3000`。

---

## 🧪 自动化测试与评测

项目内置单元测试、类型检查与 Agent 质量评测（CI 门禁防回退）：

```bash
# 后端单元测试
cd backend
pytest

# Agent 评测（尺子）：工具选择 + RAG 三元组 LLM-as-Judge
python scripts/run_evals.py --min-score 0.85            # 工具选择
python scripts/run_evals.py --suite rag --min-score 0.5  # RAG 质量

# 前端 TypeScript 类型检查 + 构建
cd frontend
npx vue-tsc --noEmit
npm run build
```

> CI（`.github/workflows/ci.yml`）：后端 ruff+pytest、前端 build、evals 门禁三作业自动跑。

---

## 👥 演示账号

| 用户名 | 密码 | 角色权限 |
|--------|------|------|
| **super_admin** | 123456 | 超级管理员 (完整管理与对话权限) |
| **admin** | 123456 | 普通管理员 |
| **user** | 123456 | 普通对话用户 |

---

## 🐳 一键 Docker 部署

进入部署目录并执行编译启动：
```bash
cd deploy
cp .env.example .env
docker compose up -d --build
```
访问线上预览服务：`http://localhost` (Nginx 自动反向代理前端与 API 流通道)。详细配置请参考 [deploy/README.md](./deploy/README.md)。
