"""
Market Analysis Task

Celery 定时任务：每周执行市场分析并缓存结果。
"""

import asyncio
import structlog

from backend.tasks.celery_app import celery_app
from backend.services.market_analysis import get_market_analysis_service

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def run_weekly_analysis(self):
    """
    每周市场分析任务

    执行搜索、分析、保存到数据库。
    供 Story Planner 后续读取使用。
    """
    logger.info("Starting weekly market analysis task")

    try:
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 执行分析
        result = loop.run_until_complete(_execute_analysis())

        logger.info("Weekly market analysis completed", genre_count=len(result.get("genres", [])))

        return {
            "status": "success",
            "genre_count": len(result.get("genres", [])),
            "insights": result.get("insights", "")[:100],
        }

    except Exception as e:
        logger.error("Weekly market analysis failed", error=str(e))
        # 重试
        raise self.retry(exc=e, countdown=3600)  # 1小时后重试


async def _execute_analysis():
    """执行实际的分析"""
    service = get_market_analysis_service()

    # 初始化数据库服务
    from backend.services.database import init_db_service
    from backend.config import settings

    init_db_service(settings.supabase_url, settings.supabase_key)

    # 执行分析
    result = await service.run_daily_analysis()

    return result
