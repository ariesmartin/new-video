"""
Editor Agent - 毒舌审阅官

使用 create_react_agent 创建，负责对内容进行毒舌审阅。
只找问题、吐槽、评分，不给修复建议。
"""

from pathlib import Path
from typing import Dict, Optional
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.services.review_service import calculate_weights, get_checkpoints
from backend.schemas.model_config import TaskType
import structlog

logger = structlog.get_logger(__name__)


async def _load_editor_prompt(
    content_type: str,
    genre_combination: list,
    weights: Dict,
    ending: str,
    total_episodes: int,
) -> str:
    """从文件加载 Editor 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "7_Editor_Reviewer.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 注入权重信息
        weights_text = "\n".join([f"- {key}: {value * 100:.0f}%" for key, value in weights.items()])
        content = content.replace("{weights}", weights_text)

        # 注入具体权重变量
        for key, value in weights.items():
            content = content.replace(f"{{{key}_weight}}", f"{value * 100:.0f}%")

        # 注入题材组合
        content = content.replace("{genre_combination}", str(genre_combination))

        # 注入内容类型
        content = content.replace("{content_type}", content_type)

        # 注入结局类型
        content = content.replace("{ending}", ending)

        # 注入总集数
        content = content.replace("{total_episodes}", str(total_episodes))

        # 注入检查点
        checkpoints = get_checkpoints(content_type)
        for category, checks in checkpoints.items():
            checks_text = "\n  - ".join([""] + checks) if checks else ""
            content = content.replace(f"{{{category}_checkpoints}}", checks_text)

        logger.info("Editor Prompt loaded", prompt_length=len(content))
        return content

    except Exception as e:
        logger.error("Failed to load Editor prompt", error=str(e))
        return "You are an editor agent. Review the content and find issues."


async def create_editor_agent(
    user_id: str,
    project_id: str,
    content_type: str = "outline",
    genre_combination: Optional[list] = None,
    ending: str = "HE",
    total_episodes: int = 80,
):
    """
    创建 Editor Agent（毒舌审阅官）

    Args:
        user_id: 用户ID
        project_id: 项目ID
        content_type: 内容类型（outline/novel/script/storyboard）
        genre_combination: 题材组合（如 ["revenge", "romance"]）
        ending: 结局类型（HE/BE/OE）
        total_episodes: 总集数

    Returns:
        create_react_agent 返回的 Compiled Graph
    """
    # 默认题材组合
    if genre_combination is None:
        genre_combination = ["revenge", "romance"]

    logger.info(
        "Creating Editor Agent",
        user_id=user_id,
        project_id=project_id,
        content_type=content_type,
        genre_combination=genre_combination,
        ending=ending,
        total_episodes=total_episodes,
    )

    # 计算权重
    weights = calculate_weights(genre_combination)
    logger.info("Calculated review weights", weights=weights)

    # 加载并格式化 Prompt
    system_prompt = await _load_editor_prompt(
        content_type=content_type,
        genre_combination=genre_combination,
        weights=weights,
        ending=ending,
        total_episodes=total_episodes,
    )

    # 获取模型（审阅任务使用 EDITOR TaskType）
    model_router = get_model_router()
    model = await model_router.get_model(
        user_id=user_id, task_type=TaskType.EDITOR, project_id=project_id
    )

    # 创建 Agent（Editor 不需要 Tools，纯审阅任务）
    agent = create_react_agent(
        model=model,
        tools=[],  # 纯审阅任务，不需要外部工具
        prompt=system_prompt,
    )

    logger.info("Editor Agent created successfully")
    return agent


# Node wrapper for LangGraph
async def editor_node(state: Dict) -> Dict:
    """
    Editor Node 包装器

    用于直接添加到 LangGraph 中作为 Node
    """
    user_id = state.get("user_id")
    project_id = state.get("project_id")
    messages = state.get("messages", [])

    # 检查前置节点是否出错
    error = state.get("error")
    if error:
        logger.error("Cannot review: previous node failed", error=error)
        return {
            "error": f"无法审阅: {error}",
            "quality_score": 0,
            "review_report": None,
            "last_successful_node": "editor_skipped",
        }

    # 检查是否有内容可以审阅
    if not messages or len(messages) < 1:
        logger.warning("No content to review", message_count=len(messages))
        # 返回一个最小化的review_report，让流程能继续
        return {
            "quality_score": 0,
            "review_report": {
                "overall_score": 0,
                "issues": [
                    {
                        "category": "system",
                        "severity": "critical",
                        "description": "没有可审阅的内容",
                    }
                ],
                "summary": "前置节点未生成内容，无法审阅",
            },
            "last_successful_node": "editor",
        }

    # 从 state 中提取完整上下文（必须包含所有元数据）
    user_config = state.get("user_config", {})
    genre_combination = user_config.get("sub_tags", ["revenge", "romance"])
    ending = user_config.get("ending_type", "HE")
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
        "Executing Editor Node",
        user_id=user_id,
        content_type=content_type,
        message_count=len(messages),
    )

    try:
        # 创建 Agent（传递完整上下文）
        agent = await create_editor_agent(
            user_id=user_id,
            project_id=project_id,
            content_type=content_type,
            genre_combination=genre_combination,
            ending=ending,
            total_episodes=total_episodes,
        )

        # 执行 Agent
        result = await agent.ainvoke({"messages": messages})

        # 解析结果
        output_messages = result.get("messages", [])

        # 从最后一个消息中提取 review_report
        review_report = None
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
                    review_report = json.loads(json_match.group(1).strip())
                    logger.info("Extracted review report", score=review_report.get("overall_score"))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse review report JSON")

        logger.info(
            "Editor Node completed",
            output_messages=len(output_messages),
            has_review_report=review_report is not None,
        )

        return {
            "messages": output_messages,
            "review_report": review_report,
            "quality_score": review_report.get("overall_score", 0) if review_report else 0,
            "last_successful_node": "editor",
        }

    except Exception as e:
        logger.error("Editor Node failed", error=str(e))
        return {
            "error": f"审阅失败: {str(e)}",
            "last_successful_node": "editor_error",
        }
