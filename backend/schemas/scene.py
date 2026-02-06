"""
Scene Schemas

场景相关的 Pydantic 模型 - v6.0 场景管理。
对应: Product-Spec.md Section 2.5
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class SceneBase(BaseModel):
    """场景基础信息"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    location: str = Field(..., min_length=1, max_length=200, description="场景地点")
    description: Optional[str] = Field(default=None, description="场景描述")


class SceneCreate(SceneBase):
    """创建场景请求"""

    create_master_node: bool = Field(default=False, description="是否同时创建 Scene Master 节点")
    master_position_x: Optional[float] = Field(default=None, description="Master 节点 X 坐标")
    master_position_y: Optional[float] = Field(default=None, description="Master 节点 Y 坐标")


class SceneUpdate(BaseModel):
    """更新场景请求"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    location: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, description="场景描述")


class SceneResponse(SceneBase):
    """场景响应"""

    scene_id: UUID
    episode_id: UUID
    scene_number: str
    master_node_id: Optional[UUID]
    shot_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, scene: Any) -> "SceneResponse":
        """从数据库模型创建响应 - 支持 dict 或对象"""
        # 处理 dict 类型（来自 Supabase REST API）
        if isinstance(scene, dict):
            return cls(
                scene_id=scene.get("scene_id"),
                episode_id=scene.get("episode_id"),
                scene_number=scene.get("scene_number"),
                location=scene.get("location"),
                description=scene.get("description"),
                master_node_id=scene.get("master_node_id"),
                shot_count=scene.get("shot_count", 0),
                created_at=scene.get("created_at"),
                updated_at=scene.get("updated_at"),
            )
        # 处理对象类型（来自 ORM）
        return cls(
            scene_id=scene.scene_id,
            episode_id=scene.episode_id,
            scene_number=scene.scene_number,
            location=scene.location,
            description=scene.description,
            master_node_id=scene.master_node_id,
            shot_count=scene.shot_count,
            created_at=scene.created_at,
            updated_at=scene.updated_at,
        )

    class Config:
        from_attributes = True
