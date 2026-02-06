"""
Graph API Routes

Endpoints for the LangGraph workflow system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import structlog
import json

from datetime import datetime
from backend.graph.main_graph import get_graph_for_request
from backend.schemas.agent_state import create_initial_state
from backend.services.chat_init_service import (
    is_cold_start_message,
    create_welcome_message,
    get_content_status,
    prepare_initial_state,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/graph", tags=["graph"])


class ActionButton(BaseModel):
    """操作按钮"""

    label: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    style: str = "primary"  # primary/secondary/danger/ghost
    icon: Optional[str] = None
    disabled: bool = False
    disabled_reason: Optional[str] = None


class UIInteractionBlock(BaseModel):
    """UI 交互块"""

    block_type: str = "action_group"  # action_group/selection/confirmation/input
    title: Optional[str] = None
    description: Optional[str] = None
    buttons: List[ActionButton] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)
    dismissible: bool = True


class ContentStatus(BaseModel):
    """内容状态"""

    has_novel_content: bool = False
    has_script: bool = False
    has_storyboard: bool = False
    has_any_content: bool = False


class ChatRequest(BaseModel):
    """Chat request payload"""

    user_id: str
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    message: Optional[str] = None
    action: Optional[str] = None  # e.g., "cold_start", "random_plan", "continue"
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Chat response"""

    routed_agent: Optional[str] = None
    workflow_plan: Optional[List[Dict[str, Any]]] = None
    ui_feedback: Optional[str] = None
    intent_analysis: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    ui_interaction: Optional[UIInteractionBlock] = None  # 新增：UI交互块
    is_cold_start: bool = False  # 新增：是否是冷启动
    content_status: Optional[ContentStatus] = None  # 新增：内容状态


class ChatInitRequest(BaseModel):
    """聊天初始化请求 - 后端决定返回历史还是冷启动"""

    user_id: str
    project_id: str
    session_id: Optional[str] = None


class ChatMessage(BaseModel):
    """统一的消息格式"""

    id: str
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    display_label: Optional[str] = None  # 友好显示标签（用于 action 消息）
    timestamp: str
    ui_interaction: Optional[UIInteractionBlock] = None


class ChatInitResponse(BaseModel):
    """聊天初始化响应 - 统一格式"""

    thread_id: str
    messages: List[ChatMessage]
    is_cold_start: bool  # true=冷启动（新会话），false=恢复历史
    ui_interaction: Optional[UIInteractionBlock] = None  # 冷启动时的 UI 组件


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for the LangGraph workflow system.

    Handles:
    - Cold start (welcome message with function entry buttons)
    - Single-step workflows
    - Multi-step workflows
    """
    try:
        logger.info(
            "Chat endpoint called",
            user_id=request.user_id,
            action=request.action,
            has_message=bool(request.message),
        )

        # Generate IDs if not provided
        project_id = request.project_id or str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())

        # Create initial state
        state = create_initial_state(
            user_id=request.user_id,
            project_id=project_id,
            thread_id=session_id,
        )

        # Add context
        if request.context:
            for key, value in request.context.items():
                state[key] = value

        # ===== 正常流程：添加用户消息 =====
        if request.message:
            from langchain_core.messages import HumanMessage

            state["messages"] = [HumanMessage(content=request.message)]
            state["user_input"] = request.message

        # Handle action-based routing
        if request.action == "random_plan":
            # AI Random Plan - route to story_planner for automatic plan generation
            logger.info("Action: random_plan - Routing to story_planner")
            state["routed_agent"] = "story_planner"
            state["ui_feedback"] = "正在为您生成AI随机方案..."

        elif request.action == "continue":
            # Continue existing workflow
            logger.info("Action: continue - Resuming workflow")
            # The graph will handle continuation
            pass

        # Get graph for request
        graph = await get_graph_for_request()

        # Prepare config for checkpointer
        config = {
            "configurable": {
                "thread_id": session_id,
            }
        }

        # Run the graph (invoke with initial state and config)
        result = await graph.ainvoke(state, config)

        # 获取内容状态
        content_status = get_content_status(result)

        # Extract response data
        response_data = {
            "routed_agent": result.get("routed_agent"),
            "workflow_plan": result.get("workflow_plan", []),
            "ui_feedback": result.get("ui_feedback"),
            "intent_analysis": result.get("intent_analysis"),
            "messages": [
                {"type": type(m).__name__, "content": m.content} for m in result.get("messages", [])
            ]
            if result.get("messages")
            else None,
            "ui_interaction": UIInteractionBlock(**result["ui_interaction"].dict())
            if result.get("ui_interaction")
            else None,
            "is_cold_start": False,
            "content_status": ContentStatus(**content_status),
        }

        logger.info(
            "Chat endpoint completed",
            routed_agent=response_data["routed_agent"],
            has_workflow_plan=bool(response_data["workflow_plan"]),
        )

        return ChatResponse(**response_data)

    except RuntimeError as e:
        # 模型未配置错误
        error_msg = str(e)
        if "未配置模型映射" in error_msg:
            logger.warning("Model not configured", user_id=request.user_id, error=error_msg)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MODEL_NOT_CONFIGURED",
                    "message": error_msg,
                    "action_required": "请前往设置 -> LLM 服务商配置模型映射",
                },
            )
        logger.error("Runtime error", error=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.error("Chat endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/init", response_model=ChatInitResponse)
async def chat_init_endpoint(request: ChatInitRequest):
    """
    聊天初始化接口 - 后端决定返回历史记录或冷启动欢迎消息

    这是前端应该调用的唯一初始化接口：
    1. 后端检查是否有历史记录
    2. 如果有：返回历史消息列表
    3. 如果没有：返回冷启动欢迎消息 + UI 按钮

    前端只需要：调用此接口 → 显示返回的消息
    """
    try:
        logger.info(
            "Chat init endpoint called",
            user_id=request.user_id,
            project_id=request.project_id,
        )

        # 生成或复用 session_id 作为 thread_id
        thread_id = request.session_id or f"thread-{uuid.uuid4()}"

        # 从 checkpointer 查询历史记录
        from backend.graph.checkpointer import get_or_create_checkpointer, checkpointer_manager
        from langchain_core.messages import HumanMessage, AIMessage

        checkpointer, conn = await get_or_create_checkpointer()
        config = {"configurable": {"thread_id": thread_id}}

        def format_message_content(content) -> str:
            """将消息内容转换为友好格式，处理 action JSON 和 Master Router JSON"""
            if not content:
                return ""

            content_str = str(content).strip()

            # Action 到友好标签的映射（用于用户消息）
            action_labels = {
                "start_creation": "🎬 开始创作",
                "adapt_script": "📜 剧本改编",
                "create_storyboard": "🎨 分镜制作",
                "inspect_assets": "👤 资产探查",
                "random_plan": "🎲 随机方案",
                "select_genre": "🎯 选择赛道",
                "start_custom": "✨ 自由创作",
                "reset_genre": "🔙 重选背景",
                "select_plan": "📋 选择方案",
                "proceed_to_planning": "🤖 AI 自动选题",
                "cold_start": "🚀 启动助手",
            }

            # 1. 尝试解析 action JSON（用户消息）
            if content_str.startswith("{") and '"action"' in content_str:
                try:
                    parsed = json.loads(content_str)
                    action = parsed.get("action") if parsed else None
                    if action and isinstance(action, str):
                        label = action_labels.get(action) or action
                        # 如果有 genre，添加到标签
                        if parsed.get("payload", {}).get("genre"):
                            genre = parsed["payload"]["genre"]
                            if genre:
                                label = f"{label} ({genre})"
                        return label
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

            # 2. 尝试解析 Master Router JSON（AI 消息）
            # 格式: {"thought_process": "...", "target_agent": "...", "ui_feedback": "..."}
            if content_str.startswith("{") and (
                '"ui_feedback"' in content_str or '"thought_process"' in content_str
            ):
                try:
                    parsed = json.loads(content_str)
                    if parsed and isinstance(parsed, dict):
                        # 优先提取 ui_feedback
                        ui_feedback = parsed.get("ui_feedback")
                        if ui_feedback and isinstance(ui_feedback, str) and ui_feedback.strip():
                            return ui_feedback.strip()

                        # 如果没有 ui_feedback，尝试提取 thought_process
                        thought_process = parsed.get("thought_process")
                        if (
                            thought_process
                            and isinstance(thought_process, str)
                            and thought_process.strip()
                        ):
                            return thought_process.strip()
                except (json.JSONDecodeError, TypeError):
                    pass

            return content_str

        # 从 checkpointer 加载历史记录
        history_messages = []
        channel_values = None
        saved_ui_interaction = None

        try:
            if checkpointer:
                read_config = {"configurable": {"thread_id": thread_id}}
                checkpoint = await checkpointer.aget(read_config)

                if checkpoint:
                    channel_values = checkpoint.get("channel_values", {})

                    # 消息已经由 JsonPlusSerializer 自动反序列化为消息对象
                    # 不需要手动调用 messages_from_dict

                    # 获取 ui_interaction
                    saved_ui_interaction = channel_values.get("ui_interaction")

            # 检查是否成功加载了消息
            if channel_values and "messages" in channel_values:
                raw_messages = channel_values["messages"]

                # 转换 LangChain 消息为 ChatMessage 格式
                for idx, msg in enumerate(raw_messages):
                    # 处理 LangChain 消息对象
                    if isinstance(msg, (HumanMessage, AIMessage)):
                        role = "user" if isinstance(msg, HumanMessage) else "assistant"
                        formatted_content = format_message_content(str(msg.content))
                        
                        # 从消息的 additional_kwargs 中提取 ui_interaction
                        # 这是最可靠的来源，因为 SDUI 在创建时就嵌入了消息中
                        msg_ui_interaction = None
                        if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                            ui_data = msg.additional_kwargs.get('ui_interaction')
                            if ui_data:
                                try:
                                    if isinstance(ui_data, UIInteractionBlock):
                                        msg_ui_interaction = ui_data
                                    elif isinstance(ui_data, dict):
                                        msg_ui_interaction = UIInteractionBlock(**ui_data)
                                except Exception as e:
                                    logger.warning(f"Failed to parse ui_interaction from additional_kwargs: {e}")
                        
                    # 处理 dict 格式消息 (从 checkpoint 加载的原始格式)
                    elif isinstance(msg, dict):
                        msg_ui_interaction = None
                        # LangChain message_to_dict 格式: {"type": "ai", "data": {"content": "..."}}
                        if "type" in msg and "data" in msg:
                            msg_type = msg.get("type", "")
                            msg_data = msg.get("data", {})
                            role = "user" if msg_type == "human" else "assistant"
                            content = (
                                msg_data.get("content", "")
                                if isinstance(msg_data, dict)
                                else str(msg_data)
                            )
                            formatted_content = format_message_content(content)
                            
                            # 从 data.additional_kwargs 中提取 ui_interaction
                            if isinstance(msg_data, dict):
                                ui_data = msg_data.get('additional_kwargs', {}).get('ui_interaction')
                                if ui_data:
                                    try:
                                        if isinstance(ui_data, UIInteractionBlock):
                                            msg_ui_interaction = ui_data
                                        elif isinstance(ui_data, dict):
                                            msg_ui_interaction = UIInteractionBlock(**ui_data)
                                    except Exception:
                                        pass
                        # 简单格式: {"role": "assistant", "content": "..."}
                        elif "role" in msg:
                            role = msg.get("role", "assistant")
                            formatted_content = format_message_content(str(msg.get("content", "")))
                        else:
                            continue  # 无法识别的格式，跳过
                    else:
                        continue  # 无法识别的类型，跳过

                    # 如果消息本身没有 ui_interaction，尝试使用全局保存的 ui_interaction
                    # 但只为欢迎消息（第一条 AI 消息）附加
                    ui_interaction_data = msg_ui_interaction
                    if not ui_interaction_data and idx == 0 and role == "assistant" and saved_ui_interaction:
                        try:
                            if isinstance(saved_ui_interaction, UIInteractionBlock):
                                ui_interaction_data = saved_ui_interaction
                            elif isinstance(saved_ui_interaction, dict):
                                ui_interaction_data = UIInteractionBlock(**saved_ui_interaction)
                        except Exception as e:
                            logger.warning(f"Failed to parse saved_ui_interaction: {e}")

                    history_messages.append(
                        ChatMessage(
                            id=f"msg-{thread_id}-{idx}",
                            role=role,
                            content=formatted_content,
                            timestamp=datetime.now().isoformat(),
                            ui_interaction=ui_interaction_data,
                        )
                    )
        except Exception as e:
            logger.warning(
                "Failed to load history from checkpointer", thread_id=thread_id, error=str(e)
            )
        finally:
            # 归还数据库连接到连接池
            if conn:
                try:
                    await checkpointer_manager._pool.putconn(conn)
                except Exception as e:
                    logger.warning("Failed to return connection to pool", error=str(e))

        # 如果有历史记录，返回历史消息
        if history_messages:
            logger.info(
                "History found, returning chat history",
                thread_id=thread_id,
                message_count=len(history_messages),
            )
            return ChatInitResponse(
                thread_id=thread_id,
                messages=history_messages,
                is_cold_start=False,
                ui_interaction=None,
            )

        # 无历史记录，触发冷启动
        # 重要修复: 通过 LangGraph 正常流程运行冷启动，让 JsonPlusSerializer 自动处理消息序列化
        # 而不是手动保存 checkpoint，这样可以保证消息格式正确
        logger.info("No history found, triggering cold start via LangGraph")

        # 创建初始状态
        state = create_initial_state(
            user_id=request.user_id,
            project_id=request.project_id,
            thread_id=thread_id,
        )

        # 标记为冷启动，让图路由到 cold_start 节点
        state["is_cold_start"] = True
        state["messages"] = []  # 确保 messages 为空，触发冷启动路由

        # 通过 LangGraph 正常流程运行冷启动
        graph = await get_graph_for_request()
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # 运行图 - LangGraph 会自动保存 checkpoint，使用 JsonPlusSerializer 正确序列化消息
        result = await graph.ainvoke(state, config)

        # 从结果中获取欢迎消息和 UI interaction
        result_messages = result.get("messages", [])
        ui_interaction = result.get("ui_interaction")

        # 构建返回的消息列表
        welcome_messages = []
        for idx, msg in enumerate(result_messages):
            # 处理 LangChain 消息对象
            role = "assistant" if hasattr(msg, "type") and msg.type == "ai" else "user"
            content = msg.content if hasattr(msg, "content") else str(msg)
            
            # 构建 UI interaction block
            ui_block = None
            if idx == len(result_messages) - 1 and ui_interaction:
                try:
                    if hasattr(ui_interaction, "dict"):
                        ui_block = UIInteractionBlock(**ui_interaction.dict())
                    elif isinstance(ui_interaction, dict):
                        ui_block = UIInteractionBlock(**ui_interaction)
                except Exception as e:
                    logger.warning("Failed to parse ui_interaction", error=str(e))
            
            welcome_messages.append(
                ChatMessage(
                    id=f"welcome-{uuid.uuid4()}",
                    role=role,
                    content=content,
                    timestamp=datetime.now().isoformat(),
                    ui_interaction=ui_block,
                )
            )

        # 如果没有消息，创建一个默认欢迎消息
        if not welcome_messages:
            logger.warning("No messages from cold start, creating default welcome")
            welcome_messages.append(
                ChatMessage(
                    id=f"welcome-{uuid.uuid4()}",
                    role="assistant",
                    content="欢迎使用 AI 创作助手！请从下方选择功能入口。",
                    timestamp=datetime.now().isoformat(),
                    ui_interaction=None,
                )
            )

        logger.info(
            "Cold start completed via LangGraph",
            thread_id=thread_id,
            message_count=len(welcome_messages),
        )

        return ChatInitResponse(
            thread_id=thread_id,
            messages=welcome_messages,
            is_cold_start=True,
            ui_interaction=welcome_messages[-1].ui_interaction if welcome_messages else None,
        )

    except Exception as e:
        logger.error("Chat init endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@router.get("/health")
async def graph_health_check():
    """Health check for graph system"""
    return {
        "status": "ok",
        "component": "graph",
        "version": "4.1.0",
        "features": ["workflow_plan", "multi_step", "agent_registry", "cold_start", "chat_init"],
    }


@router.get("/messages/{thread_id}")
async def get_chat_messages(
    thread_id: str,
    user_id: str = Query(..., description="用户ID"),
):
    """
    获取聊天历史消息

    从 checkpointer 中获取指定 thread 的所有消息历史
    """
    try:
        from backend.graph.checkpointer import get_or_create_checkpointer, checkpointer_manager

        checkpointer, conn = await get_or_create_checkpointer()

        try:
            # 查询 checkpoint
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = await checkpointer.aget(config)

            messages = []
            if checkpoint:
                channel_values = checkpoint.get("channel_values", {})
                if channel_values and "messages" in channel_values:
                    raw_messages = channel_values["messages"]
                    # 转换消息格式 - 处理消息对象和 dict 格式
                    for msg in raw_messages:
                        if isinstance(msg, dict):
                            # dict 格式（兼容旧数据）
                            if "role" in msg:
                                messages.append(
                                    {"role": msg["role"], "content": msg.get("content", "")}
                                )
                            elif "type" in msg and "data" in msg:
                                msg_data = msg.get("data", {})
                                role = "user" if msg.get("type") == "human" else "assistant"
                                content = (
                                    msg_data.get("content", "")
                                    if isinstance(msg_data, dict)
                                    else str(msg_data)
                                )
                                messages.append({"role": role, "content": content})
                        elif hasattr(msg, "type") and hasattr(msg, "content"):
                            # LangChain 消息对象（新格式）
                            role = "user" if msg.type == "human" else "assistant"
                            messages.append({"role": role, "content": str(msg.content)})

            return {
                "thread_id": thread_id,
                "messages": messages,
                "has_history": len(messages) > 0,
            }
        except Exception as e:
            logger.warning("No history found for thread", thread_id=thread_id, error=str(e))
            return {
                "thread_id": thread_id,
                "messages": [],
                "has_history": False,
            }
        finally:
            # 归还数据库连接到连接池
            if conn:
                try:
                    await checkpointer_manager._pool.putconn(conn)
                except Exception as e:
                    logger.warning("Failed to return connection to pool", error=str(e))

    except Exception as e:
        logger.error("Failed to get chat messages", thread_id=thread_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {str(e)}")


@router.get("/chat")
async def chat_sse_endpoint(
    message: str = "",
    project_id: str = "",
    thread_id: str = "",
    user_id: str = "dev-user",
    node_id: str = "",
):
    """
    SSE chat endpoint for streaming responses.
    Supports EventSource from frontend.
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def event_generator():
        try:
            # 构建请求
            request = ChatRequest(
                user_id=user_id,
                project_id=project_id or None,
                session_id=thread_id or None,
                message=message if message else None,
            )

            # 创建初始状态
            state = create_initial_state(
                user_id=user_id,
                project_id=project_id or str(uuid.uuid4()),
                thread_id=thread_id or str(uuid.uuid4()),
            )

            # 冷启动检测 - 设置标志位让 LangGraph 处理
            is_cold_start = not message or is_cold_start_message(message)

            if is_cold_start:
                # 标记为冷启动，让 LangGraph 的 cold_start 节点处理
                state["is_cold_start"] = True
                # 不直接返回，继续走下面的 LangGraph 流程
            else:
                state["is_cold_start"] = False

            # 正常流程
            if message:
                from langchain_core.messages import HumanMessage

                state["messages"] = [HumanMessage(content=message)]
                state["user_input"] = message

            # 获取 graph
            graph = await get_graph_for_request()

            # 准备 config
            config = {
                "configurable": {
                    "thread_id": thread_id or str(uuid.uuid4()),
                }
            }

            # 发送节点开始事件
            yield f"data: {json.dumps({'type': 'node_start', 'node': 'router', 'desc': '正在分析您的请求...'})}\n\n"
            await asyncio.sleep(0.1)

            # 运行 graph
            result = await graph.ainvoke(state, config)

            # 发送节点结束事件
            yield f"data: {json.dumps({'type': 'node_end', 'node': 'router'})}\n\n"
            await asyncio.sleep(0.1)

            # 提取响应内容
            messages = result.get("messages", [])
            ai_content = ""

            if messages:
                for msg in reversed(messages):
                    if hasattr(msg, "content") and msg.content:
                        ai_content = msg.content
                        break

            # 清理 AI 内容（提取 ui_feedback 或 thought_process）
            def extract_display_content(content: str) -> str:
                """从 Master Router JSON 中提取可显示内容"""
                if not content or not isinstance(content, str):
                    return content or ""

                content = content.strip()
                if content.startswith("{") and (
                    '"ui_feedback"' in content or '"thought_process"' in content
                ):
                    try:
                        parsed = json.loads(content)
                        if parsed and isinstance(parsed, dict):
                            # 优先提取 ui_feedback
                            ui_feedback = parsed.get("ui_feedback")
                            if ui_feedback and isinstance(ui_feedback, str) and ui_feedback.strip():
                                return ui_feedback.strip()

                            # 如果没有 ui_feedback，尝试提取 thought_process
                            thought_process = parsed.get("thought_process")
                            if (
                                thought_process
                                and isinstance(thought_process, str)
                                and thought_process.strip()
                            ):
                                return thought_process.strip()
                    except (json.JSONDecodeError, TypeError):
                        pass

                return content

            display_content = extract_display_content(ai_content)

            # 分词发送（模拟流式输出）
            if display_content:
                words = display_content.split()
                for i, word in enumerate(words):
                    yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
                    if i < len(words) - 1:
                        await asyncio.sleep(0.05)

            # 发送完成事件
            content_status = get_content_status(result)
            yield f"data: {
                json.dumps(
                    {
                        'type': 'done',
                        'state': {
                            'messages': [{'role': 'ai', 'content': ai_content}]
                            if ai_content
                            else [],
                            'thread_id': thread_id,
                            'content_status': content_status,
                        },
                    }
                )
            }\n\n"

        except Exception as e:
            logger.error("SSE chat error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
