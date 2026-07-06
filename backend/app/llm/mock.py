"""backend/app/llm/mock.py"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Iterator, Optional

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult


class MockChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "mock-chat"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        text = self._build_reply(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=None, **kwargs)

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        text = self._build_reply(messages)
        for char in text:
            yield ChatGenerationChunk(message=AIMessageChunk(content=char))

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        text = self._build_reply(messages)
        for char in text:
            yield ChatGenerationChunk(message=AIMessageChunk(content=char))
            await asyncio.sleep(0.005)

    def _build_reply(self, messages: list[BaseMessage]) -> str:
        user_text = ""
        for msg in reversed(messages):
            if msg.type == "human":
                user_text = str(msg.content)
                break
        if not user_text:
            return "你好，我是 AgentOne 演示助手（Mock LLM）。"
        if "计算" in user_text or any(op in user_text for op in "+-×÷*/"):
            return (
                "根据计算器工具的结果，运算已完成。"
                "（Mock LLM 模式；配置 DEEPSEEK_API_KEY 后可获得真实模型回复。）"
            )
        return (
            f"你好！你刚才说的是：「{user_text}」。"
            "这是 Mock LLM 的演示回复；将 LLM_PROVIDER 设为 deepseek 并配置 API Key 即可接入真实模型。"
        )
