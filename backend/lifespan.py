"""
Application Lifespan

FastAPI 应用生命周期管理。
处理启动和关闭时的资源初始化与清理。
"""

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI

from backend.config import settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期上下文管理器

    Startup:
    - 初始化 Supabase 客户端
    - 初始化 LangGraph Checkpointer
    - 初始化服务层
    - 创建 LangGraph 主图

    Shutdown:
    - 关闭数据库连接池
    - 清理资源
    """
    logger.info("Starting AI Video Engine", env=settings.app_env)

    db_service = None
    checkpointer = None

    # ===== Startup =====

    # 1. 初始化数据库服务
    try:
        from backend.services.database import init_db_service

        db_service = await init_db_service()
        logger.info("Database service initialized")
    except Exception as e:
        logger.warning("Database service initialization failed", error=str(e))

    # 2. 初始化存储服务 (可选)
    try:
        from backend.services.storage import init_storage_service

        await init_storage_service()
        logger.info("Storage service initialized")
    except Exception as e:
        logger.warning("Storage service initialization failed", error=str(e))

    # 3. 初始化 LangGraph Checkpointer
    try:
        from backend.graph.checkpointer import init_checkpointer

        checkpointer = await init_checkpointer()
        logger.info("Checkpointer initialized")
    except Exception as e:
        logger.warning("Checkpointer initialization failed", error=str(e))

    # 4. 预编译 LangGraph 主图（用于验证，实际使用时每个请求会创建新实例）
    # 注意：不再全局存储 Graph 实例，避免 asyncio Event Loop 冲突
    # 每个请求会调用 get_graph_for_request() 创建新的 Graph 实例
    logger.info("Graph will be created per-request to avoid event loop issues")

    # 5. 初始化模型路由器
    if db_service:
        try:
            from backend.services.model_router import init_model_router

            init_model_router(db_service)
            logger.info("Model router initialized")
        except Exception as e:
            logger.warning("Model router initialization failed", error=str(e))

    # 6. 初始化熔断器
    if settings.enable_circuit_breaker and db_service:
        try:
            from backend.services.circuit_breaker import init_circuit_breaker

            init_circuit_breaker(db_service)
            logger.info("Circuit breaker initialized")
        except Exception as e:
            logger.warning("Circuit breaker initialization failed", error=str(e))

    # 7. 验证 Redis 连接
    try:
        import redis.asyncio as redis

        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        logger.info("Redis connection verified")
    except Exception as e:
        logger.warning("Redis not available", error=str(e))

    # 8. 启动临时项目清理任务
    if db_service:
        try:
            # 启动时清理一次过期临时项目
            deleted = await db_service.cleanup_old_temp_projects(days=7)
            if deleted > 0:
                logger.info("Cleaned up old temp projects", count=deleted)
        except Exception as e:
            logger.warning("Failed to cleanup temp projects", error=str(e))

    logger.info(
        "Application startup complete",
        features={
            "vector_store": settings.enable_vector_store,
            "semantic_cache": settings.enable_semantic_cache,
            "time_travel": settings.enable_time_travel,
            "circuit_breaker": settings.enable_circuit_breaker,
            "watchdog": settings.enable_watchdog,
        },
    )

    yield  # 应用运行

    # ===== Shutdown =====
    logger.info("Shutting down AI Video Engine")

    # 关闭数据库连接
    if db_service:
        try:
            await db_service.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.warning("Failed to close database connection", error=str(e))

    # 关闭 Checkpointer 连接池
    try:
        from backend.graph.checkpointer import close_checkpointer

        await close_checkpointer()
        logger.info("Checkpointer connection closed")
    except Exception as e:
        logger.warning("Failed to close checkpointer", error=str(e))

    # 关闭存储服务连接
    try:
        from backend.services.storage import get_storage_service

        storage = get_storage_service()
        await storage.close()
        logger.info("Storage service connection closed")
    except Exception as e:
        logger.warning("Failed to close storage service", error=str(e))

    logger.info("Application shutdown complete")
