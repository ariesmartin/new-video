"""
Additional Response Schemas for OpenAPI Completeness

这些 schema 用于补充 API 响应类型，确保 OpenAPI 文档完整。
所有 schema 都遵循 Pydantic v2 规范。
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field

from backend.schemas.node import NodeType, NodeLayout


# ===== Node Schemas =====


class NodeWithLayout(BaseModel):
    """
    节点数据（包含布局信息）

    用于 GET /projects/{project_id}/nodes 端点
    """

    node_id: UUID = Field(..., description="节点 ID")
    project_id: UUID = Field(..., description="所属项目 ID")
    type: NodeType = Field(..., description="节点类型")
    content: dict[str, Any] = Field(default_factory=dict, description="节点内容")
    parent_id: UUID | None = Field(None, description="父节点 ID")
    created_at: datetime | None = Field(None, description="创建时间")
    layout: NodeLayout | None = Field(None, description="布局信息")

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "550e8400-e29b-41d4-a716-446655440002",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "type": "novel_chapter",
                "content": {
                    "episode_number": 1,
                    "title": "重生归来",
                    "text": "陈默睁开眼睛...",
                },
                "parent_id": None,
                "created_at": "2026-02-02T04:00:00Z",
                "layout": {
                    "canvas_tab": "novel",
                    "position_x": 100.0,
                    "position_y": 200.0,
                },
            }
        }


class NodeTreeItem(BaseModel):
    """节点树项（递归结构）"""

    node_id: str = Field(..., description="节点 ID")
    type: str = Field(..., description="节点类型")
    content: dict[str, Any] = Field(default_factory=dict, description="节点内容")
    children: list["NodeTreeItem"] = Field(default_factory=list, description="子节点")


class NodeTreeResponseData(BaseModel):
    """节点树响应数据"""

    project_id: str = Field(..., description="项目 ID")
    roots: list[NodeTreeItem] = Field(..., description="根节点列表")
    total_count: int = Field(..., description="总节点数")


class LayoutUpdateResponseData(BaseModel):
    """布局更新响应数据"""

    node_id: str = Field(..., description="节点 ID")
    layout: NodeLayout = Field(..., description="布局信息")
    updated_at: datetime | None = Field(None, description="更新时间")
    message: str = Field(default="Layout updated successfully", description="消息")


class BatchLayoutUpdateData(BaseModel):
    """批量布局更新数据"""

    node_id: str | None = Field(None, description="节点 ID")
    canvas_tab: str = Field(..., description="画布标签")
    position_x: float = Field(..., description="X 坐标")
    position_y: float = Field(..., description="Y 坐标")


class BatchLayoutUpdateResponseData(BaseModel):
    """批量布局更新响应数据"""

    updated_count: int = Field(..., description="更新的节点数")
    layouts: list[dict[str, Any]] = Field(default_factory=list, description="更新后的布局列表")
    message: str = Field(..., description="消息")


# ===== Asset Schemas =====


class AssetResponseData(BaseModel):
    """资产响应数据"""

    asset_id: str = Field(..., description="资产 ID")
    project_id: str = Field(..., description="所属项目 ID")
    name: str = Field(..., description="资产名称")
    asset_type: str = Field(..., description="资产类型 (character/location/prop)")
    visual_tokens: dict[str, Any] = Field(default_factory=dict, description="视觉 Token")
    reference_urls: list[str] = Field(default_factory=list, description="参考图 URL")
    prompts: dict[str, str] = Field(default_factory=dict, description="生成 Prompt")
    created_at: str | None = Field(None, description="创建时间")
    updated_at: str | None = Field(None, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "asset_id": "550e8400-e29b-41d4-a716-446655440006",
                "project_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "主角 - 陈默",
                "asset_type": "character",
                "visual_tokens": {
                    "gender": "male",
                    "age": "28",
                    "style": "modern",
                },
                "reference_urls": ["https://example.com/ref1.jpg"],
                "prompts": {
                    "nano_banana_prompt": "A young man...",
                    "sd_prompt": "portrait of a man...",
                },
                "created_at": "2026-02-02T04:00:00Z",
            }
        }


class AssetExtractResponseData(BaseModel):
    """资产提取响应数据"""

    project_id: str = Field(..., description="项目 ID")
    extracted_assets: list[AssetResponseData] = Field(
        default_factory=list, description="提取的资产列表"
    )
    message: str = Field(..., description="消息")


# ===== Graph Schemas =====


class TopologyResponse(BaseModel):
    """图拓扑结构响应"""

    mermaid: str = Field(..., description="Mermaid 格式的流程图定义")


class SSEEventBase(BaseModel):
    """SSE 事件基类"""

    type: str = Field(..., description="事件类型")


class SSENodeStartEvent(SSEEventBase):
    """SSE 节点开始事件"""

    type: Literal["node_start"] = "node_start"
    node: str = Field(..., description="节点名称")


class SSENodeEndEvent(SSEEventBase):
    """SSE 节点结束事件"""

    type: Literal["node_end"] = "node_end"
    node: str = Field(..., description="节点名称")


class SSETokenEvent(SSEEventBase):
    """SSE Token 流事件"""

    type: Literal["token"] = "token"
    content: str = Field(..., description="内容片段")


class SSEDoneEvent(SSEEventBase):
    """SSE 完成事件"""

    type: Literal["done"] = "done"
    state: dict[str, Any] = Field(default_factory=dict, description="最终状态")


class SSEErrorEvent(SSEEventBase):
    """SSE 错误事件"""

    type: Literal["error"] = "error"
    error_type: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    node: str = Field(default="unknown", description="发生错误的节点")


# ===== Branch Schemas =====


class BranchInfo(BaseModel):
    """分支信息"""

    thread_id: str = Field(..., description="线程 ID")
    branch_name: str = Field(..., description="分支名称")
    parent_thread_id: str | None = Field(None, description="父线程 ID")
    branch_point: str | None = Field(None, description="分叉点节点")
    status: str = Field(default="active", description="状态")
    created_at: str | None = Field(None, description="创建时间")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class RollbackResponseData(BaseModel):
    """回滚响应数据"""

    thread_id: str = Field(..., description="线程 ID")
    checkpoint_id: str = Field(..., description="检查点 ID")
    node: str | None = Field(None, description="节点名称")
    message: str = Field(..., description="消息")


class StatePatchResponseData(BaseModel):
    """状态修补响应数据"""

    thread_id: str = Field(..., description="线程 ID")
    applied_patches: list[str] = Field(..., description="应用的补丁字段")
    current_node: str | None = Field(None, description="当前节点")
    mode: str = Field(..., description="模式 (soft/hard)")
    message: str = Field(..., description="消息")


class CheckpointInfo(BaseModel):
    """检查点信息"""

    checkpoint_id: str = Field(..., description="检查点 ID")
    node: str | None = Field(None, description="节点名称")
    timestamp: str | None = Field(None, description="时间戳")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


# ===== Tool Schemas =====


class ToolInfo(BaseModel):
    """工具信息"""

    id: str = Field(..., description="工具 ID")
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="描述")
    category: str = Field(..., description="类别")
    icon: str = Field(..., description="图标")
    endpoint: str = Field(..., description="API 端点")
    params: list[dict[str, Any]] = Field(default_factory=list, description="参数列表")


class ToolCategory(BaseModel):
    """工具类别"""

    id: str = Field(..., description="类别 ID")
    name: str = Field(..., description="类别名称")
    icon: str = Field(..., description="图标")


class ToolListResponse(BaseModel):
    """工具列表响应"""

    tools: list[ToolInfo] = Field(..., description="工具列表")
    categories: list[ToolCategory] = Field(..., description="类别列表")


class ToolStatusDetail(BaseModel):
    """工具状态详情"""

    available: bool = Field(..., description="是否可用")
    latency_ms: float | None = Field(None, description="延迟 (毫秒)")
    error: str | None = Field(None, description="错误信息")


class ToolStatusResponse(BaseModel):
    """工具状态响应"""

    status: dict[str, ToolStatusDetail] = Field(..., description="各工具状态")


# ===== Provider Schemas (simplified for API responses) =====


class ProviderResponseData(BaseModel):
    """服务商响应数据（用于 list_providers 等端点）"""

    id: str = Field(..., description="服务商 ID")
    name: str = Field(..., description="服务商名称")
    provider_type: str = Field(..., description="服务商类型")
    protocol: str = Field(..., description="API 协议")
    base_url: str | None = Field(None, description="API Base URL")
    is_active: bool = Field(..., description="是否启用")
    available_models: list[str] = Field(default_factory=list, description="可用模型列表")
    api_key_preview: str = Field(..., description="API Key 预览")
    created_at: str | None = Field(None, description="创建时间")
    last_verified_at: str | None = Field(None, description="最后验证时间")


class MappingResponseData(BaseModel):
    """映射响应数据"""

    id: str = Field(..., description="映射 ID")
    project_id: str | None = Field(None, description="项目 ID")
    task_type: str = Field(..., description="任务类型")
    provider_id: str = Field(..., description="服务商 ID")
    model_name: str = Field(..., description="模型名称")
    parameters: dict[str, Any] = Field(default_factory=dict, description="模型参数")
    provider_name: str | None = Field(None, description="服务商名称")
    created_at: str | None = Field(None, description="创建时间")


class TaskTypeInfo(BaseModel):
    """任务类型信息"""

    value: str = Field(..., description="值")
    label: str = Field(..., description="显示标签")


# ===== Health & Common =====


class DeleteResponse(BaseModel):
    """删除操作响应（用于 204 响应的文档说明）"""

    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="Resource deleted successfully", description="消息")
