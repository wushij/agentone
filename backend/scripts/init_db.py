#!/usr/bin/env python3
"""初始化数据库 — 创建所有表并填充种子数据。

用法:
  cd backend
  python scripts/init_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal, engine
from app.db.seed import seed_all
from app.models.base import Base


def main():
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    db = SessionLocal()
    try:
        seed_all(db)
        print("Seed data inserted successfully.")
    finally:
        db.close()

    print("Database initialization complete.")


if __name__ == "__main__":
    main()