"""
Main Graph - Factory Pattern 改进版

改进点：
- 使用 Factory Pattern 构建 Graph
- 构建时传入 user_id/project_id
- Agent 直接作为 Node，不需要包装
- 符合 LangGraph 官方标准

与旧版对比：
- 旧版：Node 包装 Agent（每次执行都创建 Agent）
- 新版：Factory Pattern（Agent 只创建一次）
"""

from typing import Any, Dict, Optional
import structlog
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from backend.schemas.agent_state import AgentState
from backend.graph.agents import (
    master_router_node,
    create_market_analyst_agent,
    create_story_planner_agent,
    create_script_adapter_agent,
    create_storyboard_director_agent,
    create_image_generator_agent,
)
from backend.graph.router import (
    route_after_master,
    route_after_agent_execution,
)

logger = structlog.get_logger(__name__)


# ===== Factory Pattern 构建函数 =====


async def build_main_graph_factory(
    user_id: str,
    project_id: Optional[str] = None,
    checkpointer: Optional[BaseCheckpointSaver] = None,
):
    """
    构建主 Graph（Factory Pattern 改进版）

    改进点：
    1. 构建时传入 user_id/project_id
    2. Agent 只创建一次
    3. Agent 直接作为 Node（不需要包装）
    4. 符合 LangGraph 官方标准

    Args:
        user_id: 用户ID（运行时传入）
        project_id: 项目ID（可选）
        checkpointer: Checkpoint 用于状态持久化

    Returns:
        Compiled Graph
    """
    logger.info(
        "Building main graph with Factory Pattern",
        user_id=user_id,
        project_id=project_id,
    )

    # ===== 步骤 1：创建所有 Agents（只创建一次）=====
    logger.info("Creating agents...")

    # Market Analyst Agent
    market_analyst = await create_market_analyst_agent(user_id, project_id)
    logger.info("✅ Market Analyst agent created")

    # Story Planner Agent
    story_planner = await create_story_planner_agent(user_id, project_id)
    logger.info("✅ Story Planner agent created")

    # Script Adapter Agent
    script_adapter = await create_script_adapter_agent(user_id, project_id)
    logger.info("✅ Script Adapter agent created")

    # Storyboard Director Agent
    storyboard_director = await create_storyboard_director_agent(user_id, project_id)
    logger.info("✅ Storyboard Director agent created")

    # Image Generator Agent
    image_generator = await create_image_generator_agent(user_id, project_id)
    logger.info("✅ Image Generator agent created")

    # ===== 步骤 2：创建工作流 =====
    workflow = StateGraph(AgentState)

    # ===== 步骤 3：添加 Nodes =====

    # 普通 Nodes（辅助功能）
    workflow.add_node("cold_start", _cold_start_node)
    workflow.add_node("wait_for_input", _wait_for_input_node)
    workflow.add_node("save_and_exit", _save_and_exit_node)

    # ✅ Agent Nodes（直接作为 Node，不需要包装）
    workflow.add_node("master_router", master_router_node)
    workflow.add_node("market_analyst", market_analyst)  # ✅ Agent 直接作为 Node
    workflow.add_node("story_planner", story_planner)  # ✅ Agent 直接作为 Node
    workflow.add_node("script_adapter", script_adapter)  # ✅ Agent 直接作为 Node
    workflow.add_node("storyboard_director", storyboard_director)  # ✅ Agent 直接作为 Node
    workflow.add_node("image_generator", image_generator)  # ✅ Agent 直接作为 Node

    # ===== 步骤 4：添加边（路由）=====

    # 入口
    workflow.set_entry_point("cold_start")

    # Cold Start -> Master Router
    workflow.add_edge("cold_start", "master_router")

    # Master Router -> 各 Agent（条件路由）
    workflow.add_conditional_edges(
        "master_router",
        route_after_master,
        {
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            "script_adapter": "script_adapter",
            "storyboard_director": "storyboard_director",
            "image_generator": "image_generator",
            "wait_for_input": "wait_for_input",
            "save_and_exit": "save_and_exit",
        },
    )

    # 各 Agent -> Master Router（执行完成后返回）
    workflow.add_conditional_edges(
        "market_analyst",
        route_after_agent_execution,
        {"master_router": "master_router", "wait_for_input": "wait_for_input"},
    )
    workflow.add_conditional_edges(
        "story_planner",
        route_after_agent_execution,
        {"master_router": "master_router", "wait_for_input": "wait_for_input"},
    )
    workflow.add_conditional_edges(
        "script_adapter",
        route_after_agent_execution,
        {"master_router": "master_router", "wait_for_input": "wait_for_input"},
    )
    workflow.add_conditional_edges(
        "storyboard_director",
        route_after_agent_execution,
        {"master_router": "master_router", "wait_for_input": "wait_for_input"},
    )
    workflow.add_conditional_edges(
        "image_generator",
        route_after_agent_execution,
        {"master_router": "master_router", "wait_for_input": "wait_for_input"},
    )

    # Wait for Input -> Master Router（用户输入后继续）
    workflow.add_edge("wait_for_input", "master_router")

    # Save and Exit -> END
    workflow.add_edge("save_and_exit", END)

    # ===== 步骤 5：编译 Graph =====
    if checkpointer:
        compiled = workflow.compile(checkpointer=checkpointer)
    else:
        compiled = workflow.compile()

    logger.info(
        "✅ Main graph built successfully with Factory Pattern",
        user_id=user_id,
        nodes=list(compiled.nodes.keys()),
    )

    return compiled


# ===== 辅助 Nodes（保持不变）=====


async def _cold_start_node(state: AgentState) -> Dict[str, Any]:
    """冷启动节点 - 生成欢迎消息"""
    from backend.services.chat_init_service import create_welcome_message, get_content_status
    from langchain_core.messages import AIMessage

    logger.info("Executing cold start node", user_id=state.get("user_id"))

    try:
        welcome_msg, onboarding_ui = create_welcome_message()

        ai_message = AIMessage(
            content=welcome_msg.content,
            additional_kwargs={
                "is_welcome": True,
                "ui_interaction": onboarding_ui.dict() if onboarding_ui else None,
            },
        )

        content_status = get_content_status(state)

        return {
            "messages": [ai_message],
            "ui_interaction": onboarding_ui,
            "content_status": content_status,
            "last_successful_node": "cold_start",
            "is_cold_start": True,
        }
    except Exception as e:
        logger.error("Cold start node failed", error=str(e))
        fallback_msg = AIMessage(content="你好！我是你的 AI 创作助手。")
        return {
            "messages": [fallback_msg],
            "error": f"冷启动失败: {str(e)}",
            "last_successful_node": "cold_start_error",
            "is_cold_start": True,
        }


async def _wait_for_input_node(state: AgentState) -> Dict[str, Any]:
    """等待用户输入节点"""
    logger.info("Waiting for user input", user_id=state.get("user_id"))
    return {
        **state,
        "last_successful_node": "wait_for_input",
    }


async def _save_and_exit_node(state: AgentState) -> Dict[str, Any]:
    """保存并退出节点"""
    logger.info("Saving and exiting", user_id=state.get("user_id"))
    return {
        **state,
        "last_successful_node": "save_and_exit",
    }


# ===== 导出 =====

__all__ = [
    "build_main_graph_factory",
]
