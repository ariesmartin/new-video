from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.config import settings
from backend.api import (
    graph_router,
    projects_router,
    models_router,
    episodes_router,
    scenes_router,
    shots_router,
    canvas_router,
    connections_router,
    assets_router,
    themes_router,
)
from backend.services.database import DatabaseService
from backend.services.model_router import init_model_router
import structlog
import subprocess
import os
import signal

logger = structlog.get_logger(__name__)

# Global variables to track celery processes
celery_worker_process = None
celery_beat_process = None


def start_celery():
    """启动 Celery Worker 和 Beat 进程"""
    global celery_worker_process, celery_beat_process

    try:
        # Check if Redis is running
        import redis

        try:
            r = redis.from_url(settings.redis_url)
            r.ping()
            logger.info("Redis is running")
        except redis.ConnectionError:
            logger.error("Redis is not running! Celery will not work.")
            logger.info("Please start Redis: redis-server")
            return False

        # Get the project root directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)

        # Set PYTHONPATH to include project root
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root + ":" + env.get("PYTHONPATH", "")

        # Start Celery Worker
        logger.info("Starting Celery worker...")
        celery_worker_process = subprocess.Popen(
            [
                "python",
                "-m",
                "celery",
                "-A",
                "backend.tasks.celery_app",
                "worker",
                "--loglevel=info",
                "--concurrency=1",
                "-n",
                "worker@%h",
            ],
            cwd=backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Celery worker started (PID: {celery_worker_process.pid})")

        # Start Celery Beat
        logger.info("Starting Celery beat...")
        celery_beat_process = subprocess.Popen(
            [
                "python",
                "-m",
                "celery",
                "-A",
                "backend.tasks.celery_app",
                "beat",
                "--loglevel=info",
            ],
            cwd=backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(f"Celery beat started (PID: {celery_beat_process.pid})")

        return True

    except Exception as e:
        logger.error(f"Failed to start Celery: {e}")
        return False


def stop_celery():
    """停止 Celery Worker 和 Beat 进程"""
    global celery_worker_process, celery_beat_process

    logger.info("Stopping Celery processes...")

    # Stop Worker
    if celery_worker_process and celery_worker_process.poll() is None:
        try:
            celery_worker_process.terminate()
            celery_worker_process.wait(timeout=5)
            logger.info("Celery worker stopped")
        except subprocess.TimeoutExpired:
            celery_worker_process.kill()
            logger.info("Celery worker killed")
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")

    # Stop Beat
    if celery_beat_process and celery_beat_process.poll() is None:
        try:
            celery_beat_process.terminate()
            celery_beat_process.wait(timeout=5)
            logger.info("Celery beat stopped")
        except subprocess.TimeoutExpired:
            celery_beat_process.kill()
            logger.info("Celery beat killed")
        except Exception as e:
            logger.error(f"Error stopping beat: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup
    logger.info("Initializing services...")

    # Initialize database service
    from backend.services.database import init_db_service

    db_service = await init_db_service()
    logger.info("Database service initialized")

    init_model_router(db_service)
    logger.info("Model router initialized")

    # Start Celery (don't block startup if it fails)
    celery_started = start_celery()
    if celery_started:
        logger.info("Celery services started")
    else:
        logger.warning("Celery services failed to start. Manual cache generation required.")

    yield

    # Shutdown
    logger.info("Shutting down...")
    stop_celery()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Drama Studio API (Rebuilt)",
        description="Clean architecture backend for AI Drama Studio",
        version="4.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(graph_router)
    app.include_router(projects_router, prefix="/api")
    app.include_router(models_router, prefix="/api")
    app.include_router(episodes_router, prefix="/api")
    app.include_router(scenes_router, prefix="/api")
    app.include_router(shots_router, prefix="/api")
    app.include_router(canvas_router, prefix="/api")
    app.include_router(connections_router, prefix="/api")
    app.include_router(assets_router, prefix="/api")
    app.include_router(themes_router, prefix="/api")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "4.1.0", "features": ["workflow_plan", "multi_step"]}

    return app


app = create_app()
