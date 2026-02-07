"""
Image Generator Agent - Module C+ 图片生成师

使用 create_react_agent 创建，Prompt 从文件加载
"""

from pathlib import Path
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType
from backend.skills.image_generation import (
    storyboard_to_image_prompt,
    optimize_prompt_for_model,
)
import structlog

logger = structlog.get_logger(__name__)


def _load_image_generator_prompt() -> str:
    """从文件加载 Image Generator 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "11_Image_Generator.md"

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
        logger.debug("Loaded Image Generator prompt from file", path=str(prompt_path))
        return prompt

    except Exception as e:
        logger.error("Failed to load Image Generator prompt", error=str(e))
        return """你是图片生成师。为分镜生成高质量的图片生成提示词。"""


async def create_image_generator_agent(user_id: str, project_id: str = None):
    """
    创建 Image Generator Agent

    Args:
        user_id: 用户ID
        project_id: 项目ID（可选）

    Returns:
        create_react_agent 创建的 Agent
    """
    router = get_model_router()
    model = await router.get_model(
        user_id=user_id,
        task_type=TaskType.STORYBOARD_ARTIST,  # 使用 storyboard artist 的配置
        project_id=project_id,
    )

    # 创建 Agent - 使用 create_react_agent
    # 使用 Skills 生成和优化图片提示词
    agent = create_react_agent(
        model=model,
        tools=[
            storyboard_to_image_prompt,  # Skill: 分镜转图片提示词
            optimize_prompt_for_model,  # Skill: 针对模型优化提示词
        ],
        prompt=_load_image_generator_prompt(),
    )

    return agent


# 导出
__all__ = ["create_image_generator_agent"]
