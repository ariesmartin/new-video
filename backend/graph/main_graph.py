"""
Main Graph

LangGraph 主图定义，实现 Master Router 单一入口架构。

架构：
- 所有请求都经过 Master Router Agent 进行意图识别
- Master Router 输出 routed_agent 决定下一步
- 各 Agent 执行完成后回到 Master Router
- Module A 使用子图封装 Writer-Editor-Refiner 闭环
"""

from typing import Any, Dict
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

# 全局编译后的图实例
_compiled_graph = None


# ===== Agent 包装节点 =====


async def _cold_start_node(state: AgentState) -> Dict[str, Any]:
    """
    冷启动节点 - 生成欢迎消息和 UI 交互块

    这是 LangGraph 的入口节点，确保冷启动内容被正确保存到 checkpoint。
    根据 Context7 最佳实践，所有状态变更都应该通过节点返回，让 LangGraph 自动保存。
    """
    from backend.services.chat_init_service import create_welcome_message, get_content_status
    from langchain_core.messages import AIMessage
    import json

    logger.info("Executing cold start node", user_id=state.get("user_id"))

    try:
        # 生成欢迎消息和 UI 交互块
        welcome_msg, onboarding_ui = create_welcome_message()

        # 创建 AIMessage，包含 ui_interaction 在 metadata 中
        # 注意：LangGraph 会自动保存 messages 到 checkpoint
        ai_message = AIMessage(
            content=welcome_msg.content,
            additional_kwargs={
                "is_welcome": True,
                "ui_interaction": onboarding_ui.dict() if onboarding_ui else None,
            },
        )

        # 获取内容状态
        content_status = get_content_status(state)

        logger.info(
            "Cold start node completed",
            has_ui_interaction=bool(onboarding_ui),
            content_status=content_status,
        )

        return {
            "messages": [ai_message],  # LangGraph 会使用 add_messages reducer 追加
            "ui_interaction": onboarding_ui,  # 使用 ui_interaction_reducer 合并
            "content_status": content_status,
            "last_successful_node": "cold_start",
            "is_cold_start": True,
        }
    except Exception as e:
        logger.error("Cold start node failed", error=str(e))
        # 即使失败也返回一个基本的欢迎消息
        fallback_msg = AIMessage(content="你好！我是你的 AI 创作助手。")
        return {
            "messages": [fallback_msg],
            "error": f"冷启动失败: {str(e)}",
            "last_successful_node": "cold_start_error",
            "is_cold_start": True,
        }


async def _market_analyst_node(state: AgentState) -> Dict[str, Any]:
    """Market Analyst Agent 包装节点"""
    user_id = state.get("user_id")
    project_id = state.get("project_id")

    logger.info("Executing Market Analyst Agent", user_id=user_id)

    try:
        # 创建 Agent
        agent = await create_market_analyst_agent(user_id, project_id)

        # 执行 Agent
        result = await agent.ainvoke({"messages": state.get("messages", [])})

        # 更新状态
        messages = result.get("messages", [])
        return {
            "messages": messages,
            "market_report": messages[-1].content if messages else "",
            "last_successful_node": "market_analyst",
        }
    except Exception as e:
        logger.error("Market Analyst Agent failed", error=str(e))
        return {
            "error": f"市场分析失败: {str(e)}",
            "last_successful_node": "market_analyst_error",
        }


async def _story_planner_node(state: AgentState) -> Dict[str, Any]:
    """Story Planner Agent 包装节点"""
    user_id = state.get("user_id")
    project_id = state.get("project_id")

    logger.info("Executing Story Planner Agent", user_id=user_id)

    try:
        # 创建 Agent（会自动加载缓存的市场分析报告）
        agent = await create_story_planner_agent(user_id, project_id)

        # 执行 Agent
        result = await agent.ainvoke({"messages": state.get("messages", [])})

        # 更新状态
        messages = result.get("messages", [])
        return {
            "messages": messages,
            "story_plans": messages[-1].content if messages else "",
            "last_successful_node": "story_planner",
        }
    except Exception as e:
        logger.error("Story Planner Agent failed", error=str(e))
        return {
            "error": f"故事策划失败: {str(e)}",
            "last_successful_node": "story_planner_error",
        }


async def _script_adapter_node(state: AgentState) -> Dict[str, Any]:
    """Script Adapter Agent 包装节点"""
    user_id = state.get("user_id")
    project_id = state.get("project_id")

    logger.info("Executing Script Adapter Agent", user_id=user_id)

    try:
        agent = await create_script_adapter_agent(user_id, project_id)
        result = await agent.ainvoke({"messages": state.get("messages", [])})

        messages = result.get("messages", [])
        return {
            "messages": messages,
            "script": messages[-1].content if messages else "",
            "last_successful_node": "script_adapter",
        }
    except Exception as e:
        logger.error("Script Adapter Agent failed", error=str(e))
        return {
            "error": f"剧本改编失败: {str(e)}",
            "last_successful_node": "script_adapter_error",
        }


async def _storyboard_director_node(state: AgentState) -> Dict[str, Any]:
    """Storyboard Director Agent 包装节点"""
    user_id = state.get("user_id")
    project_id = state.get("project_id")

    logger.info("Executing Storyboard Director Agent", user_id=user_id)

    try:
        agent = await create_storyboard_director_agent(user_id, project_id)
        result = await agent.ainvoke({"messages": state.get("messages", [])})

        messages = result.get("messages", [])
        return {
            "messages": messages,
            "storyboard": messages[-1].content if messages else "",
            "last_successful_node": "storyboard_director",
        }
    except Exception as e:
        logger.error("Storyboard Director Agent failed", error=str(e))
        return {
            "error": f"分镜生成失败: {str(e)}",
            "last_successful_node": "storyboard_director_error",
        }


async def _image_generator_node(state: AgentState) -> Dict[str, Any]:
    """Image Generator Agent 包装节点"""
    user_id = state.get("user_id")
    project_id = state.get("project_id")

    logger.info("Executing Image Generator Agent", user_id=user_id)

    try:
        agent = await create_image_generator_agent(user_id, project_id)
        result = await agent.ainvoke({"messages": state.get("messages", [])})

        messages = result.get("messages", [])
        return {
            "messages": messages,
            "generated_images": messages[-1].content if messages else "",
            "last_successful_node": "image_generator",
        }
    except Exception as e:
        logger.error("Image Generator Agent failed", error=str(e))
        return {
            "error": f"图片生成失败: {str(e)}",
            "last_successful_node": "image_generator_error",
        }


# ===== 工具节点 =====


async def _wait_for_input_node(state: AgentState) -> dict[str, Any]:
    """等待用户输入节点"""
    logger.info(
        "Waiting for user input",
        current_stage=state.get("current_stage"),
        message_count=len(state.get("messages", [])),
    )

    return {
        "last_successful_node": "wait_for_input",
    }


async def _save_and_exit_node(state: AgentState) -> dict[str, Any]:
    """保存并退出节点"""
    current_episode = state.get("current_episode", 1)
    novel_content = state.get("novel_content", "")
    novel_archive = state.get("novel_archive", {})

    if novel_content:
        novel_archive[current_episode] = novel_content

    logger.info(
        "Saving and exiting",
        episode=current_episode,
        word_count=len(novel_content),
    )

    return {
        "novel_archive": novel_archive,
        "last_successful_node": "save_and_exit",
    }


def create_main_graph(checkpointer: BaseCheckpointSaver | None = None):
    """
    创建主图 - Master Router 单一入口架构

    流程：
    START -> Master Router -> (根据意图) -> 各 Agent -> 回到 Master Router

    Args:
        checkpointer: 可选的 Checkpoint 保存器

    Returns:
        编译后的 StateGraph
    """
    global _compiled_graph

    logger.info("Creating main graph with Master Router architecture")

    # 创建状态图
    graph = StateGraph(AgentState)

    # ===== 添加 Agent 节点 =====
    logger.info("Adding agent nodes...")

    # Level -1: 冷启动节点（处理欢迎消息）
    graph.add_node("cold_start", _cold_start_node)

    # Level 0: Master Router（唯一入口）
    graph.add_node("master_router", master_router_node)

    # Level 1: 市场分析
    graph.add_node("market_analyst", _market_analyst_node)

    # Level 2: 故事策划（读取缓存的市场分析）
    graph.add_node("story_planner", _story_planner_node)

    # Module B: 剧本改编
    graph.add_node("script_adapter", _script_adapter_node)

    # Module C: 分镜生成
    graph.add_node("storyboard_director", _storyboard_director_node)
    graph.add_node("image_generator", _image_generator_node)

    # 工具节点
    graph.add_node("wait_for_input", _wait_for_input_node)
    graph.add_node("save_and_exit", _save_and_exit_node)

    # ===== 添加边 =====
    logger.info("Adding edges...")

    # 入口：根据是否冷启动选择路径
    def route_from_start(state: AgentState):
        """入口路由 - 检测是否需要冷启动"""
        # 如果 messages 为空或明确标记为冷启动，走冷启动节点
        messages = state.get("messages", [])
        is_cold_start = state.get("is_cold_start", False)

        if is_cold_start or not messages:
            logger.info("Routing to cold_start node")
            return "cold_start"

        # 否则走正常流程
        logger.info("Routing to master_router")
        return "master_router"

    graph.add_conditional_edges(
        START,
        route_from_start,
        {
            "cold_start": "cold_start",
            "master_router": "master_router",
        },
    )

    # 冷启动节点直接结束（内容已保存到 checkpoint）
    graph.add_edge("cold_start", END)

    # Master Router -> 各 Agent（条件路由）
    graph.add_conditional_edges(
        "master_router",
        route_after_master,
        {
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            "script_adapter": "script_adapter",
            "storyboard_director": "storyboard_director",
            "image_generator": "image_generator",
            "master_router": "master_router",  # V4.1: 工作流继续
            "wait_for_input": "wait_for_input",
            "end": END,
        },
    )

    # 各 Agent 执行后的路由（V4.1 新增）
    # 如果有 workflow_plan 且还有下一步，回到 Master Router
    for node in [
        "market_analyst",
        "story_planner",
        "script_adapter",
        "storyboard_director",
        "image_generator",
    ]:
        graph.add_conditional_edges(
            node,
            route_after_agent_execution,
            {
                "master_router": "master_router",
                "end": END,
                "wait_for_input": "wait_for_input",
            },
        )

    # Wait for input -> END
    graph.add_edge("wait_for_input", END)

    # Save and exit -> END
    graph.add_edge("save_and_exit", END)

    # ===== 编译图 =====
    logger.info("Compiling graph...")
    _compiled_graph = graph.compile(
        checkpointer=checkpointer,
    )

    logger.info("Main graph compiled successfully")
    return _compiled_graph


def get_compiled_graph():
    """获取编译后的图（向后兼容）"""
    if _compiled_graph is None:
        raise RuntimeError("Graph not compiled. Call create_main_graph() first.")
    return _compiled_graph


async def get_graph_for_request(checkpointer=None):
    """
    为当前请求获取 Graph 实例

    这是修复 asyncio Event Loop 冲突的关键：
    - 每个请求创建新的 Graph 实例
    - 使用当前请求的事件循环
    - 避免跨事件循环的 Event 绑定问题
    """
    from backend.graph.checkpointer import checkpointer_manager

    if checkpointer is None:
        # 确保 checkpointer 管理器已初始化
        if not checkpointer_manager._initialized:
            await checkpointer_manager.initialize()
        # 使用管理器的 checkpointer 实例（用于 LangGraph 长期运行）
        checkpointer = checkpointer_manager._checkpointer

    graph = create_main_graph(checkpointer)
    logger.debug("Created new graph instance for request")
    return graph


# ===== 开发测试入口 =====

if __name__ == "__main__":
    """开发测试：直接运行此文件测试 Graph 创建"""
    import asyncio

    async def test():
        """测试 Graph 创建"""
        print("Testing main graph creation...")

        try:
            graph = create_main_graph()
            print(f"✅ Graph created successfully")
            print(f"   Nodes: {list(graph.nodes.keys())}")
            print(f"   Edges: {len(graph.edges)}")

            compiled = get_compiled_graph()
            print(f"✅ Compiled graph retrieved")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    asyncio.run(test())
