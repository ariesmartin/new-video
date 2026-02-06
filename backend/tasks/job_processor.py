"""
Job Processor

异步任务处理器。
"""

import asyncio
from datetime import datetime, timedelta, timezone
import structlog

from backend.tasks.celery_app import celery_app
from backend.schemas.job import JobStatus, JobProgress
from backend.api.websocket import publish_event

logger = structlog.get_logger(__name__)


def run_async(coro):
    """在 Celery Task 中运行异步代码"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def process_job(self, job_id: str):
    """处理异步任务"""
    return run_async(_process_job_async(self, job_id))


async def _process_job_async(task, job_id: str):
    """异步任务处理逻辑"""
    from backend.services.database import init_db_service

    logger.info("Processing job", job_id=job_id)

    db = await init_db_service()
    job = await db.get_job(job_id)

    if not job:
        logger.error("Job not found", job_id=job_id)
        return

    # 更新状态为运行中
    await db.update_job_status(
        job_id, JobStatus.RUNNING, progress_percent=0, current_step="Initializing..."
    )

    # 发布任务开始事件（失败不影响主流程）
    try:
        await publish_event(
            str(job.project_id),
            "job.started",
            {
                "job_id": job_id,
                "type": job.type.value,
                "status": "running",
                "progress": 0,
            },
        )
    except Exception as e:
        logger.warning("Failed to publish WebSocket event", error=str(e))
        # 不影响主流程

    try:
        # 根据任务类型执行不同逻辑
        job_type = job.type.value

        if job_type == "novel_writing":
            await _process_novel_writing(db, job)
        elif job_type == "video_generation":
            await _process_video_generation(db, job)
        else:
            # 通用处理
            await db.update_job_progress(
                job_id, JobProgress(progress_percent=100, current_step="Completed")
            )

        # 标记完成
        await db.update_job_status(
            job_id, JobStatus.COMPLETED, progress_percent=100, current_step="Done"
        )

        # 发布任务完成事件（失败不影响主流程）
        try:
            await publish_event(
                str(job.project_id),
                "job.completed",
                {
                    "job_id": job_id,
                    "type": job.type.value,
                    "status": "completed",
                    "progress": 100,
                },
            )
        except Exception as e:
            logger.warning("Failed to publish WebSocket event", error=str(e))
            # 不影响主流程

        logger.info("Job completed", job_id=job_id)

    except Exception as e:
        logger.error("Job failed", job_id=job_id, error=str(e))
        await db.update_job_status(job_id, JobStatus.FAILED, error_message=str(e))

        # 发布任务失败事件（失败不影响主流程）
        try:
            await publish_event(
                str(job.project_id),
                "job.failed",
                {
                    "job_id": job_id,
                    "type": job.type.value,
                    "status": "failed",
                    "error": str(e),
                },
            )
        except Exception as ws_e:
            logger.warning("Failed to publish WebSocket event", error=str(ws_e))
            # 不影响主流程
        raise


async def _process_novel_writing(db, job):
    """处理小说写作任务"""
    from backend.graph import get_compiled_graph

    project_id = str(job.project_id)
    input_payload = job.input_payload or {}

    # 获取或创建 Graph 状态
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": project_id}}

    # 执行 Graph
    async for event in graph.astream_events(input_payload, config, version="v2"):
        # 更新进度
        if event.get("event") == "on_chain_end":
            node = event.get("name", "")
            progress = _calculate_progress(node)
            await db.update_job_progress(
                str(job.job_id),
                JobProgress(progress_percent=progress, current_step=f"Processing {node}"),
            )

            # 发布进度更新事件（失败不影响主流程）
            try:
                await publish_event(
                    project_id,
                    "job.progress",
                    {
                        "job_id": str(job.job_id),
                        "type": job.type.value,
                        "progress": progress,
                        "current_step": f"Processing {node}",
                    },
                )
            except Exception as e:
                logger.warning("Failed to publish WebSocket event", error=str(e))
                # 不影响主流程


async def _process_video_generation(db, job):
    """
    处理视频生成任务

    视频生成流程:
    1. 从 job.input_payload 获取分镜数据
    2. 调用视频生成 API (Sora, Runway, Pika)
    3. 轮询生成状态
    4. 下载结果并存储到 Storage
    """
    from backend.services.video_generator import (
        VideoGenerator,
        VideoGenerationRequest,
        VideoProvider,
    )

    job_id = str(job.job_id)
    input_payload = job.input_payload or {}

    storyboard_shots = input_payload.get("shots", [])
    provider_name = input_payload.get("provider", "runway")

    # 初始化视频生成器
    video_gen = VideoGenerator()
    provider = (
        VideoProvider(provider_name)
        if provider_name in ["sora", "runway", "pika"]
        else video_gen.get_default_provider()
    )

    if not provider:
        logger.error("No video provider available", job_id=job_id)
        await db.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message="No video provider configured. Please set SORA_API_KEY, RUNWAY_API_KEY, or PIKA_API_KEY in environment.",
        )
        return

    if not storyboard_shots:
        logger.warning("No shots in payload", job_id=job_id)
        await db.update_job_progress(
            job_id, JobProgress(progress_percent=100, current_step="No shots to process")
        )
        return

    total_shots = len(storyboard_shots)
    results = []

    for i, shot in enumerate(storyboard_shots):
        shot_number = shot.get("shot_number", f"S{i + 1:02d}")
        prompt = shot.get("nano_banana_prompt", shot.get("visual_description", ""))

        # 更新进度
        progress = int((i / total_shots) * 100)
        await db.update_job_progress(
            job_id,
            JobProgress(
                progress_percent=progress,
                current_step=f"Generating shot {shot_number} ({i + 1}/{total_shots}) with {provider.value}...",
            ),
        )

        # 调用视频生成 API
        try:
            request = VideoGenerationRequest(
                prompt=prompt,
                provider=provider,
                duration=shot.get("duration", 5),
                aspect_ratio=shot.get("aspect_ratio", "16:9"),
            )

            # 提交生成任务
            gen_result = await video_gen.generate(request)

            if gen_result.status.value == "processing":
                # 轮询生成状态
                generation_id = gen_result.generation_id
                max_retries = 60  # 最多轮询 60 次 (5分钟)
                retry_count = 0

                while retry_count < max_retries:
                    await asyncio.sleep(5)  # 每 5 秒检查一次
                    status_result = await video_gen.get_status(provider, generation_id)

                    # 更新进度
                    poll_progress = min(95, progress + int((retry_count / max_retries) * 30))
                    await db.update_job_progress(
                        job_id,
                        JobProgress(
                            progress_percent=poll_progress,
                            current_step=f"Shot {shot_number}: {status_result.status.value}...",
                        ),
                    )

                    if status_result.status.value == "completed":
                        results.append(
                            {
                                "shot_number": shot_number,
                                "video_url": status_result.video_url,
                                "generation_id": generation_id,
                                "status": "completed",
                                "provider": provider.value,
                            }
                        )
                        break
                    elif status_result.status.value == "failed":
                        results.append(
                            {
                                "shot_number": shot_number,
                                "status": "failed",
                                "error": status_result.error_message or "Generation failed",
                                "provider": provider.value,
                            }
                        )
                        break

                    retry_count += 1

                if retry_count >= max_retries:
                    results.append(
                        {
                            "shot_number": shot_number,
                            "status": "timeout",
                            "error": "Generation timeout after 5 minutes",
                            "provider": provider.value,
                        }
                    )
            else:
                # 生成失败或未启动
                results.append(
                    {
                        "shot_number": shot_number,
                        "status": gen_result.status.value,
                        "error": gen_result.error_message or "Failed to start generation",
                        "provider": provider.value,
                    }
                )

        except Exception as e:
            logger.error("Shot generation failed", job_id=job_id, shot=shot_number, error=str(e))
            results.append(
                {
                    "shot_number": shot_number,
                    "status": "failed",
                    "error": str(e),
                    "provider": provider.value,
                }
            )

    # 存储结果到 output_payload - 使用正确的 DatabaseService 方法
    await db.update_job_status(
        job_id=job_id,
        status=JobStatus.COMPLETED
        if all(r.get("status") == "completed" for r in results)
        else JobStatus.FAILED,
        output_payload={
            "videos": results,
            "provider": provider.value,
            "total_shots": total_shots,
            "completed_shots": len([r for r in results if r.get("status") == "completed"]),
        },
    )

    # 同时存储到 video_results 表
    for result in results:
        if result.get("status") == "completed":
            try:
                await db.create_video_result(
                    job_id=job_id,
                    shot_number=result["shot_number"],
                    video_url=result["video_url"],
                    provider=provider.value,
                    generation_id=result.get("generation_id"),
                )
            except Exception as e:
                logger.error("Failed to save video result", error=str(e))

    logger.info(
        "Video generation completed",
        job_id=job_id,
        total=total_shots,
        success=len([r for r in results if r.get("status") == "completed"]),
        provider=provider.value,
    )


def _calculate_progress(node_name: str) -> int:
    """根据节点名称计算进度"""
    progress_map = {
        "market_analyst": 10,
        "story_planner": 20,
        "skeleton_builder": 30,
        "writer": 50,
        "editor": 70,
        "refiner": 80,
        "save_and_exit": 100,
    }
    return progress_map.get(node_name, 50)


@celery_app.task
def watchdog_scan():
    """看门狗任务：清理僵尸任务"""
    return run_async(_watchdog_scan_async())


async def _watchdog_scan_async():
    """异步看门狗逻辑"""
    from backend.services.database import init_db_service
    from backend.config import settings

    if not settings.enable_watchdog:
        return

    logger.info("Watchdog scan started")

    db = await init_db_service()

    # 查找超时的 RUNNING 任务 (15分钟无心跳)
    threshold = datetime.now(timezone.utc) - timedelta(minutes=15)
    threshold_str = threshold.isoformat()

    # 查询超时的 RUNNING 任务 - 使用正确的 DatabaseService 方法
    try:
        # 获取所有 RUNNING 状态的任务
        all_jobs = await db.list_jobs(status="running", limit=1000)

        # 筛选超时的任务
        stale_jobs = []
        for job in all_jobs:
            updated_at = job.updated_at
            if updated_at and updated_at < threshold:
                stale_jobs.append(
                    {
                        "job_id": str(job.job_id),
                        "status": job.status.value,
                        "updated_at": updated_at.isoformat() if updated_at else None,
                    }
                )

        if stale_jobs:
            logger.warning("Found stale jobs", count=len(stale_jobs))

            for job in stale_jobs:
                job_id = job.get("job_id")

                # 更新为 DEAD_LETTER 状态 - 使用 update_job_status
                await db.update_job_status(
                    job_id=job_id,
                    status=JobStatus.FAILED,  # 使用 FAILED 状态代替 dead_letter
                    error_message=f"Watchdog: No heartbeat for 15+ minutes. Last update: {job.get('updated_at')}",
                )

                logger.info("Job marked as failed by watchdog", job_id=job_id)
        else:
            logger.debug("No stale jobs found")

    except Exception as e:
        logger.error("Watchdog scan failed", error=str(e))

    logger.info("Watchdog scan completed")
