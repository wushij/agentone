# AgentOne 部署

本目录存放所有部署相关配置，与业务代码分离。

## 目录结构

```
deploy/
├── docker-compose.yml          # 全栈部署（MySQL + Redis + Backend + Frontend）
├── docker-compose.infra.yml    # 仅基础设施（本地开发）
├── .env.example                # Docker 环境变量模板
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
└── nginx/
    └── default.conf            # 前端 Nginx 反向代理
```

## 全栈 Docker 部署

```bash
cd deploy
cp .env.example .env
docker compose up -d --build
```

访问 http://localhost

MySQL 首次启动时会自动执行 `sql/` 目录下的初始化脚本。

## 本地开发（仅基础设施）

```bash
cd deploy
docker compose -f docker-compose.infra.yml up -d
```

然后分别启动后端与前端：

```bash
# 后端
cd ../backend && uvicorn main:app --reload --port 8000

# 前端
cd ../frontend && npm run dev
```

## 端口

| 服务 | 端口 |
|------|------|
| Frontend (Nginx) | 80 |
| Backend (FastAPI) | 8000 |
| MySQL | 3306 |
| Redis | 6379 |
