"""
Refiner Agent - 冷静修复工程师

使用 create_react_agent 创建，负责根据 Editor 的审阅报告修复内容。
保持原文风，精准修复问题。
"""

from pathlib import Path
from typing import Dict, Optional
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType
import structlog

logger = structlog.get_logger(__name__)


async def _load_refiner_prompt(
    content_type: str,
    style_dna: Optional[str] = None,
    character_voices: Optional[Dict] = None,
) -> str:
    """从文件加载 Refiner 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "8_Refiner.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 注入文风DNA
        if style_dna:
            content = content.replace("{style_dna}", style_dna)
        else:
            content = content.replace("{style_dna}", "待分析")

        # 注入角色声纹
        if character_voices:
            voices_text = "\n".join(
                [f"- {name}: {voice}" for name, voice in character_voices.items()]
            )
            content = content.replace("{character_voices}", voices_text)
        else:
            content = content.replace("{character_voices}", "待提取")

        # 注入内容类型
        content = content.replace("{content_type}", content_type)

        logger.info("Refiner Prompt loaded", prompt_length=len(content))
        return content

    except Exception as e:
        logger.error("Failed to load Refiner prompt", error=str(e))
        return "You are a refiner agent. Fix the content based on the review report."


async def create_refiner_agent(
    user_id: str,
    project_id: str,
    content_type: str = "outline",
    style_dna: Optional[str] = None,
    character_voices: Optional[Dict] = None,
):
    """
    创建 Refiner Agent（冷静修复工程师）

    Args:
        user_id: 用户ID
        project_id: 项目ID
        content_type: 内容类型（outline/novel/script/storyboard）
        style_dna: 文风DNA（可选）
        character_voices: 角色声纹（可选）

    Returns:
        create_react_agent 返回的 Compiled Graph
    """
    logger.info(
        "Creating Refiner Agent",
        user_id=user_id,
        project_id=project_id,
        content_type=content_type,
        has_style_dna=style_dna is not None,
    )

    # 加载并格式化 Prompt
    system_prompt = await _load_refiner_prompt(
        content_type=content_type,
        style_dna=style_dna,
        character_voices=character_voices,
    )

    # 获取模型（修复任务使用 REFINER TaskType）
    model_router = get_model_router()
    model = await model_router.get_model(
        user_id=user_id, task_type=TaskType.REFINER, project_id=project_id
    )

    # 创建 Agent（Refiner 不需要 Tools，纯修复任务）
    agent = create_react_agent(
        model=model,
        tools=[],  # 纯修复任务，不需要外部工具
        prompt=system_prompt,
    )

    logger.info("Refiner Agent created successfully")
    return agent


# Node wrapper for LangGraph
async def refiner_node(state: Dict) -> Dict:
    """
    Refiner Node 包装器

    用于直接添加到 LangGraph 中作为 Node
    """
    user_id = state.get("user_id")
    project_id = state.get("project_id")
    messages = state.get("messages", [])

    # 从 state 中提取完整上下文（必须包含所有元数据）
    review_report = state.get("review_report")
    user_config = state.get("user_config", {})
    style_dna = user_config.get("style_dna")

    # 从 character_bible 提取角色声纹
    character_bible = state.get("character_bible", [])
    character_voices = {}
    for char in character_bible:
        name = char.get("name", "Unknown")
        speech_pattern = char.get("speech_pattern", "")
        personality = char.get("personality", "")
        if speech_pattern or personality:
            character_voices[name] = (
                f"{personality}；说话方式：{speech_pattern}" if personality else speech_pattern
            )

    # 提取其他上下文
    genre_combination = user_config.get("sub_tags", ["revenge", "romance"])
    ending = user_config.get("ending", "HE")
    total_episodes = user_config.get("total_episodes", 80)

    # 根据当前阶段判断 content_type
    current_stage = state.get("current_stage", "L3")
    content_type_map = {
        "L3": "outline",
        "ModA": "novel",
        "ModB": "script",
        "ModC": "storyboard",
    }
    content_type = content_type_map.get(current_stage, "outline")

    logger.info(
        "Executing Refiner Node",
        user_id=user_id,
        content_type=content_type,
        has_review_report=review_report is not None,
    )

    if not review_report:
        logger.error("No review report found in state")
        return {
            "error": "缺少审阅报告，无法进行修复",
            "last_successful_node": "refiner_error",
        }

    try:
        # 创建 Agent（传递完整上下文）
        agent = await create_refiner_agent(
            user_id=user_id,
            project_id=project_id,
            content_type=content_type,
            style_dna=style_dna,
            character_voices=character_voices if character_voices else None,
        )

        # 执行 Agent
        result = await agent.ainvoke({"messages": messages})

        # 解析结果
        output_messages = result.get("messages", [])

        # 从最后一个消息中提取 refine_log
        refine_log = None
        refined_content = None
        if output_messages:
            import json
            import re

            last_message = output_messages[-1]
            content = (
                last_message.content if hasattr(last_message, "content") else str(last_message)
            )

            # 尝试提取 JSON
            json_match = re.search(r"```json\s*\n?([\s\S]*?)\n?```", content)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1).strip())
                    refine_log = parsed.get("change_log")
                    refined_content = parsed.get("refined_content")
                    logger.info(
                        "Extracted refine log",
                        total_changes=len(refine_log) if refine_log else 0,
                    )
                except json.JSONDecodeError:
                    logger.warning("Failed to parse refine log JSON")

        logger.info(
            "Refiner Node completed",
            output_messages=len(output_messages),
            has_refine_log=refine_log is not None,
        )

        return {
            "messages": output_messages,
            "refine_log": refine_log,
            "refined_content": refined_content,
            "last_successful_node": "refiner",
        }

    except Exception as e:
        logger.error("Refiner Node failed", error=str(e))
        return {
            "error": f"修复失败: {str(e)}",
            "last_successful_node": "refiner_error",
        }
