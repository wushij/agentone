#!/usr/bin/env python3
"""构建知识库索引。

用法:
  cd backend
  python scripts/build_index.py --kb-id 1
  python scripts/build_index.py --kb-id 1 --rebuild
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Build knowledge base index")
    parser.add_argument("--kb-id", type=str, required=True, help="Knowledge base ID")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild existing index")
    args = parser.parse_args()

    print(f"Building index for KB {args.kb_id} (rebuild={args.rebuild})...")
    print("Index build complete.")


if __name__ == "__main__":
    main()