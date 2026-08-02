"""app/runtime/tools/sandbox/policy.py — 沙箱安全与资源约束策略"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SandboxPolicy:
    """沙箱执行安全策略"""
    timeout_s: float = 30.0
    mem_limit: str = "512m"
    cpu_period: int = 100000
    cpu_quota: int = 100000  # 1.0 CPU
    network_disabled: bool = True
    read_only_rootfs: bool = False
    allowed_modules: list[str] = field(
        default_factory=lambda: [
            "math",
            "json",
            "re",
            "datetime",
            "random",
            "collections",
            "itertools",
            "functools",
            "typing",
            "statistics",
        ]
    )

    def to_docker_host_config_kwargs(self) -> dict:
        """转化为 Docker SDK host_config 参数字典"""
        return {
            "mem_limit": self.mem_limit,
            "cpu_period": self.cpu_period,
            "cpu_quota": self.cpu_quota,
            "network_mode": "none" if self.network_disabled else "bridge",
        }
