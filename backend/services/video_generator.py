"""
Video Generation Service

视频生成服务，支持多个视频生成 API：
- OpenAI Sora API
- Runway Gen-3 API
- Pika API

使用统一的接口封装不同的视频生成提供商。
"""

import asyncio
import httpx
import structlog
from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.config import settings

logger = structlog.get_logger(__name__)


class VideoProvider(str, Enum):
    """视频生成提供商"""

    SORA = "sora"
    RUNWAY = "runway"
    PIKA = "pika"


class VideoStatus(str, Enum):
    """视频生成状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoGenerationRequest:
    """视频生成请求"""

    prompt: str
    provider: VideoProvider
    negative_prompt: Optional[str] = None
    duration: Optional[int] = None  # 秒
    aspect_ratio: Optional[str] = None  # "16:9" 或 "9:16"


@dataclass
class VideoGenerationResult:
    """视频生成结果"""

    status: VideoStatus
    video_url: Optional[str] = None
    provider: Optional[VideoProvider] = None
    generation_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class VideoGenerator:
    """
    视频生成器

    统一的视频生成接口，支持多个提供商。
    从数据库 llm_providers 表读取视频生成 Provider 配置。
    """

    def __init__(self, db_service=None):
        self.db = db_service
        self._providers_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 60  # 缓存 60 秒

    async def _load_providers(self) -> dict:
        """从数据库加载视频生成 Provider 配置"""
        import time

        # 检查缓存
        if self._cache_timestamp and (time.time() - self._cache_timestamp) < self._cache_ttl:
            return self._providers_cache

        if not self.db:
            logger.error("Database service not available")
            return {}

        try:
            # 从数据库查询视频类型的 Provider
            from backend.schemas.model_config import ProviderType, ProtocolType

            providers_data = await self.db.list_providers_by_type(ProviderType.VIDEO)

            providers = {}
            for provider_data in providers_data:
                if not provider_data.get("is_active", True):
                    continue

                name = provider_data.get("name", "").lower()
                api_key = provider_data.get("api_key", "")

                if not api_key:
                    continue

                # 根据服务商名称创建对应的 Provider 实例
                if "sora" in name:
                    providers[VideoProvider.SORA] = SoraProvider(
                        api_key=api_key,
                        provider_id=str(provider_data.get("id")),
                    )
                elif "runway" in name:
                    providers[VideoProvider.RUNWAY] = RunwayProvider(
                        api_key=api_key,
                        provider_id=str(provider_data.get("id")),
                    )
                elif "pika" in name:
                    providers[VideoProvider.PIKA] = PikaProvider(
                        api_key=api_key,
                        provider_id=str(provider_data.get("id")),
                    )

            # 更新缓存
            self._providers_cache = providers
            self._cache_timestamp = time.time()

            logger.info(
                "Video providers loaded from database",
                count=len(providers),
                types=list(providers.keys()),
            )

            return providers

        except Exception as e:
            logger.error("Failed to load video providers from database", error=str(e))
            return self._providers_cache  # 返回缓存数据

    async def get_available_providers(self) -> list[VideoProvider]:
        """获取可用的视频生成提供商列表"""
        providers = await self._load_providers()
        return list(providers.keys())

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """生成视频"""
        providers = await self._load_providers()
        provider_impl = providers.get(request.provider)

        if not provider_impl:
            available = list(providers.keys())
            return VideoGenerationResult(
                status=VideoStatus.FAILED,
                error_message=f"Provider {request.provider} not available. Available: {available}",
            )

        try:
            return await provider_impl.generate(request)
        except Exception as e:
            logger.error("Video generation failed", error=str(e), provider=request.provider)
            return VideoGenerationResult(
                status=VideoStatus.FAILED, provider=request.provider, error_message=str(e)
            )

    async def get_status(
        self, provider: VideoProvider, generation_id: str
    ) -> VideoGenerationResult:
        """查询生成状态"""
        providers = await self._load_providers()
        provider_impl = providers.get(provider)

        if not provider_impl:
            return VideoGenerationResult(
                status=VideoStatus.FAILED, error_message=f"Provider {provider} not available"
            )

        try:
            return await provider_impl.get_status(generation_id)
        except Exception as e:
            logger.error("Get status failed", error=str(e), provider=provider)
            return VideoGenerationResult(
                status=VideoStatus.FAILED, provider=provider, error_message=str(e)
            )

    async def get_default_provider(self) -> Optional[VideoProvider]:
        """获取默认提供商"""
        providers = await self._load_providers()

        if providers:
            return list(providers.keys())[0]
        return None

    async def get_provider_by_id(self, provider_id: str) -> Optional[VideoProvider]:
        """通过数据库 ID 获取视频提供商类型"""
        providers = await self._load_providers()

        for vp_type, provider_impl in providers.items():
            if provider_impl.provider_id == provider_id:
                return vp_type
        return None


class SoraProvider:
    """OpenAI Sora API 提供商"""

    def __init__(self, api_key: str, provider_id: str | None = None):
        self.api_key = api_key
        self.provider_id = provider_id
        self.base_url = "https://api.openai.com/v1"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"}, timeout=60.0
        )

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """使用 Sora API 生成视频"""
        try:
            # Sora API 调用 (Beta API，可能变化)
            response = await self.client.post(
                f"{self.base_url}/videos/generations",
                json={
                    "model": "sora-1.0",
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    "duration": request.duration or 5,
                    "aspect_ratio": request.aspect_ratio or "16:9",
                },
            )

            response.raise_for_status()
            data = response.json()

            return VideoGenerationResult(
                status=VideoStatus.PROCESSING,
                provider=VideoProvider.SORA,
                generation_id=data.get("id"),
                created_at=datetime.now(),
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"Sora API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            return VideoGenerationResult(
                status=VideoStatus.FAILED, provider=VideoProvider.SORA, error_message=error_msg
            )

    async def get_status(self, generation_id: str) -> VideoGenerationResult:
        """查询 Sora 生成状态"""
        try:
            response = await self.client.get(f"{self.base_url}/videos/generations/{generation_id}")

            response.raise_for_status()
            data = response.json()

            status_map = {
                "pending": VideoStatus.PENDING,
                "processing": VideoStatus.PROCESSING,
                "completed": VideoStatus.COMPLETED,
                "failed": VideoStatus.FAILED,
            }

            return VideoGenerationResult(
                status=status_map.get(data.get("status"), VideoStatus.FAILED),
                provider=VideoProvider.SORA,
                generation_id=generation_id,
                video_url=data.get("url"),
                completed_at=datetime.now() if data.get("status") == "completed" else None,
            )

        except Exception as e:
            return VideoGenerationResult(
                status=VideoStatus.FAILED,
                provider=VideoProvider.SORA,
                generation_id=generation_id,
                error_message=str(e),
            )


class RunwayProvider:
    """Runway Gen-3 API 提供商"""

    def __init__(self, api_key: str, provider_id: str | None = None):
        self.api_key = api_key
        self.provider_id = provider_id
        self.base_url = "https://api.runwayml.com/v1"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"}, timeout=60.0
        )

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """使用 Runway API 生成视频"""
        try:
            response = await self.client.post(
                f"{self.base_url}/video/generations",
                json={
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    "duration": request.duration or 5,
                    "ratio": request.aspect_ratio or "16:9",
                },
            )

            response.raise_for_status()
            data = response.json()

            return VideoGenerationResult(
                status=VideoStatus.PROCESSING,
                provider=VideoProvider.RUNWAY,
                generation_id=data.get("id"),
                created_at=datetime.now(),
            )

        except Exception as e:
            logger.error("Runway API error", error=str(e))
            return VideoGenerationResult(
                status=VideoStatus.FAILED, provider=VideoProvider.RUNWAY, error_message=str(e)
            )

    async def get_status(self, generation_id: str) -> VideoGenerationResult:
        """查询 Runway 生成状态"""
        try:
            response = await self.client.get(f"{self.base_url}/video/generations/{generation_id}")

            response.raise_for_status()
            data = response.json()

            status_map = {
                "PENDING": VideoStatus.PENDING,
                "PROCESSING": VideoStatus.PROCESSING,
                "COMPLETED": VideoStatus.COMPLETED,
                "FAILED": VideoStatus.FAILED,
            }

            return VideoGenerationResult(
                status=status_map.get(data.get("status"), VideoStatus.FAILED),
                provider=VideoProvider.RUNWAY,
                generation_id=generation_id,
                video_url=data.get("url"),
                completed_at=datetime.now() if data.get("status") == "COMPLETED" else None,
            )

        except Exception as e:
            return VideoGenerationResult(
                status=VideoStatus.FAILED, provider=VideoProvider.RUNWAY, error_message=str(e)
            )


class PikaProvider:
    """Pika API 提供商"""

    def __init__(self, api_key: str, provider_id: str | None = None):
        self.api_key = api_key
        self.provider_id = provider_id
        self.base_url = "https://api.pika.art/v1"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"}, timeout=60.0
        )

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """使用 Pika API 生成视频"""
        try:
            response = await self.client.post(
                f"{self.base_url}/video/generations",
                json={
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    "duration": request.duration or 3,
                },
            )

            response.raise_for_status()
            data = response.json()

            return VideoGenerationResult(
                status=VideoStatus.PROCESSING,
                provider=VideoProvider.PIKA,
                generation_id=data.get("id"),
                created_at=datetime.now(),
            )

        except Exception as e:
            logger.error("Pika API error", error=str(e))
            return VideoGenerationResult(
                status=VideoStatus.FAILED, provider=VideoProvider.PIKA, error_message=str(e)
            )

    async def get_status(self, generation_id: str) -> VideoGenerationResult:
        """查询 Pika 生成状态"""
        try:
            response = await self.client.get(f"{self.base_url}/video/generations/{generation_id}")

            response.raise_for_status()
            data = response.json()

            status_map = {
                "queued": VideoStatus.PENDING,
                "processing": VideoStatus.PROCESSING,
                "completed": VideoStatus.COMPLETED,
                "failed": VideoStatus.FAILED,
            }

            return VideoGenerationResult(
                status=status_map.get(data.get("status"), VideoStatus.FAILED),
                provider=VideoProvider.PIKA,
                generation_id=generation_id,
                video_url=data.get("video_url"),
                completed_at=datetime.now() if data.get("status") == "completed" else None,
            )

        except Exception as e:
            return VideoGenerationResult(
                status=VideoStatus.FAILED, provider=VideoProvider.PIKA, error_message=str(e)
            )


# 全局视频生成器实例
_video_generator: Optional[VideoGenerator] = None


def get_video_generator() -> VideoGenerator:
    """获取视频生成器实例 (单例)"""
    global _video_generator
    if _video_generator is None:
        _video_generator = VideoGenerator()
    return _video_generator
