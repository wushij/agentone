-- ==========================================
-- AgentOne 数据库全量初始化脚本 (init.sql)
-- 包含：基础全量表结构 + V1.1 扩展表 + 记忆表 + 成本计费表 + 长任务表
-- ==========================================

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS agentone
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE agentone;

-- 2. 用户表
CREATE TABLE IF NOT EXISTS users (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  username      VARCHAR(64)  NOT NULL,
  password      VARCHAR(128) NOT NULL,
  nickname      VARCHAR(64)  NULL,
  avatar        MEDIUMTEXT   NULL COMMENT '头像 Base64 或 URL',
  role          VARCHAR(32)  NOT NULL DEFAULT 'user',
  status        SMALLINT     NOT NULL DEFAULT 1 COMMENT '1=正常 0=禁用',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  KEY ix_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 会话表
CREATE TABLE IF NOT EXISTS conversations (
  id          VARCHAR(64)  NOT NULL,
  user_id     BIGINT       NOT NULL,
  title       VARCHAR(256) NOT NULL DEFAULT '新对话',
  is_archived TINYINT      NOT NULL DEFAULT 0 COMMENT '0=未归档 1=已归档',
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_conversations_user_id (user_id),
  CONSTRAINT fk_conversations_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 消息表
CREATE TABLE IF NOT EXISTS messages (
  id              VARCHAR(64) NOT NULL,
  conversation_id VARCHAR(64) NOT NULL,
  role            VARCHAR(32) NOT NULL COMMENT 'user / assistant / system',
  content         TEXT        NOT NULL,
  tokens          INT         NOT NULL DEFAULT 0,
  created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_messages_conversation_id (conversation_id),
  CONSTRAINT fk_messages_conversation_id FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 工具调用日志表
CREATE TABLE IF NOT EXISTS tool_logs (
  id              BIGINT       NOT NULL AUTO_INCREMENT,
  tool_name       VARCHAR(128) NOT NULL,
  params          JSON         NULL COMMENT '工具入参',
  result          TEXT         NULL COMMENT '工具返回',
  duration_ms     INT          NOT NULL DEFAULT 0,
  user_id         BIGINT       NULL,
  conversation_id VARCHAR(64)  NULL,
  status          VARCHAR(32)  NOT NULL DEFAULT 'success',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_tool_logs_user_id (user_id),
  KEY ix_tool_logs_tool_name (tool_name),
  KEY ix_tool_logs_created_at (created_at),
  CONSTRAINT fk_tool_logs_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Prompt 模板表
CREATE TABLE IF NOT EXISTS prompts (
  id         BIGINT       NOT NULL AUTO_INCREMENT,
  name       VARCHAR(128) NOT NULL,
  type       VARCHAR(32)  NOT NULL COMMENT 'system / planner / tool / summary / custom',
  content    TEXT         NOT NULL,
  version    INT          NOT NULL DEFAULT 1,
  enabled    TINYINT      NOT NULL DEFAULT 1 COMMENT '1=启用 0=停用',
  updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_prompts_name (name),
  KEY ix_prompts_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 模型配置表
CREATE TABLE IF NOT EXISTS model_configs (
  id           BIGINT        NOT NULL AUTO_INCREMENT,
  name         VARCHAR(128)  NOT NULL,
  provider     VARCHAR(64)   NOT NULL COMMENT 'deepseek / openai / qwen / mock',
  api_key      VARCHAR(512)  NULL,
  base_url     VARCHAR(512)  NULL,
  model_name   VARCHAR(128)  NOT NULL,
  temperature  DECIMAL(3, 2) NOT NULL DEFAULT 0.70,
  is_default   TINYINT       NOT NULL DEFAULT 0 COMMENT '1=默认模型',
  status       SMALLINT      NOT NULL DEFAULT 1 COMMENT '1=正常 0=禁用',
  PRIMARY KEY (id),
  UNIQUE KEY uk_model_configs_name (name),
  KEY ix_model_configs_provider (provider)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 系统配置表（键值对）
CREATE TABLE IF NOT EXISTS system_settings (
  `key`   VARCHAR(128) NOT NULL,
  value   TEXT         NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. 工具配置表
CREATE TABLE IF NOT EXISTS tool_configs (
  name         VARCHAR(64)  NOT NULL,
  description  TEXT         NULL,
  tool_type    VARCHAR(32)  NOT NULL DEFAULT 'builtin',
  enabled      TINYINT      NOT NULL DEFAULT 1,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. 文件资产表
CREATE TABLE IF NOT EXISTS file_assets (
  id            VARCHAR(64)  NOT NULL,
  user_id       BIGINT       NOT NULL,
  filename      VARCHAR(256) NOT NULL,
  original_name VARCHAR(256) NOT NULL,
  mime_type     VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream',
  size_bytes    BIGINT       NOT NULL DEFAULT 0,
  category      VARCHAR(32)  NOT NULL DEFAULT 'general',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_file_assets_user_id (user_id),
  CONSTRAINT fk_file_assets_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
  id         BIGINT      NOT NULL AUTO_INCREMENT,
  user_id    BIGINT      NULL,
  module     VARCHAR(32) NOT NULL,
  action     VARCHAR(64) NOT NULL,
  detail     TEXT        NULL,
  status     VARCHAR(32) NOT NULL DEFAULT 'success',
  created_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_audit_logs_user_id (user_id),
  KEY ix_audit_logs_module (module),
  KEY ix_audit_logs_created_at (created_at),
  CONSTRAINT fk_audit_logs_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Prompt 历史表
CREATE TABLE IF NOT EXISTS prompt_histories (
  id          BIGINT       NOT NULL AUTO_INCREMENT,
  prompt_name VARCHAR(128) NOT NULL,
  content     TEXT         NOT NULL,
  version     INT          NOT NULL,
  created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_prompt_histories_prompt_name (prompt_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. 三层持久化记忆表
CREATE TABLE IF NOT EXISTS memories (
  id               BIGINT       NOT NULL AUTO_INCREMENT,
  user_id          BIGINT       NOT NULL,
  conversation_id  VARCHAR(64)  NULL,
  scope            VARCHAR(32)  NOT NULL DEFAULT 'user' COMMENT 'session/user/global',
  kind             VARCHAR(32)  NOT NULL DEFAULT 'fact' COMMENT 'fact/preference/episode/skill',
  content          TEXT         NOT NULL,
  importance       FLOAT        NOT NULL DEFAULT 1.0,
  access_count     INT          NOT NULL DEFAULT 0,
  last_accessed_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_memories_user_scope (user_id, scope),
  KEY ix_memories_created_at (created_at),
  CONSTRAINT fk_memories_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. 成本计费明细表
CREATE TABLE IF NOT EXISTS cost_records (
  id                BIGINT       NOT NULL AUTO_INCREMENT,
  user_id           BIGINT       NOT NULL,
  conversation_id   VARCHAR(64)  NULL,
  model             VARCHAR(128) NOT NULL,
  provider          VARCHAR(64)  NOT NULL,
  agent_role        VARCHAR(64)  NOT NULL DEFAULT 'assistant',
  tool_name         VARCHAR(128) NULL,
  prompt_tokens     INT          NOT NULL DEFAULT 0,
  completion_tokens INT          NOT NULL DEFAULT 0,
  total_tokens      INT          NOT NULL DEFAULT 0,
  cost_usd          DECIMAL(10, 6) NOT NULL DEFAULT 0.000000,
  trace_id          VARCHAR(64)  NULL,
  created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_cost_records_user_id (user_id),
  KEY ix_cost_records_created_at (created_at),
  CONSTRAINT fk_cost_records_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. 异步长任务表
CREATE TABLE IF NOT EXISTS agent_tasks (
  id                   VARCHAR(64)  NOT NULL PRIMARY KEY,
  user_id              BIGINT       NOT NULL,
  conversation_id      VARCHAR(64)  NULL,
  title                VARCHAR(255) NOT NULL,
  task_type            VARCHAR(64)  NOT NULL DEFAULT 'async_agent',
  status               VARCHAR(32)  NOT NULL DEFAULT 'pending',
  progress             INT          NOT NULL DEFAULT 0,
  current_step         VARCHAR(255) NULL,
  result               LONGTEXT     NULL,
  error                TEXT         NULL,
  checkpoint_thread_id VARCHAR(64)  NULL,
  created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY ix_tasks_user_status (user_id, status),
  KEY ix_tasks_created_at (created_at),
  CONSTRAINT fk_agent_tasks_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. 插入演示初始数据（演示账号密码 123456）
INSERT INTO users (username, password, nickname, role, status)
VALUES
  ('super_admin', '$2b$12$oN9HnknzV6lC7AegkoJa1OxmfY1B4B4vMCksuXmV.E2SeIiF5WttG', '超级管理员', 'super_admin', 1),
  ('admin',       '$2b$12$oN9HnknzV6lC7AegkoJa1OxmfY1B4B4vMCksuXmV.E2SeIiF5WttG', '管理员',     'admin',       1),
  ('user',        '$2b$12$oN9HnknzV6lC7AegkoJa1OxmfY1B4B4vMCksuXmV.E2SeIiF5WttG', '普通用户',   'user',        1)
ON DUPLICATE KEY UPDATE
  nickname = VALUES(nickname),
  role     = VALUES(role),
  status   = VALUES(status);
