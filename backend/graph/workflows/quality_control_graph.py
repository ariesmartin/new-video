"""
Quality Control Graph - 独立的质量控制工作流

遵循 LangGraph 官方架构规范：
- Agent = create_react_agent 返回的 Compiled Graph
- Node = 普通函数或 Agent
- Graph = StateGraph 编译后的工作流

支持四种审阅模式：
1. review_only: 单次审阅，返回报告
2. refine_only: 单次修复
3. full_cycle: 审阅 → 修复 → 审阅循环
4. chapter_review: 单章审阅（新增）

可被任何模块调用：skeleton_builder, novel_writer, script_adapter, storyboard_director
"""

from typing import Dict, Any, Literal, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from backend.agents.quality_control.editor import editor_node
from backend.agents.quality_control.refiner import refiner_node
from backend.schemas.agent_state import AgentState

import structlog

logger = structlog.get_logger(__name__)


# ===== 状态类型 =====


class QualityControlState(AgentState):
    """
    Quality Control 专用状态

    继承自 AgentState，添加质量控制相关字段
    """

    # 运行模式
    mode: Literal["global_review", "refine_only", "full_cycle", "chapter_review"]

    # 质量控制配置
    target_score: int  # 目标分数
    max_iterations: int  # 最大迭代次数

    # 输入
    input_content: Optional[str]  # 待审阅/修复的内容
    chapter_id: Optional[str]  # 单章审阅时的章节ID

    # 输出
    review_report: Optional[Dict[str, Any]]
    refined_content: Optional[str]
    refine_log: Optional[list]
    final_score: int
    iterations_performed: int

    # 状态
    qc_status: Literal["pending", "reviewing", "refining", "completed", "failed"]


# ===== Nodes =====


async def prepare_input_node(state: QualityControlState) -> Dict[str, Any]:
    """
    准备输入 Node - 普通函数

    根据 mode 准备相应的输入数据
    """
    mode = state.get("mode", "full_cycle")
    input_content = state.get("input_content")
    chapter_id = state.get("chapter_id")

    logger.info(
        "Preparing Quality Control input",
        mode=mode,
        chapter_id=chapter_id,
        has_input_content=bool(input_content),
    )

    # 如果提供了 input_content，将其添加到 messages
    if input_content and not state.get("messages"):
        from langchain_core.messages import HumanMessage

        # 根据模式添加前缀
        if mode == "chapter_review" and chapter_id:
            content = f"【单章审阅 - 章节ID: {chapter_id}】\n\n{input_content}"
        else:
            content = input_content

        return {
            "messages": [HumanMessage(content=content)],
            "qc_status": "pending",
            "iterations_performed": 0,
        }

    return {
        "qc_status": "pending",
        "iterations_performed": 0,
    }


async def finalize_output_node(state: QualityControlState) -> Dict[str, Any]:
    """
    最终输出 Node - 普通函数

    整理质量控制结果
    """
    review_report = state.get("review_report")
    mode = state.get("mode", "full_cycle")
    chapter_id = state.get("chapter_id")
    final_score = review_report.get("overall_score", 0) if review_report else 0

    logger.info(
        "Finalizing Quality Control output",
        mode=mode,
        chapter_id=chapter_id,
        final_score=final_score,
    )

    return {
        "final_score": final_score,
        "qc_status": "completed",
    }


# ===== 路由函数 =====


def route_by_mode(state: QualityControlState) -> Literal["review", "refine"]:
    """
    根据 mode 路由

    Returns:
        "review" 或 "refine"
    """
    mode = state.get("mode", "full_cycle")

    if mode == "refine_only":
        return "refine"
    else:
        # global_review, full_cycle, chapter_review 都进入 editor
        return "review"


def route_after_editor(state: QualityControlState) -> Literal["end", "refine"]:
    """
    Editor 后的路由决策

    Returns:
        "end": 结束（global_review/chapter_review 模式或已达标）
        "refine": 进入修复
    """
    mode = state.get("mode", "full_cycle")
    review_report = state.get("review_report")

    # global_review 或 chapter_review 模式：直接结束
    if mode in ["global_review", "chapter_review"]:
        return "end"

    # 没有审阅报告，结束
    if not review_report:
        logger.error("No review report, ending")
        return "end"

    score = review_report.get("overall_score", 0)
    target_score = state.get("target_score", 80)
    iterations = state.get("iterations_performed", 0)
    max_iterations = state.get("max_iterations", 3)

    # 分数达标，结束
    if score >= target_score:
        logger.info("Quality target reached", score=score)
        return "end"

    # 达到最大迭代次数，结束
    if iterations >= max_iterations:
        logger.warning("Max iterations reached", iterations=iterations)
        return "end"

    # 需要修复
    logger.info("Routing to refiner", score=score, target=target_score)
    return "refine"


def route_after_refiner(state: QualityControlState) -> Literal["end", "review"]:
    """
    Refiner 后的路由决策

    Returns:
        "end": 结束（refine_only 模式）
        "review": 回到 editor 重新审阅（full_cycle 模式）
    """
    mode = state.get("mode", "full_cycle")

    # refine_only 模式：直接结束
    if mode == "refine_only":
        return "end"

    # full_cycle 模式：回到 editor
    logger.info("Routing back to editor for re-review")
    return "review"


# ===== Graph 构建 =====


def build_quality_control_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    """
    构建 Quality Control Graph

    结构：
        START → prepare_input → [conditional]
          ├─ [review] → editor → [conditional]
          │               ├─ [end] → finalize_output → END
          │               └─ [refine] → refiner → [conditional]
          │                                   ├─ [end] → finalize_output → END (refine_only)
          │                                   └─ [review] → editor (full_cycle)
          └─ [refine] → refiner → finalize_output → END (refine_only)

    Args:
        checkpointer: 可选的 Checkpoint 保存器

    Returns:
        编译后的 StateGraph
    """
    logger.info("Building Quality Control Graph")

    # 创建状态图
    workflow = StateGraph(QualityControlState)

    # ===== 添加 Nodes =====

    # 普通函数 Nodes
    workflow.add_node("prepare_input", prepare_input_node)
    workflow.add_node("finalize_output", finalize_output_node)

    # Agent Nodes（直接使用已有的 node wrapper）
    workflow.add_node("editor", editor_node)
    workflow.add_node("refiner", refiner_node)

    # ===== 添加 Edges =====

    # START → prepare_input
    workflow.set_entry_point("prepare_input")

    # prepare_input → [conditional] → editor 或 refiner
    workflow.add_conditional_edges(
        "prepare_input",
        route_by_mode,
        {
            "review": "editor",
            "refine": "refiner",
        },
    )

    # editor → [conditional] → finalize_output 或 refiner
    workflow.add_conditional_edges(
        "editor",
        route_after_editor,
        {
            "end": "finalize_output",
            "refine": "refiner",
        },
    )

    # refiner → [conditional] → finalize_output 或 editor
    workflow.add_conditional_edges(
        "refiner",
        route_after_refiner,
        {
            "end": "finalize_output",
            "review": "editor",
        },
    )

    # finalize_output → END
    workflow.add_edge("finalize_output", END)

    # ===== 编译 Graph =====
    logger.info("Compiling Quality Control Graph")
    compiled_graph = workflow.compile(checkpointer=checkpointer)

    logger.info("Quality Control Graph compiled successfully")
    return compiled_graph


# ===== 便捷函数 =====


async def run_quality_review(
    user_id: str,
    project_id: str,
    content: str,
    content_type: str = "outline",
    checkpointer: Optional[BaseCheckpointSaver] = None,
) -> Dict[str, Any]:
    """
    运行全局质量审阅 (global_review 模式)

    适用于全局审阅
    """
    from langchain_core.messages import HumanMessage

    logger.info("Running global quality review", user_id=user_id, content_type=content_type)

    graph = build_quality_control_graph(checkpointer=checkpointer)

    # 构建初始状态
    initial_state: QualityControlState = {
        "mode": "global_review",
        "user_id": user_id,
        "project_id": project_id,
        "input_content": content,
        "messages": [HumanMessage(content=content)],
        "target_score": 80,
        "max_iterations": 0,
        "chapter_id": None,
        "review_report": None,
        "refined_content": None,
        "refine_log": None,
        "final_score": 0,
        "iterations_performed": 0,
        "qc_status": "pending",
    }

    result = await graph.ainvoke(initial_state)

    return {
        "review_report": result.get("review_report"),
        "quality_score": result.get("final_score", 0),
    }


async def run_chapter_review(
    user_id: str,
    project_id: str,
    chapter_id: str,
    content: str,
    content_type: str = "outline",
    checkpointer: Optional[BaseCheckpointSaver] = None,
) -> Dict[str, Any]:
    """
    运行单章质量审阅 (chapter_review 模式)

    适用于单章审阅
    """
    from langchain_core.messages import HumanMessage

    logger.info(
        "Running chapter review",
        user_id=user_id,
        chapter_id=chapter_id,
        content_type=content_type,
    )

    graph = build_quality_control_graph(checkpointer=checkpointer)

    # 构建初始状态
    initial_state: QualityControlState = {
        "mode": "chapter_review",
        "user_id": user_id,
        "project_id": project_id,
        "chapter_id": chapter_id,
        "input_content": content,
        "messages": [HumanMessage(content=content)],
        "target_score": 80,
        "max_iterations": 0,
        "review_report": None,
        "refined_content": None,
        "refine_log": None,
        "final_score": 0,
        "iterations_performed": 0,
        "qc_status": "pending",
    }

    result = await graph.ainvoke(initial_state)

    return {
        "review_report": result.get("review_report"),
        "quality_score": result.get("final_score", 0),
        "chapter_id": chapter_id,
    }


async def run_full_quality_cycle(
    user_id: str,
    project_id: str,
    content: str,
    content_type: str = "outline",
    target_score: int = 80,
    max_iterations: int = 3,
    checkpointer: Optional[BaseCheckpointSaver] = None,
) -> Dict[str, Any]:
    """
    运行完整质量控制循环 (full_cycle 模式)
    """
    from langchain_core.messages import HumanMessage

    logger.info(
        "Running full quality cycle",
        user_id=user_id,
        content_type=content_type,
        target_score=target_score,
        max_iterations=max_iterations,
    )

    graph = build_quality_control_graph(checkpointer=checkpointer)

    # 构建初始状态
    initial_state: QualityControlState = {
        "mode": "full_cycle",
        "user_id": user_id,
        "project_id": project_id,
        "input_content": content,
        "messages": [HumanMessage(content=content)],
        "target_score": target_score,
        "max_iterations": max_iterations,
        "chapter_id": None,
        "review_report": None,
        "refined_content": None,
        "refine_log": None,
        "final_score": 0,
        "iterations_performed": 0,
        "qc_status": "pending",
    }

    result = await graph.ainvoke(initial_state)

    return {
        "review_report": result.get("review_report"),
        "refined_content": result.get("refined_content"),
        "final_score": result.get("final_score", 0),
        "iterations": result.get("iterations_performed", 0),
    }


# ===== 测试入口 =====

if __name__ == "__main__":
    """开发测试"""
    import asyncio

    async def test():
        print("Testing Quality Control Graph creation...")

        try:
            graph = build_quality_control_graph()
            print(f"✅ Graph created successfully")
            print(f"   Nodes: {list(graph.nodes.keys())}")
            print("\n支持的模式:")
            print("  1. global_review  - 全局审阅")
            print("  2. refine_only    - 单次修复")
            print("  3. full_cycle     - 完整循环")
            print("  4. chapter_review - 单章审阅")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

    asyncio.run(test())
