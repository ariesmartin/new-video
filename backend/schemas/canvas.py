"""
Canvas Schemas

画布状态相关的 Pydantic 模型 - v6.0 每集独立画布。
对应: Product-Spec.md Section 2.6
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from backend.schemas.shot import ShotResponse


class CanvasViewport(BaseModel):
    """画布视口状态"""

    x: float = Field(0, description="视口 X 偏移")
    y: float = Field(0, description="视口 Y 偏移")
    zoom: float = Field(1, ge=0.1, le=5, description="缩放级别 10%-500%")


class Connection(BaseModel):
    """节点连线 - v6.0"""

    id: str = Field(..., description="连线 ID")
    source: str = Field(..., description="源节点 ID")
    target: str = Field(..., description="目标节点 ID")
    type: str = Field("sequence", description="sequence | reference")


class CanvasData(BaseModel):
    """画布完整数据 - v6.0"""

    episode_id: str = Field(..., description="剧集 ID")
    viewport: CanvasViewport = Field(default_factory=CanvasViewport)
    nodes: List[ShotResponse] = Field(default_factory=list, description="所有节点")
    connections: List[Connection] = Field(default_factory=list, description="所有连线")

    @classmethod
    def empty(cls, episode_id: str) -> "CanvasData":
        """创建空白画布"""
        return cls(
            episode_id=episode_id,
            viewport=CanvasViewport(),
            nodes=[],
            connections=[],
        )


class CanvasSaveRequest(BaseModel):
    """保存画布请求"""

    viewport: CanvasViewport
    nodes: List[ShotResponse]
    connections: List[Connection]
