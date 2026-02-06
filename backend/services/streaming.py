"""
Streaming Callback Handler for LangGraph

提供流式输出支持，通过回调机制在 LLM 生成 token 时实时发送 SSE 事件。
"""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Optional
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
import structlog

logger = structlog.get_logger(__name__)


class StreamingCallbackHandler(AsyncCallbackHandler):
    """
    流式回调处理器

    在 LLM 生成 token 时，通过队列实时发送事件。
    与 graph.astream_events() 配合使用，确保 token 事件被正确捕获。
    """

    def __init__(self, queue: asyncio.Queue, node_name: str):
        self.queue = queue
        self.node_name = node_name
        self.tokens: list[str] = []

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """每当 LLM 生成新 token 时调用"""
        if token:
            self.tokens.append(token)
            # 发送 token 事件到队列
            await self.queue.put(
                {
                    "type": "token",
                    "content": token,
                    "node": self.node_name,
                }
            )

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 生成完成时调用"""
        logger.debug("LLM streaming completed", node=self.node_name, tokens_count=len(self.tokens))

    async def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """LLM 发生错误时调用"""
        logger.error("LLM streaming error", node=self.node_name, error=str(error))
        await self.queue.put(
            {
                "type": "error",
                "message": str(error),
                "node": self.node_name,
            }
        )


class StreamingManager:
    """
    流式管理器

    管理 SSE 事件流，协调 LangGraph 节点和前端之间的流式通信。
    """

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._active_streams: Dict[str, bool] = {}

    def create_stream(self, thread_id: str) -> asyncio.Queue:
        """为指定线程创建流式队列"""
        queue = asyncio.Queue()
        self._queues[thread_id] = queue
        self._active_streams[thread_id] = True
        return queue

    def get_queue(self, thread_id: str) -> Optional[asyncio.Queue]:
        """获取指定线程的队列"""
        return self._queues.get(thread_id)

    async def send_token(self, thread_id: str, token: str, node: str) -> bool:
        """发送 token 到指定线程的队列"""
        queue = self._queues.get(thread_id)
        if queue and self._active_streams.get(thread_id, False):
            await queue.put({"type": "token", "content": token, "node": node})
            return True
        return False

    def end_stream(self, thread_id: str):
        """结束指定线程的流"""
        self._active_streams[thread_id] = False
        if thread_id in self._queues:
            del self._queues[thread_id]

    def create_callback_handler(self, thread_id: str, node_name: str) -> StreamingCallbackHandler:
        """为指定线程和节点创建回调处理器"""
        queue = self._queues.get(thread_id)
        if not queue:
            queue = self.create_stream(thread_id)
        return StreamingCallbackHandler(queue, node_name)


# 全局流式管理器实例
streaming_manager = StreamingManager()
