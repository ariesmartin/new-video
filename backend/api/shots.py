"""
Shots API

分镜节点管理端点 - v6.0 每集独立画布架构。
"""

from uuid import UUID
from typing import Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.schemas.shot import (
    ShotCreate,
    ShotUpdate,
    ShotResponse,
    ShotBatchCreate,
    ShotBatchUpdate,
)
from backend.schemas.common import SuccessResponse
from backend.services import get_db_service, DatabaseService

router = APIRouter(prefix="/episodes", tags=["Shots"])
logger = structlog.get_logger(__name__)


@router.get("/{episode_id}/shots", response_model=SuccessResponse[list[ShotResponse]])
async def list_shots(
    episode_id: UUID,
    scene_id: Optional[UUID] = None,
    node_type: Optional[str] = Query(None, regex="^(shot|scene_master)$"),
    db: DatabaseService = Depends(get_db_service),
):
    """获取剧集的所有分镜节点"""
    shots = await db.list_shot_nodes(
        str(episode_id), str(scene_id) if scene_id else None, node_type
    )
    return SuccessResponse.of([ShotResponse.from_db(shot) for shot in shots])


@router.get("/{episode_id}/shots/{shot_id}", response_model=SuccessResponse[ShotResponse])
async def get_shot(
    episode_id: UUID,
    shot_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取单个分镜详情"""
    shot = await db.get_shot_node(str(shot_id))
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    # 验证分镜是否属于该剧集
    if str(shot.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Shot not found in this episode")
    return SuccessResponse.of(ShotResponse.from_db(shot))


@router.post(
    "/{episode_id}/shots",
    response_model=SuccessResponse[ShotResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_shot(
    episode_id: UUID,
    data: ShotCreate,
    db: DatabaseService = Depends(get_db_service),
):
    """创建分镜节点"""
    # 获取下一个分镜编号
    shot_number = await db.get_next_shot_number(str(episode_id))

    shot = await db.create_shot_node(
        episode_id=str(episode_id),
        node_type=data.node_type,
        shot_number=shot_number,
        title=data.title,
        subtitle=data.subtitle,
        position_x=data.position_x,
        position_y=data.position_y,
        scene_id=str(data.scene_id) if data.scene_id else None,
        details=data.details.model_dump() if data.details else None,
    )
    logger.info("Shot created", shot_id=str(shot.get("shot_id")))
    return SuccessResponse.of(ShotResponse.from_db(shot))


@router.post(
    "/{episode_id}/shots/batch",
    response_model=SuccessResponse[list[ShotResponse]],
    status_code=status.HTTP_201_CREATED,
)
async def batch_create_shots(
    episode_id: UUID,
    data: ShotBatchCreate,
    db: DatabaseService = Depends(get_db_service),
):
    """批量创建分镜节点"""
    shots_data = []
    for shot in data.shots:
        shots_data.append(
            {
                "node_type": shot.node_type,
                "title": shot.title,
                "subtitle": shot.subtitle,
                "position_x": shot.position_x,
                "position_y": shot.position_y,
                "scene_id": str(shot.scene_id) if shot.scene_id else None,
                "details": shot.details.model_dump() if shot.details else None,
            }
        )

    shots = await db.batch_create_shot_nodes(episode_id=str(episode_id), shots_data=shots_data)
    logger.info("Shots batch created", count=len(shots))
    return SuccessResponse.of([ShotResponse.from_db(shot) for shot in shots])


@router.patch("/{episode_id}/shots/{shot_id}", response_model=SuccessResponse[ShotResponse])
async def update_shot(
    episode_id: UUID,
    shot_id: UUID,
    data: ShotUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """更新分镜节点"""
    # 验证分镜是否存在并属于该剧集
    existing = await db.get_shot_node(str(shot_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Shot not found")
    if str(existing.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Shot not found in this episode")

    update_data = data.model_dump(exclude_unset=True)
    # 处理 details 字段
    if "details" in update_data and update_data["details"]:
        update_data["details"] = update_data["details"].model_dump()

    shot = await db.update_shot_node(shot_id=str(shot_id), **update_data)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    logger.info("Shot updated", shot_id=str(shot_id))
    return SuccessResponse.of(ShotResponse.from_db(shot))


@router.put("/{episode_id}/shots/batch/position", response_model=SuccessResponse[dict])
async def batch_update_shot_positions(
    episode_id: UUID,
    data: ShotBatchUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """批量更新分镜位置"""
    positions = []
    for pos in data.positions:
        positions.append(
            {
                "shot_id": str(pos.shot_id),
                "x": pos.x,
                "y": pos.y,
            }
        )

    result = await db.batch_update_shot_positions(positions)
    logger.info("Shot positions batch updated", count=len(positions))
    return SuccessResponse.of(
        {"updated_count": len(positions), "message": "Positions updated successfully"}
    )


@router.delete("/{episode_id}/shots/{shot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shot(
    episode_id: UUID,
    shot_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """删除分镜节点"""
    # 验证分镜是否存在并属于该剧集
    existing = await db.get_shot_node(str(shot_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Shot not found")
    if str(existing.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Shot not found in this episode")

    success = await db.delete_shot_node(str(shot_id))
    if not success:
        raise HTTPException(status_code=404, detail="Shot not found")
    logger.info("Shot deleted", shot_id=str(shot_id))
