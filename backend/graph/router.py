"""
Router Module

路由决策函数 - 纯函数，根据状态决定下一步。

架构说明:
- 采用 Master Router 单一入口架构
- 所有请求都经过 Master Router Agent 进行意图识别
- 路由函数仅用于 LangGraph 条件边的决策
"""

from typing import Literal
import structlog

from backend.schemas.agent_state import AgentState

logger = structlog.get_logger(__name__)


def route_from_start(state: AgentState) -> Literal["master_router"]:
    """
    入口路由决策

    所有请求都经过 Master Router Agent 进行意图识别和路由决策。
    不再使用双路由模式，简化架构。
    """
    logger.info("Routing to master_router")
    return "master_router"


def route_after_master(
    state: AgentState,
) -> Literal[
    "market_analyst",
    "story_planner",
    "skeleton_builder",
    "script_adapter",
    "storyboard_director",
    "image_generator",
    "module_a",
    "module_b",
    "module_c",
    "analysis_lab",
    "asset_inspector",
    "master_router",  # V4.1: 工作流继续时回到 Master Router
    "end",
]:
    """
    Master Router 后的路由决策 (V4.1 增强版)

    根据 Master Router Agent 输出的 routed_agent 字段决定下一步。
    支持多步骤工作流 (workflow_plan)。

    Args:
        state: 当前 AgentState，包含 routed_agent 和 workflow_plan 字段

    Returns:
        下一个节点的名称
    """
    routed_agent = state.get("routed_agent")
    workflow_plan = state.get("workflow_plan", [])
    current_step_idx = state.get("current_step_idx", 0)

    if not routed_agent:
        logger.warning("No routed_agent in state, defaulting to end")
        return "end"

    # Agent 名称到节点名称的映射
    agent_map = {
        # Level 1: 市场分析
        "market_analyst": "market_analyst",
        "Market_Analyst": "market_analyst",
        # Level 2: 故事策划
        "story_planner": "story_planner",
        "Story_Planner": "story_planner",
        # Level 3: 骨架构建
        "skeleton_builder": "skeleton_builder",
        "Skeleton_Builder": "skeleton_builder",
        # Module B: 剧本提取
        "script_adapter": "script_adapter",
        "Script_Adapter": "script_adapter",
        "module_b": "script_adapter",
        "Module_B": "script_adapter",
        # Module C: 分镜生成
        "storyboard_director": "storyboard_director",
        "Storyboard_Director": "storyboard_director",
        "module_c": "storyboard_director",
        "Module_C": "storyboard_director",
        # Module C+: 图片生成
        "image_generator": "image_generator",
        "Image_Generator": "image_generator",
        # Modules (旧版映射，向后兼容)
        "novel_writer": "module_a",
        "Novel_Writer": "module_a",
        "module_a": "module_a",
        "Module_A": "module_a",
        # Special Agents
        "analysis_lab": "analysis_lab",
        "Analysis_Lab": "analysis_lab",
        "asset_inspector": "asset_inspector",
        "Asset_Inspector": "asset_inspector",
    }

    target = agent_map.get(routed_agent)

    if target:
        logger.info(
            "Routing to agent",
            target=target,
            routed_agent=routed_agent,
            workflow_active=len(workflow_plan) > 0,
            step=f"{current_step_idx + 1}/{len(workflow_plan)}" if workflow_plan else "N/A",
        )
        return target
    else:
        logger.warning("Unknown routed_agent, defaulting to end", routed_agent=routed_agent)
        return "end"


def route_after_agent_execution(
    state: AgentState,
) -> Literal["master_router", "end", "wait_for_input"]:
    """
    Agent 执行完成后的路由决策 (V4.1 新增)

    检查是否有工作流需要继续执行。
    - 如果有 workflow_plan 且还有下一步，回到 Master Router 继续
    - 如果没有工作流，结束或等待用户输入

    Args:
        state: 当前 AgentState

    Returns:
        "master_router" - 继续执行工作流的下一步
        "end" - 工作流完成或单步骤完成
        "wait_for_input" - 等待用户输入
    """
    workflow_plan = state.get("workflow_plan", [])
    current_step_idx = state.get("current_step_idx", 0)

    if not workflow_plan:
        # 没有工作流，正常结束
        logger.debug("No workflow plan, ending")
        return "end"

    # 检查是否还有下一步
    next_idx = current_step_idx + 1
    if next_idx < len(workflow_plan):
        # 还有下一步，回到 Master Router
        logger.info(
            "Workflow continuing",
            current_step=current_step_idx + 1,
            next_step=next_idx + 1,
            total_steps=len(workflow_plan),
        )
        return "master_router"
    else:
        # 工作流完成
        logger.info("Workflow completed", total_steps=len(workflow_plan))
        return "end"


def route_after_market_analyst(
    state: AgentState,
) -> Literal["story_planner", "wait_for_input"]:
    """
    Market Analyst 后的路由决策

    如果用户已选择题材，则进入 Story Planner。
    否则等待用户输入。

    Args:
        state: 当前 AgentState

    Returns:
        "story_planner" 或 "wait_for_input"
    """
    user_config = state.get("user_config", {})

    if user_config.get("genre"):
        logger.info("Genre selected, proceeding to story_planner", genre=user_config["genre"])
        return "story_planner"

    logger.info("Waiting for user genre selection")
    return "wait_for_input"


def route_after_story_planner(
    state: AgentState,
) -> Literal["skeleton_builder", "wait_for_input"]:
    """
    Story Planner 后的路由决策

    如果用户已选择方案，则进入 Skeleton Builder。
    否则等待用户输入。
    """
    selected_plan = state.get("selected_plan")

    if selected_plan:
        logger.info("Plan selected, proceeding to skeleton_builder")
        return "skeleton_builder"

    logger.info("Waiting for user plan selection")
    return "wait_for_input"


def route_after_skeleton_builder(
    state: AgentState,
) -> Literal["module_a", "wait_for_input"]:
    """
    Skeleton Builder 后的路由决策

    如果用户确认大纲，则进入 Module A（小说生成）。
    否则等待用户输入。
    """
    approval_status = state.get("approval_status")
    beat_sheet = state.get("beat_sheet", [])

    if approval_status == "APPROVED" and beat_sheet:
        logger.info("Skeleton approved, proceeding to module_a")
        return "module_a"

    logger.info("Waiting for user skeleton approval")
    return "wait_for_input"


def route_after_editor(
    state: AgentState,
) -> Literal["approve", "refine"]:
    """
    Editor Agent 后的路由决策（用于 Module A 子图）

    根据 Editor 的评分决定是通过还是需要精修。

    Args:
        state: 当前 AgentState，包含 quality_score 和 revision_count

    Returns:
        "approve" - 评分 >= 80 或达到最大重试次数
        "refine" - 评分 < 80，需要精修
    """
    quality_score = state.get("quality_score", 0)
    revision_count = state.get("revision_count", 0)
    max_retries = 3

    if quality_score >= 80:
        logger.info("Content approved", quality_score=quality_score)
        return "approve"
    elif revision_count >= max_retries:
        logger.warning(
            "Max retries reached, forcing approval",
            revision_count=revision_count,
            quality_score=quality_score,
        )
        return "approve"
    else:
        logger.info(
            "Content needs refinement",
            quality_score=quality_score,
            revision_count=revision_count,
        )
        return "refine"


def route_after_module_a(
    state: AgentState,
) -> Literal["continue", "module_b", "wait_for_input"]:
    """
    Module A 完成后的路由决策

    根据当前集数和用户意图决定下一步。

    Returns:
        "continue" - 继续生成下一集
        "module_b" - 进入剧本提取
        "wait_for_input" - 等待用户决策
    """
    current_episode = state.get("current_episode", 1)
    total_episodes = state.get("user_config", {}).get("total_episodes", 10)
    routed_agent = state.get("routed_agent")

    # 检查用户是否明确选择进入 Module B
    if routed_agent in ["script_adapter", "module_b"]:
        logger.info("User chose to proceed to module_b")
        return "module_b"

    # 如果还有剩余集数，默认继续生成
    if current_episode < total_episodes:
        logger.info(
            "Continuing to next episode",
            current_episode=current_episode,
            total_episodes=total_episodes,
        )
        return "continue"

    # 所有集数完成，询问用户是否进入 Module B
    logger.info("All episodes completed, waiting for user decision")
    return "wait_for_input"


# ===== 辅助函数 =====


def get_node_display_name(node_name: str) -> str:
    """
    获取节点的显示名称（用于前端展示）

    Args:
        node_name: 节点内部名称

    Returns:
        用户友好的显示名称
    """
    display_names = {
        "master_router": "🧠 意图识别",
        "market_analyst": "🔍 市场分析",
        "story_planner": "✍️ 故事规划",
        "skeleton_builder": "🏗️ 骨架构建",
        "module_a": "📖 小说生成",
        "module_b": "🎬 剧本提取",
        "module_c": "🎨 分镜生成",
        "analysis_lab": "🔬 分析实验室",
        "asset_inspector": "🎭 资产探查",
        "wait_for_input": "⏳ 等待用户",
    }
    return display_names.get(node_name, node_name)


def is_terminal_node(node_name: str) -> bool:
    """
    判断是否为终止节点

    Args:
        node_name: 节点名称

    Returns:
        是否为终止节点
    """
    return node_name in ["end", "wait_for_input"]
