"""
Model Configuration Schemas

LLM 服务商和任务路由配置的数据模型。
支持 BYOK (Bring Your Own Key) 和 Task-Model Routing。

对应数据库表: llm_providers, model_mappings
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr


class TaskCategory(str, Enum):
    """
    UI 层分类（前端简化配置）

    用户看到的业务分类，每个分类映射到一组具体的 TaskType。
    """

    CREATIVE = "creative"  # 创意生成
    CONTENT = "content"  # 内容处理
    QUALITY = "quality"  # 质量提升
    VIDEO = "video"  # 视频生成
    IMAGE_PROCESS = "image_process"  # 图像处理


class TaskType(str, Enum):
    """
    Agent 任务类型

    用于 Task-Model Routing，将不同任务路由到最适合的模型。
    """

    # Level 0 - 总控
    ROUTER = "router"  # 智能路由 (Master Router)

    # Level 1-3
    MARKET_ANALYST = "market_analyst"  # 市场分析
    STORY_PLANNER = "story_planner"  # 故事规划
    SKELETON_BUILDER = "skeleton_builder"  # 骨架构建

    # Module A
    NOVEL_WRITER = "novel_writer"  # 小说撰写
    EDITOR = "editor"  # 质量审阅
    REFINER = "refiner"  # 内容精修
    ANALYSIS_LAB = "analysis_lab"  # 分析实验室 (情绪曲线 + 定向修文)

    # Module B
    SCRIPT_ADAPTER = "script_adapter"  # 剧本提取 (小说 -> 剧本)
    SCRIPT_PARSER = "script_parser"  # 剧本解析
    SCRIPT_FORMATTER = "script_formatter"  # 剧本格式化

    # Module C
    STORYBOARD_DIRECTOR = "storyboard_director"  # 分镜拆分
    STORYBOARD_ARTIST = "storyboard_artist"  # 分镜绘制
    PROMPT_GENERATOR = "prompt_generator"  # Prompt 生成

    # Module X - 资产管理
    ASSET_INSPECTOR = "asset_inspector"  # 资产探查

    # Module I - 图像处理
    IMAGE_ENHANCER = "image_enhancer"  # 图像增强
    IMAGE_INPAINTER = "image_inpainter"  # 图像补全
    IMAGE_OUTPAINTER = "image_outpainter"  # 图像外扩

    # Utility
    EMBEDDING = "embedding"  # 向量嵌入
    SUMMARY = "summary"  # 摘要生成


class ProtocolType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    AZURE = "azure"


class ProviderType(str, Enum):
    LLM = "llm"
    VIDEO = "video"
    IMAGE = "image"


class ModelProviderBase(BaseModel):
    """模型服务商基础字段"""

    name: str = Field(..., min_length=1, max_length=50, description="服务商名称")
    provider_type: ProviderType = Field(
        default=ProviderType.LLM, description="服务商类型 (LLM/视频)"
    )
    protocol: ProtocolType = Field(default=ProtocolType.OPENAI, description="API 协议")
    base_url: str | None = Field(None, description="API Base URL")
    is_active: bool = Field(default=True, description="是否启用")


class ModelProviderCreate(ModelProviderBase):
    """创建服务商请求"""

    api_key: str = Field(..., min_length=1, description="API Key")


class ModelProviderUpdate(BaseModel):
    """更新服务商请求"""

    name: str | None = Field(None, min_length=1, max_length=50)
    protocol: ProtocolType | None = None
    base_url: str | None = None
    api_key: str | None = None
    is_active: bool | None = None


class ModelProvider(ModelProviderBase):
    """服务商响应"""

    id: UUID = Field(..., description="服务商 ID")
    user_id: UUID = Field(..., description="所属用户 ID")
    last_verified_at: datetime | None = Field(None, description="最后验证时间")
    available_models: list[str] = Field(default_factory=list, description="可用模型列表")
    created_at: datetime

    # API Key 脱敏显示
    api_key_preview: str = Field(..., description="API Key 预览 (sk-...xxxx)")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440004",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "DeepSeek",
                "protocol": "openai",
                "base_url": "https://api.deepseek.com/v1",
                "is_active": True,
                "last_verified_at": "2026-02-02T04:00:00Z",
                "available_models": ["deepseek-chat", "deepseek-coder"],
                "api_key_preview": "sk-...7890",
                "created_at": "2026-02-02T03:00:00Z",
            }
        }


class ModelMappingBase(BaseModel):
    """任务模型映射基础字段"""

    task_type: TaskType = Field(..., description="任务类型")
    provider_id: UUID = Field(..., description="服务商 ID")
    model_name: str = Field(..., description="模型名称")
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {"temperature": 0.7, "max_tokens": 4096}, description="模型参数"
    )


class ModelMappingCreate(ModelMappingBase):
    """创建映射请求"""

    project_id: UUID | None = Field(None, description="项目 ID (空则为全局默认)")


class ModelMappingCreateUI(BaseModel):
    """UI 层创建映射请求（使用 TaskCategory 简化配置）"""

    task_category: TaskCategory = Field(..., description="UI 分类")
    provider_id: UUID = Field(..., description="服务商 ID")
    model_name: str = Field(..., description="模型名称")
    project_id: UUID | None = Field(None, description="项目 ID (空则为全局默认)")
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {"temperature": 0.7, "max_tokens": 4096}, description="模型参数"
    )


class ModelMappingUpdate(BaseModel):
    """更新映射请求"""

    provider_id: UUID | None = None
    model_name: str | None = None
    parameters: dict[str, Any] | None = None


# TaskCategory 到 TaskType 的默认映射关系
# 支持动态扩展：添加新分类时只需在此更新映射
DEFAULT_CATEGORY_TO_TASK_TYPE: dict[TaskCategory, TaskType] = {
    TaskCategory.CREATIVE: TaskType.NOVEL_WRITER,
    TaskCategory.CONTENT: TaskType.SCRIPT_FORMATTER,
    TaskCategory.QUALITY: TaskType.EDITOR,
    TaskCategory.VIDEO: TaskType.STORYBOARD_DIRECTOR,
    TaskCategory.IMAGE_PROCESS: TaskType.IMAGE_ENHANCER,
}


def category_to_task_type(category: TaskCategory) -> TaskType:
    """将 TaskCategory 转换为默认的 TaskType

    支持动态扩展：添加新分类时只需更新 DEFAULT_CATEGORY_TO_TASK_TYPE。

    Args:
        category: UI 层分类

    Returns:
        对应的默认 TaskType
    """
    return DEFAULT_CATEGORY_TO_TASK_TYPE.get(category, TaskType.EDITOR)


class ModelMapping(ModelMappingBase):
    """映射响应"""

    id: UUID = Field(..., description="映射 ID")
    project_id: UUID | None = Field(None, description="项目 ID")
    created_at: datetime

    # 关联信息
    provider_name: str | None = Field(None, description="服务商名称")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440005",
                "project_id": None,
                "task_type": "novel_writer",
                "provider_id": "550e8400-e29b-41d4-a716-446655440004",
                "model_name": "deepseek-chat",
                "parameters": {"temperature": 0.8, "max_tokens": 8192},
                "provider_name": "DeepSeek",
                "created_at": "2026-02-02T04:00:00Z",
            }
        }


class ModelTestRequest(BaseModel):
    """模型测试请求"""

    provider_id: UUID = Field(..., description="服务商 ID")
    model_name: str = Field(..., description="要测试的模型名称")
    prompt: str = Field(default="Hello, can you respond?", description="测试 Prompt")


class ModelTestResponse(BaseModel):
    """模型测试响应"""

    success: bool
    response: str | None = None
    latency_ms: float | None = None
    error: str | None = None
