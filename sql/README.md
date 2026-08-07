# AgentOne 数据库脚本

本目录存放所有数据库相关 SQL，与 ORM 模型（`backend/app/models/`）保持同步。

## 目录说明

* **`init.sql`**：MySQL 数据库全量初始化（建库、全部表结构、种子数据）。
* **`pg_init.sql`**：PostgreSQL 数据库全量初始化（适用于 PostgreSQL 12+）。
* **`migrations/`**：**旧库增量升级**专用，可按版本单独执行。

| 迁移文件 | 说明 |
|----------|------|
| `03_extended_schema.sql` | V1.0 扩展表（prompts、model_configs 等） |
| `04_v11_schema.sql` | V1.1 扩展表 + tool_logs 字段补齐 |
| `05_user_avatar_mediumtext.sql` | users.avatar 扩容为 MEDIUMTEXT（可重复执行） |

## 初始化数据库（全新环境）

### 方式 A：MySQL 格式化初始化
```bash
mysql -u root -p < sql/init.sql
```

### 方式 B：PostgreSQL 格式化初始化
先在 PostgreSQL 中创建数据库 `agentone`，然后导入：
```bash
psql -U postgres -d agentone -f sql/pg_init.sql
```

> 💡 提示：后端启动时已集成 SQLAlchemy `create_all` 自动补全建表机制，启动后端同样可自动完成建表。

## 旧库增量升级

已有数据库时，只执行 `migrations/` 里对应脚本，不要重跑 `init.sql`：

```bash
mysql -u root -p agentone < sql/migrations/04_v11_schema.sql
mysql -u root -p agentone < sql/migrations/05_user_avatar_mediumtext.sql
```

> 执行 `ALTER TABLE` 时若卡住，请先停止 AgentOne 后端，关闭占用 `agentone` 的闲置连接。

## 演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| super_admin | 123456 | 超级管理员 |
| admin | 123456 | 管理员 |
| user | 123456 | 普通用户 |
