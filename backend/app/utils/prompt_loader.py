"""Load prompt templates — DB first, then files."""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
_cache: dict[str, str] = {}


def _load_raw_prompt(name: str, fallback: str = "") -> str:
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


def load_persona() -> str:
    return _load_raw_prompt(
        "persona",
        "你是 AgentOne 智能助手，回答准确简洁，使用 emoji 分节与 Markdown 列表排版。",
    )


def load_prompt(name: str, fallback: str = "") -> str:
    content = _load_raw_prompt(name, fallback)
    persona = load_persona()
    if "{{PERSONA}}" in content:
        content = content.replace("{{PERSONA}}", persona)
    elif name in ("system", "summary", "prompt_engineer") and "AgentOne 智能助手" not in content:
        content = f"{persona}\n\n{content}"
    return content


def clear_prompt_cache(name: str | None = None) -> None:
    if name:
        _cache.pop(name, None)
    else:
        _cache.clear()
