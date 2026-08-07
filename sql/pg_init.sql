-- ==========================================
-- AgentOne PostgreSQL 数据库全量初始化脚本 (pg_init.sql)
-- 适用于 PostgreSQL 12+ 
-- 与 app/models/ 中的 ORM 模型 100% 同步
-- ==========================================

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
  id            BIGSERIAL    PRIMARY KEY,
  username      VARCHAR(64)  NOT NULL UNIQUE,
  password      VARCHAR(128) NOT NULL,
  nickname      VARCHAR(64)  NULL,
  avatar        TEXT         NULL,
  role          VARCHAR(32)  NOT NULL DEFAULT 'user',
  status        SMALLINT     NOT NULL DEFAULT 1,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP    NULL
);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);

-- 2. 会话表
CREATE TABLE IF NOT EXISTS conversations (
  id          VARCHAR(64)  PRIMARY KEY,
  user_id     BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       VARCHAR(256) NOT NULL DEFAULT '新对话',
  is_archived SMALLINT     NOT NULL DEFAULT 0,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations (user_id);

-- 3. 消息表
CREATE TABLE IF NOT EXISTS messages (
  id              VARCHAR(64) PRIMARY KEY,
  conversation_id VARCHAR(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role            VARCHAR(32) NOT NULL,
  content         TEXT        NOT NULL,
  tokens          INT         NOT NULL DEFAULT 0,
  tools           JSONB       NULL,
  created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id);

-- 4. 工具调用日志表
CREATE TABLE IF NOT EXISTS tool_logs (
  id              BIGSERIAL    PRIMARY KEY,
  tool_name       VARCHAR(128) NOT NULL,
  params          JSONB        NULL,
  result          TEXT         NULL,
  duration_ms     INT          NOT NULL DEFAULT 0,
  user_id         BIGINT       NULL REFERENCES users(id) ON DELETE SET NULL,
  conversation_id VARCHAR(64)  NULL,
  status          VARCHAR(32)  NOT NULL DEFAULT 'success',
  created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_tool_logs_user_id ON tool_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_tool_logs_tool_name ON tool_logs (tool_name);
CREATE INDEX IF NOT EXISTS ix_tool_logs_created_at ON tool_logs (created_at);

-- 5. Prompt 模板表
CREATE TABLE IF NOT EXISTS prompts (
  id         BIGSERIAL    PRIMARY KEY,
  name       VARCHAR(64)  NOT NULL UNIQUE,
  type       VARCHAR(32)  NOT NULL,
  content    TEXT         NOT NULL,
  version    INT          NOT NULL DEFAULT 1,
  enabled    SMALLINT     NOT NULL DEFAULT 1,
  updated_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_prompts_type ON prompts (type);

-- 6. 模型配置表
CREATE TABLE IF NOT EXISTS model_configs (
  id           BIGSERIAL     PRIMARY KEY,
  name         VARCHAR(128)  NOT NULL UNIQUE,
  provider     VARCHAR(64)   NOT NULL,
  api_key      VARCHAR(512)  NULL,
  base_url     VARCHAR(512)  NULL,
  model_name   VARCHAR(128)  NOT NULL,
  temperature  NUMERIC(3, 2) NOT NULL DEFAULT 0.70,
  is_default   SMALLINT      NOT NULL DEFAULT 0,
  status       SMALLINT      NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_model_configs_provider ON model_configs (provider);

-- 7. 系统配置表（键值对）
CREATE TABLE IF NOT EXISTS system_settings (
  key     VARCHAR(128) PRIMARY KEY,
  value   TEXT         NOT NULL
);

-- 8. 工具配置表
CREATE TABLE IF NOT EXISTS tool_configs (
  name         VARCHAR(64)  PRIMARY KEY,
  description  TEXT         NULL,
  tool_type    VARCHAR(32)  NOT NULL DEFAULT 'builtin',
  enabled      SMALLINT     NOT NULL DEFAULT 1,
  updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. 文件资产表
CREATE TABLE IF NOT EXISTS file_assets (
  id            VARCHAR(64)  PRIMARY KEY,
  user_id       BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  filename      VARCHAR(256) NOT NULL,
  original_name VARCHAR(256) NOT NULL,
  mime_type     VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream',
  size_bytes    BIGINT       NOT NULL DEFAULT 0,
  category      VARCHAR(32)  NOT NULL DEFAULT 'general',
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_file_assets_user_id ON file_assets (user_id);

-- 10. 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
  id         BIGSERIAL   PRIMARY KEY,
  user_id    BIGINT      NULL REFERENCES users(id) ON DELETE SET NULL,
  module     VARCHAR(32) NOT NULL,
  action     VARCHAR(64) NOT NULL,
  detail     TEXT        NULL,
  status     VARCHAR(32) NOT NULL DEFAULT 'success',
  created_at TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_module ON audit_logs (module);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);

-- 11. Prompt 历史表
CREATE TABLE IF NOT EXISTS prompt_histories (
  id          BIGSERIAL    PRIMARY KEY,
  prompt_name VARCHAR(128) NOT NULL,
  content     TEXT         NOT NULL,
  version     INT          NOT NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_prompt_histories_prompt_name ON prompt_histories (prompt_name);

-- 12. 三层持久化记忆表
CREATE TABLE IF NOT EXISTS memories (
  id               BIGSERIAL    PRIMARY KEY,
  user_id          BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  scope            VARCHAR(32)  NOT NULL DEFAULT 'user',
  kind             VARCHAR(32)  NOT NULL DEFAULT 'fact',
  content          TEXT         NOT NULL,
  embedding        JSONB        NULL,
  importance       REAL         NOT NULL DEFAULT 0.5,
  access_count     INT          NOT NULL DEFAULT 0,
  pinned           SMALLINT     NOT NULL DEFAULT 0,
  created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_accessed_at TIMESTAMP    NULL,
  expires_at       TIMESTAMP    NULL
);
CREATE INDEX IF NOT EXISTS ix_memories_user_id ON memories (user_id);

-- 13. 成本计费明细表
CREATE TABLE IF NOT EXISTS cost_records (
  id                BIGSERIAL     PRIMARY KEY,
  user_id           BIGINT        NULL REFERENCES users(id) ON DELETE CASCADE,
  conversation_id   VARCHAR(64)   NULL,
  trace_id          VARCHAR(64)   NULL,
  model             VARCHAR(128)  NOT NULL DEFAULT '',
  provider          VARCHAR(64)   NOT NULL DEFAULT '',
  agent_role        VARCHAR(64)   NOT NULL DEFAULT 'assistant',
  tool_name         VARCHAR(128)  NOT NULL DEFAULT '',
  prompt_tokens     INT           NOT NULL DEFAULT 0,
  completion_tokens INT           NOT NULL DEFAULT 0,
  cost_usd          REAL          NOT NULL DEFAULT 0.0,
  created_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_cost_records_user_id ON cost_records (user_id);
CREATE INDEX IF NOT EXISTS ix_cost_records_created_at ON cost_records (created_at);

-- 14. 异步长任务表 (与 AgentTask ORM 模型完全同步)
CREATE TABLE IF NOT EXISTS agent_tasks (
  id                   VARCHAR(64)  PRIMARY KEY,
  user_id              BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind                 VARCHAR(32)  NOT NULL DEFAULT 'agent',
  title                VARCHAR(256) NOT NULL DEFAULT '',
  input                TEXT         NOT NULL DEFAULT '',
  status               VARCHAR(16)  NOT NULL DEFAULT 'pending',
  progress             INT          NOT NULL DEFAULT 0,
  result               TEXT         NULL,
  error                TEXT         NULL,
  checkpoint_thread_id VARCHAR(64)  NULL,
  task_metadata        JSONB        NULL,
  created_at           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_tasks_user_id ON agent_tasks (user_id);
CREATE INDEX IF NOT EXISTS ix_tasks_status ON agent_tasks (status);

-- 15. 知识库元数据表
CREATE TABLE IF NOT EXISTS knowledge_bases (
  id          VARCHAR(64)  PRIMARY KEY,
  name        VARCHAR(128) NOT NULL,
  description TEXT         NOT NULL DEFAULT '',
  config      JSONB        NOT NULL DEFAULT '{}'::jsonb,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 16. 产物表
CREATE TABLE IF NOT EXISTS artifacts (
  id              VARCHAR(64)  PRIMARY KEY,
  user_id         BIGINT       NOT NULL,
  type            VARCHAR(32)  NOT NULL DEFAULT 'markdown',
  title           VARCHAR(256) NOT NULL DEFAULT '',
  content         TEXT         NOT NULL DEFAULT '',
  language        VARCHAR(32)  NULL,
  conversation_id VARCHAR(64)  NULL,
  message_id      VARCHAR(64)  NULL,
  task_id         VARCHAR(64)  NULL,
  version         INT          NOT NULL DEFAULT 1,
  created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 17. 插入演示初始账号（密码默认 123456）
INSERT INTO users (username, password, nickname, role, status)
VALUES
  ('super_admin', '$2b$12$oN9HnknzV6lC7AegkoJa1OxmfY1B4B4vMCksuXmV.E2SeIiF5WttG', '超级管理员', 'super_admin', 1),
  ('admin',       '$2b$12$oN9HnknzV6lC7AegkoJa1OxmfY1B4B4vMCksuXmV.E2SeIiF5WttG', '管理员',     'admin',       1),
  ('user',        '$2b$12$oN9HnknzV6lC7AegkoJa1OxmfY1B4B4vMCksuXmV.E2SeIiF5WttG', '普通用户',   'user',        1)
ON CONFLICT (username) DO UPDATE SET
  nickname = EXCLUDED.nickname,
  role     = EXCLUDED.role,
  status   = EXCLUDED.status;
