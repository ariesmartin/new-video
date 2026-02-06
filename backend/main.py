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
)
from backend.services.database import DatabaseService
from backend.services.model_router import init_model_router
import structlog

logger = structlog.get_logger(__name__)


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
    yield
    # Shutdown
    logger.info("Shutting down...")


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

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "4.1.0", "features": ["workflow_plan", "multi_step"]}

    return app


app = create_app()
