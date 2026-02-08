"""
Theme Library API

主题库 API 端点，提供题材、元素、钩子模板和案例的查询功能。
"""

from typing import Optional
from uuid import UUID
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.schemas.common import SuccessResponse, PaginatedResponse
from backend.services import get_db_service, DatabaseService
from backend.api.deps import get_current_user_id

router = APIRouter(prefix="/themes", tags=["Theme Library"])
logger = structlog.get_logger(__name__)


# ============================================================================
# Static routes (must be defined BEFORE parameterized routes)
# ============================================================================


@router.get("", response_model=SuccessResponse[list])
async def list_themes(
    category: Optional[str] = Query(None, description="按分类筛选: drama, romance, suspense, etc."),
    db: DatabaseService = Depends(get_db_service),
):
    """获取所有主题/题材列表

    返回系统中所有可用的短剧题材，包括复仇逆袭、甜宠恋爱、悬疑推理等。
    可按分类筛选。
    """
    try:
        # 构建查询参数
        params = {"select": "*", "order": "name.asc"}
        if category:
            params["category"] = f"eq.{category}"

        # 查询 themes 表
        import httpx

        response = await db._client.get(f"{db._rest_url}/themes", params=params)
        response.raise_for_status()
        themes = response.json() or []

        logger.info("Themes listed", count=len(themes), category=category)
        return SuccessResponse.of(themes)

    except Exception as e:
        logger.error("Failed to list themes", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch themes: {str(e)}",
        )


@router.get("/hooks/templates", response_model=PaginatedResponse[dict])
async def list_hook_templates(
    hook_type: Optional[str] = Query(None, description="钩子类型: situation, question, visual"),
    min_effectiveness: Optional[int] = Query(None, ge=0, le=100, description="最低有效性评分"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: DatabaseService = Depends(get_db_service),
):
    """获取所有钩子模板

    钩子模板用于短剧开头3秒吸引观众注意，提高留存率。
    支持按类型和有效性评分筛选。
    """
    try:
        # 构建查询
        params = {
            "select": "*",
            "order": "effectiveness_score.desc",
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }

        if hook_type:
            params["hook_type"] = f"eq.{hook_type}"
        if min_effectiveness is not None:
            params["effectiveness_score"] = f"gte.{min_effectiveness}"

        # 查询钩子模板
        response = await db._client.get(f"{db._rest_url}/hook_templates", params=params)
        response.raise_for_status()
        hooks = response.json() or []

        # 获取总数
        count_response = await db._client.get(
            f"{db._rest_url}/hook_templates",
            params={k: v for k, v in params.items() if k not in ["limit", "offset"]},
            headers={**db._headers, "Prefer": "count=exact"},
        )
        count_header = count_response.headers.get("content-range", "0-0/0")
        try:
            total = int(count_header.split("/")[1])
        except (ValueError, IndexError):
            total = len(hooks)

        logger.info("Hook templates listed", count=len(hooks), total=total)

        return PaginatedResponse.of(hooks, total, page, page_size)

    except Exception as e:
        logger.error("Failed to list hook templates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch hooks: {str(e)}",
        )


@router.get("/search/elements", response_model=SuccessResponse[list])
async def search_elements(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    theme_slug: Optional[str] = Query(None, description="限定主题"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: DatabaseService = Depends(get_db_service),
):
    """搜索爆款元素

    在元素名称和描述中搜索关键词，返回最相关的元素。
    可用于快速查找特定类型的元素。
    """
    try:
        # 构建基础查询
        params = {"select": "*,themes(name,slug)", "limit": limit}

        # 使用 ilike 进行模糊搜索
        if query:
            # 搜索名称或描述
            params["or"] = f"(name.ilike.*{query}*,description.ilike.*{query}*)"

        # 如果指定了主题，先获取主题ID
        if theme_slug:
            theme_response = await db._client.get(
                f"{db._rest_url}/themes", params={"slug": f"eq.{theme_slug}", "select": "id"}
            )
            theme_response.raise_for_status()
            themes = theme_response.json()
            if themes:
                params["theme_id"] = f"eq.{themes[0]['id']}"

        # 执行搜索
        response = await db._client.get(f"{db._rest_url}/theme_elements", params=params)
        response.raise_for_status()
        elements = response.json() or []

        logger.info("Elements searched", query=query, theme_slug=theme_slug, results=len(elements))

        return SuccessResponse.of(elements)

    except Exception as e:
        logger.error("Failed to search elements", query=query, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}"
        )


# ============================================================================
# Parameterized routes (must be defined AFTER static routes)
# ============================================================================


@router.get("/{theme_slug}", response_model=SuccessResponse[dict])
async def get_theme(
    theme_slug: str,
    include_elements: bool = Query(True, description="是否包含爆款元素"),
    include_hooks: bool = Query(True, description="是否包含钩子模板"),
    include_examples: bool = Query(True, description="是否包含标杆案例"),
    db: DatabaseService = Depends(get_db_service),
):
    """获取指定主题的详细信息

    包含：
    - 主题基本信息（名称、描述、核心公式）
    - 爆款元素列表（可选）
    - 钩子模板（可选）
    - 标杆案例（可选）
    """
    try:
        # 1. 获取主题基本信息
        response = await db._client.get(
            f"{db._rest_url}/themes", params={"slug": f"eq.{theme_slug}", "select": "*"}
        )
        response.raise_for_status()
        themes = response.json()

        if not themes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Theme '{theme_slug}' not found"
            )

        theme = themes[0]
        theme_id = theme["id"]

        # 2. 获取关联数据
        if include_elements:
            elements_response = await db._client.get(
                f"{db._rest_url}/theme_elements",
                params={
                    "theme_id": f"eq.{theme_id}",
                    "select": "*",
                    "order": "effectiveness_score.desc",
                },
            )
            elements_response.raise_for_status()
            theme["elements"] = elements_response.json() or []

        if include_hooks:
            # 钩子模板是全局的，不按主题筛选
            hooks_response = await db._client.get(
                f"{db._rest_url}/hook_templates",
                params={"select": "*", "order": "effectiveness_score.desc"},
            )
            hooks_response.raise_for_status()
            theme["hooks"] = hooks_response.json() or []

        if include_examples:
            examples_response = await db._client.get(
                f"{db._rest_url}/theme_examples",
                params={"theme_id": f"eq.{theme_id}", "select": "*", "order": "release_year.desc"},
            )
            examples_response.raise_for_status()
            theme["examples"] = examples_response.json() or []

        logger.info("Theme retrieved", theme_slug=theme_slug)
        return SuccessResponse.of(theme)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get theme", theme_slug=theme_slug, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch theme: {str(e)}",
        )


@router.get("/{theme_slug}/elements", response_model=PaginatedResponse[dict])
async def list_theme_elements(
    theme_slug: str,
    element_type: Optional[str] = Query(None, description="元素类型筛选"),
    min_effectiveness: Optional[int] = Query(None, ge=0, le=100, description="最低有效性评分"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: DatabaseService = Depends(get_db_service),
):
    """获取指定主题的所有爆款元素

    支持按元素类型筛选和有效性评分过滤。
    按有效性评分降序排列。
    """
    try:
        # 1. 获取主题ID
        theme_response = await db._client.get(
            f"{db._rest_url}/themes", params={"slug": f"eq.{theme_slug}", "select": "id"}
        )
        theme_response.raise_for_status()
        themes = theme_response.json()

        if not themes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Theme '{theme_slug}' not found"
            )

        theme_id = themes[0]["id"]

        # 2. 构建查询
        params = {
            "theme_id": f"eq.{theme_id}",
            "select": "*",
            "order": "effectiveness_score.desc",
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }

        if element_type:
            params["element_type"] = f"eq.{element_type}"
        if min_effectiveness is not None:
            params["effectiveness_score"] = f"gte.{min_effectiveness}"

        # 3. 查询元素
        response = await db._client.get(f"{db._rest_url}/theme_elements", params=params)
        response.raise_for_status()
        elements = response.json() or []

        # 4. 获取总数
        count_response = await db._client.get(
            f"{db._rest_url}/theme_elements",
            params={k: v for k, v in params.items() if k not in ["limit", "offset"]},
            headers={**db._headers, "Prefer": "count=exact"},
        )
        count_header = count_response.headers.get("content-range", "0-0/0")
        try:
            total = int(count_header.split("/")[1])
        except (ValueError, IndexError):
            total = len(elements)

        logger.info(
            "Theme elements listed", theme_slug=theme_slug, count=len(elements), total=total
        )

        return PaginatedResponse.of(elements, total, page, page_size)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list theme elements", theme_slug=theme_slug, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch elements: {str(e)}",
        )


@router.get("/{theme_slug}/examples", response_model=PaginatedResponse[dict])
async def list_theme_examples(
    theme_slug: str,
    example_type: Optional[str] = Query(None, description="案例类型: domestic, international"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    db: DatabaseService = Depends(get_db_service),
):
    """获取指定主题的所有标杆案例

    包含国内外成功的短剧案例，用于学习和参考。
    """
    try:
        # 1. 获取主题ID
        theme_response = await db._client.get(
            f"{db._rest_url}/themes", params={"slug": f"eq.{theme_slug}", "select": "id"}
        )
        theme_response.raise_for_status()
        themes = theme_response.json()

        if not themes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Theme '{theme_slug}' not found"
            )

        theme_id = themes[0]["id"]

        # 2. 构建查询
        params = {
            "theme_id": f"eq.{theme_id}",
            "select": "*",
            "order": "release_year.desc",
            "limit": page_size,
            "offset": (page - 1) * page_size,
        }

        if example_type:
            params["example_type"] = f"eq.{example_type}"

        # 3. 查询案例
        response = await db._client.get(f"{db._rest_url}/theme_examples", params=params)
        response.raise_for_status()
        examples = response.json() or []

        # 4. 获取总数
        count_response = await db._client.get(
            f"{db._rest_url}/theme_examples",
            params={k: v for k, v in params.items() if k not in ["limit", "offset"]},
            headers={**db._headers, "Prefer": "count=exact"},
        )
        count_header = count_response.headers.get("content-range", "0-0/0")
        try:
            total = int(count_header.split("/")[1])
        except (ValueError, IndexError):
            total = len(examples)

        logger.info(
            "Theme examples listed", theme_slug=theme_slug, count=len(examples), total=total
        )

        return PaginatedResponse.of(examples, total, page, page_size)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list theme examples", theme_slug=theme_slug, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch examples: {str(e)}",
        )


@router.post("/{theme_slug}/recommend", response_model=SuccessResponse[dict])
async def get_theme_recommendations(
    theme_slug: str,
    target_episode: int = Query(..., ge=1, le=100, description="目标集数"),
    emotion_target: Optional[str] = Query(
        None, description="目标情绪: tension, relief, excitement"
    ),
    db: DatabaseService = Depends(get_db_service),
):
    """获取针对特定场景的元素推荐

    根据目标集数和期望的情绪效果，推荐最合适的爆款元素组合。
    用于辅助编剧选择剧情转折点。
    """
    try:
        # 1. 获取主题信息
        theme_response = await db._client.get(
            f"{db._rest_url}/themes", params={"slug": f"eq.{theme_slug}", "select": "*"}
        )
        theme_response.raise_for_status()
        themes = theme_response.json()

        if not themes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Theme '{theme_slug}' not found"
            )

        theme = themes[0]
        theme_id = theme["id"]

        # 2. 获取该主题的所有元素
        elements_response = await db._client.get(
            f"{db._rest_url}/theme_elements",
            params={
                "theme_id": f"eq.{theme_id}",
                "select": "*",
                "order": "effectiveness_score.desc",
            },
        )
        elements_response.raise_for_status()
        elements = elements_response.json() or []

        # 3. 根据目标集数筛选适用的元素
        # 解析 usage_guidance 中的适用集数范围
        applicable_elements = []
        for elem in elements:
            guidance = elem.get("usage_guidance", "")
            # 简单判断：如果 guidance 包含目标集数或在范围内
            # 这里使用简化逻辑，实际可以更复杂
            if target_episode <= 5 and ("开头" in guidance or "铺垫" in guidance):
                applicable_elements.append(elem)
            elif 6 <= target_episode <= 30 and ("发展" in guidance or "升级" in guidance):
                applicable_elements.append(elem)
            elif 31 <= target_episode <= 70 and ("高潮" in guidance or "冲突" in guidance):
                applicable_elements.append(elem)
            elif target_episode > 70 and ("结局" in guidance or "收尾" in guidance):
                applicable_elements.append(elem)
            elif "全剧" in guidance or "任何" in guidance:
                applicable_elements.append(elem)

        # 4. 根据情绪目标进一步筛选
        if emotion_target and applicable_elements:
            emotion_keywords = {
                "tension": ["冲突", "紧张", "危机", "对峙", "压力"],
                "relief": ["解决", "和解", "释怀", "放下", "团圆"],
                "excitement": ["高潮", "爆发", "反击", "胜利", "反转"],
                "sweet": ["甜宠", "暧昧", "浪漫", "心动", "宠溺"],
                "mystery": ["悬疑", "揭秘", "追查", "线索", "真相"],
            }

            keywords = emotion_keywords.get(emotion_target, [])
            if keywords:
                filtered = []
                for elem in applicable_elements:
                    desc = elem.get("description", "")
                    emotional_impact = elem.get("emotional_impact", "")
                    if any(kw in desc or kw in emotional_impact for kw in keywords):
                        filtered.append(elem)

                if filtered:
                    applicable_elements = filtered

        # 5. 获取推荐的钩子模板
        hooks_response = await db._client.get(
            f"{db._rest_url}/hook_templates",
            params={"select": "*", "order": "effectiveness_score.desc", "limit": 3},
        )
        hooks_response.raise_for_status()
        recommended_hooks = hooks_response.json() or []

        # 6. 组装推荐结果
        recommendations = {
            "theme": theme,
            "target_episode": target_episode,
            "emotion_target": emotion_target,
            "recommended_elements": applicable_elements[:5],  # 前5个推荐
            "recommended_hooks": recommended_hooks,
            "core_formula": theme.get("core_formula", {}),
            "notes": f"基于第{target_episode}集的场景推荐，建议结合核心公式使用",
        }

        logger.info(
            "Recommendations generated",
            theme_slug=theme_slug,
            target_episode=target_episode,
            elements_count=len(applicable_elements),
        )

        return SuccessResponse.of(recommendations)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate recommendations", theme_slug=theme_slug, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )
