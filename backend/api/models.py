"""
Models API

LLM 服务商和模型配置管理端点。
"""

from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.schemas.model_config import (
    ModelProvider,
    ModelProviderCreate,
    ModelProviderUpdate,
    ModelMapping,
    ModelMappingCreate,
    ModelMappingUpdate,
    TaskType,
    ModelTestRequest,
    ModelTestResponse,
)
from backend.schemas.common import SuccessResponse
from backend.services import get_db_service, DatabaseService
from backend.api.deps import get_current_user_id

router = APIRouter(prefix="/models", tags=["Models"])
logger = structlog.get_logger(__name__)


# ===== Providers =====


@router.post(
    "/providers", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED
)
async def create_provider(
    data: ModelProviderCreate,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """添加 LLM 服务商"""
    provider = await db.create_provider(user_id, data.model_dump())
    logger.info("Provider created", provider_id=provider.get("id"))
    return SuccessResponse.of(provider)


@router.get("/providers", response_model=SuccessResponse[list[dict]])
async def list_providers(
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """获取服务商列表"""
    providers = await db.list_providers(user_id)
    # 脱敏 API Key
    for p in providers:
        if "api_key" in p:
            key = p["api_key"]
            p["api_key_preview"] = f"{key[:7]}...{key[-4:]}" if len(key) > 11 else "****"
            del p["api_key"]
    return SuccessResponse.of(providers)


@router.patch("/providers/{provider_id}", response_model=SuccessResponse[dict])
async def update_provider(
    provider_id: str,
    data: ModelProviderUpdate,
    db: DatabaseService = Depends(get_db_service),
):
    """更新 LLM 服务商"""
    provider = await db.update_provider(provider_id, data.model_dump(exclude_unset=True))
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return SuccessResponse.of(provider)


@router.delete("/providers/{provider_id}", response_model=SuccessResponse[None])
async def delete_provider(
    provider_id: str,
    db: DatabaseService = Depends(get_db_service),
):
    """删除 LLM 服务商"""
    success = await db.delete_provider(provider_id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    return SuccessResponse.of(None)


@router.post("/providers/test", response_model=ModelTestResponse)
async def test_provider(
    request: ModelTestRequest,
    db: DatabaseService = Depends(get_db_service),
):
    """测试服务商连接"""
    import time

    provider = await db.get_provider(str(request.provider_id))
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        from backend.services.model_router import ModelRouter

        # 创建临时模型实例
        router = ModelRouter(db)
        model = router._create_model(
            protocol=provider["protocol"],
            api_key=provider["api_key"],
            base_url=provider.get("base_url"),
            model_name=request.model_name,
            parameters={"temperature": 0.1, "max_tokens": 50},
        )

        start = time.time()
        response = await model.ainvoke(request.prompt)
        latency = (time.time() - start) * 1000

        # 成功后自动添加到可用模型列表
        current_models = provider.get("available_models") or []
        if request.model_name not in current_models:
            current_models.append(request.model_name)
            await db.update_provider(str(request.provider_id), {"available_models": current_models})

        return ModelTestResponse(
            success=True,
            response=str(response.content)[:200],
            latency_ms=latency,
        )
    except Exception as e:
        logger.error("Model test failed", error=str(e))
        return ModelTestResponse(
            success=False,
            error=str(e),
        )


@router.post("/providers/{provider_id}/refresh", response_model=SuccessResponse[list[str]])
async def refresh_provider_models(
    provider_id: str,
    db: DatabaseService = Depends(get_db_service),
):
    """从服务商 API 自动刷新模型列表"""
    import httpx

    provider = await db.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    protocol = provider.get("protocol", "openai")
    base_url = provider.get("base_url")
    api_key = provider.get("api_key", "")

    # 构造请求
    fetched_models = []

    try:
        if protocol == "openai" or protocol == "azure":
            # 标准 /v1/models
            url = (
                f"{base_url.rstrip('/')}/models" if base_url else "https://api.openai.com/v1/models"
            )
            headers = {"Authorization": f"Bearer {api_key}"}

            # 处理 Local/Ollama 可能不需要 Key
            if "localhost" in url or "127.0.0.1" in url or "0.0.0.0" in url:
                if not api_key:
                    headers = {}

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                # OpenAI format: {"data": [{"id": "gpt-4"}, ...]}
                # Ollama format (api/tags): {"models": [{"name": "llama3"}, ...]}

                if "data" in data:
                    fetched_models = [m["id"] for m in data["data"]]
                elif "models" in data:
                    fetched_models = [m.get("id") or m.get("name") for m in data["models"]]
                else:
                    logger.warning("Unknown models response format", data_keys=list(data.keys()))

        elif protocol == "gemini":
            # Google Gemini List Models
            # URL: https://generativelanguage.googleapis.com/v1beta/models?key=API_KEY
            # Custom Base URL might be used by proxies

            base = base_url.rstrip("/") if base_url else "https://generativelanguage.googleapis.com"
            # Ensure v1beta/models is reachable. Some proxies might map root directly.
            # Try standard Google path first if default base_url
            if "generativelanguage.googleapis.com" in base:
                url = f"{base}/v1beta/models?key={api_key}"
            else:
                # Assumption: Local proxy follows similar structure or just /models
                # Try /models first as good practice for proxies
                url = f"{base}/models"

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Google API Key is usually in query param, causing header issues in some proxies if put in Bearer
                # But let's try standard request
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    if "models" in data:
                        # name is "models/gemini-pro", displayName is "Gemini 1.0 Pro"
                        # We usually want the part after models/
                        fetched_models = [m["name"].replace("models/", "") for m in data["models"]]
                except Exception:
                    # Retry with /v1/models or other common paths if the first failed and it's a local proxy
                    if base_url:
                        url_alt = f"{base}/v1/models"
                        resp = await client.get(url_alt)
                        resp.raise_for_status()
                        data = resp.json()
                        if "data" in data:  # OpenAI style proxy for Gemini
                            fetched_models = [m["id"] for m in data["data"]]

        if fetched_models:
            # 合并去重
            current = set(provider.get("available_models") or [])
            current.update(fetched_models)
            new_list = sorted(list(current))

            await db.update_provider(provider_id, {"available_models": new_list})
            return SuccessResponse.of(new_list)
        else:
            return SuccessResponse.of(provider.get("available_models") or [])

    except Exception as e:
        logger.error("Failed to refresh models", error=str(e))
        # Don't fail hard, just return empty so UI doesn't crash, but can show error toast if we propagate
        # Better to propagate error description
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


# ===== Mappings =====


@router.get("/mappings", response_model=SuccessResponse[list[dict]])
async def list_mappings(
    project_id: UUID | None = None,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """获取任务-模型映射列表"""
    mappings = await db.list_mappings(user_id, str(project_id) if project_id else None)
    return SuccessResponse.of(mappings)


@router.post("/mappings", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_mapping(
    data: ModelMappingCreate,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """创建任务-模型映射"""
    mapping = await db.create_mapping(user_id, data.model_dump(mode="json"))
    logger.info("Mapping created", task_type=data.task_type)
    return SuccessResponse.of(mapping)


@router.patch("/mappings/{mapping_id}", response_model=SuccessResponse[dict])
async def update_mapping(
    mapping_id: UUID,
    data: ModelMappingUpdate,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """更新任务-模型映射"""
    mapping = await db.update_mapping(
        str(mapping_id), data.model_dump(mode="json", exclude_unset=True)
    )
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    logger.info("Mapping updated", mapping_id=str(mapping_id))
    return SuccessResponse.of(mapping)


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(
    mapping_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: DatabaseService = Depends(get_db_service),
):
    """删除任务-模型映射"""
    success = await db.delete_mapping(str(mapping_id))
    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")
    logger.info("Mapping deleted", mapping_id=str(mapping_id))


@router.get("/task-types", response_model=SuccessResponse[list[dict]])
async def list_task_types():
    """获取所有任务类型"""
    task_types = [{"value": t.value, "label": t.name.replace("_", " ").title()} for t in TaskType]
    return SuccessResponse.of(task_types)


@router.get("/category-task-type-mapping", response_model=SuccessResponse[dict[str, str]])
async def get_category_task_type_mapping():
    """获取 TaskCategory 到 TaskType 的映射关系"""
    mapping = {
        "creative": "novel_writer",
        "content": "script_formatter",
        "quality": "editor",
        "video": "storyboard_director",
        "image_process": "image_enhancer",
    }
    return SuccessResponse.of(mapping)
