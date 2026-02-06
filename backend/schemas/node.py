"""
Node Data Schemas

内容节点 (story_nodes) 的数据模型。
支持通用节点系统 (Generic Node System)，通过 type 字段区分。
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """
    节点类型

    对应系统架构文档中的 story_nodes.type 字段
    """

    # Level 1-3 阶段产物
    CONFIG = "config"  # 项目配置节点 (Project Root)
    MARKET_REPORT = "market_report"  # 市场分析报告
    STORY_PLAN = "story_plan"  # 故事方案
    CHARACTER = "character"  # 角色设定
    OUTLINE = "outline"  # 分集大纲 (总大纲)
    EPISODE_OUTLINE = "episode_outline"  # 单集大纲

    # Module A 产物
    EPISODE = "episode"  # 小说章节 (旧，保留兼容)
    NOVEL_CHAPTER = "novel_chapter"  # 小说章节 (新)

    # Module B 产物
    SCENE = "scene"  # 剧本场景 (旧，保留兼容)
    SCRIPT_SCENE = "script_scene"  # 剧本场景 (新)

    # Module C 产物
    SHOT = "shot"  # 分镜 (旧，保留兼容)
    STORYBOARD_SHOT = "storyboard_shot"  # 分镜 (新)

    # Module X 产物
    ASSET = "asset"  # 资产 (角色/场景/道具 参考图)

    # 其他
    VIDEO = "video"  # 视频结果
    NOTE = "note"  # 用户笔记


class NodeBase(BaseModel):
    """节点基础字段"""

    type: NodeType = Field(..., description="节点类型")
    content: dict[str, Any] = Field(default_factory=dict, description="节点内容 (JSONB)")


class NodeCreate(NodeBase):
    """创建节点请求"""

    project_id: UUID = Field(..., description="所属项目 ID")
    parent_id: UUID | None = Field(None, description="父节点 ID (用于连线)")


class NodeUpdate(BaseModel):
    """更新节点请求"""

    content: dict[str, Any] | None = None


class NodeLayoutUpdate(BaseModel):
    """更新节点布局"""

    node_id: UUID | None = Field(None, description="节点 ID (批量更新时使用)")
    canvas_tab: str = Field(..., description="画布 Tab (novel/drama)")
    position_x: float = Field(..., description="X 坐标")
    position_y: float = Field(..., description="Y 坐标")


class NodeLayout(BaseModel):
    """节点布局数据"""

    canvas_tab: str
    position_x: float
    position_y: float


class NodeResponse(NodeBase):
    """节点响应"""

    node_id: UUID = Field(..., alias="id", description="节点 ID")
    project_id: UUID = Field(..., description="所属项目 ID")
    created_at: datetime = Field(..., description="创建时间")

    # 可选: 布局信息 (如果请求时指定了 canvas_tab)
    layout: NodeLayout | None = Field(None, description="布局信息")

    # 可选: 关联的父节点
    parent_id: UUID | None = Field(None, description="父节点 ID")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "type": "episode",
                "content": {
                    "episode_number": 1,
                    "title": "重生归来",
                    "text": "陈默睁开眼睛，发现自己回到了十年前...",
                    "word_count": 523,
                    "quality_score": 85.5,
                },
                "created_at": "2026-02-02T04:00:00Z",
                "layout": {"canvas_tab": "novel", "position_x": 100.0, "position_y": 200.0},
            }
        }


# ===== Specific Node Content Schemas =====
# 这些是 content 字段的具体结构定义


class EpisodeContent(BaseModel):
    """小说章节内容"""

    episode_number: int = Field(..., description="集数")
    title: str = Field(..., description="章节标题")
    text: str = Field(..., description="正文内容")
    word_count: int = Field(default=0, description="字数")
    quality_score: float = Field(default=0.0, description="质量评分")
    skill_scores: dict[str, float] = Field(default_factory=dict, description="技能评分")
    model_used: str | None = Field(None, description="使用的模型")
    thinking_process: str | None = Field(None, description="思维链 (CoT)")


class SceneContent(BaseModel):
    """剧本场景内容"""

    scene_number: str = Field(..., description="场号 (S01, S02...)")
    location: str = Field(..., description="场景头")
    visual_description: str = Field(..., description="视觉描述")
    elements: list[dict[str, Any]] = Field(default_factory=list, description="元素列表")
    source_episode: int | None = Field(None, description="来源章节")


class ShotContent(BaseModel):
    """分镜内容"""

    shot_number: str = Field(..., description="镜头号 (S01-01)")
    shot_type: str = Field(..., description="镜头类型")
    camera_movement: str = Field(default="固定", description="摄像机运动")
    subject: str = Field(..., description="画面主体")
    action: str = Field(..., description="主体动作")
    visual_description: str = Field(..., description="视觉描述")
    nano_banana_prompt: str = Field(..., description="Nano Banana Prompt")
    image_urls: list[str] = Field(default_factory=list, description="生成的图片 URL")
    source_scene: str | None = Field(None, description="来源场景")


class CharacterContent(BaseModel):
    """角色设定内容 (Character Bible)"""

    name: str = Field(..., description="角色名")
    role: str = Field(default="protagonist", description="角色定位")
    appearance: str = Field(..., description="外貌描述")
    personality_flaw: str = Field(..., description="性格缺陷")
    core_desire: str = Field(..., description="核心欲望")
    speech_pattern: str = Field(..., description="说话方式")
    b_story: str | None = Field(None, description="B故事暗线")
    avatar_url: str | None = Field(None, description="角色头像 URL")
    reference_images: list[str] = Field(default_factory=list, description="参考图")


class AssetContent(BaseModel):
    """资产内容"""

    name: str = Field(..., description="资产名称")
    asset_type: str = Field(..., description="类型: character/location/prop")
    visual_tokens: dict[str, Any] = Field(default_factory=dict, description="视觉 Token")
    reference_urls: list[str] = Field(default_factory=list, description="参考图 URL")
    prompts: dict[str, str] = Field(default_factory=dict, description="生成 Prompt")
