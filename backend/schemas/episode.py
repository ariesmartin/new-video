"""
Episode Schemas

剧集相关的 Pydantic 模型 - v6.0 每集独立画布架构。
对应: Product-Spec.md Section 2.6
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class EpisodeBase(BaseModel):
    """剧集基础信息"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: str = Field(..., min_length=1, max_length=100, description="剧集标题")
    summary: Optional[str] = Field(default=None, max_length=500, description="剧情摘要")


class EpisodeCreate(EpisodeBase):
    """创建剧集请求"""

    pass


class EpisodeUpdate(BaseModel):
    """更新剧集请求"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    summary: Optional[str] = Field(default=None, max_length=500, description="剧情摘要")
    script_text: Optional[str] = Field(default=None, description="剧本内容")
    novel_content: Optional[str] = Field(default=None, description="小说内容")


class EpisodeListResponse(BaseModel):
    """剧集列表响应（精简）"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    episode_id: UUID
    episode_number: int
    title: str
    summary: Optional[str]
    status: str
    shot_count: int = 0
    created_at: datetime


class EpisodeResponse(EpisodeBase):
    """剧集详情响应（完整）"""

    episode_id: UUID
    project_id: UUID
    episode_number: int

    # 内容
    script_text: Optional[str]
    script_scenes: List[Dict[str, Any]]
    novel_content: Optional[str]
    word_count: int

    # 状态
    status: str

    # 画布状态（可选，避免大数据传输）
    canvas_data: Optional[Dict[str, Any]] = None

    # 统计
    shot_count: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @classmethod
    def from_db(cls, episode: Any) -> "EpisodeResponse":
        """从数据库模型创建响应 - 支持 dict 或对象"""
        # 处理 dict 类型（来自 Supabase REST API）
        if isinstance(episode, dict):
            return cls(
                episode_id=episode.get("episode_id"),
                project_id=episode.get("project_id"),
                episode_number=episode.get("episode_number"),
                title=episode.get("title"),
                summary=episode.get("summary"),
                script_text=episode.get("script_text"),
                script_scenes=episode.get("script_scenes") or [],
                novel_content=episode.get("novel_content"),
                word_count=episode.get("word_count", 0),
                status=episode.get("status", "draft"),
                canvas_data=episode.get("canvas_data"),
                shot_count=episode.get("storyboard_shot_count", 0),
                created_at=episode.get("created_at"),
                updated_at=episode.get("updated_at"),
            )
        # 处理对象类型（来自 ORM）
        return cls(
            episode_id=episode.episode_id,
            project_id=episode.project_id,
            episode_number=episode.episode_number,
            title=episode.title,
            summary=episode.summary,
            script_text=episode.script_text,
            script_scenes=episode.script_scenes or [],
            novel_content=episode.novel_content,
            word_count=episode.word_count,
            status=episode.status,
            canvas_data=episode.canvas_data,
            shot_count=episode.storyboard_shot_count,
            created_at=episode.created_at,
            updated_at=episode.updated_at,
        )
