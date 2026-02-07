"""
Common API Response Schemas

定义通用的 API 响应格式，确保前后端协议一致。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """错误详情"""

    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    field: str | None = Field(None, description="出错字段 (校验错误时)")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid email format",
                "field": "email",
            }
        }


class APIResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式

    所有 API 端点都应返回此格式，确保前端处理一致。
    """

    success: bool = Field(..., description="请求是否成功")
    data: T | None = Field(None, description="响应数据")
    error: ErrorDetail | None = Field(None, description="错误详情 (失败时)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    request_id: str | None = Field(None, description="请求追踪 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Project A"},
                "error": None,
                "timestamp": "2026-02-02T04:00:00Z",
                "request_id": "req_abc123",
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应的简化版本"""

    model_config = ConfigDict(
        populate_by_name=True,
    )

    success: bool = True
    data: T

    @classmethod
    def of(cls, data: T) -> "SuccessResponse[T]":
        """工厂方法：创建成功响应"""
        return cls(data=data)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""

    success: bool = True
    data: list[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码 (从 1 开始)")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")

    @classmethod
    def of(
        cls,
        data: list[T],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PaginatedResponse[T]":
        """工厂方法：创建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="应用版本")
    uptime_seconds: float = Field(..., description="运行时间 (秒)")
    database: str = Field(..., description="数据库连接状态")
    redis: str = Field(..., description="Redis 连接状态")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime_seconds": 3600.5,
                "database": "connected",
                "redis": "connected",
            }
        }


class WebSocketMessage(BaseModel):
    """WebSocket 消息格式"""

    event: str = Field(..., description="事件类型")
    data: dict[str, Any] = Field(..., description="事件数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="消息时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "event": "job.progress",
                "data": {"job_id": "123", "percent": 45, "step": "Generating..."},
                "timestamp": "2026-02-02T04:00:00Z",
            }
        }


# ===== Server-Driven UI Protocol =====
# 用于 Agent 向前端发送可交互的操作按钮
# 架构遵循: Frontend-Design.md & 系统架构文档.md


class ActionButtonStyle(str, Enum):
    """按钮样式"""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"
    GHOST = "ghost"


class ActionButton(BaseModel):
    """
    操作按钮定义

    用于 Agent 向用户提供可选操作，如 "选择方案A"、"重新生成" 等。
    """

    label: str = Field(..., description="按钮显示文本")
    action: str = Field(..., description="操作标识符，如 'select_plan_a'")
    payload: dict[str, Any] = Field(default_factory=dict, description="操作参数")
    style: str = Field(default="primary", description="按钮样式: primary/secondary/danger/ghost")
    icon: str | None = Field(None, description="图标名称 (Lucide)")
    disabled: bool = Field(default=False, description="是否禁用")

    class Config:
        json_schema_extra = {
            "example": {
                "label": "选择方案 A",
                "action": "select_plan",
                "payload": {"plan_id": "plan_001"},
                "style": "primary",
                "icon": "CheckCircle",
            }
        }


class UIInteractionBlockType(str, Enum):
    """交互块类型"""

    ACTION_GROUP = "action_group"  # 操作按钮组
    SELECTION = "selection"  # 选择器
    CONFIRMATION = "confirmation"  # 确认对话框
    INPUT = "input"  # 输入表单
    FORM = "form"  # 表单类型


class FormField(BaseModel):
    """表单字段定义"""

    id: str = Field(..., description="字段唯一标识")
    label: str = Field(..., description="字段显示标签")
    type: str = Field(..., description="字段类型: number, text, select, textarea")
    placeholder: str | None = Field(None, description="占位提示文本")
    default: Any | None = Field(None, description="默认值")
    min: int | float | None = Field(None, description="最小值（数字类型）")
    max: int | float | None = Field(None, description="最大值（数字类型）")
    options: list[dict] | None = Field(None, description="选项列表（select类型）")


class UIInteractionBlock(BaseModel):
    """
    UI 交互块

    Agent 返回的结构化 UI 指令，前端解析后渲染为可交互组件。
    这是 Server-Driven UI 的核心数据结构。

    架构遵循: Frontend-Design.md Section 5
    """

    block_type: UIInteractionBlockType = Field(
        default=UIInteractionBlockType.ACTION_GROUP, description="交互块类型"
    )
    title: str | None = Field(None, description="标题，如 '请选择一个方案'")
    description: str | None = Field(None, description="描述文本")
    buttons: list[ActionButton] = Field(default_factory=list, description="操作按钮列表")
    data: dict[str, Any] = Field(default_factory=dict, description="附加数据")

    # 表单字段（用于 input 类型）
    form_fields: list[FormField] | None = Field(None, description="表单字段列表")

    # 显示控制
    dismissible: bool = Field(default=True, description="用户是否可以关闭")
    timeout_seconds: int | None = Field(None, description="自动消失时间 (秒)")

    class Config:
        json_schema_extra = {
            "example": {
                "block_type": "action_group",
                "title": "选择故事方案",
                "description": "以下是 AI 为您生成的三个方案，请选择一个继续。",
                "buttons": [
                    {
                        "label": "方案 A: 复仇之路",
                        "action": "select_plan",
                        "payload": {"plan_id": "a"},
                    },
                    {
                        "label": "方案 B: 浪漫逆袭",
                        "action": "select_plan",
                        "payload": {"plan_id": "b"},
                    },
                    {
                        "label": "融合方案",
                        "action": "fusion_plans",
                        "payload": {},
                        "style": "secondary",
                    },
                ],
                "dismissible": False,
            }
        }
