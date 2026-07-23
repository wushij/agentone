"""app/storage — 统一文件/数据落盘访问

disk:  backend/data/     （唯一物理目录）
code:  app/storage/      （唯一访问入口）
"""

from app.storage.paths import (
    EXPORTS,
    IMAGES,
    KNOWLEDGE,
    TEMP,
    UPLOADS,
    data_root,
    ensure_storage_dirs,
    exports_dir,
    images_dir,
    knowledge_dir,
    knowledge_json,
    runtime_json,
    settings_json,
    temp_dir,
    uploads_dir,
    user_stats_json,
    vector_store_json,
)

__all__ = [
    "EXPORTS",
    "IMAGES",
    "KNOWLEDGE",
    "TEMP",
    "UPLOADS",
    "data_root",
    "ensure_storage_dirs",
    "exports_dir",
    "images_dir",
    "knowledge_dir",
    "knowledge_json",
    "runtime_json",
    "settings_json",
    "temp_dir",
    "uploads_dir",
    "user_stats_json",
    "vector_store_json",
]
