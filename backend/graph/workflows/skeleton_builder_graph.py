"""
Skeleton Builder Graph - 5-Node 工作流

流程：
START → validate_input → [conditional] →
  ├─ [complete] → skeleton_builder → editor → refiner → END
  └─ [incomplete] → request_ending → END
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from backend.schemas.agent_state import AgentState, ApprovalStatus, StageType
from backend.agents.skeleton_builder import skeleton_builder_node
from backend.agents.quality_control.editor import editor_node
from backend.agents.quality_control.refiner import refiner_node

import structlog

logger = structlog.get_logger(__name__)


# ===== 普通函数 Nodes =====


async def validate_input_node(state: AgentState) -> Dict[str, Any]:
    """
    输入验证 Node

    检查必要的输入字段是否存在，自动推断配置
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

    # 自动推断配置（如果有需要）
    inferred_config = {}
    if not user_config.get("total_episodes"):
        inferred_config["total_episodes"] = 80  # 默认值

    logger.info(
        "Input validation passed",
        inferred_config=inferred_config,
    )

    return {
        "validation_status": "complete",
        "inferred_config": inferred_config,
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


def route_after_editor(state: AgentState) -> str:
    """
    Editor 后的路由决策

    根据 quality_score 决定是否需要修复
    """
    quality_score = state.get("quality_score", 0)
    revision_count = state.get("revision_count", 0)
    review_report = state.get("review_report")

    # 如果评分 >= 80，质量通过，直接结束
    if quality_score >= 80:
        logger.info(
            "Quality check passed",
            quality_score=quality_score,
            revision_count=revision_count,
        )
        return "end"

    # 如果质量为0，说明有系统错误或前置节点失败，无法修复
    if quality_score == 0:
        logger.error(
            "Quality score is 0, system error or previous node failed",
            quality_score=quality_score,
        )
        return "end"

    # 如果已达到最大重试次数，强制结束（即使质量不达标）
    if revision_count >= 3:
        logger.warning(
            "Max revision count reached, forcing end",
            quality_score=quality_score,
            revision_count=revision_count,
        )
        return "end"

    # 如果没有review_report，说明Editor执行失败，不能进入Refiner
    if not review_report:
        logger.error(
            "No review report available, cannot refine",
            quality_score=quality_score,
        )
        return "end"

    # 否则进入 Refiner 修复
    logger.info(
        "Quality check failed, routing to refiner",
        quality_score=quality_score,
    )
    return "refine"


def route_after_refiner(state: AgentState) -> str:
    """
    Refiner 后的路由决策

    修复后回到 Editor 重新审阅（循环质检）
    """
    revision_count = state.get("revision_count", 0)
    refiner_output = state.get("refiner_output")

    # 增加修改计数
    new_revision_count = revision_count + 1

    # 如果Refiner没有输出，说明修复失败
    if not refiner_output:
        logger.error(
            "Refiner failed to produce output",
            revision_count=new_revision_count,
        )
        return "review"  # 仍然回到editor，但Editor会看到没有改进

    logger.info(
        "Refiner completed, routing back to editor",
        revision_count=new_revision_count,
    )

    return "review"


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


# ===== 改进的路由函数 =====


def route_after_editor_with_formatter(state: AgentState) -> str:
    """
    Editor 后的路由决策（增强版）

    根据 quality_score 决定是否需要修复，或者进入输出格式化
    """
    quality_score = state.get("quality_score", 0)
    revision_count = state.get("revision_count", 0)
    review_report = state.get("review_report")

    # 如果评分 >= 80，质量通过，进入输出格式化
    if quality_score >= 80:
        logger.info(
            "Quality check passed, routing to output formatter",
            quality_score=quality_score,
            revision_count=revision_count,
        )
        return "format"

    # 如果质量为0，说明有系统错误或前置节点失败，无法修复
    if quality_score == 0:
        logger.error(
            "Quality score is 0, system error or previous node failed",
            quality_score=quality_score,
        )
        return "format"  # 仍然格式化输出，但会显示警告

    # 如果已达到最大重试次数，强制进入格式化
    if revision_count >= 3:
        logger.warning(
            "Max revision count reached, forcing to formatter",
            quality_score=quality_score,
            revision_count=revision_count,
        )
        return "format"

    # 如果没有review_report，说明Editor执行失败
    if not review_report:
        logger.error(
            "No review report available, cannot refine",
            quality_score=quality_score,
        )
        return "format"

    # 否则进入 Refiner 修复
    logger.info(
        "Quality check failed, routing to refiner",
        quality_score=quality_score,
    )
    return "refine"


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

    # Node 1: 输入验证（普通函数）
    workflow.add_node("validate_input", validate_input_node)

    # Node 2: 请求 ending（普通函数，条件分支）
    workflow.add_node("request_ending", request_ending_node)

    # Node 3: Skeleton Builder（Agent）
    workflow.add_node("skeleton_builder", skeleton_builder_node)

    # Node 4: Editor（Agent）
    workflow.add_node("editor", editor_node)

    # Node 5: Refiner（Agent）
    workflow.add_node("refiner", refiner_node)

    # Node 6: 输出格式化（添加 SDUI 按钮）
    workflow.add_node("output_formatter", output_formatter_node)

    # ===== 添加 Edges =====

    # START → [conditional] → handle_action 或 validate_input
    def route_entry(state: AgentState) -> str:
        """入口路由：检测是否是动作请求"""
        routed_params = state.get("routed_parameters", {})
        action = routed_params.get("action", "")

        if action in ["confirm_skeleton", "regenerate_skeleton"]:
            logger.info("Entry routing to handle_action", action=action)
            return "action"
        else:
            logger.info("Entry routing to validate_input")
            return "validate"

    workflow.set_entry_point("handle_action")
    workflow.add_conditional_edges(
        "handle_action",
        lambda state: "regenerate"
        if state.get("routed_parameters", {}).get("action") == "regenerate_skeleton"
        else "continue",
        {
            "regenerate": "validate_input",  # 重新生成：回到起点
            "continue": END,  # 确认或其他：结束
        },
    )

    # validate_input → [conditional] → skeleton_builder 或 request_ending
    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "complete": "skeleton_builder",
            "incomplete": "request_ending",
        },
    )

    # request_ending → END（等待用户输入）
    workflow.add_edge("request_ending", END)

    # skeleton_builder → editor
    workflow.add_edge("skeleton_builder", "editor")

    # editor → [conditional] → output_formatter 或 refiner
    workflow.add_conditional_edges(
        "editor",
        route_after_editor_with_formatter,
        {
            "format": "output_formatter",
            "refine": "refiner",
        },
    )

    # refiner → editor（循环质检，增加修改计数）
    def route_after_refiner_with_count(state: AgentState) -> str:
        """Refiner 后的路由，增加修改计数"""
        revision_count = state.get("revision_count", 0)
        new_count = revision_count + 1
        logger.info("Routing after refiner", revision_count=new_count)
        # 返回一个特殊标记，让 editor 知道这是第几次修改
        return "review"

    workflow.add_conditional_edges(
        "refiner",
        route_after_refiner_with_count,
        {
            "review": "editor",
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
