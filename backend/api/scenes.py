"""
Scenes API

场景管理端点。
"""

from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.scene import SceneCreate, SceneResponse, SceneUpdate
from backend.schemas.common import SuccessResponse
from backend.services import get_db_service, DatabaseService

router = APIRouter(prefix="/episodes", tags=["Scenes"])
logger = structlog.get_logger(__name__)


@router.get("/{episode_id}/scenes", response_model=SuccessResponse[list[SceneResponse]])
async def list_scenes(
    episode_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取剧集的所有场景"""
    scenes = await db.list_scenes(str(episode_id))
    return SuccessResponse.of([SceneResponse.from_db(scene) for scene in scenes])


@router.get("/{episode_id}/scenes/{scene_id}", response_model=SuccessResponse[SceneResponse])
async def get_scene(
    episode_id: UUID,
    scene_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取单个场景详情"""
    scene = await db.get_scene(str(scene_id))
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    # 验证场景是否属于该剧集
    if str(scene.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Scene not found in this episode")
    return SuccessResponse.of(SceneResponse.from_db(scene))


@router.post(
    "/{episode_id}/scenes",
    response_model=SuccessResponse[SceneResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_scene(
    episode_id: UUID,
    data: SceneCreate,
    db: DatabaseService = Depends(get_db_service),
):
    """创建场景"""
    # 验证剧集是否存在
    episode = await db.get_episode(str(episode_id))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    scene = await db.create_scene(
        episode_id=str(episode_id), location=data.location, description=data.description
    )
    logger.info("Scene created", scene_id=str(scene.get("scene_id")))
    return SuccessResponse.of(SceneResponse.from_db(scene))


@router.patch("/{episode_id}/scenes/{scene_id}", response_model=SuccessResponse[SceneResponse])
async def update_scene(
    episode_id: UUID,
    scene_id: UUID,
    data: SceneUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """更新场景"""
    # 验证场景是否存在并属于该剧集
    existing = await db.get_scene(str(scene_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Scene not found")
    if str(existing.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Scene not found in this episode")

    scene = await db.update_scene(str(scene_id), data.model_dump(exclude_unset=True))
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    logger.info("Scene updated", scene_id=str(scene_id))
    return SuccessResponse.of(SceneResponse.from_db(scene))


@router.delete("/{episode_id}/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    episode_id: UUID,
    scene_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """删除场景"""
    # 验证场景是否存在并属于该剧集
    existing = await db.get_scene(str(scene_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Scene not found")
    if str(existing.get("episode_id")) != str(episode_id):
        raise HTTPException(status_code=404, detail="Scene not found in this episode")

    success = await db.delete_scene(str(scene_id))
    if not success:
        raise HTTPException(status_code=404, detail="Scene not found")
    logger.info("Scene deleted", scene_id=str(scene_id))
