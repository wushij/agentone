"""app/config/security.py — 安全配置"""

from dataclasses import dataclass


@dataclass
class SecurityConfig:
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    rate_limit_per_minute: int = 60
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15
    cors_origins: list[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]