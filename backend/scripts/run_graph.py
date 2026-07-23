#!/usr/bin/env python3
"""本地运行 LangGraph 工作流（无需启动 FastAPI）。

用法:
  cd backend
  pip install -r requirements.txt
  python scripts/run_graph.py "hello"
  python scripts/run_graph.py "calc 123 * 456" --sse
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.events.events import AgentStatusEvent
from app.core.engine.engine import GraphRunner


def print_agent_status(event: AgentStatusEvent) -> None:
    tool_part = f" tool={event.tool}" if event.tool else ""
    print(f"  [WS agent_status] node={event.node} status={event.status}{tool_part}")


async def run_invoke(runner: GraphRunner, message: str) -> None:
    print(f"\n>> Input: {message}\n")
    result = await runner.invoke(user_input=message, session_id="demo-session")
    print("-- Result --")
    print(f"  intent      : {result.get('intent')}")
    print(f"  tool_name   : {result.get('tool_name')}")
    print(f"  tool_result : {result.get('tool_result')}")
    print(f"  final_answer: {result.get('final_answer')}")
    if result.get("error"):
        print(f"  error       : {result.get('error')}")


async def run_sse(runner: GraphRunner, message: str) -> None:
    print(f"\n>> SSE stream: {message}\n")
    async for chunk in runner.stream_sse_encoded(message, session_id="demo-session"):
        sys.stdout.write(chunk)
        sys.stdout.flush()
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(description="AgentOne LangGraph local demo")
    parser.add_argument("message", nargs="?", default="hello AgentOne")
    parser.add_argument("--sse", action="store_true", help="output as SSE events")
    args = parser.parse_args()

    runner = GraphRunner(on_agent_status=print_agent_status)
    if args.sse:
        await run_sse(runner, args.message)
    else:
        await run_invoke(runner, args.message)


if __name__ == "__main__":
    asyncio.run(main())