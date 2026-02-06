"""
API Dependencies

认证和授权依赖项。支持 Supabase Auth JWT 验证。
"""

from typing import Annotated
from uuid import UUID
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from backend.config import settings

logger = structlog.get_logger(__name__)

# JWT Bearer Token 提取器
security = HTTPBearer(auto_error=False)


class AuthUser:
    """
    认证用户信息
    """

    def __init__(self, user_id: str, email: str | None = None, role: str = "authenticated"):
        self.id = user_id
        self.email = email
        self.role = role

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email})"


async def verify_jwt(token: str) -> dict:
    """
    验证 Supabase JWT Token

    通过调用 Supabase Auth API 验证 Token 有效性。
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={
                "apikey": settings.supabase_anon_key,
                "Authorization": f"Bearer {token}",
            },
            timeout=10.0,
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            logger.error(
                "Auth verification failed", status=response.status_code, body=response.text
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthUser:
    """
    获取当前认证用户

    从 JWT Token 中提取用户信息。

    开发模式: 如果没有 Token 但 DEBUG=True，返回测试用户。
    生产模式: 必须提供有效 Token。
    """
    # 开发模式: 允许匿名访问
    if credentials is None:
        if settings.debug:
            logger.warning("No auth token provided, using dev user")
            return AuthUser(
                user_id="00000000-0000-0000-0000-000000000001",
                email="dev@local.test",
                role="authenticated",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 JWT
    token = credentials.credentials
    user_data = await verify_jwt(token)

    return AuthUser(
        user_id=user_data.get("id"),
        email=user_data.get("email"),
        role=user_data.get("role", "authenticated"),
    )


async def get_current_user_id(
    user: AuthUser = Depends(get_current_user),
) -> str:
    """
    获取当前用户 ID (简化版本)

    用于只需要 user_id 的场景。
    """
    return user.id


# 类型别名，方便使用
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def require_authenticated(user: CurrentUser) -> AuthUser:
    """
    要求已认证用户 (非匿名)

    生产环境使用此依赖确保必须登录。
    """
    if user.id == "00000000-0000-0000-0000-000000000001" and settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Anonymous access not allowed in production",
        )
    return user
