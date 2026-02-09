"""
Skeleton Builder Graph - 大纲构建工作流

流程：
START → validate_input → [conditional] →
  ├─ [complete] → skeleton_builder → quality_control (子图) → END
  └─ [incomplete] → request_ending → END

注意：质量控制使用独立的 quality_control_graph 子图
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from backend.schemas.agent_state import AgentState, ApprovalStatus, StageType
from backend.agents.skeleton_builder import skeleton_builder_node
from backend.graph.workflows.quality_control_graph import (
    build_quality_control_graph,
    QualityControlState,
)

import structlog

logger = structlog.get_logger(__name__)


# ===== 章节映射计算函数 =====


def parse_paywall_range(range_str: str) -> List[int]:
    """
    解析付费卡点范围字符串

    Args:
        range_str: "10-12" 或 "12"

    Returns:
        [10, 11, 12] 或 [12]
    """
    if not range_str:
        return [12]  # 默认值

    try:
        if "-" in str(range_str):
            parts = str(range_str).split("-")
            start = int(parts[0])
            end = int(parts[1])
            return list(range(start, end + 1))
        else:
            return [int(range_str)]
    except (ValueError, IndexError):
        logger.warning(f"Invalid paywall range format: {range_str}, using default")
        return [12]


def calculate_chapter_mapping(total_episodes: int, paywall_episodes: List[int]) -> Dict[str, Any]:
    """
    计算章节到短剧的映射

    映射规则：
    - 开篇阶段（0-15%集数）: 1章 = 1-1.5集，字数8-9k
    - 发展阶段（15-75%）: 1章 = 2集，字数10k
    - 付费卡点章节: 1章 = 3集，字数12k（覆盖所有付费集数）
    - 高潮阶段（75-90%）: 1章 = 1集，字数8k
    - 结局阶段（90-100%）: 1章 = 1-2集，字数8-10k

    Args:
        total_episodes: 短剧总集数
        paywall_episodes: 付费卡点集数列表（如[10, 11, 12]）

    Returns:
        {
            "total_chapters": 61,
            "paywall_chapter": 12,
            "estimated_words": 800000,
            "chapters": [...],
            "adaptation_ratio": 1.31
        }
    """
    chapters = []
    current_ep = 1
    paywall_first = paywall_episodes[0] if paywall_episodes else 12
    paywall_last = paywall_episodes[-1] if paywall_episodes else 12

    # 计算总字数（1分钟 ≈ 4000字，假设每集2分钟）
    total_minutes = total_episodes * 2
    estimated_words = total_minutes * 4000

    logger.info(
        "Calculating chapter mapping",
        total_episodes=total_episodes,
        paywall_first=paywall_first,
        paywall_last=paywall_last,
        estimated_words=estimated_words,
    )

    # 1. 开篇阶段（前15%集数）
    opening_eps = max(3, int(total_episodes * 0.15))
    for i in range(opening_eps):
        # 前3章每章1.5集，之后每章1集
        if i < 3:
            eps = 1.5
            word_count = 9000
        else:
            eps = 1.0
            word_count = 8000

        end_ep = min(int(current_ep + eps - 1), total_episodes)
        chapters.append(
            {
                "chapter_num": len(chapters) + 1,
                "episode_start": int(current_ep),
                "episode_end": end_ep,
                "word_count": word_count,
                "stage": "opening",
                "is_paywall": False,
            }
        )
        current_ep += eps

    # 2. 发展阶段（到付费卡点前）
    while current_ep < paywall_first - 2:
        chapters.append(
            {
                "chapter_num": len(chapters) + 1,
                "episode_start": int(current_ep),
                "episode_end": min(int(current_ep + 1), total_episodes),
                "word_count": 10000,
                "stage": "development",
                "is_paywall": False,
            }
        )
        current_ep += 2

    # 3. 付费卡点章节（覆盖所有付费集数）
    paywall_chapter_idx = len(chapters) + 1
    chapters.append(
        {
            "chapter_num": paywall_chapter_idx,
            "episode_start": int(current_ep),
            "episode_end": paywall_last,
            "word_count": 12000,  # 付费卡点章节加长
            "stage": "paywall",
            "is_paywall": True,
            "paywall_position": "70-80%",  # 卡点在本章的位置
        }
    )
    current_ep = paywall_last + 1

    # 4. 发展阶段（付费卡点后到75%）
    dev_end = int(total_episodes * 0.75)
    while current_ep < dev_end:
        chapters.append(
            {
                "chapter_num": len(chapters) + 1,
                "episode_start": int(current_ep),
                "episode_end": min(int(current_ep + 1), total_episodes),
                "word_count": 10000,
                "stage": "development",
                "is_paywall": False,
            }
        )
        current_ep += 2

    # 5. 高潮阶段（75-90%）
    climax_end = int(total_episodes * 0.90)
    while current_ep < climax_end:
        chapters.append(
            {
                "chapter_num": len(chapters) + 1,
                "episode_start": int(current_ep),
                "episode_end": int(current_ep),
                "word_count": 8000,
                "stage": "climax",
                "is_paywall": False,
            }
        )
        current_ep += 1

    # 6. 结局阶段（90-100%）
    while current_ep <= total_episodes:
        remaining = total_episodes - current_ep + 1
        eps = min(remaining, 2)
        chapters.append(
            {
                "chapter_num": len(chapters) + 1,
                "episode_start": int(current_ep),
                "episode_end": min(int(current_ep + eps - 1), total_episodes),
                "word_count": 8000 if eps == 1 else 10000,
                "stage": "ending",
                "is_paywall": False,
            }
        )
        current_ep += eps

    result = {
        "total_chapters": len(chapters),
        "paywall_chapter": paywall_chapter_idx,
        "estimated_words": estimated_words,
        "chapters": chapters,
        "adaptation_ratio": round(total_episodes / len(chapters), 2) if chapters else 0,
        "key_points": {
            "opening_end": max(3, int(len(chapters) * 0.05)),
            "development_start": max(3, int(len(chapters) * 0.05)) + 1,
            "development_end": int(len(chapters) * 0.75),
            "midpoint_chapter": int(len(chapters) * 0.50),
            "climax_chapter": int(len(chapters) * 0.875),
            "paywall_chapter": paywall_chapter_idx,
        },
    }

    logger.info(
        "Chapter mapping calculated",
        total_chapters=result["total_chapters"],
        paywall_chapter=result["paywall_chapter"],
        adaptation_ratio=result["adaptation_ratio"],
    )

    return result


# ===== 普通函数 Nodes =====


async def quality_control_node(state: AgentState) -> Dict[str, Any]:
    """
    质量控制 Node

    调用独立的 quality_control_graph 子图进行审阅和修复
    支持 full_cycle 模式：审阅 → 修复 → 审阅循环
    """
    user_id = state.get("user_id")
    project_id = state.get("project_id")
    skeleton_content = state.get("skeleton_content", "")
    revision_count = state.get("revision_count", 0)

    logger.info(
        "Executing Quality Control Node",
        user_id=user_id,
        content_length=len(skeleton_content),
        revision_count=revision_count,
    )

    if not skeleton_content:
        logger.error("No skeleton content to review")
        return {
            "error": "没有可审阅的大纲内容",
            "quality_score": 0,
            "review_report": None,
            "last_successful_node": "quality_control_error",
        }

    try:
        # 构建 quality_control_graph 子图
        qc_graph = build_quality_control_graph()

        # 创建子图状态
        qc_state = QualityControlState(
            mode="full_cycle",
            user_id=user_id,
            project_id=project_id,
            input_content=skeleton_content,
            target_score=80,
            max_iterations=3 - revision_count,  # 考虑已进行的迭代次数
            iterations_performed=revision_count,
            user_config=state.get("user_config", {}),
        )

        # 执行子图
        result = await qc_graph.ainvoke(qc_state.__dict__)

        # 提取结果
        review_report = result.get("review_report")
        refined_content = result.get("refined_content")
        final_score = result.get("final_score", 0)
        iterations = result.get("iterations_performed", 0)

        logger.info(
            "Quality Control completed",
            final_score=final_score,
            iterations=iterations,
            has_refined_content=bool(refined_content),
        )

        return {
            "review_report": review_report,
            "quality_score": final_score,
            "refined_content": refined_content,
            "revision_count": revision_count + iterations,
            "last_successful_node": "quality_control",
        }

    except Exception as e:
        logger.error("Quality Control failed", error=str(e))
        return {
            "error": f"质量控制失败: {str(e)}",
            "quality_score": 0,
            "review_report": None,
            "last_successful_node": "quality_control_error",
        }


async def validate_input_node(state: AgentState) -> Dict[str, Any]:
    """
    输入验证 Node - 增强版

    检查必要的输入字段，并自动计算章节映射
    """
    user_config = state.get("user_config", {})
    selected_plan = state.get("selected_plan", {})

    logger.info(
        "Validating input",
        has_user_config=bool(user_config),
        has_selected_plan=bool(selected_plan),
    )

    # 检查必要的字段
    missing_fields = []

    if not selected_plan:
        missing_fields.append("selected_plan")

    if not user_config.get("ending_type"):
        missing_fields.append("ending_type")

    if missing_fields:
        logger.warning(
            "Input validation failed",
            missing_fields=missing_fields,
        )
        return {
            "validation_status": "incomplete",
            "missing_fields": missing_fields,
            "last_successful_node": "validate_input",
        }

    # ===== 新增：计算章节映射 =====
    total_episodes = user_config.get("total_episodes", 80)
    episode_duration = user_config.get("episode_duration", 2)

    # 获取付费卡点信息
    paywall_design = selected_plan.get("paywall_design", {})
    paywall_range = paywall_design.get("episode_range", "10-12")
    paywall_episodes = parse_paywall_range(paywall_range)

    # 计算章节映射
    chapter_mapping = calculate_chapter_mapping(total_episodes, paywall_episodes)

    # 构建推断配置
    inferred_config = {
        "total_episodes": total_episodes,
        "episode_duration": episode_duration,
        "total_drama_minutes": total_episodes * episode_duration,
        "total_chapters": chapter_mapping["total_chapters"],
        "paywall_chapter": chapter_mapping["paywall_chapter"],
        "paywall_episodes": paywall_episodes,
        "estimated_words": chapter_mapping["estimated_words"],
        "chapter_map": chapter_mapping["chapters"],
        "adaptation_ratio": chapter_mapping["adaptation_ratio"],
        **chapter_mapping["key_points"],  # 展开关键节点
    }

    logger.info(
        "Input validation passed with chapter mapping",
        total_episodes=total_episodes,
        total_chapters=inferred_config["total_chapters"],
        paywall_chapter=inferred_config["paywall_chapter"],
        estimated_words=inferred_config["estimated_words"],
    )

    return {
        "validation_status": "complete",
        "inferred_config": inferred_config,
        "chapter_mapping": chapter_mapping,  # 供后续节点使用
        "current_stage": StageType.LEVEL_3,
        "last_successful_node": "validate_input",
    }


async def request_ending_node(state: AgentState) -> Dict[str, Any]:
    """
    请求 Ending Node

    当缺少 ending 时，返回 UI 询问用户
    """
    from backend.schemas.common import (
        UIInteractionBlock,
        UIInteractionBlockType,
        ActionButton,
    )
    from langchain_core.messages import AIMessage

    logger.info("Requesting ending from user")

    # 创建 UI 交互块
    ending_ui = UIInteractionBlock(
        block_type=UIInteractionBlockType.ACTION_GROUP,
        title="选择结局类型",
        description="请为故事选择一个结局类型：",
        buttons=[
            ActionButton(
                label="💕 圆满结局 (HE)",
                action="select_ending",
                payload={"ending": "HE"},
                style="primary",
                icon="Heart",
            ),
            ActionButton(
                label="💔 悲剧结局 (BE)",
                action="select_ending",
                payload={"ending": "BE"},
                style="secondary",
                icon="HeartCrack",
            ),
            ActionButton(
                label="🌅 开放式结局 (OE)",
                action="select_ending",
                payload={"ending": "OE"},
                style="ghost",
                icon="Sunrise",
            ),
        ],
        dismissible=False,
    )

    message = AIMessage(
        content="请为故事选择一个结局类型。这将影响大纲的走向和节奏设计。",
        additional_kwargs={"ui_interaction": ending_ui.dict()},
    )

    return {
        "messages": [message],
        "ui_interaction": ending_ui,
        "last_successful_node": "request_ending",
    }


# ===== 路由函数 =====


def route_after_validation(state: AgentState) -> str:
    """
    验证后的路由决策

    根据 validation_status 决定下一步
    """
    validation_status = state.get("validation_status", "incomplete")

    logger.info(
        "Route after validation",
        validation_status=validation_status,
        state_keys=list(state.keys()),
    )

    if validation_status == "complete":
        logger.info("Routing to skeleton_builder")
        return "complete"
    else:
        logger.info("Routing to request_ending")
        return "incomplete"


# ===== 输出验证 Node =====


async def validate_output_node(state: AgentState) -> Dict[str, Any]:
    """
    输出验证 Node

    验证生成的章节大纲是否完整，检查：
    1. 章节数量是否达标
    2. 是否包含付费卡点章节
    3. JSON是否完整
    4. 关键字段是否存在
    """
    import json
    import re

    skeleton_content = state.get("skeleton_content", "")
    chapter_mapping = state.get("chapter_mapping", {})
    total_chapters_expected = chapter_mapping.get("total_chapters", 60)

    logger.info(
        "Validating output",
        content_length=len(skeleton_content),
        expected_chapters=total_chapters_expected,
    )

    issues = []

    # 检查1：章节数量
    chapter_count = len(re.findall(r"### Chapter \d+:", skeleton_content))
    if chapter_count < total_chapters_expected * 0.7:  # 允许30%容错
        issues.append(f"章节不完整: 期望{total_chapters_expected}章，实际约{chapter_count}章")

    # 检查2：付费卡点章节
    has_paywall = "⚠️ 付费卡点章节" in skeleton_content or "付费卡点" in skeleton_content
    if not has_paywall:
        issues.append("缺少付费卡点专项设计")

    # 检查3：UI JSON
    has_ui_json = '"ui_mode"' in skeleton_content and '"novel_skeleton_editor"' in skeleton_content
    if not has_ui_json:
        issues.append("缺少UI交互数据")

    # 检查4：关键字段
    required_sections = ["元数据", "核心设定", "人物体系", "情节架构", "章节大纲"]
    missing_sections = []
    for section in required_sections:
        if section not in skeleton_content:
            missing_sections.append(section)
    if missing_sections:
        issues.append(f"缺少关键部分: {', '.join(missing_sections)}")

    # 检查5：JSON完整性
    json_complete = True
    json_matches = re.findall(r"```json\s*([\s\S]*?)\s*```", skeleton_content)
    for json_str in json_matches:
        try:
            json.loads(json_str)
        except json.JSONDecodeError:
            json_complete = False
            issues.append("JSON格式不完整")
            break

    if issues:
        logger.warning("Output validation failed", issues=issues)
        return {
            "validation_status": "incomplete",
            "validation_issues": issues,
            "chapter_count": chapter_count,
            "needs_retry": True,
            "last_successful_node": "validate_output",
        }

    logger.info("Output validation passed", chapter_count=chapter_count)
    return {
        "validation_status": "complete",
        "chapter_count": chapter_count,
        "last_successful_node": "validate_output",
    }


# ===== 分批生成协调 Node =====


async def batch_coordinator_node(state: AgentState) -> Dict[str, Any]:
    """
    分批生成协调 Node

    根据章节数决定是否分批生成，以及分批策略
    """
    chapter_mapping = state.get("chapter_mapping", {})
    total_chapters = chapter_mapping.get("total_chapters", 60)

    logger.info(
        "Coordinating batch generation",
        total_chapters=total_chapters,
    )

    # 分批策略
    if total_chapters <= 30:
        # 30章以内，一次性生成
        batches = [{"range": (1, total_chapters), "type": "full", "description": "完整大纲"}]
    elif total_chapters <= 50:
        # 50章以内，分2批
        mid = total_chapters // 2
        batches = [
            {"range": (1, mid), "type": "opening", "description": f"第1-{mid}章（开篇+发展）"},
            {
                "range": (mid + 1, total_chapters),
                "type": "ending",
                "description": f"第{mid + 1}-{total_chapters}章（高潮+结局）",
            },
        ]
    else:
        # 50章以上，分4批
        q1 = total_chapters // 4
        q2 = total_chapters // 2
        q3 = total_chapters * 3 // 4

        # 找到付费卡点章节，确保它在某一批中
        paywall_chapter = chapter_mapping.get("paywall_chapter", q2)

        batches = [
            {
                "range": (1, min(q1, paywall_chapter - 1)),
                "type": "opening",
                "description": f"第1-{min(q1, paywall_chapter - 1)}章（开篇）",
            },
        ]

        # 付费卡点章节所在批次
        if paywall_chapter <= q2:
            batches.append(
                {
                    "range": (batches[-1]["range"][1] + 1, q2),
                    "type": "paywall",
                    "description": f"第{batches[-1]['range'][1] + 1}-{q2}章（发展+付费卡点）",
                }
            )
            batches.append(
                {
                    "range": (q2 + 1, q3),
                    "type": "middle",
                    "description": f"第{q2 + 1}-{q3}章（发展中段）",
                }
            )
        else:
            batches.append(
                {
                    "range": (batches[-1]["range"][1] + 1, min(paywall_chapter - 1, q2)),
                    "type": "development",
                    "description": "发展阶段",
                }
            )
            batches.append(
                {
                    "range": (batches[-1]["range"][1] + 1, min(paywall_chapter + 5, q3)),
                    "type": "paywall",
                    "description": f"第{batches[-1]['range'][1] + 1}-{min(paywall_chapter + 5, q3)}章（付费卡点+后续）",
                }
            )

        batches.append(
            {
                "range": (batches[-1]["range"][1] + 1, total_chapters),
                "type": "climax",
                "description": f"第{batches[-1]['range'][1] + 1}-{total_chapters}章（高潮+结局）",
            }
        )

    logger.info("Batch strategy determined", batch_count=len(batches))

    return {
        "generation_batches": batches,
        "current_batch_index": 0,
        "total_batches": len(batches),
        "accumulated_content": "",  # 累积生成的内容
        "last_successful_node": "batch_coordinator",
    }


# ===== 输出格式化 Node =====


async def output_formatter_node(state: AgentState) -> Dict[str, Any]:
    """
    输出格式化 Node

    当大纲生成完成并通过质检后，格式化输出并添加 SDUI 交互按钮
    """
    from backend.schemas.common import (
        UIInteractionBlock,
        UIInteractionBlockType,
        ActionButton,
    )
    from langchain_core.messages import AIMessage

    skeleton_content = state.get("skeleton_content", "")
    quality_score = state.get("quality_score", 0)
    revision_count = state.get("revision_count", 0)
    selected_plan = state.get("selected_plan", {})

    plan_title = selected_plan.get("title", "未知方案")

    logger.info(
        "Formatting skeleton output",
        quality_score=quality_score,
        revision_count=revision_count,
        content_length=len(skeleton_content),
    )

    # 构建状态标签
    status_emoji = "✅" if quality_score >= 80 else "⚠️"
    quality_label = f"质检评分: {quality_score}/100"
    revision_label = f"修改轮次: {revision_count}"

    # 创建格式化后的消息
    formatted_content = f"""{status_emoji} **大纲生成完成**

**方案**: 《{plan_title}》
**质检**: {quality_label}
**迭代**: {revision_label}

---

{skeleton_content}

---

💡 您可以确认此大纲开始剧本创作，或要求重新生成。"""

    # 创建 SDUI 交互块
    action_ui = UIInteractionBlock(
        block_type=UIInteractionBlockType.ACTION_GROUP,
        title="大纲确认",
        description=f"质检评分: {quality_score}/100 | 修改轮次: {revision_count}",
        buttons=[
            ActionButton(
                label="✅ 确认大纲",
                action="confirm_skeleton",
                payload={"skeleton_content": skeleton_content, "quality_score": quality_score},
                style="primary",
                icon="Check",
            ),
            ActionButton(
                label="🔄 重新生成",
                action="regenerate_skeleton",
                payload={"variation_seed": hash(skeleton_content) % 10000},  # 确保不同种子
                style="secondary",
                icon="RefreshCw",
            ),
        ],
        dismissible=False,
    )

    message = AIMessage(
        content=formatted_content,
        additional_kwargs={"ui_interaction": action_ui.dict()},
    )

    return {
        "messages": [message],
        "ui_interaction": action_ui,
        "last_successful_node": "output_formatter",
    }


async def handle_action_node(state: AgentState) -> Dict[str, Any]:
    """
    处理用户 Action Node

    处理 confirm_skeleton 和 regenerate_skeleton 动作
    """
    from langchain_core.messages import HumanMessage, AIMessage

    routed_params = state.get("routed_parameters", {})
    action = routed_params.get("action", "")
    current_stage = state.get("current_stage")

    logger.info(
        "Handling skeleton builder action",
        action=action,
        current_stage=current_stage,
    )

    if action == "confirm_skeleton":
        # 用户确认大纲，标记为已批准
        logger.info("User confirmed skeleton")

        return {
            "messages": [
                AIMessage(
                    content="✅ 大纲已确认！接下来可以开始剧本创作。",
                    additional_kwargs={"skeleton_confirmed": True},
                )
            ],
            "skeleton_approved": True,
            "current_stage": StageType.LEVEL_4,  # 升级到剧本创作阶段
            "last_successful_node": "handle_action_confirm",
        }

    elif action == "regenerate_skeleton":
        # 用户要求重新生成
        variation_seed = routed_params.get("variation_seed", 0)
        logger.info(
            "User requested regeneration",
            variation_seed=variation_seed,
        )

        # 重置相关状态，保留用户配置
        return {
            "messages": [
                HumanMessage(
                    content=f"请重新生成大纲（变异种子: {variation_seed}），尝试不同的创意方向。"
                )
            ],
            "skeleton_content": None,
            "quality_score": 0,
            "review_report": None,
            "refiner_output": None,
            "revision_count": 0,
            "regeneration_seed": variation_seed,
            "last_successful_node": "handle_action_regenerate",
        }

    else:
        # 未知动作，返回错误
        logger.warning("Unknown action", action=action)
        return {
            "messages": [AIMessage(content=f"⚠️ 未知操作: {action}")],
            "last_successful_node": "handle_action_unknown",
        }


# ===== Graph 构建 =====


def build_skeleton_builder_graph(checkpointer: BaseCheckpointSaver | None = None):
    """
    构建 Skeleton Builder Graph

    完整结构：
    START → [action_check] → validate → [conditional] → skeleton_builder → editor → [conditional] →
      ├─ [format] → output_formatter → END
      ├─ [refine] → refiner → editor (loop)
      └─ [incomplete] → request_ending → END

    Args:
        checkpointer: 可选的 Checkpoint 保存器

    Returns:
        编译后的 StateGraph
    """
    logger.info("Building Skeleton Builder Graph")

    # 创建状态图
    workflow = StateGraph(AgentState)

    # ===== 添加 Nodes =====

    # Node 0: 动作处理（处理 confirm/regenerate）
    workflow.add_node("handle_action", handle_action_node)

    # Node 1: 输入验证（普通函数）- 增强版，包含章节映射计算
    workflow.add_node("validate_input", validate_input_node)

    # Node 2: 请求 ending（普通函数，条件分支）
    workflow.add_node("request_ending", request_ending_node)

    # Node 3: 分批生成协调（新增）
    workflow.add_node("batch_coordinator", batch_coordinator_node)

    # Node 4: Skeleton Builder（Agent）
    workflow.add_node("skeleton_builder", skeleton_builder_node)

    # Node 5: 输出验证（新增）
    workflow.add_node("validate_output", validate_output_node)

    # Node 6: Quality Control（调用独立子图）
    workflow.add_node("quality_control", quality_control_node)

    # Node 7: 输出格式化（添加 SDUI 按钮）
    workflow.add_node("output_formatter", output_formatter_node)

    # ===== 添加 Edges =====

    # START → [conditional] → handle_action 或 validate_input
    def route_entry(state: AgentState) -> str:
        """入口路由：检测是否是动作请求"""
        routed_params = state.get("routed_parameters", {})
        action = routed_params.get("action", "")

        if action in ["confirm_skeleton", "regenerate_skeleton"]:
            logger.info("Entry routing to handle_action", action=action)
            return "handle_action"
        else:
            # start_skeleton_building 或无 action 的情况，走 validate_input
            logger.info("Entry routing to validate_input", action=action or "none")
            return "validate_input"

    # ✅ 使用条件路由从 START 开始，根据 action 决定走哪条路径
    workflow.add_conditional_edges(
        START,
        route_entry,
        {
            "handle_action": "handle_action",
            "validate_input": "validate_input",
        },
    )

    # handle_action 的后续路由
    workflow.add_conditional_edges(
        "handle_action",
        lambda state: "regenerate"
        if state.get("routed_parameters", {}).get("action") == "regenerate_skeleton"
        else "continue",
        {
            "regenerate": "validate_input",  # 重新生成：回到起点
            "continue": END,  # 确认：结束
        },
    )

    # validate_input → [conditional] → batch_coordinator 或 request_ending
    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "complete": "batch_coordinator",  # 改道到分批协调器
            "incomplete": "request_ending",
        },
    )

    # request_ending → END（等待用户输入）
    workflow.add_edge("request_ending", END)

    # batch_coordinator → skeleton_builder（根据分批策略生成）
    workflow.add_edge("batch_coordinator", "skeleton_builder")

    # skeleton_builder → validate_output（先生成，再验证）
    workflow.add_edge("skeleton_builder", "validate_output")

    # validate_output → [conditional] → quality_control 或 skeleton_builder(重试)
    def route_after_validate_output(state: AgentState) -> str:
        """输出验证后的路由决策"""
        validation_status = state.get("validation_status", "complete")
        retry_count = state.get("retry_count", 0)
        max_retries = 3

        if validation_status == "incomplete" and retry_count < max_retries:
            logger.warning(
                "Output validation failed, retrying",
                retry_count=retry_count + 1,
                max_retries=max_retries,
            )
            state["retry_count"] = retry_count + 1
            return "retry"
        elif validation_status == "incomplete":
            logger.error("Output validation failed after max retries")
            return "proceed"  # 即使失败也继续，避免死循环

        return "proceed"

    workflow.add_conditional_edges(
        "validate_output",
        route_after_validate_output,
        {
            "retry": "skeleton_builder",  # 重试生成
            "proceed": "quality_control",  # 继续到质检
        },
    )

    # quality_control → [conditional] → output_formatter 或 END
    def route_after_quality_control(state: AgentState) -> str:
        """
        Quality Control 后的路由决策

        根据质检结果决定是否进入输出格式化
        """
        quality_score = state.get("quality_score", 0)
        error = state.get("error")

        # 如果有错误，仍然格式化输出但会显示警告
        if error:
            logger.error(
                "Quality control returned error",
                error=error,
            )
            return "format"

        logger.info(
            "Quality control completed, routing to formatter",
            quality_score=quality_score,
        )
        return "format"

    workflow.add_conditional_edges(
        "quality_control",
        route_after_quality_control,
        {
            "format": "output_formatter",
        },
    )

    # output_formatter → END
    workflow.add_edge("output_formatter", END)

    # ===== 编译 Graph =====
    logger.info("Compiling Skeleton Builder Graph")
    compiled_graph = workflow.compile(checkpointer=checkpointer)

    logger.info("Skeleton Builder Graph compiled successfully")
    return compiled_graph


# ===== 便捷函数 =====


async def run_skeleton_builder(
    user_id: str,
    project_id: str,
    selected_plan: Dict[str, Any],
    user_config: Dict[str, Any],
    market_report: Dict[str, Any] | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """
    运行 Skeleton Builder Graph 的便捷函数

    Args:
        user_id: 用户ID
        project_id: 项目ID
        selected_plan: 选中的故事方案
        user_config: 用户配置
        market_report: 市场分析报告（可选）
        checkpointer: Checkpoint 保存器（可选）

    Returns:
        执行结果
    """
    from backend.schemas.agent_state import create_initial_state
    from langchain_core.messages import HumanMessage

    logger.info(
        "Running Skeleton Builder",
        user_id=user_id,
        project_id=project_id,
    )

    # 创建初始状态
    state = create_initial_state(
        user_id=user_id,
        project_id=project_id,
    )

    # 注入输入数据
    state["selected_plan"] = selected_plan
    state["user_config"] = user_config
    state["market_report"] = market_report
    state["messages"] = [HumanMessage(content="请根据选中的方案生成故事大纲。")]

    # 构建 Graph
    graph = build_skeleton_builder_graph(checkpointer=checkpointer)

    # 执行 Graph
    result = await graph.ainvoke(state)

    logger.info(
        "Skeleton Builder completed",
        last_node=result.get("last_successful_node"),
    )

    return result


# ===== 测试入口 =====

if __name__ == "__main__":
    """开发测试：直接运行此文件测试 Graph 创建"""
    import asyncio

    async def test():
        """测试 Graph 创建"""
        print("Testing Skeleton Builder Graph creation...")

        try:
            graph = build_skeleton_builder_graph()
            print(f"✅ Graph created successfully")
            print(f"   Nodes: {list(graph.nodes.keys())}")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    asyncio.run(test())
