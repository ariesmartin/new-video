"""
消息类型定义 - 明确区分系统消息、用户消息和AI消息

这是消息系统的核心类型定义，所有消息处理逻辑都基于这些类型。
"""

from enum import Enum
from typing import Literal, TypedDict, Any
from datetime import datetime


class MessageRole(str, Enum):
    """消息角色类型"""

    SYSTEM = "system"  # 系统内部消息，不显示给用户
    USER = "user"  # 用户发送的消息
    ASSISTANT = "assistant"  # AI助手回复的消息


class MessageType(str, Enum):
    """消息类型 - 用于更细粒度的分类"""

    # 系统消息类型
    SYSTEM_INIT = "system_init"  # 系统初始化消息
    SYSTEM_INTERNAL = "system_internal"  # 系统内部处理消息

    # 用户消息类型
    USER_TEXT = "user_text"  # 普通文本消息
    USER_INIT = "user_init"  # 用户初始化消息（如"你好，开始创作"）
    USER_ACTION = "user_action"  # 用户点击按钮等操作

    # AI消息类型
    AI_WELCOME = "ai_welcome"  # AI欢迎消息
    AI_RESPONSE = "ai_response"  # AI普通回复
    AI_STATUS = "ai_status"  # AI状态更新（如"正在搜索..."）
    AI_ERROR = "ai_error"  # AI错误消息


class MessageMetadata(TypedDict, total=False):
    """消息元数据"""

    # 消息来源信息
    checkpoint_id: str | None  # 关联的checkpoint ID
    node_id: str | None  # 生成该消息的节点ID

    # 消息类型标记
    is_system_init: bool  # 是否是系统初始化消息
    is_hidden: bool  # 是否对用户隐藏

    # UI关联
    has_ui_interaction: bool  # 是否有关联的ui_interaction
    ui_interaction_id: str | None  # 关联的ui_interaction ID

    # 其他
    action: str | None  # 用户操作类型
    timestamp_ms: int | None  # 精确到毫秒的时间戳


class ChatMessage(TypedDict):
    """标准聊天消息结构"""

    id: str
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime
    metadata: MessageMetadata
    ui_interaction: dict | None


# ===== 消息过滤规则 =====

# 对用户隐藏的消息类型（不显示在UI中）
HIDDEN_MESSAGE_TYPES = {
    MessageType.SYSTEM_INIT,
    MessageType.SYSTEM_INTERNAL,
    MessageType.USER_INIT,  # "你好，开始创作"等初始化消息
}

# 可以显示给用户的消息类型
VISIBLE_MESSAGE_TYPES = {
    MessageType.USER_TEXT,
    MessageType.USER_ACTION,
    MessageType.AI_WELCOME,
    MessageType.AI_RESPONSE,
    MessageType.AI_STATUS,
    MessageType.AI_ERROR,
}


def should_show_to_user(message: ChatMessage) -> bool:
    """
    判断消息是否应该显示给用户

    Args:
        message: 聊天消息

    Returns:
        True: 应该显示
        False: 应该隐藏
    """
    # 系统消息默认隐藏
    if message["role"] == MessageRole.SYSTEM:
        return False

    # 检查元数据中的隐藏标记
    metadata = message.get("metadata", {})
    if metadata.get("is_hidden", False):
        return False

    # 检查消息类型
    msg_type = metadata.get("message_type")
    if msg_type in HIDDEN_MESSAGE_TYPES:
        return False

    # 特殊处理：用户初始化消息
    if message["role"] == MessageRole.USER:
        content = message["content"].lower()
        if content in ["你好，开始创作", "开始创作", "你好，开始"]:
            return False

    return True


def create_system_init_message(content: str) -> ChatMessage:
    """创建系统初始化消息"""
    return {
        "id": f"sys_init_{datetime.now().timestamp()}",
        "role": MessageRole.SYSTEM,
        "content": content,
        "timestamp": datetime.now(),
        "metadata": {
            "is_system_init": True,
            "is_hidden": True,
        },
        "ui_interaction": None,
    }


def create_user_init_message(content: str = "你好，开始创作") -> ChatMessage:
    """创建用户初始化消息（对用户隐藏）"""
    return {
        "id": f"user_init_{datetime.now().timestamp()}",
        "role": MessageRole.USER,
        "content": content,
        "timestamp": datetime.now(),
        "metadata": {
            "is_hidden": True,
            "message_type": MessageType.USER_INIT,
        },
        "ui_interaction": None,
    }


def create_ai_welcome_message(content: str) -> ChatMessage:
    """创建AI欢迎消息"""
    return {
        "id": f"ai_welcome_{datetime.now().timestamp()}",
        "role": MessageRole.ASSISTANT,
        "content": content,
        "timestamp": datetime.now(),
        "metadata": {
            "message_type": MessageType.AI_WELCOME,
        },
        "ui_interaction": None,
    }
