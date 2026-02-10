"""
Skeleton Builder Agent - Level 3 大纲架构师

使用 create_react_agent 创建，负责生成故事骨架结构。
调用 TensionService 生成张力曲线。
支持自主调用题材库 Tools 获取题材指导。
"""

from pathlib import Path
from typing import Dict, Optional
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType
from backend.services.tension_service import generate_tension_curve
from backend.skills.theme_library import (
    load_genre_context,
    search_elements_by_effectiveness,
    get_hook_templates_by_type,
    analyze_genre_compatibility,
)
import structlog

logger = structlog.get_logger(__name__)


def dispatch_progress_event(stage: str, progress: int):
    """发送进度事件（用于前端显示）"""
    try:
        from langchain_core.callbacks import dispatch_custom_event

        dispatch_custom_event("skeleton_progress", {"stage": stage, "progress": progress})
    except Exception:
        # 如果无法发送事件（比如不在回调上下文中），静默忽略
        pass


async def _load_skeleton_builder_prompt(
    selected_plan: Dict,
    user_config: Dict,
    market_report: Optional[Dict] = None,
    chapter_mapping: Optional[Dict] = None,
) -> str:
    """从文件加载 Skeleton Builder 的 System Prompt - 增强版"""
    import json

    prompt_path = Path(__file__).parent.parent / "prompts" / "3_Skeleton_Builder.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 基础变量注入
        content = content.replace("{total_episodes}", str(user_config.get("total_episodes", 80)))
        content = content.replace("{episode_duration}", str(user_config.get("episode_duration", 2)))
        content = content.replace("{genre}", user_config.get("genre", "revenge"))
        content = content.replace("{setting}", user_config.get("setting", "modern"))
        content = content.replace("{ending}", user_config.get("ending_type", "HE"))
        content = content.replace("{selected_plan}", str(selected_plan))
        content = content.replace("{user_config}", str(user_config))

        # 新增：章节映射变量注入
        if chapter_mapping:
            content = content.replace(
                "{total_words}", str(chapter_mapping.get("estimated_words", 800000))
            )
            content = content.replace(
                "{total_chapters}", str(chapter_mapping.get("total_chapters", 61))
            )
            content = content.replace(
                "{paywall_chapter}", str(chapter_mapping.get("paywall_chapter", 12))
            )

            # 付费卡点集数列表转字符串
            paywall_eps = chapter_mapping.get("paywall_episodes", [12])
            content = content.replace("{paywall_episodes}", str(paywall_eps))

            # 章节映射表转JSON字符串
            chapters = chapter_mapping.get("chapters", [])
            content = content.replace(
                "{chapter_map}", json.dumps(chapters, ensure_ascii=False, indent=2)
            )

            content = content.replace("{ratio}", str(chapter_mapping.get("adaptation_ratio", 1.31)))
            content = content.replace(
                "{total_drama_minutes}",
                str(user_config.get("total_episodes", 80) * user_config.get("episode_duration", 2)),
            )

            # 关键节点
            key_points = chapter_mapping.get("key_points", {})
            content = content.replace("{opening_end}", str(key_points.get("opening_end", 3)))
            content = content.replace(
                "{development_start}", str(key_points.get("development_start", 4))
            )
            content = content.replace(
                "{development_end}", str(key_points.get("development_end", 45))
            )
            content = content.replace(
                "{midpoint_chapter}", str(key_points.get("midpoint_chapter", 31))
            )
            content = content.replace("{climax_chapter}", str(key_points.get("climax_chapter", 53)))
            content = content.replace(
                "{final_chapter}", str(chapter_mapping.get("total_chapters", 61))
            )

            # 付费卡点位置百分比
            paywall_pos = round(
                chapter_mapping.get("paywall_chapter", 12)
                / chapter_mapping.get("total_chapters", 61)
                * 100,
                1,
            )
            content = content.replace("{paywall_position}", str(paywall_pos))
        else:
            # 默认值
            content = content.replace("{total_words}", "800000")
            content = content.replace("{total_chapters}", "61")
            content = content.replace("{paywall_chapter}", "12")
            content = content.replace("{paywall_episodes}", "[12]")
            content = content.replace("{chapter_map}", "[]")
            content = content.replace("{ratio}", "1.31")
            content = content.replace("{total_drama_minutes}", "160")
            content = content.replace("{opening_end}", "3")
            content = content.replace("{development_start}", "4")
            content = content.replace("{development_end}", "45")
            content = content.replace("{midpoint_chapter}", "31")
            content = content.replace("{climax_chapter}", "53")
            content = content.replace("{final_chapter}", "61")
            content = content.replace("{paywall_position}", "20")

        if market_report:
            content = content.replace("{market_report}", str(market_report))
        else:
            content = content.replace("{market_report}", "未提供")

        logger.info(
            "Skeleton Builder Prompt loaded",
            prompt_length=len(content),
            has_chapter_mapping=bool(chapter_mapping),
        )
        return content

    except Exception as e:
        logger.error("Failed to load Skeleton Builder prompt", error=str(e))
        # Fallback prompt
        return "You are a skeleton builder agent. Generate a story outline based on the input."


async def create_skeleton_builder_agent(
    user_id: str,
    project_id: str,
    selected_plan: Dict,
    user_config: Dict,
    market_report: Optional[Dict] = None,
    chapter_mapping: Optional[Dict] = None,
):
    """
    创建 Skeleton Builder Agent - 增强版

    Args:
        user_id: 用户ID
        project_id: 项目ID
        selected_plan: 选中的故事方案
        user_config: 用户配置（包含total_episodes等）
        market_report: 市场分析报告（可选）
        chapter_mapping: 章节映射配置（可选，包含total_chapters等）

    Returns:
        create_react_agent 返回的 Compiled Graph
    """
    logger.info(
        "Creating Skeleton Builder Agent",
        user_id=user_id,
        project_id=project_id,
        title=selected_plan.get("title", "Unknown"),
        total_episodes=user_config.get("total_episodes", 80),
        total_chapters=chapter_mapping.get("total_chapters") if chapter_mapping else None,
    )

    # 加载并格式化 Prompt（传递章节映射）
    system_prompt = await _load_skeleton_builder_prompt(
        selected_plan=selected_plan,
        user_config=user_config,
        market_report=market_report,
        chapter_mapping=chapter_mapping,
    )

    # 获取模型（骨架构建使用 SKELETON_BUILDER TaskType）
    model_router = get_model_router()
    model = await model_router.get_model(
        user_id=user_id, task_type=TaskType.SKELETON_BUILDER, project_id=project_id
    )

    # 创建 Agent（Skeleton Builder 可以自主调用题材库 Tools）
    # 这些 Tools 让 Agent 能够根据查询题材指导、爆款元素、钩子模板等
    tools = [
        load_genre_context,  # 加载题材完整上下文（核心公式、避雷清单等）
        search_elements_by_effectiveness,  # 搜索高效果爆款元素
        get_hook_templates_by_type,  # 获取钩子模板（前3秒留存）
        analyze_genre_compatibility,  # 分析题材兼容性（双题材时）
    ]

    agent = create_react_agent(
        model=model,
        tools=tools,  # Agent 自主决定何时调用这些 Tools
        prompt=system_prompt,
    )

    logger.info("Skeleton Builder Agent created successfully")
    return agent


async def generate_tension_curve_for_skeleton(
    total_episodes: int, curve_type: str = "standard"
) -> Dict:
    """
    为大纲生成张力曲线

    Args:
        total_episodes: 总集数
        curve_type: 曲线类型（standard/fast/slow）

    Returns:
        张力曲线数据
    """
    logger.info(
        "Generating tension curve",
        total_episodes=total_episodes,
        curve_type=curve_type,
    )

    return generate_tension_curve(total_episodes=total_episodes, curve_type=curve_type)


# Node wrapper for LangGraph
async def skeleton_builder_node(state: Dict) -> Dict:
    """
    Skeleton Builder Node 包装器 - 分批生成版

    支持分批生成大纲，每次只生成一个批次的章节。
    用于直接添加到 LangGraph 中作为 Node。
    """
    from backend.schemas.agent_state import AgentState
    from langchain_core.messages import HumanMessage

    user_id = state.get("user_id")
    project_id = state.get("project_id")
    selected_plan = state.get("selected_plan") or {}
    user_config = state.get("user_config") or {}
    market_report = state.get("market_report")
    messages = state.get("messages") or []
    retry_count = state.get("retry_count", 0)

    # 从 state 获取章节映射
    chapter_mapping = state.get("chapter_mapping") or state.get("inferred_config") or {}
    total_chapters = (
        chapter_mapping.get("total_chapters", 60) if isinstance(chapter_mapping, dict) else 60
    )

    # ===== 分批生成逻辑 =====
    generation_batches = state.get("generation_batches", [])
    current_batch_index = state.get("current_batch_index", 0)
    accumulated_content = state.get("accumulated_content", "")
    total_batches = state.get("total_batches", len(generation_batches) if generation_batches else 1)

    # 获取当前批次信息
    current_batch = None
    batch_start = 1
    batch_end = total_chapters
    batch_type = "full"
    batch_description = "完整大纲"

    if generation_batches and current_batch_index < len(generation_batches):
        current_batch = generation_batches[current_batch_index]
        batch_range = current_batch.get("range", (1, total_chapters))
        batch_start = batch_range[0]
        batch_end = batch_range[1]
        batch_type = current_batch.get("type", "full")
        batch_description = current_batch.get("description", f"第{batch_start}-{batch_end}章")

    is_first_batch = current_batch_index == 0
    is_last_batch = current_batch_index >= total_batches - 1

    logger.info(
        "Batch generation info",
        current_batch_index=current_batch_index,
        total_batches=total_batches,
        batch_range=f"{batch_start}-{batch_end}",
        batch_type=batch_type,
        is_first_batch=is_first_batch,
        is_last_batch=is_last_batch,
    )

    # ===== 构造分批生成指令 =====
    # System Prompt 保持使用 3_Skeleton_Builder.md 不变
    # 只通过附加的 User Prompt 控制本次生成的范围

    if is_first_batch:
        # 第一批：生成完整骨架（章节清单）
        batch_instruction = f"""【第1批：完整骨架 - 章节清单模式】

本次生成任务：构建完整的故事大纲骨架（不包含详细章节内容）

**重要说明**：
- 本次只生成"骨架"，不展开详细章节内容
- 骨架将作为后续批次的指导，必须完整且一致
- 后续批次（第2-5批）将基于此骨架展开详细内容

**需要输出的完整部分**：

1. 一、元数据（Metadata）- 完整项目信息

2. 二、核心设定（Core Setting）- 完整世界观架构

3. 三、人物体系（Character System）- **完整且详细**
   - 女主：完整人物小传 + **完整成长弧光**（从Chapter 1到Chapter {total_chapters}）
   - 男主：完整人物小传 + **完整成长弧光**（从Chapter 1到Chapter {total_chapters}）
   - 反派1号、反派2号、辅助角色：基础档案 + 人物关系 + 在故事中的作用
   - 人物关系图谱
   - 人物成长对照表（Chapter 1, 付费点, 中点, Chapter {total_chapters}）

4. 四、情节架构（Plot Architecture）- **完整节拍表**
   - 核心梗概（超短版、短版、标准版、详细版）
   - **完整情节节拍表**：列出从"开场画面"到"结局"的所有节拍
     * 开场画面（Chapter 1）
     * 主题呈现（Chapter 1-2）
     * 布局（Chapter 3-5）
     * 催化剂（Chapter 6）
     * ...一直到结局（Chapter {total_chapters}）
   - 张力曲线设计

5. 五、章节清单（Chapter List）- **所有{total_chapters}章的清单**
   每章格式（简洁，不展开）：
   ### Chapter X: [标题]
   - **核心任务**：[本章必须完成的任务]
   - **核心冲突**：[具体冲突]
   - **一句话摘要**：[50字内概括本章内容]
   - **钩子**：[章节结尾的钩子，用于吸引读者继续]
   - **预计字数**：[根据阶段：开篇9000/发展10000/高潮12000/结局9000]
   - **对应短剧**：[第X-Y集]
   - **故事阶段**：[开篇/发展/高潮/结局]

**约束**：
- 人物成长弧光必须覆盖全部{total_chapters}章
- 节拍表必须列出所有节拍（Chapter 1到Chapter {total_chapters}）
- 章节清单必须列出所有{total_chapters}章（每章只需标题+核心任务+摘要+钩子）
- 不输出详细章节内容（如场景清单、情绪曲线等），留到后续批次展开

**输出格式**：严格按照 System Prompt 定义的格式输出
"""
    elif is_last_batch:
        # 最后一批：生成最后N章 + 映射表 + UI JSON
        batch_instruction = f"""【第{current_batch_index + 1}批：最后部分 - Chapter {batch_start}-{batch_end} + 映射表 + UI数据】

本次生成任务：生成最后一批章节 + 完整映射表 + UI数据

**基于已生成的故事骨架和前几批详细内容**：
- 所有元数据、核心设定、人物体系已在第1批生成
- Chapter 1-{batch_start - 1} 的详细内容已在前几批生成

**需要输出的部分**：

1. 五、章节大纲（续）- **Chapter {batch_start} 到 Chapter {batch_end}**
   - Chapter {batch_end} 是大结局，必须收束所有伏笔
   - 高潮章节需要详细描写，不能简化

2. 六、短剧映射表（Drama Mapping）- **完整映射表**
   - 列出从第1集到第80集的所有映射
   - 基于所有章节的实际内容生成准确的场景摘要

3. 七、创作指导（Writing Guidelines）- 完整

4. 八、UI交互数据 - **完整JSON**
   - 包含准确的字数统计（基于所有已生成章节）
   - 包含所有章节的映射信息

**约束**：
- 必须收束所有伏笔
- 映射表不能省略，必须列出所有80集
- UI JSON 中的 chapter_map 必须列出所有 {total_chapters} 个章节

**输出格式**：严格按照 System Prompt 定义的格式输出
"""
    else:
        # 中间批次：基于骨架展开详细章节
        batch_instruction = f"""【第{current_batch_index + 1}批：展开 Chapter {batch_start}-{batch_end}】

本次生成任务：基于故事骨架，展开 Chapter {batch_start} 到 Chapter {batch_end} 的详细内容

**需要基于的故事骨架**（必须在所有批次中保持一致）：
- 第1批生成的完整人物设定和成长弧光
- 第1批生成的完整节拍表
- 第1批生成的章节清单（作为每章的指导）

**本次展开详细内容**：
Chapter {batch_start} 到 Chapter {batch_end}

每章必须包含的详细要素：
1. **元数据**：字数、对应短剧、故事阶段、是否付费卡点
2. **核心要素**：任务、冲突、抉择
3. **节奏设计**：类型、钩子位置、钩子内容
4. **情绪曲线**：起始值 → 变化 → 结束值
5. **场景清单**：3-5个场景（地点、核心事件、作用）
6. **伏笔系统**：新埋设 + 计划回收

**约束**：
- 严格遵循骨架中的人物设定
- 严格实现骨架中规划的节拍
- 保持与前面章节的连贯性
- 继续发展伏笔和角色成长

**输出格式**：严格按照 System Prompt 定义的章节格式输出
"""

    # ===== 构建完整消息（骨架 + 上下文 + 本次指令）=====
    def build_context_message(is_first, accumulated, instruction, batch_idx):
        """构建包含上下文的消息"""
        if is_first:
            # 第一批：只有骨架指令，没有上下文
            return instruction

        # 中间批次和最后一批：添加上下文
        # 提取最后3000字作为上下文（避免Token超限）
        context_text = accumulated[-3000:] if accumulated else ""

        return f"""【上下文】（基于已生成内容）
{context_text}

---

【本次任务指令】
{instruction}"""

    # 重试时简化消息
    if retry_count > 0:
        logger.info(
            "Retry detected, using simplified batch prompt",
            retry_count=retry_count,
            batch_index=current_batch_index,
        )
        messages = [HumanMessage(content=f"【重试第{retry_count}次】\n\n" + batch_instruction)]
    else:
        # 首次生成：构建完整消息（包含上下文）
        full_message = build_context_message(
            is_first_batch,
            accumulated_content,
            batch_instruction,
            current_batch_index,
        )
        messages = [HumanMessage(content=full_message)]

    # 过滤掉空消息，避免 Gemini 400 错误
    messages = [msg for msg in messages if hasattr(msg, "content") and msg.content]

    logger.info(
        "Executing Skeleton Builder Node",
        user_id=user_id,
        message_count=len(messages),
        has_chapter_mapping=bool(chapter_mapping),
        total_chapters=total_chapters,
        current_batch=f"{batch_start}-{batch_end}",
        batch_index=f"{current_batch_index + 1}/{total_batches}",
    )

    try:
        # 发送进度：开始创建 Agent
        dispatch_progress_event("准备大纲生成环境...", 5)

        # 创建 Agent（传递章节映射）
        agent = await create_skeleton_builder_agent(
            user_id=user_id,
            project_id=project_id,
            selected_plan=selected_plan,
            user_config=user_config,
            market_report=market_report,
            chapter_mapping=chapter_mapping if isinstance(chapter_mapping, dict) else None,
        )

        # 发送进度：Agent 创建完成，开始生成
        dispatch_progress_event("AI 正在构思故事结构...", 10)

        # 执行 Agent
        result = await agent.ainvoke({"messages": messages})

        # 记录原始结果以供调试
        logger.info("Agent raw result", result_keys=list(result.keys()))

        # 解析结果
        output_messages = result.get("messages", [])

        # 详细记录所有消息类型
        for i, msg in enumerate(output_messages):
            logger.info(
                f"Message {i}",
                type=type(msg).__name__,
                content_len=len(msg.content) if hasattr(msg, "content") else 0,
            )

        # 从 AI 消息中提取生成的内容作为 skeleton_content
        # 策略：找到内容最长的 AIMessage（因为大纲内容应该是最长的）
        skeleton_content = ""
        max_content_length = 0

        def extract_text_from_content(content) -> str:
            """将 content 转换为字符串（处理 list/dict 类型）"""
            if content is None:
                return ""
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Gemini 多部分响应：提取所有文本部分
                text_parts = []
                for part in content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif hasattr(part, "text"):
                        text_parts.append(part.text)
                return "\n".join(text_parts)
            if isinstance(content, dict):
                if "text" in content:
                    return content["text"]
                return str(content)
            return str(content)

        if output_messages:
            # 遍历所有消息，找到内容最长的 AIMessage
            for i, msg in enumerate(output_messages):
                msg_type = type(msg).__name__
                if msg_type == "AIMessage" and hasattr(msg, "content"):
                    # 转换 content 为字符串
                    content_str = extract_text_from_content(msg.content)
                    content_len = len(content_str) if content_str else 0

                    logger.debug(
                        f"Checking AIMessage {i}",
                        content_length=content_len,
                        has_tool_calls=bool(getattr(msg, "tool_calls", None)),
                    )

                    # 只考虑没有 tool_calls 的消息，或者内容足够长的消息
                    has_tool_calls = bool(getattr(msg, "tool_calls", None))
                    if content_len > max_content_length and (
                        not has_tool_calls or content_len > 500
                    ):
                        max_content_length = content_len
                        skeleton_content = content_str
                        logger.info(
                            f"Found better AIMessage at index {i}",
                            content_length=content_len,
                        )

            # 如果没有找到 AIMessage，尝试使用最后一个消息
            if not skeleton_content:
                last_message = output_messages[-1]
                if hasattr(last_message, "content"):
                    skeleton_content = extract_text_from_content(last_message.content)
                    logger.warning(
                        "Using last message as fallback",
                        msg_type=type(last_message).__name__,
                        content_length=len(skeleton_content) if skeleton_content else 0,
                    )

        # 生成张力曲线（只在第一批或最后一批生成）
        tension_curve = None
        if is_first_batch or is_last_batch:
            total_episodes = user_config.get("total_episodes", 80)
            tension_curve = await generate_tension_curve_for_skeleton(total_episodes)

        # ===== 累积内容 =====
        # 将当前批次的内容追加到累积内容中
        new_accumulated_content = accumulated_content
        if skeleton_content:
            if accumulated_content:
                # 添加分隔符，便于后续合并
                new_accumulated_content = accumulated_content + "\n\n---\n\n" + skeleton_content
            else:
                new_accumulated_content = skeleton_content

        # ===== 更新批次索引 =====
        new_batch_index = current_batch_index + 1
        batch_completed = new_batch_index >= total_batches

        logger.info(
            "Skeleton Builder Node completed",
            output_messages=len(output_messages),
            content_length=len(skeleton_content),
            batch_index=f"{current_batch_index + 1}/{total_batches}",
            batch_completed=batch_completed,
            accumulated_length=len(new_accumulated_content),
        )

        return {
            "messages": output_messages,
            "skeleton_content": new_accumulated_content if batch_completed else skeleton_content,
            "tension_curve": tension_curve,
            "last_successful_node": "skeleton_builder",
            # 分批生成状态更新
            "current_batch_index": new_batch_index,
            "accumulated_content": new_accumulated_content,
            "batch_completed": batch_completed,
            "current_batch_range": f"{batch_start}-{batch_end}",
        }

    except Exception as e:
        logger.error("Skeleton Builder Node failed", error=str(e))
        return {
            "error": f"大纲生成失败: {str(e)}",
            "last_successful_node": "skeleton_builder_error",
        }
