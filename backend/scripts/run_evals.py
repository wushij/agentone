#!/usr/bin/env python3
"""scripts/run_evals.py — 工具选择评测（§13.1 最小 evals，改造全程的"尺子"）

用法:
  cd backend
  python scripts/run_evals.py                                   # 规则引擎基线
  python scripts/run_evals.py --mode fc                         # Function Calling（需真实 API Key）
  python scripts/run_evals.py --min-score 0.85                  # CI 门禁：低于阈值退出码 1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

DEFAULT_DATASET = BACKEND_ROOT / "evals" / "datasets" / "tool_selection.jsonl"


def load_dataset(path: Path) -> list[dict]:
    cases: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


def predict_by_rules(query: str) -> str:
    """规则引擎（detect_intent 回退路径）的工具选择。"""
    from app.agents.planner import detect_intent

    intent, tool_name, _ = detect_intent(query)
    if tool_name:
        return tool_name
    return "none"


async def predict_by_fc(query: str) -> str:
    """Function Calling 路径的工具选择（需模型支持 bind_tools）。"""
    from app.llm.factory import create_chat_model
    from app.runtime.context.builder import get_context_builder
    from app.runtime.executor.tool_binding import bind_tools_if_supported, extract_tool_calls
    from app.runtime.tools.manager import get_tool_manager

    manager = get_tool_manager()
    await manager.setup()
    llm = create_chat_model()
    llm_with_tools = bind_tools_if_supported(llm, manager.list_available_tools())
    if llm_with_tools is None:
        raise RuntimeError("当前模型不支持 Function Calling（Mock 模式请用 --mode rules）")

    messages, _ = get_context_builder().build("react_agent", {"user_input": query, "messages": [], "metadata": {}})
    response = await llm_with_tools.ainvoke(messages)
    calls = extract_tool_calls(response)
    return calls[0]["name"] if calls else "none"


async def run(dataset_path: Path, mode: str, min_score: float, verbose: bool) -> int:
    cases = load_dataset(dataset_path)
    correct = 0
    failures: list[str] = []

    for case in cases:
        query = str(case["query"])
        expected = str(case["expected_tool"])
        try:
            if mode == "fc":
                predicted = await predict_by_fc(query)
            else:
                predicted = predict_by_rules(query)
        except Exception as exc:
            predicted = f"<error: {exc}>"

        ok = predicted == expected
        correct += int(ok)
        if not ok:
            failures.append(f"  [#{case.get('id')}] {query!r}: expected={expected} got={predicted}")
        if verbose:
            mark = "OK " if ok else "FAIL"
            print(f"{mark} #{case.get('id'):>3} expected={expected:<10} got={predicted:<10} {query}")

    score = correct / len(cases) if cases else 0.0
    print(f"\n=== Tool Selection Evals ({mode}) ===")
    print(f"dataset : {dataset_path}")
    print(f"cases   : {len(cases)}")
    print(f"correct : {correct}")
    print(f"score   : {score:.2%}  (gate: {min_score:.2%})")
    if failures:
        print(f"\nfailures ({len(failures)}):")
        print("\n".join(failures))

    if score < min_score:
        print("\nRESULT: FAIL（低于门禁阈值）")
        return 1
    print("\nRESULT: PASS")
    return 0


async def run_rag(dataset_path: Path, min_score: float, verbose: bool) -> int:
    """RAG 三元组 LLM-as-Judge（§13.1）：对 (query, context, reference) 评分。

    验证 Judge 尺子端到端可用；分数为三维均值归一化到 0~1。
    """
    from app.runtime.evals.judge import judge_rag

    cases = load_dataset(dataset_path)
    total_score = 0.0
    for case in cases:
        query = str(case["query"])
        context = str(case.get("context", ""))
        reference = str(case.get("reference", ""))
        scores = await judge_rag(query, context, reference)
        avg5 = sum(scores.values()) / 3.0
        norm = (avg5 - 1) / 4.0
        total_score += norm
        if verbose:
            print(f"#{case.get('id'):>3} faith={scores['faithfulness']} rel={scores['answerRelevancy']} prec={scores['contextPrecision']} {query}")

    score = total_score / len(cases) if cases else 0.0
    print("\n=== RAG Judge Evals ===")
    print(f"dataset : {dataset_path}")
    print(f"cases   : {len(cases)}")
    print(f"score   : {score:.2%}  (gate: {min_score:.2%})")
    if score < min_score:
        print("\nRESULT: FAIL（低于门禁阈值）")
        return 1
    print("\nRESULT: PASS")
    return 0


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="AgentOne tool-selection evals")
    parser.add_argument("--suite", choices=["tool", "rag"], default="tool", help="tool=工具选择；rag=RAG 三元组 LLM-as-Judge")
    parser.add_argument("--dataset", default="")
    parser.add_argument("--mode", choices=["rules", "fc"], default="rules")
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.suite == "rag":
        dataset = Path(args.dataset) if args.dataset else (BACKEND_ROOT / "evals" / "datasets" / "rag_qa.jsonl")
        exit_code = asyncio.run(run_rag(dataset, args.min_score, args.verbose))
    else:
        dataset = Path(args.dataset) if args.dataset else DEFAULT_DATASET
        exit_code = asyncio.run(run(dataset, args.mode, args.min_score, args.verbose))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
