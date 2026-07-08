"""backend/app/services/user_stats_service.py"""

import json
import threading
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "user_stats.json"
_lock = threading.Lock()

def _load_stats() -> dict:
    if _DATA_FILE.exists():
        try:
            return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_stats(data: dict) -> None:
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    _DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_deleted_tokens(user_id: int) -> int:
    with _lock:
        stats = _load_stats()
        deleted_tokens = stats.get("deleted_tokens", {})
        return int(deleted_tokens.get(str(user_id), 0))

def add_deleted_tokens(user_id: int, tokens: int) -> None:
    tokens = int(tokens or 0)
    if tokens <= 0:
        return
    with _lock:
        stats = _load_stats()
        if "deleted_tokens" not in stats:
            stats["deleted_tokens"] = {}

        user_key = str(user_id)
        current = int(stats["deleted_tokens"].get(user_key, 0) or 0)
        stats["deleted_tokens"][user_key] = current + tokens
        _save_stats(stats)
