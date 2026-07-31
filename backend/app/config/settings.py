"""app/config/settings.py — 应用配置中心"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "mysql+pymysql://root:root@127.0.0.1:3306/agentone?charset=utf8mb4"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # 双 token（§17.4）：refresh token 长有效期（默认 7 天）
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    # 安全（§17.4）：为 true 时，SECRET_KEY 仍为默认弱值则拒绝启动
    REQUIRE_STRONG_SECRET: bool = False
    # 安全（§4.9）：仅在可信反向代理后部署时置 true，才采信 X-Forwarded-For 头；
    # 默认 false 避免直连后端伪造 IP 绕过限流/黑名单。
    TRUST_PROXY: bool = False

    LLM_PROVIDER: str = "mock"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    TOOL_MAX_RETRIES: int = 3

    # 向量库（§8.1）：空=使用 JSON 向量存储；设置后启用 Qdrant
    QDRANT_URL: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()