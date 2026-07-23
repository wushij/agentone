"""app/storage/paths.py — 唯一磁盘数据访问层

职责划分（不要再建第二套目录概念）：
- app/storage/     → Python 代码模块（路径解析 / 建目录）
- backend/data/    → 唯一运行时磁盘根（gitignore，不进仓库）

所有业务请通过本模块取路径，禁止再写 Path(...)/"data"。
"""

from __future__ import annotations

from pathlib import Path

# backend/data —— 唯一落盘根
_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

UPLOADS = _DATA_ROOT / "uploads"
KNOWLEDGE = _DATA_ROOT / "knowledge"
IMAGES = _DATA_ROOT / "images"
TEMP = _DATA_ROOT / "temp"
EXPORTS = _DATA_ROOT / "exports"

_ALL_DIRS = (UPLOADS, KNOWLEDGE, IMAGES, TEMP, EXPORTS)


def ensure_storage_dirs() -> Path:
    """创建全部存储子目录，返回 data 根路径。"""
    _DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for d in _ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    return _DATA_ROOT


def data_root() -> Path:
    """返回 backend/data 根目录（必要时自动创建）。"""
    ensure_storage_dirs()
    return _DATA_ROOT


def uploads_dir() -> Path:
    ensure_storage_dirs()
    return UPLOADS


def knowledge_dir() -> Path:
    ensure_storage_dirs()
    return KNOWLEDGE


def images_dir() -> Path:
    ensure_storage_dirs()
    return IMAGES


def temp_dir() -> Path:
    ensure_storage_dirs()
    return TEMP


def exports_dir() -> Path:
    ensure_storage_dirs()
    return EXPORTS


def runtime_json(name: str) -> Path:
    """backend/data 下的运行时 JSON 文件路径（如 settings.json）。"""
    ensure_storage_dirs()
    return _DATA_ROOT / name


def knowledge_json() -> Path:
    return runtime_json("knowledge.json")


def vector_store_json() -> Path:
    return runtime_json("vector_store.json")


def settings_json() -> Path:
    return runtime_json("settings.json")


def user_stats_json() -> Path:
    return runtime_json("user_stats.json")
