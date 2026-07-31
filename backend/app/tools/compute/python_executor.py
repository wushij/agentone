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
_TIMEOUT = 15.0
# 基础静态拦截：本地子进程非强隔离，禁掉明显危险操作
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
        started = time.perf_counter()
        code = str(kwargs.get("code") or "").strip()
        if not code:
            return ToolResult(output="", duration_ms=0, error="缺少要执行的代码")

        lowered = code.lower()
        hit = next((kw for kw in _FORBIDDEN if kw in lowered), None)
        if hit:
            return ToolResult(output="", duration_ms=0, error=f"安全限制：代码包含禁用操作「{hit}」")

        tmpdir = tempfile.mkdtemp(prefix="agentone_py_")
        script = Path(tmpdir) / "snippet.py"
        script.write_text(code, encoding="utf-8")
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-I", "-B", str(script),
                cwd=tmpdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=_TIMEOUT)
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000),
                                  error=f"执行超时（>{_TIMEOUT}s）")

            out = stdout.decode("utf-8", errors="ignore")[:_MAX_OUTPUT]
            err = stderr.decode("utf-8", errors="ignore")[:2000]
            duration_ms = int((time.perf_counter() - started) * 1000)
            if proc.returncode != 0:
                return ToolResult(output=out, duration_ms=duration_ms, error=err or f"退出码 {proc.returncode}")
            return ToolResult(
                output=out or "(无 stdout 输出)",
                duration_ms=duration_ms,
                artifact={"type": "code", "title": "Python 代码", "content": code, "language": "python"},
            )
        except Exception as exc:
            return ToolResult(output="", duration_ms=int((time.perf_counter() - started) * 1000), error=str(exc))
        finally:
            import shutil as _sh
            _sh.rmtree(tmpdir, ignore_errors=True)
