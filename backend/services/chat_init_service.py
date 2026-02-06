"""
聊天初始化服务

处理冷启动和热恢复的逻辑，确保欢迎消息正确显示
"""

import structlog
from typing import Any
from langchain_core.messages import AIMessage, HumanMessage
from backend.schemas.agent_state import AgentState
from backend.schemas.common import UIInteractionBlock, UIInteractionBlockType, ActionButton

logger = structlog.get_logger(__name__)


# 冷启动触发短语 - 识别用户想要开始创作的意图
COLD_START_TRIGGERS = [
    "你好，开始创作",
    "开始创作",
    "你好，开始",
    "开始",
    "init",
    "hello",
    "你好",
]


def is_cold_start_message(content: str) -> bool:
    """
    判断消息是否是冷启动触发消息

    Args:
        content: 消息内容

    Returns:
        True: 是冷启动触发消息
        False: 普通用户消息
    """
    content_lower = content.lower().strip()
    return any(trigger.lower() in content_lower for trigger in COLD_START_TRIGGERS)


def create_welcome_message() -> tuple[AIMessage, UIInteractionBlock]:
    """
    创建AI欢迎消息和功能入口UI

    显示4个核心功能入口按钮，基于当前内容状态动态启用/禁用

    Returns:
        tuple[AIMessage, UIInteractionBlock]: 消息和 UI 块
    """
    welcome_content = """你好！我是你的 AI 创作助手。

我可以帮你：
• 🎬 从零开始创作短剧
• 📜 将小说改编为剧本
• 🎨 为剧本生成分镜
• 👤 提取和管理角色/场景资产

请从下方选择功能入口，或直接在输入框告诉我你想做什么。"""

    message = AIMessage(
        content=welcome_content,
        additional_kwargs={
            "message_type": "ai_welcome",
            "is_welcome": True,
        },
    )

    # 功能入口按钮（4个核心功能）
    buttons = [
        ActionButton(
            label="🎬 开始创作",
            action="start_creation",
            payload={"target": "story_planner"},
            style="primary",
            icon="Play",
        ),
        ActionButton(
            label="📜 剧本改编",
            action="adapt_script",
            payload={"target": "script_adapter"},
            style="secondary",
            icon="FileText",
        ),
        ActionButton(
            label="🎨 分镜制作",
            action="create_storyboard",
            payload={"target": "storyboard_director"},
            style="secondary",
            icon="Image",
        ),
        ActionButton(
            label="👤 资产探查",
            action="inspect_assets",
            payload={"target": "asset_inspector"},
            style="secondary",
            icon="Users",
        ),
    ]

    # 构造 Onboarding UI
    onboarding_ui = UIInteractionBlock(
        block_type=UIInteractionBlockType.ACTION_GROUP,
        title="选择功能入口",
        description="基于您的创作需求，选择以下功能入口：",
        buttons=buttons,
        data={
            "show_input_hint": True,
            "input_placeholder": "告诉我你想创作什么类型的短剧...",
        },
        dismissible=False,
    )

    return message, onboarding_ui


def should_auto_trigger_welcome(state: AgentState) -> bool:
    """
    判断是否应该自动触发欢迎消息
    """
    messages = state.get("messages", [])

    # 如果没有消息，是冷启动
    if not messages:
        return True

    # 检查是否只有系统消息或初始化消息
    visible_messages = [
        msg
        for msg in messages
        if isinstance(msg, (HumanMessage, AIMessage)) and not _is_init_message(msg)
    ]

    return len(visible_messages) == 0


def _is_init_message(msg: HumanMessage | AIMessage) -> bool:
    """判断消息是否是初始化消息（不应该显示给用户的）"""
    if isinstance(msg, HumanMessage):
        content = msg.content.lower().strip()
        return is_cold_start_message(content)

    if isinstance(msg, AIMessage):
        # 检查是否是系统提示消息
        content = msg.content.lower().strip()
        if content.startswith("[系统]"):
            return True
        # 检查元数据
        if msg.additional_kwargs.get("is_system"):
            return True
        # 检查是否是欢迎消息 (避免重复显示)
        if msg.additional_kwargs.get("is_welcome"):
            return False

    return False


def filter_visible_messages(
    messages: list[HumanMessage | AIMessage],
) -> list[HumanMessage | AIMessage]:
    """过滤消息列表，只保留对用户可见的消息"""
    return [msg for msg in messages if not _is_init_message(msg)]


def get_content_status(state: AgentState) -> dict[str, bool]:
    """
    获取当前内容状态，用于前端按钮启用/禁用判断

    Returns:
        {
            "has_novel_content": bool,
            "has_script": bool,
            "has_storyboard": bool,
            "has_any_content": bool,
        }
    """
    novel_content = state.get("novel_content", "")
    script = state.get("script", [])
    storyboard = state.get("storyboard", [])

    has_novel = bool(novel_content and len(novel_content) > 0)
    has_script = bool(script and len(script) > 0)
    has_storyboard = bool(storyboard and len(storyboard) > 0)

    return {
        "has_novel_content": has_novel,
        "has_script": has_script,
        "has_storyboard": has_storyboard,
        "has_any_content": has_novel or has_script or has_storyboard,
    }


def prepare_initial_state(
    state: AgentState, user_message: str, is_cold_start: bool = False
) -> AgentState:
    """
    准备初始状态

    Args:
        state: 当前状态
        user_message: 用户消息
        is_cold_start: 是否是冷启动

    Returns:
        更新后的状态
    """
    import json

    # 复制状态避免修改原始状态
    new_state = state.copy()

    # 获取现有消息
    messages = new_state.get("messages", [])

    if is_cold_start:
        # 冷启动：不添加用户的"你好，开始创作"到消息列表
        # 而是直接生成AI欢迎消息
        logger.info("Cold start detected, generating welcome message")
        welcome_msg, onboarding_ui = create_welcome_message()
        new_state["messages"] = messages + [welcome_msg]
        # 关键：手动注入 UI Interaction
        new_state["ui_interaction"] = onboarding_ui

        new_state["last_successful_node"] = "welcome"
        # 🔧 关键修复：冷启动时不设置 routed_agent
        # 让图自然结束，而不是强制路由到 "end"
        new_state["use_master_router"] = False
        new_state["routed_agent"] = None  # 不设置 routed_agent，让图正常结束
        new_state["routed_function"] = None
        new_state["routed_parameters"] = None

        # 添加内容状态
        new_state["content_status"] = get_content_status(new_state)
    else:
        # 正常流程：添加用户消息
        human_msg = HumanMessage(content=user_message)
        new_state["messages"] = messages + [human_msg]

        # 检测是否是 SDUI action 消息
        is_sdui_action = False
        try:
            if user_message.strip().startswith("{") and "action" in user_message:
                data = json.loads(user_message)
                action = data.get("action", "")
                # 定义所有 SDUI action
                sdui_actions = [
                    "select_genre",
                    "start_custom",
                    "proceed_to_planning",
                    "reset_genre",
                    "random_plan",
                    "select_plan",
                    "start_creation",
                    "adapt_script",
                    "create_storyboard",
                    "inspect_assets",
                ]
                # 包括 CMD 前缀的命令
                if action.startswith("CMD:") or action in sdui_actions:
                    is_sdui_action = True
                    logger.info("SDUI action detected in prepare_initial_state", action=action)
        except json.JSONDecodeError:
            pass

        # SDUI action 不需要 master_router 进行意图识别
        # 让 _route_from_start 中的 SDUI action 拦截处理
        new_state["use_master_router"] = not is_sdui_action
        new_state["routed_agent"] = None

        # 添加内容状态
        new_state["content_status"] = get_content_status(new_state)

        if is_sdui_action:
            logger.info("Skipping master_router for SDUI action")

    return new_state


__all__ = [
    "is_cold_start_message",
    "create_welcome_message",
    "should_auto_trigger_welcome",
    "filter_visible_messages",
    "prepare_initial_state",
    "get_content_status",
]
