"""
Script Adapter Agent - Module B 剧本改编师

使用 create_react_agent 创建，Prompt 从文件加载
"""

from pathlib import Path
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType
from backend.skills.script_adaptation import (
    novel_to_script,
    extract_scenes,
    generate_dialogue,
)
import structlog

logger = structlog.get_logger(__name__)


def _load_script_adapter_prompt() -> str:
    """从文件加载 Script Adapter 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "5_Script_Adapter.md"

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
        logger.debug("Loaded Script Adapter prompt from file", path=str(prompt_path))
        return prompt

    except Exception as e:
        logger.error("Failed to load Script Adapter prompt", error=str(e))
        return """你是剧本改编师。将小说转换为结构化剧本并返回JSON格式。"""


async def create_script_adapter_agent(user_id: str, project_id: str = None):
    """
    创建 Script Adapter Agent

    Args:
        user_id: 用户ID
        project_id: 项目ID（可选）

    Returns:
        create_react_agent 创建的 Agent
    """
    router = get_model_router()
    model = await router.get_model(
        user_id=user_id, task_type=TaskType.SCRIPT_ADAPTER, project_id=project_id
    )

    # 创建 Agent - 使用 create_react_agent
    # 使用 Skills 而不是直接调用 Tools
    agent = create_react_agent(
        model=model,
        tools=[
            novel_to_script,  # Skill: 小说转剧本
            extract_scenes,  # Skill: 场景提取
            generate_dialogue,  # Skill: 对话生成
        ],
        prompt=_load_script_adapter_prompt(),
    )

    return agent


# 导出
__all__ = ["create_script_adapter_agent"]
