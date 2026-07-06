"""Load prompt templates — DB first, then files."""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
_cache: dict[str, str] = {}


def load_prompt(name: str, fallback: str = "") -> str:
    if name in _cache:
        return _cache[name]
    try:
        from app.db.session import SessionLocal
        from app.services.prompt_service import PromptService

        db = SessionLocal()
        try:
            content = PromptService(db).get_content(name, "")
            if content:
                _cache[name] = content
                return content
        finally:
            db.close()
    except Exception:
        pass
    path = _PROMPTS_DIR / f"{name}.md"
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        _cache[name] = content
        return content
    return fallback


def clear_prompt_cache(name: str | None = None) -> None:
    if name:
        _cache.pop(name, None)
    else:
        _cache.clear()
