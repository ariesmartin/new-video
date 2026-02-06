"""
Story Planner Agent - Level 2 故事策划

使用 create_react_agent 创建，Prompt 从文件加载。
需要读取缓存的市场分析报告并注入到 Prompt 中。
"""

from pathlib import Path
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.services.market_analysis import get_market_analysis_service
from backend.schemas.model_config import TaskType
import structlog

logger = structlog.get_logger(__name__)


def _load_story_planner_prompt(market_report: dict = None) -> str:
    """
    从文件加载 Story Planner 的 System Prompt

    Args:
        market_report: 缓存的市场分析报告（可选）

    Returns:
        完整的 System Prompt（含市场数据注入）
    """
    prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "2_Story_Planner.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 Markdown 内容
        lines = content.split("\n")
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                start_idx = i
                break

        prompt = "\n".join(lines[start_idx:]).strip()

        # 注入市场分析报告（如果存在）
        if market_report:
            market_context = _format_market_report(market_report)
            prompt = prompt.replace("{market_report}", market_context)
        else:
            # 使用默认市场数据
            prompt = prompt.replace("{market_report}", _get_default_market_report())

        logger.debug("Loaded Story Planner prompt from file", path=str(prompt_path))
        return prompt

    except Exception as e:
        logger.error("Failed to load Story Planner prompt", error=str(e))
        return """你是短剧故事策划专家。基于市场趋势生成3个不同维度的故事方案。"""


def _format_market_report(report: dict) -> str:
    """格式化市场分析报告为 Prompt 可用的字符串"""
    lines = ["## 最新市场分析报告"]

    # 添加题材趋势
    genres = report.get("genres", [])
    if genres:
        lines.append("\n### 热门题材")
        for g in genres:
            trend_emoji = {"hot": "🔥", "up": "📈", "stable": "➡️", "down": "📉"}.get(
                g.get("trend"), "•"
            )
            lines.append(f"{trend_emoji} {g.get('name', 'N/A')}: {g.get('description', '')}")

    # 添加调性
    tones = report.get("tones", [])
    if tones:
        lines.append(f"\n### 推荐调性\n{', '.join(tones)}")

    # 添加洞察
    insights = report.get("insights", "")
    if insights:
        lines.append(f"\n### 市场洞察\n{insights}")

    # 添加受众
    audience = report.get("audience", "")
    if audience:
        lines.append(f"\n### 目标受众\n{audience}")

    return "\n".join(lines)


def _get_default_market_report() -> str:
    """获取默认市场报告（当缓存不存在时使用）"""
    return """## 默认市场参考
- 逆袭复仇题材持续热门
- 现代都市爱情稳定需求
- 用户偏好：快节奏、强情绪、反套路
"""


async def create_story_planner_agent(user_id: str, project_id: str = None):
    """
    创建 Story Planner Agent

    会自动获取最新的市场分析报告并注入到 Prompt 中。

    Args:
        user_id: 用户ID
        project_id: 项目ID（可选）

    Returns:
        create_react_agent 创建的 Agent
    """
    # 1. 获取缓存的市场分析报告
    try:
        market_service = get_market_analysis_service()
        market_report = await market_service.get_latest_analysis()
        logger.info(
            "Loaded market report for Story Planner",
            has_report=bool(market_report),
            user_id=user_id,
        )
    except Exception as e:
        logger.warning("Failed to load market report, using defaults", error=str(e))
        market_report = None

    # 2. 获取配置好的模型
    router = get_model_router()
    model = await router.get_model(
        user_id=user_id, task_type=TaskType.STORY_PLANNER, project_id=project_id
    )

    # 3. 创建 Agent（注入市场报告到 Prompt）
    agent = create_react_agent(
        model=model,
        tools=[],  # Story Planner 是纯创作任务，不需要工具
        state_modifier=_load_story_planner_prompt(market_report),
    )

    return agent


# 导出
__all__ = ["create_story_planner_agent"]
