"""
Master Router (Enhanced V4.1)

Level 0 - 总控中枢 (增强版)

职责：
1. 意图识别：理解用户的自然语言指令
2. 上下文感知：结合当前状态推断真实意图
3. 工作流规划：支持多步骤工作流（新增）
4. 精准路由：将任务分发给最合适的专家 Agent
5. 参数提取：从口语中提取精确的函数参数

增强功能 (V4.1)：
- 支持 workflow_plan 多步骤工作流规划
- 动态 Agent Registry 集成
- 自动工作流验证

注意：Master Router 不使用 Agent Skill，而是直接调用 LLM。
原因：
- Master Router 是纯决策节点，不需要 Tool 调用
- 直接调用 LLM 更轻量、更高效
- 架构更清晰：Router 是调度器，Agents 是执行器
"""

from typing import Dict, Any, List
import json
import structlog
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from backend.schemas.agent_state import AgentState, WorkflowStep
from backend.services.model_router import get_model_router
from backend.graph.agents.registry import AgentRegistry
from backend.schemas.model_config import TaskType
from backend.utils.message_converter import normalize_messages

logger = structlog.get_logger(__name__)


def _load_master_router_prompt_base() -> str:
    """
    加载 Master Router 的基础 System Prompt

    从 prompts/0_Master_Router.md 文件加载

    Returns:
        System Prompt 基础字符串
    """
    prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "0_Master_Router.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 Markdown 内容（去掉开头的标题）
        lines = content.split("\n")
        # 找到第一个非标题行
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                start_idx = i
                break

        prompt = "\n".join(lines[start_idx:]).strip()
        logger.debug("Loaded Master Router prompt from file", path=str(prompt_path))
        return prompt

    except FileNotFoundError:
        logger.error("Master Router prompt file not found", path=str(prompt_path))
        # 返回基础 Prompt 作为 fallback
        return _get_fallback_prompt()
    except Exception as e:
        logger.error("Failed to load Master Router prompt", error=str(e))
        return _get_fallback_prompt()


def _get_fallback_prompt() -> str:
    """获取基础 Prompt（当文件加载失败时使用）"""
    return """你是 AI 短剧生成引擎的总控大脑。

你的职责：
1. 深度语义分析用户输入
2. 结合上下文推断真实意图
3. 规划工作流（单步骤或多步骤）
4. 输出路由决策

输出必须是 JSON 格式。"""


def _build_dynamic_prompt() -> str:
    """
    构建动态的 System Prompt

    从文件加载基础 Prompt，并动态注入 Agent Registry 信息。
    所有业务逻辑内容都在 prompt 文件中，这里只追加动态的 Agent 列表。

    Returns:
        完整的 System Prompt
    """
    # 1. 从文件加载基础 Prompt（包含所有业务逻辑、workflow planning 等）
    base_prompt = _load_master_router_prompt_base()

    # 2. 获取动态生成的 Agent Registry 描述
    agent_description = AgentRegistry.get_prompt_description()

    # 3. 组合：基础 Prompt + Agent 列表
    # 注意：所有 workflow planning、输出格式、示例等都在 base_prompt 中
    full_prompt = f"""{base_prompt}

{agent_description}
"""

    return full_prompt


# 加载动态 System Prompt（每次调用时重新构建以获取最新 Agent 列表）
def _get_master_router_prompt() -> str:
    """获取 Master Router 的 System Prompt"""
    return _build_dynamic_prompt()


def _extract_routing_decision(response_content: str) -> Dict[str, Any]:
    """
    从 LLM 响应中提取路由决策（支持单步骤和多步骤）

    Args:
        response_content: LLM 返回的文本内容

    Returns:
        解析后的路由决策字典
    """
    try:
        # 尝试解析 JSON
        # 查找 JSON 代码块
        if "```json" in response_content:
            json_str = response_content.split("```json")[1].split("```")[0].strip()
        elif "```" in response_content:
            json_str = response_content.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_content.strip()

        decision = json.loads(json_str)

        # 检查是否是多步骤工作流（V4.1）
        if "workflow_plan" in decision and decision["workflow_plan"]:
            # 多步骤模式
            logger.info("Multi-step workflow detected", step_count=len(decision["workflow_plan"]))

            # 验证工作流
            workflow = decision["workflow_plan"]
            is_valid, error_msg = AgentRegistry.validate_workflow(workflow)

            if not is_valid:
                logger.error("Invalid workflow", error=error_msg)
                return {
                    "intent_analysis": decision.get("intent_analysis", ""),
                    "workflow_plan": [],
                    "current_step_idx": 0,
                    "routed_agent": "end",
                    "routed_function": None,
                    "routed_parameters": {},
                    "ui_feedback": f"工作流规划有误: {error_msg}",
                }

            # 获取第一个步骤的 Agent
            first_step = workflow[0] if workflow else None
            if first_step:
                return {
                    "intent_analysis": decision.get("intent_analysis", ""),
                    "workflow_plan": workflow,
                    "current_step_idx": 0,
                    "routed_agent": first_step["agent"],
                    "routed_function": None,  # 工作流模式不使用 function_name
                    "routed_parameters": first_step.get("input_mapping", {}),
                    "ui_feedback": decision.get("ui_feedback", "正在执行多步骤任务..."),
                }

        # 单步骤模式（向后兼容）
        # 验证必要字段
        if "target_agent" not in decision:
            logger.warning("Missing target_agent in decision", content=response_content[:200])
            decision["target_agent"] = "end"

        # 转换 target_agent 到 routed_agent（统一字段名）
        decision["routed_agent"] = decision.pop("target_agent")

        # 工作流相关字段置空
        decision["workflow_plan"] = []
        decision["current_step_idx"] = 0
        decision["intent_analysis"] = decision.get("thought_process", "")

        if "ui_feedback" not in decision:
            decision["ui_feedback"] = "正在处理您的请求..."

        return decision

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse routing decision", error=str(e), content=response_content[:500]
        )
        # 返回默认决策
        return {
            "intent_analysis": "解析失败，使用默认路由",
            "workflow_plan": [],
            "current_step_idx": 0,
            "routed_agent": "end",
            "routed_function": None,
            "routed_parameters": {},
            "ui_feedback": "抱歉，我遇到了一些问题，请重新描述您的需求。",
        }


def _build_master_router_context(state: AgentState) -> str:
    """
    构建 Master Router 的上下文信息

    Args:
        state: 当前 AgentState

    Returns:
        格式化的上下文字符串
    """
    context_parts = []

    # 当前阶段
    current_stage = state.get("current_stage", "Unknown")
    context_parts.append(f"当前阶段: {current_stage}")

    # 用户配置
    user_config = state.get("user_config", {})
    if user_config.get("genre"):
        context_parts.append(f"已选题材: {user_config['genre']}")
    if user_config.get("tone"):
        context_parts.append(f"内容调性: {', '.join(user_config['tone'])}")

    # 故事方案
    story_plans = state.get("story_plans", [])
    if story_plans:
        context_parts.append(f"已生成方案数: {len(story_plans)}")

    selected_plan = state.get("selected_plan")
    if selected_plan:
        context_parts.append(f"已选方案: {selected_plan.get('title', 'Unknown')}")

    # 骨架构建
    character_bible = state.get("character_bible", [])
    if character_bible:
        context_parts.append(f"角色数: {len(character_bible)}")

    beat_sheet = state.get("beat_sheet", [])
    if beat_sheet:
        context_parts.append(f"分集数: {len(beat_sheet)}")

    # 小说创作
    current_episode = state.get("current_episode", 1)
    novel_content = state.get("novel_content", "")
    if novel_content:
        context_parts.append(f"当前集数: {current_episode}, 字数: {len(novel_content)}")

    # 工作流状态（V4.1）
    workflow_plan = state.get("workflow_plan", [])
    current_step_idx = state.get("current_step_idx", 0)
    if workflow_plan:
        context_parts.append(
            f"\n当前工作流: {len(workflow_plan)} 步，正在执行第 {current_step_idx + 1} 步"
        )
        if current_step_idx < len(workflow_plan):
            current_step = workflow_plan[current_step_idx]
            context_parts.append(f"当前步骤: {current_step.get('task', 'Unknown')}")

    return "\n".join(context_parts)


def _check_workflow_continuation(state: AgentState) -> Dict[str, Any] | None:
    """
    检查是否需要继续执行工作流的下一步

    Args:
        state: 当前 AgentState

    Returns:
        如果需要继续，返回状态更新字典；否则返回 None
    """
    workflow_plan = state.get("workflow_plan", [])
    current_step_idx = state.get("current_step_idx", 0)

    if not workflow_plan:
        return None

    # 检查是否还有下一步
    next_idx = current_step_idx + 1
    if next_idx >= len(workflow_plan):
        # 工作流完成
        logger.info("Workflow completed", total_steps=len(workflow_plan))
        return {
            "workflow_plan": None,  # 清空工作流
            "current_step_idx": 0,
            "routed_agent": "end",
            "ui_feedback": "所有任务已完成！",
        }

    # 继续执行下一步
    next_step = workflow_plan[next_idx]
    logger.info(
        "Continuing workflow",
        next_step=next_step["step_id"],
        agent=next_step["agent"],
    )

    return {
        "current_step_idx": next_idx,
        "routed_agent": next_step["agent"],
        "routed_parameters": next_step.get("input_mapping", {}),
        "ui_feedback": f"步骤 {next_idx + 1}/{len(workflow_plan)}: {next_step.get('task', '执行中...')}",
    }


async def master_router_node(state: AgentState) -> Dict[str, Any]:
    """
    Master Router 节点（增强版 V4.1）

    支持单步骤路由和多步骤工作流规划。

    Args:
        state: 当前 AgentState

    Returns:
        状态更新字典
    """
    # 首先检查是否需要继续执行工作流
    continuation = _check_workflow_continuation(state)
    if continuation:
        logger.info("Resuming workflow", next_step=continuation.get("current_step_idx", 0) + 1)
        return continuation

    # 检查是否已经有预设的 routed_agent（来自 SDUI Action）
    pre_set_agent = state.get("routed_agent")
    if pre_set_agent and pre_set_agent != "end":
        logger.info(
            "Using pre-set routed_agent from SDUI action, skipping LLM call",
            routed_agent=pre_set_agent,
        )
        # 直接返回预设的路由决策，不调用 LLM，不添加消息到 messages
        return {
            "intent_analysis": state.get(
                "intent_analysis", f"SDUI action routing to {pre_set_agent}"
            ),
            "workflow_plan": state.get("workflow_plan", []),
            "current_step_idx": state.get("current_step_idx", 0),
            "routed_agent": pre_set_agent,
            "routed_function": state.get("routed_function"),
            "routed_parameters": state.get("routed_parameters", {}),
            "ui_feedback": state.get(
                "ui_feedback", f"正在为您启动 {pre_set_agent.replace('_', ' ')}..."
            ),
            "last_successful_node": "master_router",
        }

    # 获取模型
    router = get_model_router()
    model = await router.get_model(
        user_id=state["user_id"], task_type=TaskType.ROUTER, project_id=state.get("project_id")
    )

    # 构建上下文
    context = _build_master_router_context(state)

    # 获取原始消息并标准化格式
    # 修复: 从 checkpoint 恢复的消息可能是字典格式，需要转换为 LangChain 消息对象
    raw_messages = state.get("messages", [])
    messages = normalize_messages(raw_messages)

    # 获取最后一条用户消息
    last_user_message = ""
    for msg in reversed(messages):
        if isinstance(msg, BaseMessage) and msg.type == "human":
            last_user_message = msg.content
            break
        # 兼容旧逻辑
        elif hasattr(msg, "type") and msg.type == "human":
            last_user_message = msg.content
            break

    # 构建输入（注入 Agent Registry 信息）
    agent_description = AgentRegistry.get_prompt_description()
    user_input = f"""## 当前上下文
{context}

## 可用 Agents
{agent_description}

## 用户输入
{last_user_message}

## 任务
请分析用户意图：
1. 如果是单步骤任务，输出传统路由决策
2. 如果是多步骤任务（包含"并"、"然后"、"先...再..."等词），输出 workflow_plan
3. 确保 workflow_plan 中的 Agent 名称与上面列出的完全一致"""

    logger.info(
        "Master Router processing",
        user_message=last_user_message[:100],
        current_stage=state.get("current_stage"),
    )

    # 调用 LLM
    prompt = _get_master_router_prompt()
    response = await model.ainvoke(
        [SystemMessage(content=prompt), HumanMessage(content=user_input)]
    )

    # 解析路由决策
    decision = _extract_routing_decision(response.content)

    logger.info(
        "Master Router decision",
        routed_agent=decision.get("routed_agent"),
        workflow_steps=len(decision.get("workflow_plan", [])),
        ui_feedback=decision.get("ui_feedback", "")[:50],
    )

    # 返回状态更新
    # 注意：不添加 response 到 messages，避免将 JSON 决策显示给用户
    # ui_feedback 会在 API 端点被提取并显示
    return {
        "intent_analysis": decision.get("intent_analysis"),
        "workflow_plan": decision.get("workflow_plan"),
        "current_step_idx": decision.get("current_step_idx", 0),
        "routed_agent": decision.get("routed_agent"),
        "routed_function": decision.get("routed_function"),
        "routed_parameters": decision.get("routed_parameters", {}),
        "ui_feedback": decision.get("ui_feedback"),
        "last_successful_node": "master_router",
    }


__all__ = ["master_router_node"]
