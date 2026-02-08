"""
Market Analyst Agent - Level 1 市场分析

使用 create_react_agent 创建，Prompt 从文件加载
"""

from pathlib import Path
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType

# ✅ 使用 Skills 替代直接调用 Tools
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes,
    get_hooks,
    get_character_archetypes,
    get_market_trends,
)
import structlog

logger = structlog.get_logger(__name__)


def _load_market_analyst_prompt() -> str:
    """从文件加载 Market Analyst 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "1_Market_Analyst.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 Markdown 内容（去掉开头的标题）
        lines = content.split("\n")
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                start_idx = i
                break

        prompt = "\n".join(lines[start_idx:]).strip()
        logger.debug("Loaded Market Analyst prompt from file", path=str(prompt_path))
        return prompt

    except Exception as e:
        logger.error("Failed to load Market Analyst prompt", error=str(e))
        return """你是短剧市场分析专家。分析市场趋势并返回JSON格式报告。"""


async def create_market_analyst_agent(user_id: str, project_id: str = None):
    """
    创建 Market Analyst Agent

    Args:
        user_id: 用户ID
        project_id: 项目ID（可选）

    Returns:
        create_react_agent 创建的 Agent
    """
    # 获取配置好的模型
    router = get_model_router()
    model = await router.get_model(
        user_id=user_id, task_type=TaskType.MARKET_ANALYST, project_id=project_id
    )

    # 创建 Agent - 使用 Skills 替代直接 Tools
    agent = create_react_agent(
        model=model,
        tools=[
            load_genre_context,  # ✅ 加载题材上下文
            get_tropes,  # ✅ 获取推荐元素
            get_hooks,  # ✅ 获取钩子模板
            get_character_archetypes,  # ✅ 获取角色原型
            get_market_trends,  # ✅ 获取市场趋势
        ],
        prompt=_load_market_analyst_prompt(),
    )

    return agent


# 导出
__all__ = ["create_market_analyst_agent"]
