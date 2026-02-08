"""
Cache Service for Theme Library

提供基于Redis的缓存服务，用于缓存题材库数据，减少数据库查询次数。
"""

import json
import pickle
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis
from redis import Redis
import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)


class ThemeCache:
    """
    Theme Library Cache Service

    使用Redis缓存题材库数据，支持：
    - 题材上下文缓存
    - 爆款元素缓存
    - 钩子模板缓存
    - 角色原型缓存
    - 市场趋势缓存

    默认TTL：1小时（3600秒）
    """

    DEFAULT_TTL = 3600  # 1小时
    KEY_PREFIX = "theme:"

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._initialized = False

    def initialize(self):
        """初始化Redis连接"""
        if self._initialized:
            return

        try:
            self._redis = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 测试连接
            self._redis.ping()
            self._initialized = True
            logger.info("ThemeCache initialized", redis_url=settings.redis_url)
        except Exception as e:
            logger.warning("Failed to connect to Redis, cache disabled", error=str(e))
            self._redis = None
            self._initialized = True  # 标记为已初始化，但缓存不可用

    def _get_key(self, key: str) -> str:
        """生成带前缀的缓存键"""
        return f"{self.KEY_PREFIX}{key}"

    def _hash_key(self, *args, **kwargs) -> str:
        """生成参数的哈希键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._redis:
            return None

        try:
            value = self._redis.get(self._get_key(key))
            if value:
                return pickle.loads(value.encode("latin1"))
            return None
        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL):
        """设置缓存值"""
        if not self._redis:
            return

        try:
            serialized = pickle.dumps(value).decode("latin1")
            self._redis.setex(self._get_key(key), ttl, serialized)
            logger.debug("Cache set", key=key, ttl=ttl)
        except Exception as e:
            logger.warning("Cache set failed", key=key, error=str(e))

    def delete(self, key: str):
        """删除缓存"""
        if not self._redis:
            return

        try:
            self._redis.delete(self._get_key(key))
            logger.debug("Cache deleted", key=key)
        except Exception as e:
            logger.warning("Cache delete failed", key=key, error=str(e))

    def clear_pattern(self, pattern: str):
        """删除匹配模式的所有缓存"""
        if not self._redis:
            return

        try:
            keys = self._redis.keys(self._get_key(pattern))
            if keys:
                self._redis.delete(*keys)
                logger.info("Cache cleared by pattern", pattern=pattern, count=len(keys))
        except Exception as e:
            logger.warning("Cache clear failed", pattern=pattern, error=str(e))

    # ===== Theme Library Specific Methods =====

    def get_genre_context(self, genre_id: str) -> Optional[str]:
        """获取缓存的题材上下文"""
        return self.get(f"context:{genre_id}")

    def set_genre_context(self, genre_id: str, context: str, ttl: int = DEFAULT_TTL):
        """缓存题材上下文"""
        self.set(f"context:{genre_id}", context, ttl)

    def get_tropes(self, genre_id: str, min_score: int, limit: int) -> Optional[str]:
        """获取缓存的爆款元素"""
        key = f"tropes:{genre_id}:{min_score}:{limit}"
        return self.get(key)

    def set_tropes(
        self, genre_id: str, min_score: int, limit: int, tropes: str, ttl: int = DEFAULT_TTL
    ):
        """缓存爆款元素"""
        key = f"tropes:{genre_id}:{min_score}:{limit}"
        self.set(key, tropes, ttl)

    def get_hooks(self, hook_type: str, limit: int) -> Optional[str]:
        """获取缓存的钩子模板"""
        key = f"hooks:{hook_type}:{limit}"
        return self.get(key)

    def set_hooks(self, hook_type: str, limit: int, hooks: str, ttl: int = DEFAULT_TTL):
        """缓存钩子模板"""
        key = f"hooks:{hook_type}:{limit}"
        self.set(key, hooks, ttl)

    def get_market_trends(self, genre_id: Optional[str] = None) -> Optional[str]:
        """获取缓存的市场趋势"""
        key = f"market_trends:{genre_id or 'all'}"
        return self.get(key)

    def set_market_trends(
        self, trends: str, genre_id: Optional[str] = None, ttl: int = DEFAULT_TTL
    ):
        """缓存市场趋势"""
        key = f"market_trends:{genre_id or 'all'}"
        self.set(key, trends, ttl)

    def get_character_archetypes(self, genre_id: str) -> Optional[str]:
        """获取缓存的角色原型"""
        return self.get(f"archetypes:{genre_id}")

    def set_character_archetypes(self, genre_id: str, archetypes: str, ttl: int = DEFAULT_TTL):
        """缓存角色原型"""
        self.set(f"archetypes:{genre_id}", archetypes, ttl)

    def get_writing_keywords(self, genre_id: str) -> Optional[str]:
        """获取缓存的写作关键词"""
        return self.get(f"keywords:{genre_id}")

    def set_writing_keywords(self, genre_id: str, keywords: str, ttl: int = DEFAULT_TTL):
        """缓存写作关键词"""
        self.set(f"keywords:{genre_id}", keywords, ttl)

    def invalidate_genre(self, genre_id: str):
        """使特定题材的所有缓存失效"""
        self.clear_pattern(f"*:{genre_id}:*")
        self.delete(f"context:{genre_id}")
        self.delete(f"archetypes:{genre_id}")
        self.delete(f"keywords:{genre_id}")
        self.delete(f"market_trends:{genre_id}")
        logger.info("Cache invalidated for genre", genre_id=genre_id)

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        if not self._redis:
            return {"enabled": False}

        try:
            theme_keys = len(self._redis.keys(f"{self.KEY_PREFIX}*"))
            info = self._redis.info()
            return {
                "enabled": True,
                "theme_keys": theme_keys,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
            }
        except Exception as e:
            logger.warning("Failed to get cache stats", error=str(e))
            return {"enabled": True, "error": str(e)}


# 全局缓存实例
theme_cache = ThemeCache()


def cached_theme(ttl: int = ThemeCache.DEFAULT_TTL):
    """
    装饰器：缓存题材库函数的结果

    Usage:
        @cached_theme(ttl=3600)
        def get_expensive_data(genre_id: str) -> str:
            return expensive_query()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{ThemeCache()._hash_key(*args, **kwargs)}"

            # 尝试从缓存获取
            cached_value = theme_cache.get(cache_key)
            if cached_value is not None:
                logger.debug("Cache hit", key=cache_key, func=func.__name__)
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            theme_cache.set(cache_key, result, ttl)
            logger.debug("Cache miss, stored result", key=cache_key, func=func.__name__)

            return result

        return wrapper

    return decorator


def initialize_cache():
    """初始化缓存服务（应用启动时调用）"""
    theme_cache.initialize()
    stats = theme_cache.get_stats()
    logger.info("Theme cache initialized", stats=stats)
