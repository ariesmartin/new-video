"""
API Package

FastAPI 路由定义。
"""

from backend.api.graph import router as graph_router
from backend.api.projects import router as projects_router
from backend.api.models import router as models_router
from backend.api.episodes import router as episodes_router
from backend.api.scenes import router as scenes_router
from backend.api.shots import router as shots_router
from backend.api.canvas import router as canvas_router
from backend.api.connections import router as connections_router
from backend.api.assets import router as assets_router
from backend.api.themes import router as themes_router

__all__ = [
    "graph_router",
    "projects_router",
    "models_router",
    "episodes_router",
    "scenes_router",
    "shots_router",
    "canvas_router",
    "connections_router",
    "assets_router",
    "themes_router",
]
