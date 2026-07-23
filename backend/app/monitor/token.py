"""app/monitor/token.py — Token 用量累计"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TokenCounter:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, *, prompt: int = 0, completion: int = 0) -> None:
        self.prompt_tokens += max(0, prompt)
        self.completion_tokens += max(0, completion)


@dataclass
class TokenStats:
    by_provider: dict[str, TokenCounter] = field(default_factory=dict)

    def add(self, provider: str, *, prompt: int = 0, completion: int = 0) -> TokenCounter:
        key = provider or "unknown"
        counter = self.by_provider.setdefault(key, TokenCounter())
        counter.add(prompt=prompt, completion=completion)
        return counter

    def snapshot(self) -> dict:
        return {
            name: {
                "promptTokens": c.prompt_tokens,
                "completionTokens": c.completion_tokens,
                "totalTokens": c.total_tokens,
            }
            for name, c in self.by_provider.items()
        }
