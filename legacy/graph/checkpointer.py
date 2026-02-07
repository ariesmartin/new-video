"""
LangGraph Checkpointer

带有全局连接池的健壮 AsyncPostgresSaver 实现。
支持 PostgreSQL 持久化存储 LangGraph 状态检查点。

Reference:
- Context7: langgraph-checkpoint-postgres
- https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-postgres
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Any

import structlog
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from psycopg_pool import AsyncConnectionPool

from backend.config import settings

logger = structlog.get_logger(__name__)


class CheckpointerManager:
    """
    Checkpointer 管理器

    使用单例模式管理 AsyncPostgresSaver 实例和连接池。
    确保应用生命周期内只有一个连接池实例。
    """

    _instance = None
    _pool: AsyncConnectionPool | None = None
    _checkpointer: AsyncPostgresSaver | None = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """
        初始化 Checkpointer

        创建连接池和 AsyncPostgresSaver 实例，并设置数据库表。
        必须在应用启动时调用一次。
        """
        if self._initialized:
            logger.debug("Checkpointer already initialized")
            return

        try:
            # 创建异步连接池
            # 参考 Context7: 需要设置 autocommit=True 和 row_factory=dict_row
            self._pool = AsyncConnectionPool(
                conninfo=settings.database_url,
                min_size=2,
                max_size=10,
                kwargs={
                    "autocommit": True,
                    "row_factory": None,  # 使用默认，AsyncPostgresSaver 内部处理
                },
            )

            # 等待连接池准备就绪
            await self._pool.wait()
            logger.info("Postgres connection pool created", min_size=2, max_size=10)

            # 创建 AsyncPostgresSaver 实例，使用 JsonPlusSerializer 处理复杂类型
            async with self._pool.connection() as conn:
                self._checkpointer = AsyncPostgresSaver(
                    conn=conn, serde=JsonPlusSerializer(pickle_fallback=True)
                )

                # 首次使用需要设置数据库表
                await self._checkpointer.setup()
                logger.info("Postgres checkpointer tables created")

            self._initialized = True
            logger.info("Checkpointer manager initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize checkpointer", error=str(e))
            raise

    async def cleanup(self) -> None:
        """
        清理 Checkpointer 资源

        关闭连接池，释放数据库连接。
        应该在应用关闭时调用。
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._checkpointer = None
            self._initialized = False
            logger.info("Checkpointer manager cleaned up")

    @asynccontextmanager
    async def get_checkpointer(self) -> AsyncGenerator[AsyncPostgresSaver, None]:
        """
        获取 Checkpointer 实例（上下文管理器）

        使用方式:
            async with checkpointer_manager.get_checkpointer() as saver:
                graph = builder.compile(checkpointer=saver)
                result = await graph.ainvoke(input_data, config)

        Yields:
            AsyncPostgresSaver: 配置好的检查点保存器实例
        """
        if not self._initialized or not self._pool:
            raise RuntimeError("Checkpointer not initialized. Call initialize() first.")

        async with self._pool.connection() as conn:
            # 关键：使用 JsonPlusSerializer 确保消息正确序列化/反序列化
            saver = AsyncPostgresSaver(conn=conn, serde=JsonPlusSerializer(pickle_fallback=True))
            yield saver

    async def health_check(self) -> dict:
        """
        健康检查

        Returns:
            包含连接池状态的字典
        """
        if not self._pool:
            return {"status": "not_initialized", "pool_size": 0, "available": 0}

        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "pool_size": self._pool.get_stats().get("pool_size", 0),
            "available": self._pool.get_stats().get("available", 0),
        }


# 全局 Checkpointer 管理器实例
checkpointer_manager = CheckpointerManager()


# ===== Convenience Functions =====


async def init_checkpointer() -> None:
    """初始化 Checkpointer（在应用启动时调用）"""
    await checkpointer_manager.initialize()


async def close_checkpointer() -> None:
    """关闭 Checkpointer（在应用关闭时调用）"""
    await checkpointer_manager.cleanup()


@asynccontextmanager
async def get_checkpointer():
    """获取 Checkpointer 实例的快捷方式"""
    async with checkpointer_manager.get_checkpointer() as saver:
        yield saver


async def get_or_create_checkpointer():
    """获取或创建 Checkpointer 实例（向后兼容）

    重要：每次调用都返回一个新的 checkpointer 实例，使用新的数据库连接。
    不要缓存 checkpointer 实例，因为连接可能会关闭。

    Returns:
        tuple: (AsyncPostgresSaver, AsyncConnection) - checkpointer 和连接对象
               调用者需要在完成后使用 await checkpointer_manager._pool.putconn(conn) 归还连接
    """
    if not checkpointer_manager._initialized:
        await checkpointer_manager.initialize()

    # 从连接池获取新连接创建 checkpointer
    conn = await checkpointer_manager._pool.getconn()
    saver = AsyncPostgresSaver(conn=conn)
    return saver, conn
