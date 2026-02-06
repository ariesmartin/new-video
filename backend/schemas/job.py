"""
Job Queue Schemas

异步任务队列的数据模型。
对应数据库表: job_queue
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """任务状态"""
    PENDING = "PENDING"       # 等待执行
    RUNNING = "RUNNING"       # 执行中
    COMPLETED = "COMPLETED"   # 完成
    FAILED = "FAILED"         # 失败
    CANCELLED = "CANCELLED"   # 已取消
    DEAD_LETTER = "DEAD_LETTER"  # 僵尸任务 (被 Watchdog 清理)


class JobType(str, Enum):
    """任务类型"""
    # Agent 推理任务
    AGENT_REASONING = "agent_reasoning"
    
    # 内容生成任务
    NOVEL_WRITING = "novel_writing"
    SCRIPT_EXTRACTION = "script_extraction"
    STORYBOARD_GENERATION = "storyboard_generation"
    
    # 资产生成任务
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    
    # 批量任务
    BATCH_EXPORT = "batch_export"
    
    # 系统任务
    CHECKPOINT_CLEANUP = "checkpoint_cleanup"
    WATCHDOG_SCAN = "watchdog_scan"


class JobCreate(BaseModel):
    """创建任务请求"""
    project_id: UUID = Field(..., description="所属项目 ID")
    type: JobType = Field(..., description="任务类型")
    priority: int = Field(default=0, ge=0, le=10, description="优先级 (0-10, 10最高)")
    input_payload: dict[str, Any] = Field(default_factory=dict, description="任务输入参数")


class JobProgress(BaseModel):
    """任务进度更新"""
    progress_percent: int = Field(..., ge=0, le=100, description="进度百分比")
    current_step: str = Field(..., description="当前步骤描述")


class JobResponse(BaseModel):
    """任务响应"""
    job_id: UUID = Field(..., description="任务 ID")
    project_id: UUID = Field(..., description="所属项目 ID")
    type: JobType = Field(..., description="任务类型")
    status: JobStatus = Field(..., description="任务状态")
    priority: int = Field(..., description="优先级")
    
    # 进度
    progress_percent: int = Field(default=0, description="进度百分比")
    current_step: str | None = Field(None, description="当前步骤")
    
    # 输入输出
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_result: dict[str, Any] | None = Field(None, description="任务结果")
    error_message: str | None = Field(None, description="错误信息")
    
    # 生命周期
    created_at: datetime = Field(..., description="创建时间")
    started_at: datetime | None = Field(None, description="开始时间")
    ended_at: datetime | None = Field(None, description="结束时间")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440003",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "type": "novel_writing",
                "status": "RUNNING",
                "priority": 5,
                "progress_percent": 45,
                "current_step": "Generating episode 3...",
                "input_payload": {"episode_number": 3},
                "output_result": None,
                "error_message": None,
                "created_at": "2026-02-02T04:00:00Z",
                "started_at": "2026-02-02T04:00:05Z",
                "ended_at": None
            }
        }


class JobListFilter(BaseModel):
    """任务列表过滤条件"""
    project_id: UUID | None = None
    status: JobStatus | None = None
    type: JobType | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
