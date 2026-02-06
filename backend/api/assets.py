"""
Assets API

资产管理端点 - 角色、场景、道具等视觉资产。
"""

from uuid import UUID
from typing import Literal, Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.schemas.responses import AssetResponseData
from backend.schemas.common import SuccessResponse, PaginatedResponse
from backend.services import get_db_service, DatabaseService

router = APIRouter(prefix="/projects", tags=["Assets"])
logger = structlog.get_logger(__name__)


class AssetCreate(BaseModel):
    """创建资产请求"""

    name: str = Field(..., min_length=1, max_length=100, description="资产名称")
    asset_type: Literal["character", "location", "prop"] = Field(..., description="资产类型")
    description: Optional[str] = Field(None, description="资产描述")
    image_url: Optional[str] = Field(None, description="参考图 URL")
    visual_tokens: dict = Field(default_factory=dict, description="视觉 Token")
    prompts: dict = Field(default_factory=dict, description="生成 Prompt")


class AssetUpdate(BaseModel):
    """更新资产请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    visual_tokens: Optional[dict] = Field(None)
    prompts: Optional[dict] = Field(None)


@router.get("/{project_id}/assets", response_model=PaginatedResponse[AssetResponseData])
async def list_assets(
    project_id: UUID,
    asset_type: Optional[Literal["character", "location", "prop"]] = Query(
        None, description="资产类型过滤"
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: DatabaseService = Depends(get_db_service),
):
    """获取项目的资产列表"""
    # 验证项目是否存在
    project = await db.get_project(str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 注意：数据库层可能没有 list_assets 方法，这里需要模拟返回
    # 实际项目中应该查询 assets 表
    offset = (page - 1) * page_size

    # 模拟返回空列表（实际应查询数据库）
    assets = []
    total = 0

    return PaginatedResponse.of(assets, total, page, page_size)


@router.get("/assets/{asset_id}", response_model=SuccessResponse[AssetResponseData])
async def get_asset(
    asset_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """获取单个资产详情"""
    # 注意：数据库层需要实现 get_asset 方法
    # 这里模拟返回 404
    raise HTTPException(status_code=404, detail="Asset not found")


@router.post(
    "/{project_id}/assets",
    response_model=SuccessResponse[AssetResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def create_asset(
    project_id: UUID,
    data: AssetCreate,
    db: DatabaseService = Depends(get_db_service),
):
    """创建资产"""
    # 验证项目是否存在
    project = await db.get_project(str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 注意：数据库层需要实现 create_asset 方法
    # 这里模拟创建
    asset = {
        "asset_id": str(UUID(int=0)),  # 临时ID
        "project_id": str(project_id),
        "name": data.name,
        "asset_type": data.asset_type,
        "visual_tokens": data.visual_tokens,
        "reference_urls": [data.image_url] if data.image_url else [],
        "prompts": data.prompts,
        "created_at": None,
        "updated_at": None,
    }
    logger.info("Asset created", asset_id=asset["asset_id"])
    return SuccessResponse.of(AssetResponseData(**asset))


@router.patch("/assets/{asset_id}", response_model=SuccessResponse[AssetResponseData])
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """更新资产"""
    # 注意：数据库层需要实现 update_asset 方法
    raise HTTPException(status_code=404, detail="Asset not found")


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: DatabaseService = Depends(get_db_service),
):
    """删除资产"""
    # 注意：数据库层需要实现 delete_asset 方法
    raise HTTPException(status_code=404, detail="Asset not found")
