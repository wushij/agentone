# AgentOne 🚀

**AgentOne** 是一个企业级 AI 智能体编排与工作流监控平台，采用 **LangGraph 状态机** 作为底座，配合 **FastAPI 后端** 与 **Vue3 + Element Plus 前端**，实现了多智能体协作、知识库（RAG）管理、工具链管理、实时工作流可视化等功能。

---

## 🌟 核心能力

* **🤝 多代理协同 (Multi-Agent V2)**：内置 Planner (规划)、Researcher (检索)、Tool (工具执行)、Reviewer (审阅)、Summarizer (总结) 五个专业代理角色，协同输出高质量回答。
* **📊 工作流实时可视化**：提供可视化 Agent 工作流面板，节点状态（Pending / Running / Success / Error）及执行耗时通过 WebSocket 实时推送到前端。
* **📚 国际级知识库 (RAG)**：支持文件中心拖拽上传（PDF, Word, TXT, MD）并按 Dify 规格组织为独立向量知识库仓，支持设定 Embedding 模型、检索模式（混合检索/语义检索/BM25 全文检索）及 Top-K 与匹配评分阈值。
* **🛠️ 工具链启停控制**：管理端支持对集成工具（如 Calculator 计算器）的实时启停，后端图引擎在路由级别（Router）实现控制联动。
* **🖥️ 大模型与 Prompt 维护**：支持配置多提供商（DeepSeek, OpenAI, Qwen 等）的接口、检测连接延时（ms），并拥有专有等宽编辑器的 Prompt 模板管理面板。
* **📜 多维日志中心**：多维度审计与分析，包含用户操作行为、Agent 编译进度、Tool 执行状态、系统性能与心跳检测。
* **💎 Premium 视觉设计**：基于靛蓝（Indigo）高阶毛玻璃设计系统，支持主题预设（石墨、青绿、紫韵等）与深浅色模式。

---

## 🛠️ 技术栈

* **前端**：Vue 3 + Vite + TypeScript + Pinia + Element Plus + Vanilla CSS 变量系统
* **后端**：FastAPI + LangGraph + LangChain + SQLAlchemy + Redis (Pub/Sub 心跳与 SSE 锁锁机制)
* **数据库**：MySQL (持久化业务与对话数据) + SQLite (本地快速启动支持)

---

## 📁 项目结构

```text
AgentOne/
├── backend/          # FastAPI 后端服务及 LangGraph 代理模型
│   ├── app/
│   │   ├── api/      # 路由控制器（Files, Knowledge, Tools, Prompts 等）
│   │   ├── graph/    # LangGraph 工作流、状态机、多代理节点
│   │   └── tools/    # 集成内置工具集
│   └── scripts/      # 本地调试与初始化脚本
├── frontend/         # Vue 3 前端工程
│   └── src/
│       ├── views/    # 页面视图（Chat 对话, Agent 状态, 管理后台）
│       └── stores/   # 状态仓储（Agent 流转, Chat 记录）
├── sql/              # 数据库结构与初始化脚本
│   ├── init.sql      # 一键建库建表与演示账号初始化 SQL
│   └── migrations/   # 增量版本数据库迁移脚本
├── deploy/           # Docker Compose 与 Nginx 部署模板
└── docs/             # 详细的设计文档
```

---

## ⚡ 快速开始

### 1. 启动基础设施（MySQL + Redis）
```bash
cd deploy
docker compose -f docker-compose.infra.yml up -d
```

### 2. 初始化数据库
```bash
# 推荐方式：直接导入统一初始化脚本
mysql -u root -p < sql/init.sql

# 或进入后端目录执行 Python 自动建表脚本
cd backend
python scripts/init_db.py
```

### 3. 配置并运行后端
```bash
cd backend
cp .env.example .env   # 配置您的 DEEPSEEK_API_KEY 与数据库连接
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. 运行前端
```bash
cd frontend
npm install
npm run dev
```
访问本地开发页面：`http://localhost:3088`。

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

---

## 📋 设计文档与实现进度

- [docs/README.md](./docs/README.md) — 全部设计文档索引
- [**docs/实现进度对照.md**](./docs/实现进度对照.md) — 设计 vs 代码完成度审计、缺口与优先级
