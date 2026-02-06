"""
Canvas API

画布状态管理端点 - v6.0 每集独立画布架构。
"""

from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.canvas import CanvasData, CanvasViewport, CanvasSaveRequest
from backend.schemas.common import SuccessResponse
from backend.services import get_db_service, DatabaseService

router = APIRouter(prefix="/episodes", tags=["Canvas"])
logger = structlog.get_logger(__name__)


@router.get("/{episode_id}/canvas", response_model=SuccessResponse[CanvasData])
async def get_canvas(
    episode_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取剧集画布状态"""
    # 验证剧集是否存在
    episode = await db.get_episode(str(episode_id))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    canvas_data = await db.get_episode_canvas(str(episode_id))
    if not canvas_data:
        # 返回空白画布
        return SuccessResponse.of(CanvasData.empty(str(episode_id)))

    return SuccessResponse.of(CanvasData(**canvas_data))


@router.put("/{episode_id}/canvas", response_model=SuccessResponse[CanvasData])
async def save_canvas(
    episode_id: UUID,
    data: CanvasSaveRequest,
    db: DatabaseService = Depends(get_db_service),
):
    """保存剧集画布状态"""
    # 验证剧集是否存在
    episode = await db.get_episode(str(episode_id))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    canvas_data = {
        "viewport": data.viewport.model_dump(),
        "nodes": [node.model_dump() for node in data.nodes],
        "connections": [conn.model_dump() for conn in data.connections],
    }

    result = await db.save_episode_canvas(episode_id=str(episode_id), canvas_data=canvas_data)
    logger.info("Canvas saved", episode_id=str(episode_id))
    return SuccessResponse.of(CanvasData(**result))


@router.patch("/{episode_id}/canvas/viewport", response_model=SuccessResponse[CanvasData])
async def update_viewport(
    episode_id: UUID,
    viewport: CanvasViewport,
    db: DatabaseService = Depends(get_db_service),
):
    """仅更新画布视口状态"""
    # 验证剧集是否存在
    episode = await db.get_episode(str(episode_id))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    result = await db.update_episode_viewport(
        episode_id=str(episode_id), x=viewport.x, y=viewport.y, zoom=viewport.zoom
    )
    logger.info(
        "Viewport updated",
        episode_id=str(episode_id),
        x=viewport.x,
        y=viewport.y,
        zoom=viewport.zoom,
    )
    return SuccessResponse.of(CanvasData(**result))
