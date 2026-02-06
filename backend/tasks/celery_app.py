"""
Celery Application

Celery 配置和应用实例。
"""

from celery import Celery

from backend.config import settings

celery_app = Celery(
    "ai_video_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "backend.tasks.job_processor",
        "backend.tasks.market_analysis_task",  # 添加市场分析任务
    ],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # 任务设置
    task_track_started=True,
    task_time_limit=3600,  # 1 小时超时
    task_soft_time_limit=3300,  # 55 分钟软超时
    # 重试设置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # 并发设置
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    # 结果过期
    result_expires=86400,  # 24 小时
)

# 定时任务 (Beat)
celery_app.conf.beat_schedule = {
    "watchdog-scan": {
        "task": "backend.tasks.job_processor.watchdog_scan",
        "schedule": 300.0,  # 每 5 分钟
        "args": (),
    },
    "market-analysis-weekly": {
        "task": "backend.tasks.market_analysis_task.run_weekly_analysis",
        "schedule": 604800.0,  # 每周一次 (7天)
        "args": (),
    },
}
