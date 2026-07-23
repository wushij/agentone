"""app/config/provider.py — 模型提供商配置"""

from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    provider: str = "deepseek"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    extra: dict = field(default_factory=dict)


PROVIDER_PRESETS: dict[str, ProviderConfig] = {
    "deepseek": ProviderConfig(
        provider="deepseek",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
    ),
    "openai": ProviderConfig(
        provider="openai",
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
    ),
}