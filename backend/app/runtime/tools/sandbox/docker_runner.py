"""app/runtime/tools/sandbox/docker_runner.py — Docker 代码沙箱运行器"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import time
from typing import Any

from app.runtime.tools.sandbox.policy import SandboxPolicy

logger = logging.getLogger(__name__)


class DockerRunner:
    """Docker 容器代码沙箱运行器，提供高隔离度的安全代码执行"""

    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image
        self._docker_available: bool | None = None

    def is_docker_available(self) -> bool:
        if self._docker_available is not None:
            return self._docker_available
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3,
            )
            self._docker_available = res.returncode == 0
        except Exception:
            self._docker_available = False
        return self._docker_available

    def run_code(self, code: str, policy: SandboxPolicy | None = None) -> dict[str, Any]:
        policy = policy or SandboxPolicy()
        start_time = time.perf_counter()

        if self.is_docker_available():
            return self._run_in_docker(code, policy, start_time)
        return self._run_in_local_process(code, policy, start_time)

    def _run_in_docker(self, code: str, policy: SandboxPolicy, start_time: float) -> dict[str, Any]:
        """在 Docker 容器中隔离运行 Python 代码"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_script_path = f.name

        try:
            cmd = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none" if policy.network_disabled else "bridge",
                "--memory",
                policy.mem_limit,
                "-v",
                f"{tmp_script_path}:/app/script.py:ro",
                self.image,
                "python",
                "/app/script.py",
            ]
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=policy.timeout_s,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            stdout = res.stdout.decode("utf-8", errors="ignore")
            stderr = res.stderr.decode("utf-8", errors="ignore")

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": res.returncode,
                "duration_ms": duration_ms,
                "sandboxed": True,
                "error": "" if res.returncode == 0 else f"Process exited with code {res.returncode}: {stderr}",
            }
        except subprocess.TimeoutExpired:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {policy.timeout_s}s",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "sandboxed": True,
                "error": f"超时阻断：代码执行超过最大限定时长（{policy.timeout_s} 秒）",
            }
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "stdout": "",
                "stderr": str(exc),
                "exit_code": -1,
                "duration_ms": duration_ms,
                "sandboxed": True,
                "error": str(exc),
            }
        finally:
            if os.path.exists(tmp_script_path):
                try:
                    os.remove(tmp_script_path)
                except Exception:
                    pass

    def _run_in_local_process(self, code: str, policy: SandboxPolicy, start_time: float) -> dict[str, Any]:
        """本地子进程受限降级运行（Docker 不可用时的 fallback）"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_script_path = f.name

        try:
            res = subprocess.run(
                [sys.executable, tmp_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=policy.timeout_s,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            stdout = res.stdout.decode("utf-8", errors="ignore")
            stderr = res.stderr.decode("utf-8", errors="ignore")

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": res.returncode,
                "duration_ms": duration_ms,
                "sandboxed": False,
                "error": "" if res.returncode == 0 else f"Process exited with code {res.returncode}: {stderr}",
            }
        except subprocess.TimeoutExpired:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {policy.timeout_s}s",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "sandboxed": False,
                "error": f"超时阻断：代码执行超过最大限定时长（{policy.timeout_s} 秒）",
            }
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return {
                "stdout": "",
                "stderr": str(exc),
                "exit_code": -1,
                "duration_ms": duration_ms,
                "sandboxed": False,
                "error": str(exc),
            }
        finally:
            if os.path.exists(tmp_script_path):
                try:
                    os.remove(tmp_script_path)
                except Exception:
                    pass
