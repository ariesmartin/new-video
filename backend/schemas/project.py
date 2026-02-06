"""
Project Data Schemas

项目 CRUD 操作的数据模型。
对应数据库表: projects
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class ProjectMeta(BaseModel):
    """
    项目元数据 (存储在 JSONB 字段)

    对应 Product-Spec.md 中的 UserConfig
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    genre: str | None = Field(default=None, description="题材赛道")
    sub_tags: list[str] = Field(default_factory=list, description="细分标签")
    tone: list[str] = Field(default_factory=list, description="内容调性")
    target_word_count: int = Field(default=500, description="单集字数")
    total_episodes: int = Field(default=80, description="目标集数")
    ending_type: str = Field(default="HE", description="结局类型")
    aspect_ratio: str = Field(default="9:16", description="画幅比例")
    drawing_type: str | None = Field(default=None, description="绘图类型")
    visual_style: str | None = Field(default=None, description="画面风格")
    style_dna: str | None = Field(default=None, description="文风 DNA")
    avoid_tags: list[str] = Field(default_factory=list, description="排除标签")


class ProjectBase(BaseModel):
    """项目基础字段"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    cover_image: str | None = Field(None, description="封面图 URL")
    meta: ProjectMeta | None = Field(default=None, description="项目元数据")


class ProjectCreate(ProjectBase):
    """创建项目请求"""

    pass


class ProjectUpdate(BaseModel):
    """更新项目请求 (所有字段可选)"""

    name: str | None = Field(None, min_length=1, max_length=100)
    cover_image: str | None = None
    meta: ProjectMeta | None = None


class ProjectResponse(ProjectBase):
    """项目响应"""

    id: UUID = Field(..., description="项目 ID")
    user_id: UUID = Field(..., description="所属用户 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 临时项目标记
    is_temporary: bool = Field(default=False, description="是否为临时项目")

    # 统计信息
    node_count: int = Field(default=0, description="节点数量")
    episode_count: int = Field(default=0, description="已生成集数")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "重生之逆袭人生",
                "cover_image": "https://storage.example.com/covers/project1.jpg",
                "meta": {
                    "genre": "逆袭复仇",
                    "sub_tags": ["战神回归", "重生改命"],
                    "tone": ["爽", "虐"],
                    "target_word_count": 500,
                    "total_episodes": 80,
                    "ending_type": "HE",
                },
                "created_at": "2026-02-02T04:00:00Z",
                "updated_at": "2026-02-02T04:00:00Z",
                "node_count": 25,
                "episode_count": 5,
            }
        }


class ProjectListResponse(BaseModel):
    """项目列表项 (简化版)"""

    id: UUID
    name: str
    cover_image: str | None
    updated_at: datetime
    node_count: int = 0

    class Config:
        from_attributes = True
