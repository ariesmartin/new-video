"""
Main Graph

LangGraph 主图定义，实现 Master Router 单一入口架构。

架构：
- 所有请求都经过 Master Router Agent 进行意图识别
- Master Router 输出 routed_agent 决定下一步
- 各 Agent 执行完成后回到 Master Router
- Module A 使用子图封装 Writer-Editor-Refiner 闭环
"""

from typing import Any, Dict, Optional
import json
import re
import structlog
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from backend.schemas.agent_state import AgentState
from backend.schemas.project import ProjectUpdate
from backend.agents import (
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
    route_after_market_analyst,
    route_after_story_planner,
    route_after_skeleton_builder,
)

logger = structlog.get_logger(__name__)

# 全局编译后的图实例
_compiled_graph = None


# ===== 辅助函数 =====


def _content_to_string(content) -> str:
    """将 LLM 返回的 content 转换为字符串。

    Gemini 模型返回多部分响应时，content 是 list 而非 str，
    直接对 list 调用 re.search / str.strip 等方法会抛出 TypeError。
    此函数统一处理 None / str / list / dict 等类型。
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(str(part["text"]))
            elif hasattr(part, "text"):
                text_parts.append(str(getattr(part, "text", "")))
        return "\n".join(text_parts)
    if isinstance(content, dict):
        if "text" in content:
            return str(content["text"])
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _extract_plan_content(story_plans_markdown: str, plan_id: str) -> str:
    """从完整的 Story Planner 输出 markdown 中提取指定方案的完整内容。

    Story Planner 输出格式示例：
      ### 方案 A: 《剧名A》
      **一句话梗概** ...
      ...
      ---
      ### 方案 B: 《剧名B》
      ...

    Args:
        story_plans_markdown: Story Planner 生成的完整 markdown 文本
        plan_id: 方案 ID（如 "A", "B", "C", "Fusion"）

    Returns:
        该方案的完整 markdown 内容（从标题到下一个方案之前）
    """
    if not story_plans_markdown or not plan_id:
        logger.warning(
            "Cannot extract plan content: missing data",
            has_markdown=bool(story_plans_markdown),
            plan_id=plan_id,
        )
        return ""

    # 将 story_plans_markdown 统一为字符串（可能是 list 类型）
    if not isinstance(story_plans_markdown, str):
        story_plans_markdown = _content_to_string(story_plans_markdown)

    # ✅ GAP-9 修复：加固 regex 匹配
    # 支持 ## 和 ### 标题、全角冒号、Fusion 特殊 ID、无冒号格式
    # 注意：f-string 中 {{ 和 }} 表示字面值 { 和 }
    plan_pattern = rf"#{{2,3}}\s*方案\s*{re.escape(plan_id)}\s*[:：]"
    match = re.search(plan_pattern, story_plans_markdown)
    if not match:
        # 备选1：不带冒号
        plan_pattern_alt = rf"#{{2,3}}\s*方案\s*{re.escape(plan_id)}\b"
        match = re.search(plan_pattern_alt, story_plans_markdown)
    if not match:
        # 备选2：融合方案特殊格式 "### 融合方案" 或 "### Fusion方案"
        if plan_id.lower() == "fusion":
            fusion_patterns = [
                r"#{2,3}\s*融合方案\s*[:：]?",
                r"#{2,3}\s*Fusion\s*方案\s*[:：]?",
                r"#{2,3}\s*方案\s*(?:融合|Fusion)\s*[:：]?",
            ]
            for fp in fusion_patterns:
                match = re.search(fp, story_plans_markdown, re.IGNORECASE)
                if match:
                    break

    if not match:
        logger.warning(
            "Plan content not found in story_plans markdown",
            plan_id=plan_id,
            markdown_length=len(story_plans_markdown),
        )
        return ""

    start = match.start()

    # 在匹配位置之后的文本中查找结束标记
    remaining = story_plans_markdown[match.end() :]
    end_patterns = [
        r"#{2,3}\s*方案\s*[A-Za-z]",  # 下一个方案标题（支持 ## 和 ###）
        r"📊\s*方案对比",  # 方案对比表
        r"```json",  # JSON 交互数据块
    ]

    end_offset = len(remaining)
    for pattern in end_patterns:
        end_match = re.search(pattern, remaining)
        if end_match and end_match.start() < end_offset:
            end_offset = end_match.start()

    # 提取内容并清理尾部分隔符
    content = story_plans_markdown[start : match.end() + end_offset]
    # 移除尾部的 --- 分隔符和空白
    content = re.sub(r"\n---\s*$", "", content.rstrip())

    logger.info(
        "✅ Extracted plan content from story_plans",
        plan_id=plan_id,
        content_length=len(content),
    )
    return content


def _get_background_info(background: str) -> dict:
    """
    获取背景设定的描述和推荐题材组合。

    注意：这只是参考信息，AI完全可以自由选择其他组合。
    """
    background_info = {
        "现代都市": {
            "description": "现代城市背景，包含职场、豪门、校园等元素",
            "recommended_combinations": [
                ["revenge", "romance"],  # 复仇+甜宠
                ["family_urban", "suspense"],  # 家庭+悬疑
                ["revenge", "family_urban"],  # 复仇+家庭
            ],
        },
        "古装仙侠": {
            "description": "古代或仙侠世界，包含宫廷、江湖、修仙等元素",
            "recommended_combinations": [
                ["transmigration", "romance"],  # 穿越+甜宠
                ["revenge", "suspense"],  # 复仇+悬疑
                ["transmigration", "revenge"],  # 穿越+复仇
            ],
        },
        "民国传奇": {
            "description": "民国时期，包含军阀、谍战、宅门等元素",
            "recommended_combinations": [
                ["suspense", "romance"],  # 悬疑+甜宠
                ["family_urban", "revenge"],  # 家庭+复仇
                ["suspense", "family_urban"],  # 悬疑+家庭
            ],
        },
        "未来科幻": {
            "description": "未来或科幻世界，包含高科技、星际、末世等元素",
            "recommended_combinations": [
                ["suspense", "revenge"],  # 悬疑+复仇
                ["transmigration", "suspense"],  # 穿越+悬疑
                ["revenge", "romance"],  # 复仇+甜宠
            ],
        },
    }
    return background_info.get(
        background,
        {
            "description": f"背景设定：{background}",
            "recommended_combinations": [
                ["revenge", "romance"],
                ["suspense", "transmigration"],
                ["family_urban", "romance"],
            ],
        },
    )


def _genre_to_slug(genre: str) -> Optional[str]:
    """
    【已弃用】不再强制映射题材到slug。
    请使用 _get_background_info() 获取背景信息。
    返回 None 表示AI可以自由选择任何题材组合。
    """
    return None  # AI 完全自由选择


# ===== Agent 包装节点 =====


async def _cold_start_node(state: AgentState) -> Dict[str, Any]:
    """
    冷启动节点 - 生成欢迎消息和 UI 交互块

    这是 LangGraph 的入口节点，确保冷启动内容被正确保存到 checkpoint。
    根据 Context7 最佳实践，所有状态变更都应该通过节点返回，让 LangGraph 自动保存。
    """
    from backend.services.chat_init_service import create_welcome_message, get_content_status
    from langchain_core.messages import AIMessage

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
            "market_report": _content_to_string(messages[-1].content) if messages else "",
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

    # 导入需要的类（在函数级别导入以避免循环依赖）
    from langchain_core.messages import AIMessage, SystemMessage
    from backend.schemas.common import (
        UIInteractionBlock,
        UIInteractionBlockType,
        ActionButton,
    )

    try:
        # 检查用户是否已选择分类（genre/setting）
        user_config = state.get("user_config", {}).copy()

        # 从 routed_parameters 获取用户选择（如果存在）
        routed_params = state.get("routed_parameters", {})

        # ✅ 从数据库加载已保存的 selected_plan（如果状态中没有）
        current_selected_plan = state.get("selected_plan")
        if not current_selected_plan and project_id:
            try:
                from backend.services.database import get_db_service

                db = get_db_service()
                saved_plan = await db.get_selected_plan(project_id)
                if saved_plan:
                    # 从 plan_data JSONB 恢复完整方案内容
                    raw_plan_data = saved_plan.get("plan_data") or {}
                    plan_data_dict: dict = {}
                    restored_content = ""

                    if isinstance(raw_plan_data, dict):
                        plan_data_dict = raw_plan_data
                        restored_content = raw_plan_data.get("content", "")
                    elif isinstance(raw_plan_data, str):
                        try:
                            parsed = json.loads(raw_plan_data)
                            if isinstance(parsed, dict):
                                plan_data_dict = parsed
                                restored_content = parsed.get("content", "")
                        except (json.JSONDecodeError, AttributeError):
                            pass

                    state["selected_plan"] = {
                        "id": saved_plan.get("plan_id") or plan_data_dict.get("plan_id", ""),
                        "title": saved_plan.get("title", ""),
                        "label": saved_plan.get("label") or plan_data_dict.get("label", ""),
                        "content": restored_content,
                    }
                    logger.info(
                        "✅ Loaded selected_plan from database", plan_id=saved_plan.get("plan_id")
                    )
            except Exception as e:
                logger.warning("Failed to load selected_plan from database", error=str(e))

        logger.info(
            "Story planner node started",
            routed_params=routed_params,
            has_action=bool(routed_params.get("action")),
            has_selected_plan=bool(state.get("selected_plan")),
        )

        # ✅ 处理 select_plan action - 用户已选择方案，直接保存并确认
        if routed_params.get("action") == "select_plan":
            plan_id = routed_params.get("plan_id", "")
            plan_label = routed_params.get("label", f"方案{plan_id}")

            logger.info(
                "✅ User selected plan",
                plan_id=plan_id,
                plan_label=plan_label,
            )

            # 从 plan_label 中提取剧名（格式：「锁定《剧名》进行细化」）
            title_match = re.search(r"《([^》]+)》", plan_label)
            plan_title = title_match.group(1) if title_match else plan_label

            # 从 story_plans 中提取方案完整内容
            story_plans_md = state.get("story_plans", "")
            plan_content = _extract_plan_content(story_plans_md, plan_id)

            if not plan_content:
                logger.warning(
                    "⚠️ Plan content extraction returned empty",
                    plan_id=plan_id,
                    story_plans_length=len(str(story_plans_md)),
                )

            # 构建 selected_plan 数据（包含完整内容）
            selected_plan = {
                "id": plan_id,
                "title": plan_title,
                "label": plan_label,
                "content": plan_content,
            }

            # 返回确认消息
            confirmation_ui = UIInteractionBlock(
                block_type=UIInteractionBlockType.ACTION_GROUP,
                title="选题已确认",
                description=f"✅ 已选择 **{plan_title}**\n\n接下来可以进行：",
                buttons=[
                    ActionButton(
                        label="📝 开始大纲拆解",
                        action="start_skeleton_building",
                        payload={"plan_id": plan_id, "plan_title": plan_title},
                        style="primary",
                        icon="FileText",
                    ),
                    ActionButton(
                        label="🔀 重新选择方案",
                        action="regenerate_plans",
                        payload={
                            "genre": user_config.get("genre"),
                            "setting": user_config.get("setting"),
                        },
                        style="secondary",
                        icon="RefreshCw",
                    ),
                ],
                dismissible=False,
            )

            # ✅ 保存 selected_plan 到数据库，确保状态持久化
            try:
                from backend.services.database import get_db_service
                import uuid

                db = get_db_service()
                # 检查是否已存在该方案
                existing = await db.get_plan(plan_id)
                # 构建 plan_data JSONB 数据（完整方案内容）
                plan_data_json = {
                    "content": plan_content,
                    "title": plan_title,
                    "label": plan_label,
                    "plan_id": plan_id,
                }

                if existing:
                    # 更新现有方案为选中状态，并写入完整内容
                    await db._client.patch(
                        f"{db._rest_url}/story_plans",
                        params={"plan_id": f"eq.{existing['plan_id']}"},
                        json={
                            "is_selected": True,
                            "plan_data": plan_data_json,
                        },
                    )
                else:
                    # 创建新方案记录，包含完整方案内容
                    await db._client.post(
                        f"{db._rest_url}/story_plans",
                        json={
                            "plan_id": plan_id,  # ✅ GAP-1 修复：添加 plan_id，使 get_plan() 可检索
                            "project_id": project_id,
                            "user_id": user_id,
                            "title": plan_title,
                            "description": plan_label,
                            "genre": user_config.get("genre"),
                            "is_selected": True,
                            "status": "active",
                            "plan_data": plan_data_json,
                        },
                    )
                logger.info(
                    "✅ Saved selected_plan to database", plan_id=plan_id, project_id=project_id
                )

                # ✅ 项目转正逻辑：如果是临时项目，则使用选题名转正
                try:
                    # 获取当前项目信息
                    project = await db.get_project(project_id)
                    logger.info(
                        "Checking project for conversion",
                        project_id=project_id,
                        project_exists=project is not None,
                        project_name=project.name if project else None,
                        is_temporary=project.is_temporary if project else None,
                    )

                    if project:
                        # 处理可能的字符串类型（Supabase 有时返回字符串）
                        is_temp = project.is_temporary
                        if isinstance(is_temp, str):
                            is_temp = is_temp.lower() == "true"

                        if is_temp:
                            # 检查项目名称是否需要更新（只有默认名称才自动更新）
                            current_name = project.name or ""
                            should_update_name = (
                                "临时项目" in current_name
                                or current_name.startswith("项目-")
                                or current_name.startswith("未命名")
                                or current_name == ""
                                or len(current_name) < 6  # 短名称可能是默认生成的
                            )

                            update_data = ProjectUpdate()
                            if should_update_name:
                                update_data.name = plan_title
                                logger.info(
                                    "Auto-updating project name from temporary to formal",
                                    old_name=current_name,
                                    new_name=plan_title,
                                    project_id=project_id,
                                )

                            # 执行转正（save_temp_project 会将 is_temporary 设为 False）
                            await db.save_temp_project(project_id, update_data)
                            logger.info(
                                "Project converted from temporary to formal",
                                project_id=project_id,
                                name_updated=should_update_name,
                                old_name=current_name,
                            )
                        else:
                            logger.info(
                                "Project is already formal, skipping conversion",
                                project_id=project_id,
                            )
                    else:
                        logger.warning(
                            "Project not found for conversion",
                            project_id=project_id,
                        )
                except Exception as e:
                    logger.error(
                        "Failed to convert temporary project to formal",
                        error=str(e),
                        project_id=project_id,
                        error_type=type(e).__name__,
                    )
                    # 不阻塞主流程，继续执行

            except Exception as e:
                # ✅ GAP-7 修复：DB 保存失败时升级为 error 级别并记录到 state
                # 之前用 logger.warning 静默吞掉，导致后续 get_plan() 返回 None
                logger.error(
                    "❌ Failed to save selected_plan to database - plan may not persist",
                    error=str(e),
                    plan_id=plan_id,
                    project_id=project_id,
                )

            return {
                "messages": [
                    AIMessage(
                        content=f"✅ **选题已确认：{plan_title}**\n\n已成功选择方案 **{plan_label}**。接下来可以开始大纲拆解和剧本创作。",
                        additional_kwargs={"ui_interaction": confirmation_ui.dict()},
                    )
                ],
                "ui_interaction": confirmation_ui,  # ✅ 更新 state 中的 ui_interaction
                "selected_plan": selected_plan,
                "user_config": user_config,
                "last_successful_node": "story_planner_plan_selected",
                "routed_parameters": {},  # ✅ 清空routed_parameters，避免传递到下一个节点
            }

        # 如果 routed_params 中有 genre，更新 user_config
        if routed_params.get("genre"):
            user_config["genre"] = routed_params["genre"]
            user_config["setting"] = routed_params.get("setting", "modern")
            logger.info(
                "✅ Updated genre/setting from routed_parameters",
                genre=user_config["genre"],
                setting=user_config["setting"],
            )

        # 如果 routed_params 中有 episode_count/episode_duration，也更新 user_config
        if routed_params.get("episode_count"):
            user_config["episode_count"] = int(routed_params["episode_count"])
            user_config["episode_duration"] = float(routed_params.get("episode_duration", 1.5))
            logger.info(
                "✅ Updated episode config from routed_parameters",
                episode_count=user_config["episode_count"],
                episode_duration=user_config["episode_duration"],
            )

        genre = user_config.get("genre")
        setting = user_config.get("setting")

        # 检查是否是随机方案请求
        if not genre and routed_params.get("action") == "random_plan":
            # 随机选择一个分类
            import random

            random_categories = [
                {"genre": "现代都市", "setting": "modern"},
                {"genre": "古装仙侠", "setting": "ancient"},
                {"genre": "民国传奇", "setting": "republic"},
                {"genre": "未来科幻", "setting": "future"},
            ]
            random_choice = random.choice(random_categories)
            user_config["genre"] = random_choice["genre"]
            user_config["setting"] = random_choice["setting"]
            genre = user_config["genre"]
            setting = user_config["setting"]
            logger.info(
                "🎲 Random plan selected",
                genre=genre,
                setting=setting,
            )

        # 如果没有选择分类，返回分类选择 UI
        if not genre:
            from backend.services.market_analysis import get_market_analysis_service

            logger.info("No genre selected, showing category selection UI")

            # 获取市场分析报告，用于推荐热门赛道
            recommended_categories = []
            market_insights = ""
            try:
                market_service = get_market_analysis_service()
                market_report = await market_service.get_latest_analysis()

                if market_report:
                    # 分析热门题材，映射到分类
                    genres = market_report.get("genres", [])
                    insights = market_report.get("insights", "")
                    market_insights = insights[:100] + "..." if len(insights) > 100 else insights

                    # 根据热门题材推荐分类
                    for g in genres[:3]:  # 取前3个热门题材
                        genre_name = g.get("name", "").lower()
                        trend = g.get("trend", "")

                        # 映射题材到分类
                        if any(
                            kw in genre_name
                            for kw in ["现代", "都市", "职场", "豪门", "复仇", "甜宠"]
                        ):
                            if "modern" not in recommended_categories:
                                recommended_categories.append("modern")
                        elif any(
                            kw in genre_name
                            for kw in ["古装", "仙侠", "宫廷", "穿越", "玄幻", "江湖"]
                        ):
                            if "ancient" not in recommended_categories:
                                recommended_categories.append("ancient")
                        elif any(kw in genre_name for kw in ["民国", "军阀", "谍战", "宅门"]):
                            if "republic" not in recommended_categories:
                                recommended_categories.append("republic")
                        elif any(
                            kw in genre_name
                            for kw in ["科幻", "未来", "末世", "赛博", "星际", "无限流"]
                        ):
                            if "future" not in recommended_categories:
                                recommended_categories.append("future")

                    logger.info(
                        "Market analysis loaded for category recommendations",
                        recommended=recommended_categories,
                        hot_genres=[g.get("name") for g in genres[:3]],
                    )
            except Exception as e:
                logger.warning("Failed to load market analysis for recommendations", error=str(e))

            # 构建分类按钮，热门推荐使用 primary 样式
            is_recommended_modern = "modern" in recommended_categories
            is_recommended_ancient = "ancient" in recommended_categories
            is_recommended_republic = "republic" in recommended_categories
            is_recommended_future = "future" in recommended_categories

            category_buttons = [
                ActionButton(
                    label=f"🏙️ 现代都市 {'🔥' if is_recommended_modern else ''}",
                    action="select_genre",
                    payload={"genre": "现代都市", "setting": "modern"},
                    style="primary" if is_recommended_modern else "secondary",
                    icon="Building",
                ),
                ActionButton(
                    label=f"👘 古装仙侠 {'🔥' if is_recommended_ancient else ''}",
                    action="select_genre",
                    payload={"genre": "古装仙侠", "setting": "ancient"},
                    style="primary" if is_recommended_ancient else "secondary",
                    icon="Crown",
                ),
                ActionButton(
                    label=f"🎩 民国传奇 {'🔥' if is_recommended_republic else ''}",
                    action="select_genre",
                    payload={"genre": "民国传奇", "setting": "republic"},
                    style="primary" if is_recommended_republic else "secondary",
                    icon="History",
                ),
                ActionButton(
                    label=f"🤖 未来科幻 {'🔥' if is_recommended_future else ''}",
                    action="select_genre",
                    payload={"genre": "未来科幻", "setting": "future"},
                    style="primary" if is_recommended_future else "secondary",
                    icon="Rocket",
                ),
                ActionButton(
                    label="🎲 AI 随机方案",
                    action="random_plan",
                    payload={},
                    style="ghost",
                    icon="Shuffle",
                ),
            ]

            # 构建描述文本，包含市场洞察
            description = "请选择您想创作的故事背景："
            if recommended_categories and market_insights:
                description = (
                    f"📊 **市场趋势**：{market_insights}\n\n🔥 标记为当前热门推荐，请选择故事背景："
                )

            category_ui = UIInteractionBlock(
                block_type=UIInteractionBlockType.ACTION_GROUP,
                title="选择故事背景",
                description=description,
                buttons=category_buttons,
                dismissible=False,
            )

            return {
                "messages": [
                    AIMessage(
                        content="🎬 **开始创作**：请选择故事背景",
                        additional_kwargs={"ui_interaction": category_ui.dict()},
                    )
                ],
                "ui_interaction": category_ui,
                "user_config": user_config,
                "last_successful_node": "story_planner_select_category",
            }

        # 已选择分类，获取剧集配置
        episode_count = user_config.get("episode_count")
        episode_duration = user_config.get("episode_duration")

        # 检查是否是自定义配置请求（优先处理）
        if routed_params.get("action") == "custom_episode_config":
            # 显示自定义配置表单
            logger.info("Showing custom episode config form", genre=genre)

            custom_config_ui = UIInteractionBlock(
                block_type=UIInteractionBlockType.FORM,
                title="自定义剧集配置",
                description=f"已选择题材：**{genre}**\n\n请设置剧集参数：",
                form_fields=[
                    {
                        "id": "episode_count",
                        "label": "总集数",
                        "type": "number",
                        "min": 20,
                        "max": 120,
                        "default": 80,
                        "placeholder": "建议 40-100 集",
                    },
                    {
                        "id": "episode_duration",
                        "label": "每集时长（分钟）",
                        "type": "select",
                        "options": [
                            {"value": 1, "label": "1 分钟"},
                            {"value": 1.5, "label": "1.5 分钟"},
                            {"value": 2, "label": "2 分钟"},
                            {"value": 2.5, "label": "2.5 分钟"},
                            {"value": 3, "label": "3 分钟"},
                            {"value": 4, "label": "4 分钟"},
                            {"value": 5, "label": "5 分钟"},
                        ],
                        "default": 1.5,
                    },
                ],
                buttons=[
                    ActionButton(
                        label="✅ 确认配置",
                        action="set_episode_config",
                        payload={"genre": genre, "setting": setting},
                        style="primary",
                        icon="Check",
                    ),
                    ActionButton(
                        label="🔙 返回预设",
                        action="select_genre",
                        payload={"genre": genre, "setting": setting},
                        style="ghost",
                        icon="ArrowLeft",
                    ),
                ],
                dismissible=False,
            )

            return {
                "messages": [
                    AIMessage(
                        content=f"⚙️ **自定义配置**\n\n已选择题材：**{genre}**\n\n请设置剧集参数：",
                        additional_kwargs={"ui_interaction": custom_config_ui.dict()},
                    )
                ],
                "ui_interaction": custom_config_ui,
                "user_config": user_config,
                "last_successful_node": "story_planner_custom_config",
            }

        # 检查是否已配置集数和时长
        if not episode_count or not episode_duration:
            # 未配置，显示配置 UI
            logger.info("Genre selected but no episode config, showing config UI", genre=genre)

            config_ui = UIInteractionBlock(
                block_type=UIInteractionBlockType.ACTION_GROUP,
                title="配置剧集信息",
                description=f"已选择题材：**{genre}**\n\n请配置剧集的基本信息，这将影响方案的 pacing 和付费卡点设计：",
                buttons=[
                    ActionButton(
                        label="📱 抖音/快手短剧（80-100集，每集1-2分钟）",
                        action="set_episode_config",
                        payload={
                            "episode_count": 80,
                            "episode_duration": 1.5,
                            "genre": genre,
                            "setting": setting,
                        },
                        style="primary",
                        icon="Smartphone",
                    ),
                    ActionButton(
                        label="📺 小程序短剧（60-80集，每集2-3分钟）",
                        action="set_episode_config",
                        payload={
                            "episode_count": 60,
                            "episode_duration": 2.5,
                            "genre": genre,
                            "setting": setting,
                        },
                        style="primary",
                        icon="Tablet",
                    ),
                    ActionButton(
                        label="🎬 精品短剧（40-60集，每集3-5分钟）",
                        action="set_episode_config",
                        payload={
                            "episode_count": 40,
                            "episode_duration": 4,
                            "genre": genre,
                            "setting": setting,
                        },
                        style="secondary",
                        icon="Monitor",
                    ),
                    ActionButton(
                        label="⚙️ 自定义配置",
                        action="custom_episode_config",
                        payload={"genre": genre, "setting": setting},
                        style="ghost",
                        icon="Settings",
                    ),
                ],
                dismissible=False,
            )

            return {
                "messages": [
                    AIMessage(
                        content=f"🎬 **开始创作**\n\n已选择题材：**{genre}**\n\n请配置剧集信息：",
                        additional_kwargs={"ui_interaction": config_ui.dict()},
                    )
                ],
                "ui_interaction": config_ui,
                "user_config": user_config,
                "last_successful_node": "story_planner_config_episode",
            }

        # 已选择分类且已配置集数/时长，创建 Agent 生成故事方案
        logger.info(
            "Generating story plans",
            genre=genre,
            episode_count=episode_count,
            episode_duration=episode_duration,
        )

        # 检测是否是重新生成请求（用于调整发散性）
        is_regenerate = routed_params.get("action") == "regenerate_plans"

        # 将配置信息传递给 Prompt
        config_context = f"""## 剧集配置信息
- **总集数**: {episode_count} 集
- **每集时长**: {episode_duration} 分钟
- **题材**: {genre}
- **背景设定**: {setting}

基于以上配置生成方案，付费卡点必须根据总集数调整位置。
"""

        # ✅ 如果是重新生成，添加发散性提示
        if is_regenerate:
            config_context += """

## 🌡️ 发散性创作模式（重新生成）
**本次为重新生成请求，请使用更高的发散性和创意：**
- 大胆尝试不常见的题材组合
- 跳出常规思维，创造意想不到的剧情转折
- 每个方案都要与前次有明显差异
- 可以使用更激进、更有张力的设定
- 避免保守，勇于创新！
"""
            logger.info(
                "Applied high divergence mode for regenerate_plans",
                genre=genre,
                user_id=user_id,
            )

        # 在 messages 中添加上下文
        from langchain_core.messages import BaseMessage, HumanMessage

        messages: list[BaseMessage] = state.get("messages", [])

        # ✅ 修复：如果是重新生成，清理之前的方案生成消息，避免影响新内容
        if is_regenerate:
            # 只保留用户的消息（HumanMessage），清理AI的方案生成消息
            messages = [m for m in messages if isinstance(m, HumanMessage)]
            logger.info(
                "🔄 Regenerate: cleared previous AI messages", remaining_messages=len(messages)
            )

        messages.append(SystemMessage(content=config_context))
        state["messages"] = messages

        agent = await create_story_planner_agent(
            user_id=user_id,
            project_id=project_id,
            episode_count=episode_count,
            episode_duration=episode_duration,
            genre=genre,
            setting=setting,
        )

        # 执行 Agent
        result = await agent.ainvoke({"messages": state.get("messages", [])})

        # 更新状态
        messages = result.get("messages", [])

        # 从 Agent 输出中提取 JSON UI 数据并解析
        ui_interaction = None
        if messages:
            last_message = messages[-1]
            raw_content = (
                last_message.content if hasattr(last_message, "content") else str(last_message)
            )
            # ✅ 修复：Gemini 返回 list 类型 content，统一转为 str
            content = _content_to_string(raw_content)

            # 查找 ```json ... ``` 代码块
            json_match = re.search(r"```json\s*\n?([\s\S]*?)\n?```", content)

            if json_match:
                try:
                    json_str = json_match.group(1).strip()
                    ui_data = json.loads(json_str)

                    # 验证是否包含预期的 UI 字段
                    if "options" in ui_data:
                        buttons = []

                        # 处理 options（主要方案按钮）
                        for opt in ui_data.get("options", []):
                            plan_id = opt.get("id", "")
                            label = opt.get("label", f"选择方案{plan_id}")
                            tagline = opt.get("tagline", "")

                            # ✅ 按钮直接显示方案题目（如"锁定《万劫不复》进行细化"）
                            # payload 中包含 label 和 tagline，供后续使用
                            buttons.append(
                                ActionButton(
                                    label=label,
                                    action="select_plan",
                                    payload={
                                        "plan_id": plan_id,
                                        "label": label,
                                        "tagline": tagline,
                                    },
                                    style="primary",
                                )
                            )

                        # 处理 secondary_actions（次要操作，如重新生成）
                        for action in ui_data.get("secondary_actions", []):
                            action_type = action.get("action", "")
                            # 为 regenerate_plans 操作包含当前配置，确保重新生成时不会丢失 genre
                            if action_type == "regenerate_plans":
                                import random
                                import time

                                # ✅ 定义所有可能的跨题材组合（黄金组合 + 创新组合）
                                fusion_combinations = [
                                    # 黄金组合（市场验证）
                                    ["revenge", "romance"],  # 复仇甜宠
                                    ["suspense", "romance"],  # 悬疑甜宠
                                    ["transmigration", "suspense"],  # 穿越探案
                                    ["family_urban", "romance"],  # 治愈甜宠
                                    ["revenge", "suspense"],  # 复仇悬疑
                                    # 创新组合（新颖搭配）
                                    ["transmigration", "revenge"],  # 穿越复仇
                                    ["revenge", "family_urban"],  # 复仇家庭
                                    ["suspense", "family_urban"],  # 悬疑家庭
                                    ["transmigration", "romance"],  # 穿越甜宠
                                    ["revenge", "transmigration"],  # 复仇穿越
                                ]

                                # 根据背景设定过滤不适用的组合
                                background = genre if genre else "现代都市"
                                filtered_combinations = fusion_combinations.copy()

                                # 根据背景排除违和的组合
                                if "现代" in background or "都市" in background:
                                    # 现代背景不适合穿越题材
                                    filtered_combinations = [
                                        c
                                        for c in filtered_combinations
                                        if "transmigration" not in c
                                    ]
                                elif "科幻" in background or "未来" in background:
                                    # 科幻背景不适合家庭伦理
                                    filtered_combinations = [
                                        c for c in filtered_combinations if "family_urban" not in c
                                    ]

                                # 随机选择 3 个不同的组合方案
                                if len(filtered_combinations) >= 3:
                                    selected_combinations = random.sample(
                                        filtered_combinations, k=3
                                    )
                                else:
                                    selected_combinations = filtered_combinations

                                # 构建组合提示
                                combo_hints = []
                                theme_names = {
                                    "revenge": "复仇逆袭",
                                    "romance": "甜宠恋爱",
                                    "suspense": "悬疑推理",
                                    "transmigration": "穿越重生",
                                    "family_urban": "家庭伦理",
                                }
                                for i, combo in enumerate(selected_combinations, 1):
                                    combo_name = "+".join([theme_names.get(t, t) for t in combo])
                                    combo_hints.append(f"方案{i}：{combo_name}")

                                payload = {
                                    "genre": genre,
                                    "setting": setting,
                                    "episode_count": episode_count,
                                    "episode_duration": episode_duration,
                                    # ✅ 添加随机化参数，确保每次重新生成都有不同的结果
                                    "variation_seed": random.randint(1, 10000),
                                    "timestamp": int(time.time()),
                                    "is_regenerate": True,
                                    # ✅ 强制跨主题组合 - 提供3种不同的组合方案
                                    "fusion_combinations": selected_combinations,
                                    "cross_theme_hint": f"本次重新生成必须使用跨题材融合。推荐的组合方案：{' | '.join(combo_hints)}",
                                    "regenerate_instruction": "重要：这次生成的3个方案必须分别使用上面列出的3种不同题材组合，不允许单一题材方案。",
                                }
                            else:
                                payload = {}

                            buttons.append(
                                ActionButton(
                                    label=action.get("label", ""),
                                    action=action_type,
                                    payload=payload,
                                    style=action.get("style", "secondary"),
                                )
                            )

                        # 创建 UIInteractionBlock
                        ui_interaction = UIInteractionBlock(
                            block_type=UIInteractionBlockType.ACTION_GROUP,
                            title="选择故事方案",
                            description=ui_data.get("hint", "请选择一个方案继续创作："),
                            buttons=buttons,
                            dismissible=False,
                        )

                        # 清理消息内容：移除 JSON 代码块
                        clean_content = content[: json_match.start()].rstrip()

                        # 如果清理后的内容为空（AI可能格式不对），保留原始内容
                        if not clean_content:
                            # 移除 JSON 代码块但保留其他内容
                            clean_content = content.replace(json_match.group(0), "").strip()
                            logger.warning(
                                "Agent output format issue: content before JSON is empty, using cleaned full content"
                            )

                        # 更新消息
                        if isinstance(last_message, AIMessage):
                            messages[-1] = AIMessage(
                                content=clean_content,
                                additional_kwargs={
                                    **(
                                        last_message.additional_kwargs
                                        if hasattr(last_message, "additional_kwargs")
                                        else {}
                                    ),
                                    "ui_interaction": ui_interaction,
                                },
                            )

                        logger.info(
                            "Parsed Agent UI JSON",
                            options_count=len(ui_data.get("options", [])),
                            secondary_actions_count=len(ui_data.get("secondary_actions", [])),
                        )

                except Exception as parse_error:
                    logger.warning("Failed to parse Agent UI JSON", error=str(parse_error))

        # 确保 user_config 包含 episode_count 和 episode_duration，以便正确保存到 checkpoint
        user_config["episode_count"] = episode_count
        user_config["episode_duration"] = episode_duration
        user_config["genre"] = genre
        user_config["setting"] = setting

        return {
            "messages": messages,
            "story_plans": _content_to_string(messages[-1].content) if messages else "",
            "ui_interaction": ui_interaction,
            "user_config": user_config,
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
            "script": _content_to_string(messages[-1].content) if messages else "",
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
            "storyboard": _content_to_string(messages[-1].content) if messages else "",
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
            "generated_images": _content_to_string(messages[-1].content) if messages else "",
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

    # Level 3: 骨架构建（大纲生成 + 审阅修复闭环）
    # Skeleton Builder Graph 作为子图集成，包含完整的 5-Node 工作流：
    # validate → skeleton_builder → editor → refiner → END
    from backend.graph.workflows.skeleton_builder_graph import build_skeleton_builder_graph

    skeleton_builder_graph = build_skeleton_builder_graph(checkpointer=checkpointer)
    graph.add_node("skeleton_builder", skeleton_builder_graph)

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

    # ✅ GAP-3 修复：SDUI Action Router Node（从 route_from_start 路由函数中拆出状态突变逻辑）
    # LangGraph 规范：路由函数（conditional edge）必须是纯函数，不得修改 state
    # 状态变更必须在 Node 中通过返回值完成
    _SDUI_ACTION_MAP = {
        "start_creation": "story_planner",
        "adapt_script": "script_adapter",
        "create_storyboard": "storyboard_director",
        "inspect_assets": "asset_inspector",
        "random_plan": "story_planner",
        "select_genre": "story_planner",
        "select_plan": "story_planner",
        "start_custom": "story_planner",
        "proceed_to_planning": "story_planner",
        "reset_genre": "story_planner",
        "start_skeleton_building": "skeleton_builder",
        "confirm_skeleton": "skeleton_builder",
        "regenerate_skeleton": "skeleton_builder",
        "continue_skeleton_generation": "skeleton_builder",  # 断点续传：继续下一批生成
    }

    def _detect_sdui_action(state: AgentState) -> dict | None:
        """从消息中检测 SDUI action 数据（纯函数，不修改 state）"""
        messages = state.get("messages", [])
        last_successful_node = state.get("last_successful_node", "")
        already_processed = last_successful_node in [
            "story_planner_plan_selected",
            "skeleton_builder_completed",
        ]
        if not messages or already_processed:
            return None

        for msg in reversed(messages):
            content = _content_to_string(msg.content if hasattr(msg, "content") else str(msg))
            if content.strip().startswith("{") and '"action"' in content:
                try:
                    data = json.loads(content)
                    if data.get("action") and data["action"] in _SDUI_ACTION_MAP:
                        return data
                except Exception:
                    continue
        return None

    async def _sdui_action_router_node(state: AgentState) -> dict:
        """SDUI Action Router Node - 解析用户按钮动作并设置路由状态

        此 Node 将 SDUI action 转化为 routed_agent/routed_parameters，
        供 master_router 直接路由到目标 Agent。
        """
        action_data = _detect_sdui_action(state)
        if not action_data:
            # 防御性兜底：不应到达这里（route_from_start 已过滤）
            logger.warning("sdui_action_router_node called but no action detected")
            return {}

        action = action_data.get("action", "")
        target_agent = _SDUI_ACTION_MAP.get(action, "")
        logger.info(
            "SDUI action router: setting state for master_router",
            action=action,
            target_agent=target_agent,
        )
        return {
            "routed_agent": target_agent,
            "routed_parameters": action_data,
            "ui_feedback": f"正在为您启动{target_agent.replace('_', ' ')}...",
            "intent_analysis": f"SDUI action: {action}",
        }

    graph.add_node("sdui_action_router", _sdui_action_router_node)

    # 入口：根据是否冷启动选择路径
    def route_from_start(state: AgentState):
        """入口路由 - 纯函数，只返回路由名称，不修改 state"""
        messages = state.get("messages", [])
        is_cold_start = state.get("is_cold_start", False)

        if is_cold_start or not messages:
            logger.info("Routing to cold_start node")
            return "cold_start"

        # 检测 SDUI Action → 走 sdui_action_router Node（由 Node 负责设置 state）
        if _detect_sdui_action(state):
            logger.info("SDUI action detected, routing to sdui_action_router node")
            return "sdui_action_router"

        # 否则走正常流程
        logger.info("Routing to master_router")
        return "master_router"

    graph.add_conditional_edges(
        START,
        route_from_start,
        {
            "cold_start": "cold_start",
            "sdui_action_router": "sdui_action_router",
            "master_router": "master_router",
        },
    )

    # sdui_action_router → master_router（状态已设置，直接进入路由）
    graph.add_edge("sdui_action_router", "master_router")

    # 冷启动节点直接结束（内容已保存到 checkpoint）
    graph.add_edge("cold_start", END)

    # Master Router -> 各 Agent（条件路由）
    graph.add_conditional_edges(
        "master_router",
        route_after_master,
        {
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            "skeleton_builder": "skeleton_builder",  # V3.0: 骨架构建
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

    # Market Analyst -> Story Planner / Wait
    graph.add_conditional_edges(
        "market_analyst",
        route_after_market_analyst,
        {
            "story_planner": "story_planner",
            "wait_for_input": "wait_for_input",
        },
    )

    # Story Planner -> Skeleton Builder / Wait (关键修复：使用特定的路由函数)
    graph.add_conditional_edges(
        "story_planner",
        route_after_story_planner,
        {
            "skeleton_builder": "skeleton_builder",
            "wait_for_input": "wait_for_input",
        },
    )

    # Skeleton Builder -> END / Wait (module_a not yet implemented)
    graph.add_conditional_edges(
        "skeleton_builder",
        route_after_skeleton_builder,
        {
            "module_a": END,  # Route to END for now until module_a is implemented
            "wait_for_input": "wait_for_input",
        },
    )

    # 其他 Agent 使用通用路由
    for node in [
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
