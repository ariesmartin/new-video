"""
Connections API

节点连线管理端点 - v6.0 每集独立画布架构。
"""

from uuid import UUID
from typing import Literal
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.schemas.canvas import Connection
from backend.schemas.common import SuccessResponse
from backend.services import get_db_service, DatabaseService

router = APIRouter(prefix="/episodes", tags=["Connections"])
logger = structlog.get_logger(__name__)


class ConnectionCreate(BaseModel):
    """创建连线请求"""

    source_shot_id: UUID = Field(..., description="源分镜 ID")
    target_shot_id: UUID = Field(..., description="目标分镜 ID")
    connection_type: Literal["sequence", "reference"] = Field(
        default="sequence", description="连线类型"
    )


@router.get("/{episode_id}/connections", response_model=SuccessResponse[list[Connection]])
async def list_connections(
    episode_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取剧集的所有连线"""
    # 验证剧集是否存在
    episode = await db.get_episode(str(episode_id))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    connections = await db.list_shot_connections(str(episode_id))
    return SuccessResponse.of([Connection(**conn) for conn in connections])


@router.post(
    "/{episode_id}/connections",
    response_model=SuccessResponse[Connection],
    status_code=status.HTTP_201_CREATED,
)
async def create_connection(
    episode_id: UUID,
    data: ConnectionCreate,
    db: DatabaseService = Depends(get_db_service),
):
    """创建连线"""
    # 验证剧集是否存在
    episode = await db.get_episode(str(episode_id))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # 验证源分镜和目标分镜是否属于该剧集
    source_shot = await db.get_shot_node(str(data.source_shot_id))
    if not source_shot or str(source_shot.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Source shot not found in this episode")

    target_shot = await db.get_shot_node(str(data.target_shot_id))
    if not target_shot or str(target_shot.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Target shot not found in this episode")

    connection = await db.create_shot_connection(
        episode_id=str(episode_id),
        source_shot_id=str(data.source_shot_id),
        target_shot_id=str(data.target_shot_id),
        connection_type=data.connection_type,
    )
    logger.info("Connection created", connection_id=str(connection.get("connection_id")))
    return SuccessResponse.of(Connection(**connection))


@router.delete("/{episode_id}/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    episode_id: UUID,
    connection_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """删除连线"""
    # 注意：当前数据库层没有 get_connection 方法，直接尝试删除
    # 删除操作会验证连接是否存在
    success = await db.delete_shot_connection(str(connection_id))
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")
    logger.info("Connection deleted", connection_id=str(connection_id))
