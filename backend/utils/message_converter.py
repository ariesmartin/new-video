"""
消息格式转换工具

解决 LangGraph checkpoint 序列化/反序列化后的消息格式不一致问题。

问题场景:
1. AIMessage/HumanMessage 对象被 JsonPlusSerializer 序列化为 {"type": "ai", "data": {...}}
2. 从 checkpoint 恢复时，消息可能是字典格式而非消息对象
3. 当字典格式的消息传递给 LLM 时，LangChain 期望 OpenAI 风格的 {"role": "...", "content": "..."}
4. 格式不匹配导致 MESSAGE_COERCION_FAILURE 错误

解决方案:
在消息传递给 LLM 之前，将所有格式的消息统一转换为 LangChain 消息对象。
"""

from typing import Any, Union
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
import structlog

logger = structlog.get_logger(__name__)


def convert_to_langchain_message(msg: Any) -> BaseMessage | None:
    """
    将任意格式的消息转换为 LangChain 消息对象

    支持的输入格式:
    1. LangChain 消息对象 (BaseMessage 子类) - 直接返回
    2. OpenAI 风格字典: {"role": "user"|"assistant"|"system", "content": "..."}
    3. LangChain 序列化格式: {"type": "human"|"ai"|"system", "data": {"content": "..."}}
    4. 简化字典: {"role": "...", "content": "..."}

    Args:
        msg: 任意格式的消息

    Returns:
        LangChain 消息对象，或 None（无法转换时）
    """
    # 1. 已经是 LangChain 消息对象
    if isinstance(msg, BaseMessage):
        return msg

    # 2. 字典格式
    if isinstance(msg, dict):
        # 2a. LangChain 序列化格式: {"type": "human", "data": {"content": "..."}}
        if "type" in msg and "data" in msg:
            msg_type = msg.get("type", "")
            msg_data = msg.get("data", {})

            # 提取内容
            if isinstance(msg_data, dict):
                content = msg_data.get("content", "")
                additional_kwargs = msg_data.get("additional_kwargs", {})
            else:
                content = str(msg_data)
                additional_kwargs = {}

            # 处理内容可能是列表的情况 (多模态消息)
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                )

            # 转换为对应的消息类型
            if msg_type in ("human", "user"):
                return HumanMessage(content=content, additional_kwargs=additional_kwargs)
            elif msg_type in ("ai", "assistant"):
                return AIMessage(content=content, additional_kwargs=additional_kwargs)
            elif msg_type == "system":
                return SystemMessage(content=content, additional_kwargs=additional_kwargs)
            else:
                logger.warning(f"Unknown message type in LangChain format: {msg_type}")
                # 默认作为 HumanMessage
                return HumanMessage(content=content, additional_kwargs=additional_kwargs)

        # 2b. OpenAI 风格: {"role": "user", "content": "..."}
        elif "role" in msg and "content" in msg:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # 处理内容可能是列表的情况
            if isinstance(content, list):
                content = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                )

            if role in ("user", "human"):
                return HumanMessage(content=content)
            elif role in ("assistant", "ai"):
                return AIMessage(content=content)
            elif role == "system":
                return SystemMessage(content=content)
            else:
                logger.warning(f"Unknown role in OpenAI format: {role}")
                return HumanMessage(content=content)

        # 2c. 只有 role 没有 content (无效消息)
        elif "role" in msg:
            logger.warning(f"Message dict missing 'content' key: {msg}")
            return None

        else:
            logger.warning(f"Unknown dict format: {list(msg.keys())[:5]}")
            return None

    # 3. 无法识别的类型
    logger.warning(f"Cannot convert message of type {type(msg).__name__}")
    return None


def normalize_messages(messages: list[Any]) -> list[BaseMessage]:
    """
    将消息列表标准化为 LangChain 消息对象列表

    过滤掉无法转换的消息，确保返回的列表只包含有效的 BaseMessage 对象。

    Args:
        messages: 任意格式的消息列表

    Returns:
        LangChain 消息对象列表
    """
    result = []
    conversion_errors = 0

    for msg in messages:
        converted = convert_to_langchain_message(msg)
        if converted is not None:
            result.append(converted)
        else:
            conversion_errors += 1

    if conversion_errors > 0:
        logger.warning(
            f"Failed to convert {conversion_errors} messages out of {len(messages)}"
        )

    return result


def ensure_messages_are_objects(state: dict[str, Any]) -> dict[str, Any]:
    """
    确保状态中的 messages 字段是 LangChain 消息对象列表

    这个函数应该在消息传递给 LLM 之前调用，以确保格式正确。

    Args:
        state: Agent 状态字典

    Returns:
        更新后的状态字典（messages 已标准化）
    """
    messages = state.get("messages", [])

    if not messages:
        return state

    # 检查是否需要转换
    needs_conversion = any(
        not isinstance(msg, BaseMessage) for msg in messages
    )

    if needs_conversion:
        logger.debug(f"Converting {len(messages)} messages to LangChain format")
        state["messages"] = normalize_messages(messages)

    return state


__all__ = [
    "convert_to_langchain_message",
    "normalize_messages",
    "ensure_messages_are_objects",
]
