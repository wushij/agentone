"""Seed demo users for development."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository

DEMO_USERS: list[tuple[str, str, str]] = [
    ("super_admin", "super_admin", "超级管理员"),
    ("admin", "admin", "管理员"),
    ("user", "user", "普通用户"),
]

DEMO_PASSWORD = "123456"


def seed_demo_users(db: Session) -> None:
    repo = UserRepository(db)
    password_hash = hash_password(DEMO_PASSWORD)
    for username, role, nickname in DEMO_USERS:
        if repo.get_by_username(username) is not None:
            continue
        repo.create(
            username=username,
            password=password_hash,
            nickname=nickname,
            role=role,
            status=1,
        )
    db.commit()


def seed_all(db: Session) -> None:
    # Seed users
    seed_demo_users(db)

    # Seed models
    from app.services.model_service import ModelService
    ModelService(db).seed_defaults()

    # Seed prompts
    from app.services.prompt_service import PromptService
    PromptService(db).seed_defaults()

    # Seed tools
    from app.services.tool_service import ToolService
    ToolService(db).seed_defaults()

