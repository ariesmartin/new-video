"""
Shot Schemas

ShotNode 相关的 Pydantic 模型 - 严格遵循 v6.0 定义。
对应: Product-Spec.md Section 2.6 / Frontend-Design-V3.md 3.5.4
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class ShotDetails(BaseModel):
    """ShotNode 详细内容 - v6.0 嵌套在 details 中"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    # 内容
    dialogue: Optional[str] = Field(default=None, description="对白")
    sound: Optional[str] = Field(default=None, description="音效")
    camera_move: Optional[str] = Field(default=None, description="运镜方式")
    description: Optional[str] = Field(default=None, description="画面描述")

    # 生成参数
    prompt: Optional[str] = Field(default=None, description="AI 生图提示词")
    negative_prompt: Optional[str] = Field(default=None, description="负面提示词")
    resolution: Optional[str] = Field(default=None, description="2K | 4K")
    aspect_ratio: Optional[str] = Field(default=None, description="16:9 | 9:16 | 1:1 | 4:3")
    style: Optional[str] = Field(default=None, description="画面风格")

    # 参考图 - v6.0 支持三种
    reference_images: Optional[Dict[str, Optional[str]]] = Field(
        default=None, description="{ sketch, material, threeD }"
    )

    # 生成参数
    generation_params: Optional[Dict[str, Any]] = Field(
        default=None, description="{ seed, steps, cfg }"
    )


class ShotBase(BaseModel):
    """ShotNode 基础信息"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: str = Field(..., min_length=1, max_length=50, description="景别")
    subtitle: Optional[str] = Field(default=None, max_length=100, description="运镜方式")


class ShotCreate(ShotBase):
    """创建分镜请求"""

    scene_id: Optional[UUID] = Field(default=None)
    node_type: str = Field(..., pattern="^(shot|scene_master)$")
    position_x: float = Field(default=0, description="X 坐标")
    position_y: float = Field(default=0, description="Y 坐标")
    details: Optional[ShotDetails] = Field(default=None)


class ShotUpdate(BaseModel):
    """更新分镜请求"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    title: Optional[str] = Field(default=None)
    subtitle: Optional[str] = Field(default=None)
    status: Optional[str] = Field(
        default=None, pattern="^(pending|processing|completed|approved|revision)$"
    )
    position_x: Optional[float] = Field(default=None)
    position_y: Optional[float] = Field(default=None)
    thumbnail_url: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    details: Optional[ShotDetails] = Field(default=None)


class ShotResponse(ShotBase):
    """分镜响应 - 完整 ShotNode"""

    shot_id: UUID
    episode_id: UUID
    scene_id: Optional[UUID]

    # 类型和编号
    node_type: str
    shot_number: int

    # 媒体
    thumbnail_url: Optional[str]
    image_url: Optional[str]

    # 状态
    status: str

    # 位置
    position_x: float
    position_y: float

    # 详情
    details: Optional[ShotDetails]

    # 时间
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, shot: Any) -> "ShotResponse":
        """从数据库模型创建响应 - 支持 dict 或对象"""
        # 处理 dict 类型（来自 Supabase REST API）
        if isinstance(shot, dict):
            details = shot.get("details")
            return cls(
                shot_id=shot.get("shot_id"),
                episode_id=shot.get("episode_id"),
                scene_id=shot.get("scene_id"),
                node_type=shot.get("node_type"),
                shot_number=shot.get("shot_number"),
                title=shot.get("title"),
                subtitle=shot.get("subtitle"),
                thumbnail_url=shot.get("thumbnail_url"),
                image_url=shot.get("image_url"),
                status=shot.get("status"),
                position_x=shot.get("position_x"),
                position_y=shot.get("position_y"),
                details=ShotDetails(**details) if details else None,
                created_at=shot.get("created_at"),
                updated_at=shot.get("updated_at"),
            )
        # 处理对象类型（来自 ORM）
        return cls(
            shot_id=shot.shot_id,
            episode_id=shot.episode_id,
            scene_id=shot.scene_id,
            node_type=shot.node_type,
            shot_number=shot.shot_number,
            title=shot.title,
            subtitle=shot.subtitle,
            thumbnail_url=shot.thumbnail_url,
            image_url=shot.image_url,
            status=shot.status,
            position_x=shot.position_x,
            position_y=shot.position_y,
            details=ShotDetails(**shot.details) if shot.details else None,
            created_at=shot.created_at,
            updated_at=shot.updated_at,
        )

    class Config:
        from_attributes = True


class ShotBatchCreate(BaseModel):
    """批量创建分镜请求"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    shots: List[ShotCreate]


class ShotPositionUpdate(BaseModel):
    """位置更新项"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    shot_id: UUID
    x: float
    y: float


class ShotBatchUpdate(BaseModel):
    """批量更新位置请求"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    positions: List[ShotPositionUpdate]
