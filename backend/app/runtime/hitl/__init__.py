"""app/runtime/hitl — Human-in-the-Loop 审批（§16.2）"""

from app.runtime.hitl.gate import ApprovalGate, get_approval_gate

__all__ = ["ApprovalGate", "get_approval_gate"]
