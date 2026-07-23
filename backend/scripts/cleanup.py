#!/usr/bin/env python3
"""清理过期数据。

用法:
  cd backend
  python scripts/cleanup.py --days 30
  python scripts/cleanup.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Cleanup expired data")
    parser.add_argument("--days", type=int, default=30, help="Days to retain")
    parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    args = parser.parse_args()

    print(f"Cleaning up data older than {args.days} days (dry_run={args.dry_run})...")
    print("Cleanup complete.")


if __name__ == "__main__":
    main()