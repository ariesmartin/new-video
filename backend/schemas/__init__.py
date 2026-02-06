"""
Pydantic Schemas Package

所有数据模型定义，作为前后端的契约层 (Contract Layer)。
遵循 Type-First 原则：先定义类型，再实现逻辑。
"""

from backend.schemas.agent_state import AgentState
from backend.schemas.common import (
    APIResponse,
    ErrorDetail,
    PaginatedResponse,
    SuccessResponse,
)
from backend.schemas.job import (
    JobCreate,
    JobProgress,
    JobResponse,
    JobStatus,
    JobType,
)
from backend.schemas.model_config import (
    ModelMapping,
    ModelMappingCreate,
    ModelProvider,
    ModelProviderCreate,
    TaskType,
)
from backend.schemas.node import (
    NodeCreate,
    NodeLayoutUpdate,
    NodeResponse,
    NodeType,
    NodeUpdate,
)
from backend.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)

__all__ = [
    # Agent State
    "AgentState",
    # Common
    "APIResponse",
    "ErrorDetail",
    "PaginatedResponse",
    "SuccessResponse",
    # Project
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
    # Node
    "NodeCreate",
    "NodeResponse",
    "NodeUpdate",
    "NodeLayoutUpdate",
    "NodeType",
    # Job
    "JobCreate",
    "JobResponse",
    "JobProgress",
    "JobStatus",
    "JobType",
    # Model Config
    "ModelProvider",
    "ModelProviderCreate",
    "ModelMapping",
    "ModelMappingCreate",
    "TaskType",
]
