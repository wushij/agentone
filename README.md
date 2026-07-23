# AgentOne 🚀

**AgentOne** 是一个企业级 AI 智能体编排与工作流监控平台，采用 **LangGraph / 自研图状态机** 作为底座，配合 **FastAPI 后端** 与 **Vue3 + Element Plus 前端**，实现了多智能体协作、知识库（RAG）管理、工具链管理、实时工作流可视化等功能。

---

## 🌟 核心能力

* **🤝 多代理协同 (Multi-Agent Engine)**：内置 Planner (规划)、Researcher (检索)、Tool (工具执行)、Reviewer (审阅)、Summarizer (总结) 五个专业代理角色，协同输出高质量回答。
* **📊 工作流实时可视化**：提供可视化 Agent 工作流面板，节点状态（Pending / Running / Success / Error）及执行耗时通过 WebSocket 实时推送到前端。
* **📚 深度知识库 (RAG)**：支持文件中心拖拽上传（PDF, Word, TXT, MD），由 `KnowledgeManager` 门面统一封装，支持向量检索、混合检索及分块重排序。
* **🛠️ 工具链与 Function Calling**：基于 `ToolMetadata` 规范化工具元数据，支持导出标准 OpenAI/DeepSeek Function Calling Schema，管理端支持实时启停控制。
* **🖥️ 多模型与 Prompt 维护**：支持配置多提供商（DeepSeek, OpenAI, Gemini, Ollama 等）的接口、检测连接延时（ms），并拥有专有等宽编辑器的 Prompt 模板管理面板。
* **🛡️ P0 级生产容错与日志透明**：全系统异常捕获补齐 `logger` 追溯，配置项建立 `SettingsStore` 三级优先级求值机制 (UI 动态 > `.env` 静态 > 默认值)。
* **📜 多维日志中心**：多维度审计与分析，包含用户操作行为、Agent 编译进度、Tool 执行状态、系统性能与心跳检测。
* **💎 Premium 视觉设计**：基于靛蓝（Indigo）高阶毛玻璃设计系统，支持主题预设（石墨、青绿、紫韵等）与深浅色模式。

---

## 🛠️ 技术栈

* **前端**：Vue 3 + Vite + TypeScript + Pinia + Element Plus + Vanilla CSS + Web Workers
* **后端**：FastAPI + LangGraph / GraphEngine + LangChain + SQLAlchemy + Redis (Pub/Sub 心跳与 SSE 锁机制)
* **数据库**：MySQL (持久化业务与对话数据) + Redis (缓存、限流与实时推送)

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
│   └── app/                             # 后端核心业务代码
│       ├── agents/                      # Agent 角色与智能体实现 (Planner/Writer/Reviewer...)
│       ├── api/                         # RESTful API 端点层
│       │   └── v1/                      # API v1 版本号隔离层 (/api/v1/)
│       ├── cache/                       # 多级缓存管理 (Redis & Memory)
│       ├── config/                      # Pydantic 环境变量配置
│       ├── constants/                   # 全局常量与枚举 (Role, Status, Provider, Event)
│       ├── core/                        # 核心图执行引擎 (GraphRunner & AgentState)
│       ├── db/                          # SQLAlchemy Engine & Redis 连接池
│       ├── events/                      # 全局事件总线基础设施 (EventBus)
│       ├── knowledge/                   # RAG 知识库加载、切分与统一门面 (KnowledgeManager)
│       ├── llm/                         # LLM 模型工厂与 Mock 模型
│       ├── memory/                      # Agent 上下文与长短期记忆调度 (MemoryManager)
│       ├── middleware/                  # 全局异常拦截、请求审计与限流中间件
│       ├── models/                      # SQLAlchemy ORM 数据表模型
│       ├── monitor/                     # Token 估算、Cost 计费与 OpenTelemetry 导出预留
│       ├── prompts/                     # 系统级与模板级 Prompt 仓库 (.md)
│       ├── providers/                   # 大模型厂商适配接入 (OpenAI, DeepSeek, Gemini, Ollama)
│       ├── repositories/                # 数据持久化仓储层 (Repository Layer)
│       ├── schemas/                     # Pydantic 数据契约校验层 (与 API 1:1 对齐)
│       ├── services/                    # 业务领域服务层 (Auth, Chat, Knowledge, User...)
│       ├── skills/                      # Agent Skill 扩展能力集
│       ├── storage/                     # 唯一磁盘 Path 访问控制层 (paths.py)
│       ├── tools/                       # Agent 内置工具集 (ToolMetadata & ToolRegistry)
│       ├── utils/                       # 通用基础工具 (Response, Pagination, Logger...)
│       └── workflows/                   # 场景工作流 (Chat, RAG, Coding, Research)
├── frontend/                            # Vue 3 前端工程
│   └── src/                             # 前端源码
│       ├── api/                         # API 请求封装 (modules/ 细化)
│       ├── components/                  # UI 组件库 (base/ 原子组件包)
│       ├── composables/                 # Vue 3 组合式逻辑复用函数 (useChatView, useDashboard...)
│       ├── constants/                   # 前端全局常量
│       ├── directives/                  # Vue 自定义指令集 (v-permission, v-copy, v-debounce)
│       ├── enums/                       # 前端业务枚举 (ChatStatus, MessageRole...)
│       ├── layouts/                     # 系统 Shell 整体布局 (AppLayout.vue)
│       ├── plugins/                     # 插件集中注册器 (Pinia, Router, Directives...)
│       ├── router/                      # Vue Router 路由配置与全局守卫
│       ├── services/                    # 业务服务解耦层 (ChatService, UserService...)
│       ├── stores/                      # Pinia 状态集中管理 (User, Chat, Agent, Theme)
│       ├── styles/                      # 样式系统 (global.css, theme.css, chat-markdown.css)
│       ├── types/                       # TypeScript 类型声明库
│       ├── utils/                       # 前端实用工具函数
│       ├── views/                       # 视图组件 (chat/, dashboard/, login/, profile/, admin/)
│       └── workers/                     # Web Worker 后台计算线程 (markdown.worker.ts)
├── sql/                                 # 数据库结构与初始化脚本
│   ├── init.sql                         # 一键建库建表与演示账号初始化 SQL
│   └── migrations/                      # 增量版本数据库迁移脚本
├── deploy/                              # Docker Compose 与 Nginx 部署模板
└── docs/                                # 架构设计与知识库文档
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

## 🧪 自动化测试

项目内置完整的单元测试与静态类型检查校验：

```bash
# 后端单元测试
cd backend
pytest

# 前端 TypeScript 类型检查
cd frontend
npx vue-tsc --noEmit
```

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
