"""
Projects API

项目 CRUD 端点。
"""

from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from backend.schemas.common import SuccessResponse, PaginatedResponse
from backend.services import get_db_service, DatabaseService
from backend.api.deps import get_current_user_id

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = structlog.get_logger(__name__)


@router.post(
    "", response_model=SuccessResponse[ProjectResponse], status_code=status.HTTP_201_CREATED
)
async def create_project(
    data: ProjectCreate,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """创建项目"""
    project = await db.create_project(user_id, data)
    logger.info("Project created", project_id=str(project.id))
    return SuccessResponse.of(project)


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """获取项目列表"""
    offset = (page - 1) * page_size
    projects = await db.list_projects(user_id, limit=page_size, offset=offset)
    total = await db.count_projects(user_id)
    return PaginatedResponse.of(projects, total, page, page_size)


@router.get("/{project_id}", response_model=SuccessResponse[ProjectResponse])
async def get_project(
    project_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取项目详情"""
    project = await db.get_project(str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return SuccessResponse.of(project)


@router.patch("/{project_id}", response_model=SuccessResponse[ProjectResponse])
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """更新项目"""
    project = await db.update_project(str(project_id), data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return SuccessResponse.of(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """删除项目"""
    success = await db.delete_project(str(project_id))
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post(
    "/temp", response_model=SuccessResponse[ProjectResponse], status_code=status.HTTP_201_CREATED
)
async def create_temp_project(
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """创建临时项目"""
    # 限制临时项目数量（最多5个）
    temp_count = await db.count_temp_projects(user_id)
    if temp_count >= 5:
        # 删除最旧的临时项目
        await db.delete_oldest_temp_project(user_id)

    # 创建临时项目
    data = ProjectCreate(name="未命名项目")
    project = await db.create_temp_project(user_id, data)
    logger.info("Temp project created", project_id=str(project.id))
    return SuccessResponse.of(project)


@router.post("/{project_id}/save", response_model=SuccessResponse[ProjectResponse])
async def save_temp_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """将临时项目转为正式项目"""
    # 验证项目是否存在
    existing = await db.get_project(str(project_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    project = await db.save_temp_project(str(project_id), data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    logger.info("Temp project saved", project_id=str(project_id))
    return SuccessResponse.of(project)
