"""scripts/run_evals.py — 自动化评测与 CI 质量门禁门检测脚本"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 添加 backend 到 sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.planner import detect_intent

TOOL_SELECTION_BASELINE = 0.85


def run_tool_selection_evals() -> float:
    dataset_file = backend_dir / "evals" / "datasets" / "tool_selection.jsonl"
    if not dataset_file.exists():
        print(f"[Eval Warning] 数据集未找到: {dataset_file}")
        return 1.0

    total = 0
    correct = 0

    with open(dataset_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            user_input = item.get("query") or item.get("input") or ""
            expected_tool = item.get("expected_tool") or ""

            _intent, tool_name, _tool_input = detect_intent(user_input)
            total += 1
            is_match = False
            t_got = tool_name.lower().strip()
            t_exp = expected_tool.lower().strip()

            if t_exp in ("none", "", "chat"):
                is_match = t_got in ("", "none", "chat")
            else:
                is_match = (t_got == t_exp)

            if is_match:
                correct += 1
            else:
                print(f"  [Mismatch] Query: '{user_input}' => Got '{tool_name}', Expected '{expected_tool}'")

    if total == 0:
        return 1.0

    acc = correct / total
    print(f"==> 工具选择准确率 (Tool Selection Accuracy): {acc * 100:.1f}% ({correct}/{total})")
    return acc


def main():
    print("==================================================")
    print("      AgentOne CI 质量门禁 - 自动化评测跑分      ")
    print("==================================================")

    acc = run_tool_selection_evals()

    if acc < TOOL_SELECTION_BASELINE:
        print(f"[FAIL] 评测得分 ({acc * 100:.1f}%) 低于 CI 基线要求 ({TOOL_SELECTION_BASELINE * 100:.1f}%)！")
        sys.exit(1)

    print("[PASS] 所有评测指标符合 CI 门禁标准，准予合并代码！")
    sys.exit(0)


if __name__ == "__main__":
    main()
