"""
Circuit Breaker Service

实现熔断器模式，保护 LLM API 调用。
"""

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, TypeVar
import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # 正常状态
    OPEN = "OPEN"          # 熔断状态
    HALF_OPEN = "HALF_OPEN"  # 半开状态


class CircuitBreaker:
    """
    熔断器
    
    防止 LLM API 崩坏或账号被封时的雪崩效应。
    规则: 1 分钟内失败 > 5 次 -> 开启熔断，5 分钟后进入半开状态试探。
    """
    
    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, db_service):
        self._db = db_service
        self._local_states: dict[str, dict[str, Any]] = {}
    
    async def can_execute(self, provider_id: str) -> bool:
        """检查是否可以执行请求"""
        if not settings.enable_circuit_breaker:
            return True
        
        state = await self._get_state(provider_id)
        
        if state["state"] == CircuitState.CLOSED:
            return True
        
        if state["state"] == CircuitState.OPEN:
            # 检查是否可以进入半开状态
            opened_at = state.get("opened_at")
            if opened_at:
                elapsed = (datetime.now(timezone.utc) - opened_at).total_seconds()
                if elapsed >= self.RECOVERY_TIMEOUT:
                    await self._set_state(provider_id, CircuitState.HALF_OPEN)
                    return True
            return False
        
        # HALF_OPEN: 允许试探请求
        return True
    
    async def record_success(self, provider_id: str) -> None:
        """记录成功"""
        state = await self._get_state(provider_id)
        
        if state["state"] == CircuitState.HALF_OPEN:
            # 试探成功，关闭熔断器
            await self._set_state(provider_id, CircuitState.CLOSED, failure_count=0)
            logger.info("Circuit breaker closed", provider_id=provider_id)
    
    async def record_failure(self, provider_id: str) -> None:
        """记录失败"""
        state = await self._get_state(provider_id)
        new_count = state.get("failure_count", 0) + 1
        
        if state["state"] == CircuitState.HALF_OPEN:
            # 试探失败，重新开启熔断
            await self._set_state(provider_id, CircuitState.OPEN, failure_count=new_count)
            logger.warning("Circuit breaker reopened", provider_id=provider_id)
        elif new_count >= self.FAILURE_THRESHOLD:
            # 达到阈值，开启熔断
            await self._set_state(provider_id, CircuitState.OPEN, failure_count=new_count)
            logger.warning("Circuit breaker opened", provider_id=provider_id, failures=new_count)
        else:
            # 更新失败计数
            await self._set_state(provider_id, state["state"], failure_count=new_count)
    
    async def _get_state(self, provider_id: str) -> dict[str, Any]:
        """获取熔断器状态"""
        # 优先从本地缓存获取
        if provider_id in self._local_states:
            return self._local_states[provider_id]
        
        # 从数据库获取
        db_state = await self._db.get_circuit_state(provider_id)
        if db_state:
            self._local_states[provider_id] = db_state
            return db_state
        
        # 初始化状态
        default = {"state": CircuitState.CLOSED, "failure_count": 0}
        self._local_states[provider_id] = default
        return default
    
    async def _set_state(
        self, provider_id: str, state: CircuitState, failure_count: int = 0
    ) -> None:
        """设置熔断器状态"""
        state_dict = {
            "state": state,
            "failure_count": failure_count,
            "opened_at": datetime.now(timezone.utc) if state == CircuitState.OPEN else None,
        }
        self._local_states[provider_id] = state_dict
        
        # 异步持久化到数据库
        await self._db.update_circuit_state(provider_id, state.value, failure_count)


_circuit_breaker: CircuitBreaker | None = None

def init_circuit_breaker(db_service) -> CircuitBreaker:
    global _circuit_breaker
    _circuit_breaker = CircuitBreaker(db_service)
    return _circuit_breaker

def get_circuit_breaker() -> CircuitBreaker:
    if _circuit_breaker is None:
        raise RuntimeError("Circuit breaker not initialized")
    return _circuit_breaker
