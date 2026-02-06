"""
Storage Service

使用 httpx 直接调用 Supabase Storage API。
"""

import os
import uuid
from datetime import datetime, timezone

import httpx
import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)


class StorageService:
    """对象存储服务"""
    
    BUCKET_PRIVATE = "private-assets"
    BUCKET_PUBLIC = "public-publish"
    
    def __init__(self, base_url: str, service_key: str):
        self._base_url = base_url.rstrip("/")
        self._storage_url = f"{self._base_url}/storage/v1"
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        }
        self._client = httpx.AsyncClient(headers=self._headers, timeout=60.0)
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self._client.aclose()
    
    async def ensure_buckets_exist(self) -> None:
        """确保 Bucket 存在"""
        # 获取现有 buckets
        response = await self._client.get(f"{self._storage_url}/bucket")
        existing = {b["name"] for b in response.json()} if response.status_code == 200 else set()
        
        # 创建私有 bucket
        if self.BUCKET_PRIVATE not in existing:
            await self._client.post(
                f"{self._storage_url}/bucket",
                json={"id": self.BUCKET_PRIVATE, "name": self.BUCKET_PRIVATE, "public": False}
            )
            logger.info("Created private bucket", name=self.BUCKET_PRIVATE)
        
        # 创建公开 bucket
        if self.BUCKET_PUBLIC not in existing:
            await self._client.post(
                f"{self._storage_url}/bucket",
                json={"id": self.BUCKET_PUBLIC, "name": self.BUCKET_PUBLIC, "public": True}
            )
            logger.info("Created public bucket", name=self.BUCKET_PUBLIC)
    
    async def upload_file(
        self, project_id: str, content: bytes, filename: str,
        folder: str = "source", content_type: str = "application/octet-stream"
    ) -> str:
        """上传文件到私有 Bucket"""
        ext = os.path.splitext(filename)[1] or ""
        path = f"projects/{project_id}/{folder}/{uuid.uuid4().hex}{ext}"
        
        response = await self._client.post(
            f"{self._storage_url}/object/{self.BUCKET_PRIVATE}/{path}",
            content=content,
            headers={**self._headers, "Content-Type": content_type}
        )
        response.raise_for_status()
        
        logger.info("File uploaded", path=path)
        return path
    
    async def download_file(self, path: str, bucket: str | None = None) -> bytes:
        """下载文件"""
        bucket = bucket or self.BUCKET_PRIVATE
        response = await self._client.get(
            f"{self._storage_url}/object/{bucket}/{path}"
        )
        response.raise_for_status()
        return response.content
    
    async def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """获取临时 URL"""
        response = await self._client.post(
            f"{self._storage_url}/object/sign/{self.BUCKET_PRIVATE}/{path}",
            json={"expiresIn": expires_in}
        )
        response.raise_for_status()
        data = response.json()
        return f"{self._storage_url}{data.get('signedURL', '')}"
    
    async def get_public_url(self, path: str) -> str:
        """获取公开 URL"""
        return f"{self._storage_url}/object/public/{self.BUCKET_PUBLIC}/{path}"
    
    async def delete_file(self, path: str) -> bool:
        """删除文件"""
        try:
            response = await self._client.delete(
                f"{self._storage_url}/object/{self.BUCKET_PRIVATE}",
                json={"prefixes": [path]}
            )
            return response.status_code in (200, 204)
        except Exception:
            return False


_storage_service: StorageService | None = None


async def init_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService(
            base_url=settings.supabase_url,
            service_key=settings.supabase_key,
        )
        await _storage_service.ensure_buckets_exist()
        logger.info("Storage service initialized")
    return _storage_service


def get_storage_service() -> StorageService:
    if _storage_service is None:
        raise RuntimeError("Storage service not initialized")
    return _storage_service
