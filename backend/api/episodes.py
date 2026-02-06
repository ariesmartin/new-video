"""
Episodes API

剧集 CRUD 端点。
"""

from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.episode import (
    EpisodeCreate,
    EpisodeResponse,
    EpisodeUpdate,
    EpisodeListResponse,
)
from backend.schemas.common import SuccessResponse
from backend.services import get_db_service, DatabaseService
from backend.api.deps import get_current_user_id

router = APIRouter(prefix="/projects", tags=["Episodes"])
logger = structlog.get_logger(__name__)


@router.get("/{project_id}/episodes", response_model=SuccessResponse[list[EpisodeListResponse]])
async def list_episodes(
    project_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取项目的所有剧集"""
    episodes = await db.list_episodes(str(project_id))
    return SuccessResponse.of([EpisodeListResponse(**ep) for ep in episodes])


@router.get("/{project_id}/episodes/{episode_id}", response_model=SuccessResponse[EpisodeResponse])
async def get_episode(
    project_id: UUID,
    episode_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取单个剧集详情"""
    episode = await db.get_episode(str(episode_id))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    # 验证剧集是否属于该项目
    if str(episode.get("project_id")) != str(project_id):
        raise HTTPException(status_code=404, detail="Episode not found in this project")
    return SuccessResponse.of(EpisodeResponse.from_db(episode))


@router.post(
    "/{project_id}/episodes",
    response_model=SuccessResponse[EpisodeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_episode(
    project_id: UUID,
    data: EpisodeCreate,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """创建剧集"""
    # 获取下一个剧集编号
    episode_number = await db.get_next_episode_number(str(project_id))

    episode = await db.create_episode(
        project_id=str(project_id),
        episode_number=episode_number,
        title=data.title,
        summary=data.summary,
    )
    logger.info("Episode created", episode_id=str(episode.get("episode_id")))
    return SuccessResponse.of(EpisodeResponse.from_db(episode))


@router.patch(
    "/{project_id}/episodes/{episode_id}", response_model=SuccessResponse[EpisodeResponse]
)
async def update_episode(
    project_id: UUID,
    episode_id: UUID,
    data: EpisodeUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """更新剧集"""
    # 验证剧集是否存在并属于该项目
    existing = await db.get_episode(str(episode_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Episode not found")
    if str(existing.get("project_id")) != str(project_id):
        raise HTTPException(status_code=404, detail="Episode not found in this project")

    episode = await db.update_episode(str(episode_id), data.model_dump(exclude_unset=True))
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    logger.info("Episode updated", episode_id=str(episode_id))
    return SuccessResponse.of(EpisodeResponse.from_db(episode))


@router.delete("/{project_id}/episodes/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    project_id: UUID,
    episode_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """删除剧集"""
    # 验证剧集是否存在并属于该项目
    existing = await db.get_episode(str(episode_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Episode not found")
    if str(existing.get("project_id")) != str(project_id):
        raise HTTPException(status_code=404, detail="Episode not found in this project")

    success = await db.delete_episode(str(episode_id))
    if not success:
        raise HTTPException(status_code=404, detail="Episode not found")
    logger.info("Episode deleted", episode_id=str(episode_id))
