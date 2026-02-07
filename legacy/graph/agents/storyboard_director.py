"""
Storyboard Director Agent - Module C 分镜导演

使用 create_react_agent 创建，Prompt 从文件加载
"""

from pathlib import Path
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType
import structlog

logger = structlog.get_logger(__name__)


def _load_storyboard_director_prompt() -> str:
    """从文件加载 Storyboard Director 的 System Prompt"""
    prompt_path = (
        Path(__file__).parent.parent.parent.parent / "prompts" / "6_Storyboard_Director.md"
    )

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
        logger.debug("Loaded Storyboard Director prompt from file", path=str(prompt_path))
        return prompt

    except Exception as e:
        logger.error("Failed to load Storyboard Director prompt", error=str(e))
        return """你是分镜导演。将剧本转换为分镜设计并返回JSON格式。"""


async def create_storyboard_director_agent(user_id: str, project_id: str = None):
    """
    创建 Storyboard Director Agent

    Args:
        user_id: 用户ID
        project_id: 项目ID（可选）

    Returns:
        create_react_agent 创建的 Agent
    """
    router = get_model_router()
    model = await router.get_model(
        user_id=user_id, task_type=TaskType.STORYBOARD_DIRECTOR, project_id=project_id
    )

    # 创建 Agent - 使用 create_react_agent
    agent = create_react_agent(
        model=model,
        tools=[],  # 分镜导演目前不需要外部工具
        prompt=_load_storyboard_director_prompt(),
    )

    return agent


# 导出
__all__ = ["create_storyboard_director_agent"]
