"""
Review API Routes

审阅相关的独立API端点
符合架构文档 15.4 审阅 API 设计
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

from backend.services.database import get_db_service
from backend.graph.workflows.quality_control_graph import (
    run_quality_review,
    run_chapter_review,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/review", tags=["review"])


# ===== 数据模型 =====


class ReReviewRequest(BaseModel):
    """重新审阅请求"""

    chapterId: Optional[str] = None  # 如为空则重新审阅全局


# ===== API 端点 =====


@router.get("/{project_id}/global")
async def get_global_review(project_id: str):
    """
    获取全局审阅报告

    获取大纲全局审阅结果，包含：
    - overallScore: 总体评分
    - categories: 6大分类评分
    - tensionCurve: 张力曲线
    - chapterReviews: 章节审阅映射
    """
    try:
        logger.info("Getting global review", project_id=project_id)

        db = get_db_service()
        review = await db.get_outline_review(project_id, review_type="global")

        if not review:
            raise HTTPException(status_code=404, detail="全局审阅结果不存在，请先触发审阅")

        return {"success": True, "review": review}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get global review", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"获取全局审阅失败: {str(e)}")


@router.get("/{project_id}/chapters/{chapter_id}")
async def get_chapter_review(project_id: str, chapter_id: str):
    """
    获取单章审阅详情

    获取指定章节的审阅结果
    """
    try:
        logger.info("Getting chapter review", project_id=project_id, chapter_id=chapter_id)

        db = get_db_service()
        review = await db.get_chapter_review(project_id, chapter_id)

        if not review:
            raise HTTPException(status_code=404, detail="单章审阅结果不存在")

        return {"success": True, "review": review}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get chapter review",
            project_id=project_id,
            chapter_id=chapter_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"获取单章审阅失败: {str(e)}")


@router.post("/{project_id}/re_review")
async def re_review(project_id: str, request: ReReviewRequest):
    """
    触发重新审阅

    - 如 chapterId 为空，重新审阅全局
    - 如 chapterId 不为空，重新审阅指定章节
    """
    try:
        logger.info("Triggering re-review", project_id=project_id, chapter_id=request.chapterId)

        db = get_db_service()

        if request.chapterId:
            # 重新审阅单章
            from backend.api.skeleton_builder import trigger_chapter_review

            review = await trigger_chapter_review(project_id, request.chapterId)

            return {
                "success": True,
                "message": f"章节 {request.chapterId} 重新审阅完成",
                "review": review,
            }
        else:
            # 重新审阅全局
            from backend.api.skeleton_builder import trigger_global_review

            # 获取大纲数据
            outline_data = await db.get_outline(project_id)
            if not outline_data:
                raise HTTPException(status_code=404, detail="大纲不存在")

            review = await trigger_global_review(project_id, outline_data)

            return {"success": True, "message": "全局审阅完成", "review": review}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to re-review", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"重新审阅失败: {str(e)}")


@router.get("/{project_id}/tension_curve")
async def get_tension_curve(project_id: str, chapter_id: Optional[str] = None):
    """
    获取张力曲线

    - 如 chapterId 为空，返回全局张力曲线
    - 如 chapterId 不为空，返回该章节的张力曲线（如有）
    """
    try:
        logger.info("Getting tension curve", project_id=project_id, chapter_id=chapter_id)

        db = get_db_service()

        if chapter_id:
            # 获取单章审阅中的张力数据
            review = await db.get_chapter_review(project_id, chapter_id)
            if not review:
                raise HTTPException(status_code=404, detail="章节审阅结果不存在")

            return {
                "success": True,
                "chapterId": chapter_id,
                "tensionData": review.get("tensionData", {}),
            }
        else:
            # 获取全局审阅中的张力曲线
            review = await db.get_outline_review(project_id, review_type="global")
            if not review:
                raise HTTPException(status_code=404, detail="全局审阅结果不存在")

            return {"success": True, "tensionCurve": review.get("tensionCurve", [])}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get tension curve", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"获取张力曲线失败: {str(e)}")


@router.get("/{project_id}/status")
async def get_review_status(project_id: str):
    """
    获取审阅状态概览

    返回项目所有章节的审阅状态统计
    """
    try:
        logger.info("Getting review status", project_id=project_id)

        db = get_db_service()

        # 获取全局审阅
        global_review = await db.get_outline_review(project_id, review_type="global")

        if not global_review:
            return {
                "success": True,
                "status": "not_reviewed",
                "message": "尚未进行审阅",
                "statistics": {
                    "totalChapters": 0,
                    "passed": 0,
                    "warning": 0,
                    "error": 0,
                    "notReviewed": 0,
                },
            }

        # 统计章节审阅状态
        chapter_reviews = global_review.get("chapterReviews", {})

        stats = {
            "totalChapters": len(chapter_reviews),
            "passed": 0,
            "warning": 0,
            "error": 0,
            "notReviewed": 0,
        }

        for chapter_review in chapter_reviews.values():
            status = chapter_review.get("status", "not_reviewed")
            if status in stats:
                stats[status] += 1

        return {
            "success": True,
            "status": "reviewed",
            "overallScore": global_review.get("overallScore", 0),
            "statistics": stats,
            "lastReviewedAt": global_review.get("generatedAt"),
            "summary": global_review.get("summary", ""),
        }

    except Exception as e:
        logger.error("Failed to get review status", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"获取审阅状态失败: {str(e)}")
