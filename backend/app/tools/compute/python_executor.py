"""app/tools/compute/python_executor.py — Python 沙箱执行工具（§4.3）

在受限子进程中执行 Python 代码，捕获 stdout。本地无 Docker 时用子进程 +
超时 + 独立临时工作目录做基础隔离；生产建议接 Docker（docker_runner）。
产出代码正文登记为 code Artifact。
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult

_MAX_OUTPUT = 8000
_FORBIDDEN = (
    "import os", "import shutil", "import socket", "subprocess",
    "__import__", "open(", "eval(", "exec(", "os.system", "rmtree",
)


class PythonArgs(BaseModel):
    code: str = Field(description="要执行的 Python 代码，用 print 输出结果")


class PythonExecutorTool(BaseTool):
    name = "python_executor"
    description = "在受限沙箱中执行 Python 代码并返回 stdout（用于计算/数据处理，禁用文件与网络）"
    args_schema = PythonArgs
    timeout_s = 20.0

    async def run(self, **kwargs: Any) -> ToolResult:
        from app.runtime.tools.sandbox.docker_runner import DockerRunner
        from app.runtime.tools.sandbox.policy import SandboxPolicy

        started = time.perf_counter()
        code = str(kwargs.get("code") or "").strip()
        if not code:
            return ToolResult(output="", duration_ms=0, error="缺少要执行的代码")

        lowered = code.lower()
        hit = next((kw for kw in _FORBIDDEN if kw in lowered), None)
        if hit:
            return ToolResult(output="", duration_ms=0, error=f"安全限制：代码包含禁用操作「{hit}」")

        runner = DockerRunner()
        policy = SandboxPolicy(timeout_s=self.timeout_s, mem_limit="512m", network_disabled=True)
        res = await asyncio.to_thread(runner.run_code, code, policy)

        out = (res.get("stdout") or "")[:_MAX_OUTPUT]
        err = res.get("error") or ""
        duration_ms = res.get("duration_ms", int((time.perf_counter() - started) * 1000))

        if err:
            return ToolResult(output=out, duration_ms=duration_ms, error=err)

        return ToolResult(
            output=out or "(无 stdout 输出)",
            duration_ms=duration_ms,
            artifact={"type": "code", "title": "Python 代码", "content": code, "language": "python"},
        )
