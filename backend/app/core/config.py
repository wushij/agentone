"""backend/app/core/config.py"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "mysql+pymysql://root:root@127.0.0.1:3306/agentone?charset=utf8mb4"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    LLM_PROVIDER: str = "mock"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    TOOL_MAX_RETRIES: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
