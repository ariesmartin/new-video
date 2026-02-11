"""
LangGraph Agent State Schema

定义 LangGraph 核心状态类型，这是整个智能体系统的 "DNA"。
所有 Agent Node 共享此状态，通过 Reducer 进行合并更新。

严格遵循系统架构文档 Section 3.1 的定义。
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# 导入 SDUI 协议
from backend.schemas.common import UIInteractionBlock


# ===== Reducer for UI Interaction =====
def ui_interaction_reducer(
    existing: UIInteractionBlock | dict | None, new: UIInteractionBlock | dict | None
) -> UIInteractionBlock | dict | None:
    """
    Reducer for ui_interaction field.

    Strategy:
    - If new value is provided, use it (allows clearing with None)
    - If new value is None, keep existing value (preserves UI state across nodes)
    - This ensures buttons remain visible until user interacts with them

    Args:
        existing: Current ui_interaction value from state
        new: New ui_interaction value from node output

    Returns:
        Merged ui_interaction value
    """
    # If new value is explicitly provided (including None), use it
    if new is not None:
        return new
    # If new is None but existing has value, preserve existing
    # This prevents UI from disappearing between nodes
    if existing is not None:
        return existing
    return None


class StageType(str, Enum):
    """当前流程阶段"""

    LEVEL_1 = "L1"  # 参数收集
    LEVEL_2 = "L2"  # 故事方案生成
    LEVEL_3 = "L3"  # 骨架构建
    MODULE_A = "ModA"  # 小说生成
    MODULE_B = "ModB"  # 剧本提取
    MODULE_C = "ModC"  # 分镜拆分
    MODULE_X = "ModX"  # 资产探查
    COMPLETED = "Completed"  # 流程完成
    ERROR = "Error"  # 错误状态


class ApprovalStatus(str, Enum):
    """用户审批状态"""

    PENDING = "PENDING"  # 等待用户确认
    APPROVED = "APPROVED"  # 用户批准
    REJECTED = "REJECTED"  # 用户拒绝/需修改


class CharacterProfile(TypedDict, total=False):
    """角色设定 (Character Bible)"""

    character_id: str
    name: str
    appearance: str  # 外貌描述 (为画图准备)
    personality_flaw: str  # 性格缺陷
    core_desire: str  # 核心欲望
    speech_pattern: str  # 说话方式
    b_story: str | None  # B故事暗线 (仅配角)


class EpisodeOutline(TypedDict, total=False):
    """分集大纲 (Beat Sheet)"""

    episode_id: str
    episode_number: int
    title: str
    summary: str  # 剧情摘要 (100字内)
    key_scenes: list[str]  # 关键场景 (3-5个)
    cliffhanger: str  # 悬念结尾


class StoryPlan(TypedDict, total=False):
    """故事方案 (Level 2 生成)"""

    plan_id: str
    title: str  # 剧名
    logline: str  # 一句话梗概
    protagonist: dict  # 男主人设简报
    deuteragonist: dict  # 女主人设简报
    core_appeal: list[str]  # 核心爽点
    anti_cliche_applied: bool  # 是否触发了反套路雷达


class SceneData(TypedDict, total=False):
    """结构化场景数据"""

    scene_id: str
    scene_number: str  # S01, S02, ...
    location: str  # 场景头: [室内/室外] [地点] [时间]
    visual_description: str  # 环境氛围描述
    elements: list[dict]  # 对话(D), 动作(A), 旁白(V), 音效(S)


class ShotData(TypedDict, total=False):
    """分镜数据"""

    shot_id: str
    shot_number: str  # S01-01, S01-02, ...
    shot_type: str  # 特写/中景/全景
    camera_movement: str  # 固定/推/拉/摇/移
    subject: str  # 画面主体
    action: str  # 主体动作
    visual_description: str  # 光影、色彩、构图
    nano_banana_prompt: str  # 英文 Prompt


class HeroState(TypedDict, total=False):
    """主角状态追踪 (Character Arc Tracker)"""

    current_phase: str  # 英雄之旅阶段
    emotional_state: str  # 当前情绪
    growth_percentage: float  # 成长曲线 (0-100%)
    last_updated_episode: int


class EmotionPoint(TypedDict, total=False):
    """情绪曲线数据点"""

    offset: float  # 进度 (0.0 - 1.0)
    valence: float  # 效价 (-10 ~ 10)
    arousal: float  # 唤醒度 (0 ~ 10)
    tag: str  # 情绪标签 (e.g., "Anxiety")
    beat_id: str | None  # 关联的节拍 ID


class AssetPrompt(TypedDict, total=False):
    """设定图 Prompt 数据"""

    asset_id: str
    asset_type: str  # char/prop/loc
    visual_description: str  # 中文视觉描述
    nano_banana_prompt: str  # 英文生成 Prompt


class UserConfig(TypedDict, total=False):
    """用户配置 (Level 1 收集)"""

    genre: str  # 题材赛道
    sub_tags: list[str]  # 细分标签
    tone: list[str]  # 内容调性
    target_word_count: int  # 单集字数
    total_episodes: int  # 目标集数
    ending_type: str  # HE/BE/OE
    aspect_ratio: str  # 9:16 或 16:9
    drawing_type: str  # 绘图类型
    visual_style: str  # 画面风格
    style_dna: str | None  # 文风 DNA (用户克隆)
    avoid_tags: list[str]  # 排除标签


def merge_user_config(existing: UserConfig | None, new: UserConfig | None) -> UserConfig:
    """
    合并用户配置

    策略：
    - 如果 new 有值，更新对应的字段
    - 保持 existing 中未被覆盖的字段
    - 确保配置不会丢失
    """
    if existing is None:
        return new if new is not None else UserConfig()

    if new is None:
        return existing

    # 合并两个字典，new 的值优先
    result = dict(existing)
    result.update({k: v for k, v in new.items() if v is not None})

    return UserConfig(**result)


class WorkflowStep(TypedDict, total=False):
    """工作流步骤定义 - 用于多步骤工作流规划"""

    step_id: str  # 步骤唯一 ID (如 "step_1", "step_2")
    agent: str  # Agent 名称 (如 "Storyboard_Director")
    task: str  # 任务描述 (如 "将第一章剧本转换为分镜")
    depends_on: list[str]  # 依赖的步骤 ID 列表
    input_mapping: dict[str, str]  # 输入映射: {参数名: state字段名}
    output_mapping: str  # 输出写入的 state 字段名


class WorkflowPlan(TypedDict, total=False):
    """工作流计划 - Master Router 输出"""

    intent_analysis: str  # 意图分析文本
    workflow_plan: list[WorkflowStep]  # 步骤列表
    ui_feedback: str  # 用户反馈文本
    estimated_steps: int  # 预计步骤数


class AgentState(TypedDict, total=False):
    """
    LangGraph 全局状态定义

    这是所有 Agent 节点共享的状态字典。
    使用 TypedDict 确保类型安全，支持 IDE 自动补全。

    Architecture Reference: 系统架构文档.md Section 3.1
    """

    # ===== Core Identifiers =====
    user_id: str
    project_id: str
    thread_id: str  # LangGraph 会话 ID (用于 Checkpointing)

    # ===== Message History (LangGraph Standard) =====
    # 使用 add_messages Reducer 自动合并消息
    messages: Annotated[list[BaseMessage], add_messages]

    # ===== Level 1: User Configuration =====
    # 使用 Annotated 和 merge_user_config reducer 确保配置正确合并
    user_config: Annotated[UserConfig, merge_user_config]
    market_report: dict | None  # Market Analyst 生成的市场分析报告

    # ===== Level 2: Story Planning =====
    # ✅ GAP-6 修复：story_plans 实际存储的是 AI 输出的 markdown 字符串
    # main_graph.py:1069 赋值为 _content_to_string(messages[-1].content)
    story_plans: str | list[StoryPlan]  # markdown 文本或结构化方案列表
    selected_plan: StoryPlan | None  # 用户选中的方案
    fusion_request: dict | None  # 方案融合请求

    # ===== Level 3: Skeleton Building =====
    character_bible: list[CharacterProfile]  # 角色圣经
    beat_sheet: list[EpisodeOutline]  # 分集大纲
    chapter_mapping: dict | None  # 章节映射（章节数、付费卡点等）
    inferred_config: dict | None  # 推断配置（总章节数、总字数估算等）
    skeleton_content: str | None  # 大纲内容（Skeleton Builder 生成）

    # ===== Level 3: Skeleton Building - Batch Generation (V4.2 新增) =====
    generation_batches: (
        list[dict] | None
    )  # 分批生成策略列表 [{"range": (1, 13), "type": "opening", "description": "..."}]
    current_batch_index: int  # 当前批次索引 (0-based)
    total_batches: int  # 总批次数
    accumulated_content: str | None  # 累积的所有批次内容
    batch_completed: bool  # 所有批次是否已完成
    current_batch_range: str | None  # 当前批次范围描述 (如 "1-13")
    needs_next_batch: bool  # 是否需要继续下一批（用于前端交互）
    auto_batch_mode: bool  # 自动分批模式: True=自动连续生成, False=每批暂停等待用户确认

    # ===== Module A: Novel Generation =====
    current_episode: int  # 当前生成的集数
    novel_content: str  # 当前集小说内容
    novel_archive: dict[int, str]  # 归档: {episode_num: content}

    # ===== Module B: Script Extraction =====
    script: list[SceneData]  # 结构化剧本
    narrative_mode: str  # 叙事模式: dialog/voiceover/hybrid

    # ===== Module C: Storyboard =====
    storyboard: list[ShotData]  # 分镜列表
    generation_model: str  # sora/vidu

    # ===== Module X: Asset Inspector =====
    asset_manifest: dict  # 资产清单 (角色/场景/道具)
    asset_prompts: list[AssetPrompt]  # 设定图提示词列表

    # ===== Module A+: Analysis Lab =====
    emotion_curve: list[EmotionPoint]  # 情绪曲线数据 (Visual Emotion Curve)
    surgery_result: str  # 定向修文结果 (Targeted Surgery)

    # ===== Long-Term Memory (Logic Guardian) =====
    hero_state: HeroState  # 主角弧光追踪
    unresolved_mysteries: list[str]  # 未填坑的伏笔列表
    history_summary: str  # 滚动剧情摘要 (Rolling Context)

    # ===== Control Flags =====
    current_stage: StageType  # 当前阶段
    approval_status: ApprovalStatus  # 用户审批状态
    human_feedback: str  # 用户修改意见
    revision_count: int  # 修改次数 (防止无限循环, max=3)
    quality_score: float  # Editor Agent 评分
    validation_status: str  # 输入验证状态: "complete" | "incomplete"

    # ===== Skill Scores (详细评分) =====
    skill_scores: dict[str, float]  # {"S_Engagement": 85.0, "S_Logic": 90.0, ...}

    # ===== Level 3: Skeleton Building (Quality Control) =====
    review_report: dict | None  # Editor Agent 审阅报告
    refine_log: dict | None  # Refiner Agent 修复日志

    # ===== Server-Driven UI (SDUI) =====
    # Agent 返回的 UI 交互指令，前端解析后渲染为可交互组件
    # 使用 Annotated 确保 LangGraph 正确处理和保存此字段
    ui_interaction: Annotated[UIInteractionBlock | dict | None, ui_interaction_reducer]

    # ===== Routing Control =====
    # 双路由机制控制标志
    use_master_router: bool  # 是否强制使用智能路由 (Master Router)
    routed_agent: str | None  # AI 解析出的目标 Agent 名称
    routed_function: str | None  # AI 解析出的函数名称
    routed_parameters: dict | None  # AI 解析出的函数参数

    # ===== Workflow Planning (V4.1 新增) =====
    # 多步骤工作流规划
    workflow_plan: list[WorkflowStep] | None  # 工作流步骤列表
    current_step_idx: int  # 当前执行到第几步
    workflow_results: dict[str, Any]  # 各步骤的中间结果 {step_id: output}
    intent_analysis: str | None  # 意图分析文本

    # ===== Error Handling =====
    error_message: str | None  # 错误信息
    last_successful_node: str | None  # 最后成功执行的节点

    # ===== Timestamps =====
    created_at: datetime | None
    updated_at: datetime | None

    # ===== UI Feedback (V3新增) =====
    ui_feedback: str | None  # 用户可读的反馈文本


# ===== Reducer Functions =====
# LangGraph 使用 Reducer 合并并发 Node 的输出


def merge_novel_archive(
    existing: dict[int, str] | None, new: dict[int, str] | None
) -> dict[int, str]:
    """合并小说归档"""
    result = existing.copy() if existing else {}
    if new:
        result.update(new)
    return result


def increment_revision(existing: int | None, new: int | None) -> int:
    """增加修改计数"""
    current = existing or 0
    delta = new or 0
    return current + delta


# ===== State Factory =====
def create_initial_state(
    user_id: str,
    project_id: str,
    thread_id: str | None = None,
) -> AgentState:
    """
    创建初始 Agent 状态

    Args:
        user_id: 用户 ID
        project_id: 项目 ID
        thread_id: 可选的会话 ID，若不提供则自动生成

    Returns:
        初始化的 AgentState
    """
    import uuid
    from datetime import datetime, timezone

    return AgentState(
        user_id=user_id,
        project_id=project_id,
        thread_id=thread_id or str(uuid.uuid4()),
        messages=[],
        user_config=UserConfig(),
        market_report=None,
        story_plans=[],
        selected_plan=None,
        fusion_request=None,
        character_bible=[],
        beat_sheet=[],
        current_episode=1,
        novel_content="",
        novel_archive={},
        script=[],
        narrative_mode="dialog",
        storyboard=[],
        generation_model="sora",
        asset_manifest={},
        asset_prompts=[],
        emotion_curve=[],
        surgery_result="",
        hero_state=HeroState(
            current_phase="Ordinary World",
            emotional_state="neutral",
            growth_percentage=0.0,
            last_updated_episode=0,
        ),
        unresolved_mysteries=[],
        history_summary="",
        current_stage=StageType.LEVEL_1,
        approval_status=ApprovalStatus.PENDING,
        human_feedback="",
        revision_count=0,
        quality_score=0.0,
        skill_scores={},
        review_report=None,
        refine_log=None,
        ui_interaction=None,
        use_master_router=False,
        routed_agent=None,
        routed_function=None,
        routed_parameters=None,
        # Workflow Planning (V4.1)
        workflow_plan=None,
        current_step_idx=0,
        workflow_results={},
        intent_analysis=None,
        error_message=None,
        last_successful_node=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
