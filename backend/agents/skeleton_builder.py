"""
Skeleton Builder Agent - Level 3 大纲架构师

使用 create_react_agent 创建，负责生成故事骨架结构。
调用 TensionService 生成张力曲线。
支持自主调用题材库 Tools 获取题材指导。
"""

from pathlib import Path
from typing import Dict, Optional
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType
from backend.services.tension_service import generate_tension_curve
from backend.skills.theme_library import (
    load_genre_context,
    search_elements_by_effectiveness,
    get_hook_templates_by_type,
    analyze_genre_compatibility,
)
import structlog

logger = structlog.get_logger(__name__)


async def _load_skeleton_builder_prompt(
    selected_plan: Dict,
    user_config: Dict,
    market_report: Optional[Dict] = None,
) -> str:
    """从文件加载 Skeleton Builder 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "3_Skeleton_Builder.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 注入变量到 Prompt
        content = content.replace("{total_episodes}", str(user_config.get("total_episodes", 80)))
        content = content.replace("{genre}", user_config.get("genre", "revenge"))
        content = content.replace("{setting}", user_config.get("setting", "modern"))
        content = content.replace("{ending}", user_config.get("ending", "HE"))
        content = content.replace("{selected_plan}", str(selected_plan))
        content = content.replace("{user_config}", str(user_config))

        if market_report:
            content = content.replace("{market_report}", str(market_report))
        else:
            content = content.replace("{market_report}", "未提供")

        logger.info("Skeleton Builder Prompt loaded", prompt_length=len(content))
        return content

    except Exception as e:
        logger.error("Failed to load Skeleton Builder prompt", error=str(e))
        # Fallback prompt
        return "You are a skeleton builder agent. Generate a story outline based on the input."


async def create_skeleton_builder_agent(
    user_id: str,
    project_id: str,
    selected_plan: Dict,
    user_config: Dict,
    market_report: Optional[Dict] = None,
):
    """
    创建 Skeleton Builder Agent

    Args:
        user_id: 用户ID
        project_id: 项目ID
        selected_plan: 选中的故事方案
        user_config: 用户配置（包含total_episodes等）
        market_report: 市场分析报告（可选）

    Returns:
        create_react_agent 返回的 Compiled Graph
    """
    logger.info(
        "Creating Skeleton Builder Agent",
        user_id=user_id,
        project_id=project_id,
        title=selected_plan.get("title", "Unknown"),
        total_episodes=user_config.get("total_episodes", 80),
    )

    # 加载并格式化 Prompt
    system_prompt = await _load_skeleton_builder_prompt(
        selected_plan=selected_plan,
        user_config=user_config,
        market_report=market_report,
    )

    # 获取模型（骨架构建使用 SKELETON_BUILDER TaskType）
    model_router = get_model_router()
    model = await model_router.get_model(
        user_id=user_id, task_type=TaskType.SKELETON_BUILDER, project_id=project_id
    )

    # 创建 Agent（Skeleton Builder 可以自主调用题材库 Tools）
    # 这些 Tools 让 Agent 能够根据查询题材指导、爆款元素、钩子模板等
    tools = [
        load_genre_context,  # 加载题材完整上下文（核心公式、避雷清单等）
        search_elements_by_effectiveness,  # 搜索高效果爆款元素
        get_hook_templates_by_type,  # 获取钩子模板（前3秒留存）
        analyze_genre_compatibility,  # 分析题材兼容性（双题材时）
    ]

    agent = create_react_agent(
        model=model,
        tools=tools,  # Agent 自主决定何时调用这些 Tools
        prompt=system_prompt,
    )

    logger.info("Skeleton Builder Agent created successfully")
    return agent


async def generate_tension_curve_for_skeleton(
    total_episodes: int, curve_type: str = "standard"
) -> Dict:
    """
    为大纲生成张力曲线

    Args:
        total_episodes: 总集数
        curve_type: 曲线类型（standard/fast/slow）

    Returns:
        张力曲线数据
    """
    logger.info(
        "Generating tension curve",
        total_episodes=total_episodes,
        curve_type=curve_type,
    )

    return generate_tension_curve(total_episodes=total_episodes, curve_type=curve_type)


# Node wrapper for LangGraph
async def skeleton_builder_node(state: Dict) -> Dict:
    """
    Skeleton Builder Node 包装器

    用于直接添加到 LangGraph 中作为 Node
    """
    from backend.schemas.agent_state import AgentState

    user_id = state.get("user_id")
    project_id = state.get("project_id")
    selected_plan = state.get("selected_plan", {})
    user_config = state.get("user_config", {})
    market_report = state.get("market_report")
    messages = state.get("messages", [])

    logger.info(
        "Executing Skeleton Builder Node",
        user_id=user_id,
        message_count=len(messages),
    )

    try:
        # 创建 Agent
        agent = await create_skeleton_builder_agent(
            user_id=user_id,
            project_id=project_id,
            selected_plan=selected_plan,
            user_config=user_config,
            market_report=market_report,
        )

        # 执行 Agent
        result = await agent.ainvoke({"messages": messages})

        # 解析结果
        output_messages = result.get("messages", [])

        # 生成张力曲线
        total_episodes = user_config.get("total_episodes", 80)
        tension_curve = await generate_tension_curve_for_skeleton(total_episodes)

        logger.info(
            "Skeleton Builder Node completed",
            output_messages=len(output_messages),
        )

        return {
            "messages": output_messages,
            "tension_curve": tension_curve,
            "last_successful_node": "skeleton_builder",
        }

    except Exception as e:
        logger.error("Skeleton Builder Node failed", error=str(e))
        return {
            "error": f"大纲生成失败: {str(e)}",
            "last_successful_node": "skeleton_builder_error",
        }
