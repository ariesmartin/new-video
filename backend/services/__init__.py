"""
Services Package

业务逻辑服务层，封装数据库操作和外部服务调用。
"""

from backend.services.database import DatabaseService, get_db_service
from backend.services.storage import StorageService, get_storage_service
from backend.services.model_router import ModelRouter, get_model_router
from backend.services.circuit_breaker import CircuitBreaker, get_circuit_breaker
from backend.services.prompt_service import PromptService, get_prompt_service
from backend.services.sync_service import SyncService, get_sync_service
from backend.services.video_generator import (
    VideoGenerator,
    get_video_generator,
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoProvider,
    VideoStatus,
)

__all__ = [
    "DatabaseService",
    "get_db_service",
    "StorageService",
    "get_storage_service",
    "ModelRouter",
    "get_model_router",
    "CircuitBreaker",
    "get_circuit_breaker",
    "PromptService",
    "get_prompt_service",
    "SyncService",
    "get_sync_service",
    "VideoGenerator",
    "get_video_generator",
    "VideoGenerationRequest",
    "VideoGenerationResult",
    "VideoProvider",
    "VideoStatus",
]
