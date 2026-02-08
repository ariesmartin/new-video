"""
Database Service

使用 httpx 直接调用 Supabase REST API，提供类型安全的 CRUD 方法。
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, TypeVar

import httpx
import structlog

from backend.config import settings
from backend.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from backend.schemas.node import NodeCreate, NodeResponse, NodeLayoutUpdate
from backend.schemas.job import JobCreate, JobResponse, JobStatus, JobProgress

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class DatabaseService:
    """
    数据库服务类

    使用 httpx 调用 Supabase PostgREST API。

    注意：使用懒加载 client 模式，自动处理 event loop 变化问题。
    每次访问 client 时检查当前事件循环，如果变化则重新创建 client。
    """

    def __init__(self, base_url: str, service_key: str):
        self._base_url = base_url.rstrip("/")
        self._rest_url = f"{self._base_url}/rest/v1"
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        # 不立即创建 client，使用懒加载
        self._client: httpx.AsyncClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def _client(self) -> httpx.AsyncClient:
        """懒加载 HTTP client，自动检测 event loop 变化"""
        current_loop = asyncio.get_running_loop()

        # 如果 client 不存在或 event loop 已变化，重新创建 client
        if self.__client is None or self._loop is not current_loop:
            if self.__client is not None and self._loop is not current_loop:
                # Event loop 变化，关闭旧 client
                try:
                    # 使用 asyncio.run_coroutine_thread_safe 或忽略关闭
                    pass
                except Exception:
                    pass

            self.__client = httpx.AsyncClient(headers=self._headers, timeout=30.0)
            self._loop = current_loop
            logger.debug("Created new httpx client", loop_id=id(current_loop))

        return self.__client

    @_client.setter
    def _client(self, value: httpx.AsyncClient | None):
        self.__client = value

    async def close(self):
        """关闭 HTTP 客户端"""
        if self.__client is not None:
            await self.__client.aclose()
            self.__client = None
            self._loop = None

    # ===== Project CRUD =====

    async def create_project(self, user_id: str, data: ProjectCreate) -> ProjectResponse:
        """创建项目"""
        payload = {
            "user_id": user_id,
            "name": data.name,
            "cover_image": data.cover_image,
            "meta": data.meta.model_dump() if data.meta else {},
        }

        response = await self._client.post(f"{self._rest_url}/projects", json=payload)
        response.raise_for_status()
        result = response.json()

        if not result:
            raise ValueError("Failed to create project")

        return ProjectResponse(**result[0], node_count=0, episode_count=0)

    async def get_project(self, project_id: str) -> ProjectResponse | None:
        """获取项目详情"""
        response = await self._client.get(
            f"{self._rest_url}/projects", params={"id": f"eq.{project_id}", "select": "*"}
        )
        response.raise_for_status()
        result = response.json()

        if not result:
            return None

        node_count = await self._count_nodes(project_id)
        episode_count = await self._count_episodes(project_id)

        return ProjectResponse(**result[0], node_count=node_count, episode_count=episode_count)

    async def list_projects(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[ProjectResponse]:
        """获取用户的项目列表"""
        response = await self._client.get(
            f"{self._rest_url}/projects",
            params={
                "user_id": f"eq.{user_id}",
                "select": "*",
                "order": "updated_at.desc",
                "limit": limit,
                "offset": offset,
            },
        )
        response.raise_for_status()

        projects = []
        for row in response.json() or []:
            node_count = await self._count_nodes(row["id"])
            projects.append(ProjectResponse(**row, node_count=node_count, episode_count=0))

        return projects

    async def update_project(self, project_id: str, data: ProjectUpdate) -> ProjectResponse | None:
        """更新项目"""
        payload = data.model_dump(exclude_unset=True)
        if "meta" in payload and payload["meta"]:
            payload["meta"] = (
                payload["meta"].model_dump()
                if hasattr(payload["meta"], "model_dump")
                else payload["meta"]
            )

        response = await self._client.patch(
            f"{self._rest_url}/projects", params={"id": f"eq.{project_id}"}, json=payload
        )
        response.raise_for_status()

        return await self.get_project(project_id)

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        response = await self._client.delete(
            f"{self._rest_url}/projects", params={"id": f"eq.{project_id}"}
        )
        return response.status_code == 204 or response.status_code == 200

    async def create_temp_project(self, user_id: str, data: ProjectCreate) -> ProjectResponse:
        """创建临时项目"""
        payload = {
            "user_id": user_id,
            "name": data.name,
            "cover_image": data.cover_image,
            "meta": data.meta.model_dump() if data.meta else {},
            "is_temporary": True,
        }

        response = await self._client.post(f"{self._rest_url}/projects", json=payload)
        response.raise_for_status()
        result = response.json()

        if not result:
            raise ValueError("Failed to create temp project")

        return ProjectResponse(**result[0], node_count=0, episode_count=0)

    async def count_temp_projects(self, user_id: str) -> int:
        """统计用户的临时项目数量"""
        response = await self._client.get(
            f"{self._rest_url}/projects",
            params={
                "user_id": f"eq.{user_id}",
                "is_temporary": "eq.true",
                "select": "count",
            },
        )
        response.raise_for_status()
        result = response.json()
        return len(result) if result else 0

    async def delete_oldest_temp_project(self, user_id: str) -> bool:
        """删除用户最旧的临时项目"""
        # 获取最旧的临时项目
        response = await self._client.get(
            f"{self._rest_url}/projects",
            params={
                "user_id": f"eq.{user_id}",
                "is_temporary": "eq.true",
                "select": "id",
                "order": "created_at.asc",
                "limit": 1,
            },
        )
        response.raise_for_status()
        result = response.json()

        if not result:
            return False

        oldest_id = result[0]["id"]
        return await self.delete_project(oldest_id)

    async def save_temp_project(
        self, project_id: str, data: ProjectUpdate
    ) -> ProjectResponse | None:
        """将临时项目转为正式项目"""
        payload = data.model_dump(exclude_unset=True)
        if "meta" in payload and payload["meta"]:
            payload["meta"] = (
                payload["meta"].model_dump()
                if hasattr(payload["meta"], "model_dump")
                else payload["meta"]
            )
        payload["is_temporary"] = False

        response = await self._client.patch(
            f"{self._rest_url}/projects", params={"id": f"eq.{project_id}"}, json=payload
        )
        response.raise_for_status()

        return await self.get_project(project_id)

    async def cleanup_old_temp_projects(self, days: int = 7) -> int:
        """清理指定天数前创建的临时项目"""
        from datetime import datetime, timedelta, timezone

        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # 获取需要清理的临时项目
        response = await self._client.get(
            f"{self._rest_url}/projects",
            params={
                "is_temporary": "eq.true",
                "created_at": f"lt.{cutoff_date}",
                "select": "id",
            },
        )
        response.raise_for_status()
        result = response.json()

        if not result:
            return 0

        # 删除这些项目
        deleted_count = 0
        for row in result:
            if await self.delete_project(row["id"]):
                deleted_count += 1

        return deleted_count

    # ===== Node CRUD =====

    async def create_node(
        self, data: NodeCreate, layout: NodeLayoutUpdate | None = None
    ) -> NodeResponse:
        """创建内容节点"""
        node_id = str(uuid.uuid4())
        payload = {
            "node_id": node_id,
            "project_id": str(data.project_id),
            "parent_id": str(data.parent_id) if data.parent_id else None,
            "type": data.type.value,
            "content": data.content,
        }

        response = await self._client.post(f"{self._rest_url}/story_nodes", json=payload)
        response.raise_for_status()
        result = response.json()

        if not result:
            raise ValueError("Failed to create node")

        # 创建布局
        if layout:
            layout_payload = {
                "node_id": node_id,
                "canvas_tab": layout.canvas_tab,
                "position_x": layout.position_x,
                "position_y": layout.position_y,
            }
            await self._client.post(f"{self._rest_url}/node_layouts", json=layout_payload)

        return NodeResponse(
            id=uuid.UUID(node_id),
            project_id=data.project_id,
            type=data.type,
            content=data.content,
            created_at=datetime.now(timezone.utc),
            layout=layout,
            parent_id=data.parent_id,
        )

    async def get_node(self, node_id: str) -> NodeResponse | None:
        """获取节点详情"""
        response = await self._client.get(
            f"{self._rest_url}/story_nodes", params={"node_id": f"eq.{node_id}", "select": "*"}
        )
        response.raise_for_status()
        result = response.json()

        if not result:
            return None

        return NodeResponse(**result[0])

    async def list_nodes(self, project_id: str, node_type: str | None = None) -> list[NodeResponse]:
        """列出项目的节点"""
        params = {"project_id": f"eq.{project_id}", "select": "*"}
        if node_type:
            params["type"] = f"eq.{node_type}"

        response = await self._client.get(f"{self._rest_url}/story_nodes", params=params)
        response.raise_for_status()

        return [NodeResponse(**row) for row in response.json() or []]

    async def update_node(self, node_id: str, content: dict[str, Any]) -> NodeResponse | None:
        """更新节点内容"""
        response = await self._client.patch(
            f"{self._rest_url}/story_nodes",
            params={"node_id": f"eq.{node_id}"},
            json={"content": content},
        )
        response.raise_for_status()

        return await self.get_node(node_id)

    async def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        response = await self._client.delete(
            f"{self._rest_url}/story_nodes", params={"node_id": f"eq.{node_id}"}
        )
        return response.status_code in (200, 204)

    async def update_node_layout(
        self, node_id: str, layout: dict[str, Any]
    ) -> dict[str, Any] | None:
        """更新节点布局

        Args:
            node_id: 节点 ID
            layout: 布局数据 {
                "canvas_tab": str,
                "position_x": float,
                "position_y": float
            }

        Returns:
            更新后的布局数据
        """
        logger.info("Updating node layout", node_id=node_id, layout=layout)

        # 首先检查节点是否存在
        node = await self.get_node(node_id)
        if not node:
            logger.warning("Node not found for layout update", node_id=node_id)
            return None

        # 准备布局数据
        layout_payload = {
            "node_id": node_id,
            "canvas_tab": layout.get("canvas_tab", "novel"),
            "position_x": layout.get("position_x", 0),
            "position_y": layout.get("position_y", 0),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # 使用 upsert 操作（如果不存在则创建，存在则更新）
        headers = {**self._headers, "Prefer": "resolution=merge-duplicates"}

        try:
            response = await self._client.post(
                f"{self._rest_url}/node_layouts",
                json=layout_payload,
                headers=headers,
            )
            response.raise_for_status()

            result = response.json()
            if result:
                logger.info("Layout updated successfully", node_id=node_id)
                return result[0]
            else:
                # 查询现有布局
                get_response = await self._client.get(
                    f"{self._rest_url}/node_layouts",
                    params={"node_id": f"eq.{node_id}", "select": "*"},
                )
                get_response.raise_for_status()
                existing = get_response.json()
                return existing[0] if existing else layout_payload

        except Exception as e:
            logger.error("Failed to update layout", node_id=node_id, error=str(e))
            raise

    async def get_node_layout(self, node_id: str) -> dict[str, Any] | None:
        """获取节点布局

        Args:
            node_id: 节点 ID

        Returns:
            布局数据或 None
        """
        response = await self._client.get(
            f"{self._rest_url}/node_layouts",
            params={"node_id": f"eq.{node_id}", "select": "*"},
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None

    async def batch_update_layouts(self, layouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量更新节点布局

        Args:
            layouts: 布局数据列表 [{"node_id": str, "canvas_tab": str, "position_x": float, "position_y": float}]

        Returns:
            更新后的布局数据列表
        """
        logger.info("Batch updating layouts", count=len(layouts))

        results = []
        for layout in layouts:
            node_id = layout.get("node_id")
            if node_id:
                try:
                    result = await self.update_node_layout(node_id, layout)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(
                        "Failed to update layout in batch",
                        node_id=node_id,
                        error=str(e),
                    )

        logger.info("Batch layout update completed", updated=len(results))
        return results

    # ===== Job Queue =====

    async def create_job(self, data: JobCreate) -> JobResponse:
        """创建任务"""
        job_id = str(uuid.uuid4())
        payload = {
            "job_id": job_id,
            "project_id": str(data.project_id),
            "type": data.type.value,
            "priority": data.priority,
            "input_payload": data.input_payload,
            "status": JobStatus.PENDING.value,
        }

        response = await self._client.post(f"{self._rest_url}/job_queue", json=payload)
        response.raise_for_status()
        result = response.json()

        if not result:
            raise ValueError("Failed to create job")

        return JobResponse(**result[0])

    async def get_job(self, job_id: str) -> JobResponse | None:
        """获取任务详情"""
        response = await self._client.get(
            f"{self._rest_url}/job_queue", params={"job_id": f"eq.{job_id}", "select": "*"}
        )
        response.raise_for_status()
        result = response.json()

        return JobResponse(**result[0]) if result else None

    async def update_job_status(self, job_id: str, status: JobStatus, **kwargs: Any) -> bool:
        """更新任务状态"""
        payload: dict[str, Any] = {"status": status.value}

        if status == JobStatus.RUNNING:
            payload["started_at"] = datetime.now(timezone.utc).isoformat()
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            payload["ended_at"] = datetime.now(timezone.utc).isoformat()

        payload.update(kwargs)

        response = await self._client.patch(
            f"{self._rest_url}/job_queue", params={"job_id": f"eq.{job_id}"}, json=payload
        )
        return response.status_code in (200, 204)

    async def update_job_progress(self, job_id: str, progress: JobProgress) -> bool:
        """更新任务进度"""
        payload = {
            "progress_percent": progress.progress_percent,
            "current_step": progress.current_step,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.patch(
            f"{self._rest_url}/job_queue", params={"job_id": f"eq.{job_id}"}, json=payload
        )
        return response.status_code in (200, 204)

    async def list_jobs(
        self,
        project_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[JobResponse]:
        """列出任务"""
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": limit,
            "offset": offset,
        }

        if project_id:
            params["project_id"] = f"eq.{project_id}"
        if status:
            params["status"] = f"eq.{status}"

        response = await self._client.get(f"{self._rest_url}/job_queue", params=params)
        response.raise_for_status()

        return [JobResponse(**row) for row in response.json() or []]

    # ===== LLM Providers =====

    async def get_provider(self, provider_id: str) -> dict[str, Any] | None:
        """获取 LLM 服务商配置"""
        response = await self._client.get(
            f"{self._rest_url}/llm_providers", params={"id": f"eq.{provider_id}", "select": "*"}
        )
        response.raise_for_status()
        result = response.json()
        if result:
            provider = result[0]
            logger.info(
                "get_provider result",
                provider_id=provider_id,
                provider_name=provider.get("name"),
                has_api_key=bool(provider.get("api_key")),
                api_key_length=len(provider.get("api_key", "")),
                all_keys=list(provider.keys()),
            )
            return provider
        return None

    async def list_providers(self, user_id: str) -> list[dict[str, Any]]:
        """列出用户的 LLM 服务商"""
        response = await self._client.get(
            f"{self._rest_url}/llm_providers",
            params={"user_id": f"eq.{user_id}", "is_active": "eq.true", "select": "*"},
        )
        response.raise_for_status()
        return response.json() or []

    async def list_providers_by_type(self, provider_type: str) -> list[dict[str, Any]]:
        """按类型列出服务商 (支持视频生成 Provider)"""
        response = await self._client.get(
            f"{self._rest_url}/llm_providers",
            params={"provider_type": f"eq.{provider_type}", "is_active": "eq.true", "select": "*"},
        )
        response.raise_for_status()
        return response.json() or []

    async def create_provider(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """创建 LLM/视频生成服务商"""
        payload = {
            "user_id": user_id,
            "name": data.get("name"),
            "provider_type": data.get("provider_type", "llm"),  # llm 或 video
            "protocol": data.get("protocol", "openai"),
            "base_url": data.get("base_url"),
            "api_key": data.get("api_key"),
            "is_active": True,
            "available_models": data.get("available_models", []),
        }

        response = await self._client.post(f"{self._rest_url}/llm_providers", json=payload)
        response.raise_for_status()
        result = response.json()

        if not result:
            raise ValueError("Failed to create provider")

        return result[0]

    async def update_provider(
        self, provider_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """更新 LLM 服务商"""
        # 只保留有效字段
        payload = {}
        for key in ["name", "protocol", "base_url", "api_key", "is_active", "available_models"]:
            if key in data and data[key] is not None:
                payload[key] = data[key]

        if not payload:
            return await self.get_provider(provider_id)

        logger.info("Updating provider", provider_id=provider_id, payload_keys=list(payload.keys()))

        response = await self._client.patch(
            f"{self._rest_url}/llm_providers", params={"id": f"eq.{provider_id}"}, json=payload
        )
        response.raise_for_status()

        return await self.get_provider(provider_id)

    async def delete_provider(self, provider_id: str) -> bool:
        """删除 LLM 服务商"""
        response = await self._client.delete(
            f"{self._rest_url}/llm_providers", params={"id": f"eq.{provider_id}"}
        )
        return response.status_code in (200, 204)

    async def list_mappings(
        self, user_id: str, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        """列出任务-模型映射"""
        params = {
            "user_id": f"eq.{user_id}",
            "select": "*,llm_providers(name,protocol)",
            "order": "task_type.asc",
        }

        if project_id:
            # 项目级配置
            params["project_id"] = f"eq.{project_id}"
        else:
            # 全局默认配置
            params["project_id"] = "is.null"

        response = await self._client.get(f"{self._rest_url}/model_mappings", params=params)
        response.raise_for_status()
        return response.json() or []

    async def create_mapping(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """创建任务-模型映射"""
        payload = {
            "user_id": user_id,
            "project_id": data.get("project_id"),  # 可以为 None (全局)
            "task_type": data.get("task_type"),
            "provider_id": data.get("provider_id"),
            "model_name": data.get("model_name"),
            "parameters": data.get("parameters", {"temperature": 0.7, "max_tokens": 4096}),
        }

        response = await self._client.post(f"{self._rest_url}/model_mappings", json=payload)
        response.raise_for_status()
        result = response.json()

        if not result:
            raise ValueError("Failed to create mapping")

        return result[0]

    async def update_mapping(self, mapping_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """更新任务-模型映射"""
        payload = {}
        for key in ["provider_id", "model_name", "parameters"]:
            if key in data and data[key] is not None:
                payload[key] = data[key]

        if not payload:
            return None

        response = await self._client.patch(
            f"{self._rest_url}/model_mappings", params={"id": f"eq.{mapping_id}"}, json=payload
        )
        response.raise_for_status()

        # 返回更新后的记录
        result = response.json()
        return result[0] if result else None

    async def delete_mapping(self, mapping_id: str) -> bool:
        """删除任务-模型映射"""
        response = await self._client.delete(
            f"{self._rest_url}/model_mappings", params={"id": f"eq.{mapping_id}"}
        )
        return response.status_code in (200, 204)

    async def get_model_mapping(
        self, user_id: str, task_type: str, project_id: str | None = None
    ) -> dict[str, Any] | None:
        """获取任务-模型映射"""
        logger.info(
            "get_model_mapping called", user_id=user_id, task_type=task_type, project_id=project_id
        )

        # 检查 user_id 是否为有效的 UUID 格式
        import uuid

        is_valid_uuid = True
        try:
            uuid.UUID(user_id)
        except ValueError:
            is_valid_uuid = False
            logger.warning(
                "User ID is not a valid UUID, skipping user-specific mapping", user_id=user_id
            )

        # 构建基础参数
        params: dict[str, str] = {
            "task_type": f"eq.{task_type}",
            "select": "*,llm_providers(*)",
        }

        # 只有有效的 UUID 才添加 user_id 过滤
        if is_valid_uuid:
            params["user_id"] = f"eq.{user_id}"

        if project_id and is_valid_uuid:
            params["project_id"] = f"eq.{project_id}"
            response = await self._client.get(f"{self._rest_url}/model_mappings", params=params)
            result = response.json()

            # 检查响应是否为错误（字典）
            if isinstance(result, dict):
                logger.error("Project mapping query returned error", error=result)
                # 继续到全局回退
            elif result:
                logger.info("Project mapping query result", count=len(result))
                mapping = result[0]
                # 嵌套查询可能被RLS限制，单独查询provider获取完整api_key
                provider_id = mapping.get("provider_id")
                nested_provider = mapping.get("llm_providers", {})
                logger.info(
                    "Nested provider from query",
                    provider_id=provider_id,
                    nested_provider_keys=list(nested_provider.keys()) if nested_provider else None,
                    nested_has_api_key=bool(nested_provider.get("api_key"))
                    if nested_provider
                    else False,
                )
                if provider_id:
                    provider = await self.get_provider(provider_id)
                    if provider:
                        mapping["llm_providers"] = provider
                        logger.info(
                            "Provider replaced with direct query result",
                            has_api_key=bool(provider.get("api_key")),
                        )
                return mapping

        # 回退到全局默认（不指定 user_id，获取系统默认映射）
        params["project_id"] = "is.null"
        # 对于无效 UUID，不添加 user_id 过滤，查询所有全局映射
        if not is_valid_uuid and "user_id" in params:
            del params["user_id"]

        response = await self._client.get(f"{self._rest_url}/model_mappings", params=params)
        result = response.json()

        # 检查响应是否为错误（字典）
        if isinstance(result, dict):
            logger.error("Global mapping query returned error", error=result)
            return None

        logger.info("Global mapping query result", count=len(result) if result else 0)
        if result:
            mapping = result[0]
            # 嵌套查询可能被RLS限制，单独查询provider获取完整api_key
            provider_id = mapping.get("provider_id")
            nested_provider = mapping.get("llm_providers", {})
            logger.info(
                "Nested provider from global query",
                provider_id=provider_id,
                nested_provider_keys=list(nested_provider.keys()) if nested_provider else None,
                nested_has_api_key=bool(nested_provider.get("api_key"))
                if nested_provider
                else False,
            )
            if provider_id:
                provider = await self.get_provider(provider_id)
                if provider:
                    mapping["llm_providers"] = provider
                    logger.info(
                        "Provider replaced with direct query result",
                        has_api_key=bool(provider.get("api_key")),
                    )
            return mapping
        return None

    # ===== Branches (Graph Branch Persistence) =====

    async def create_branch(
        self,
        thread_id: str,
        project_id: str,
        user_id: str,
        branch_name: str,
        parent_thread_id: str | None = None,
        branch_point: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建分支记录"""
        payload = {
            "thread_id": thread_id,
            "project_id": project_id,
            "user_id": user_id,
            "branch_name": branch_name,
            "parent_thread_id": parent_thread_id,
            "branch_point": branch_point,
            "status": "active",
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.post(
            f"{self._rest_url}/branches", json=payload, headers=self._headers
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else payload

    async def get_branch(self, thread_id: str) -> dict[str, Any] | None:
        """获取分支详情"""
        response = await self._client.get(
            f"{self._rest_url}/branches",
            params={"thread_id": f"eq.{thread_id}", "select": "*"},
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None

    async def list_branches(
        self, project_id: str, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """获取项目下的所有分支"""
        params: dict[str, str] = {"project_id": f"eq.{project_id}", "select": "*"}
        if user_id:
            params["user_id"] = f"eq.{user_id}"

        response = await self._client.get(f"{self._rest_url}/branches", params=params)
        response.raise_for_status()
        return response.json()

    async def update_branch_status(self, thread_id: str, status: str) -> dict[str, Any] | None:
        """更新分支状态"""
        payload = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.patch(
            f"{self._rest_url}/branches",
            json=payload,
            params={"thread_id": f"eq.{thread_id}"},
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None

    async def delete_branch(self, thread_id: str) -> bool:
        """删除分支"""
        response = await self._client.delete(
            f"{self._rest_url}/branches", params={"thread_id": f"eq.{thread_id}"}
        )
        return response.status_code in (200, 204)

    # ===== Circuit Breaker =====

    async def get_circuit_state(self, provider_id: str) -> dict[str, Any] | None:
        """获取熔断器状态"""
        response = await self._client.get(
            f"{self._rest_url}/circuit_breaker_states",
            params={"provider_id": f"eq.{provider_id}", "select": "*"},
        )
        result = response.json()
        return result[0] if result else None

    async def update_circuit_state(
        self, provider_id: str, state: str, failure_count: int = 0
    ) -> None:
        """更新熔断器状态"""
        payload = {
            "provider_id": provider_id,
            "state": state,
            "failure_count": failure_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if state == "OPEN":
            payload["opened_at"] = datetime.now(timezone.utc).isoformat()

        # Upsert
        headers = {**self._headers, "Prefer": "resolution=merge-duplicates"}
        await self._client.post(
            f"{self._rest_url}/circuit_breaker_states", json=payload, headers=headers
        )

    # ===== Video Results =====

    async def create_video_result(
        self,
        job_id: str,
        shot_number: str,
        video_url: str,
        provider: str,
        generation_id: str | None = None,
    ) -> dict[str, Any]:
        """创建视频结果记录"""
        payload = {
            "job_id": job_id,
            "shot_number": shot_number,
            "video_url": video_url,
            "provider": provider,
            "generation_id": generation_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.post(
            f"{self._rest_url}/video_results", json=payload, headers=self._headers
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else payload

    async def get_video_results(self, job_id: str) -> list[dict[str, Any]]:
        """获取任务的所有视频结果"""
        response = await self._client.get(
            f"{self._rest_url}/video_results",
            params={"job_id": f"eq.{job_id}", "select": "*"},
        )
        response.raise_for_status()
        return response.json()

    # ===== Helper Methods =====

    async def _count_nodes(self, project_id: str) -> int:
        """统计项目节点数"""
        response = await self._client.get(
            f"{self._rest_url}/story_nodes",
            params={"project_id": f"eq.{project_id}", "select": "node_id"},
            headers={**self._headers, "Prefer": "count=exact"},
        )
        count_header = response.headers.get("content-range", "0-0/0")
        try:
            return int(count_header.split("/")[1])
        except (ValueError, IndexError):
            return len(response.json() or [])

    async def _count_episodes(self, project_id: str) -> int:
        """统计已生成集数"""
        response = await self._client.get(
            f"{self._rest_url}/story_nodes",
            params={"project_id": f"eq.{project_id}", "type": "eq.episode", "select": "node_id"},
            headers={**self._headers, "Prefer": "count=exact"},
        )
        count_header = response.headers.get("content-range", "0-0/0")
        try:
            return int(count_header.split("/")[1])
        except (ValueError, IndexError):
            return len(response.json() or [])

    async def count_projects(self, user_id: str) -> int:
        """统计用户项目总数"""
        response = await self._client.get(
            f"{self._rest_url}/projects",
            params={"user_id": f"eq.{user_id}", "select": "id"},
            headers={**self._headers, "Prefer": "count=exact"},
        )
        count_header = response.headers.get("content-range", "0-0/0")
        try:
            return int(count_header.split("/")[1])
        except (ValueError, IndexError):
            return len(response.json() or [])

    async def count_jobs(
        self,
        project_id: str | None = None,
        status: str | None = None,
    ) -> int:
        """统计任务总数"""
        params = {"select": "job_id"}
        if project_id:
            params["project_id"] = f"eq.{project_id}"
        if status:
            params["status"] = f"eq.{status}"

        response = await self._client.get(
            f"{self._rest_url}/job_queue",
            params=params,
            headers={**self._headers, "Prefer": "count=exact"},
        )
        count_header = response.headers.get("content-range", "0-0/0")
        try:
            return int(count_header.split("/")[1])
        except (ValueError, IndexError):
            return len(response.json() or [])

    # ===== v6.0 Episodes CRUD =====

    async def list_episodes(self, project_id: str) -> list[dict[str, Any]]:
        """获取项目的所有剧集列表"""
        response = await self._client.get(
            f"{self._rest_url}/episodes",
            params={
                "project_id": f"eq.{project_id}",
                "select": "*",
                "order": "episode_number.asc",
            },
        )
        response.raise_for_status()
        return response.json() or []

    async def get_next_episode_number(self, project_id: str) -> int:
        """获取下一个剧集编号"""
        response = await self._client.get(
            f"{self._rest_url}/episodes",
            params={
                "project_id": f"eq.{project_id}",
                "select": "episode_number",
                "order": "episode_number.desc",
                "limit": 1,
            },
        )
        response.raise_for_status()
        result = response.json()
        if result:
            return result[0].get("episode_number", 0) + 1
        return 1

    async def create_episode(
        self,
        project_id: str,
        episode_number: int,
        title: str,
        summary: str | None = None,
    ) -> dict[str, Any]:
        """创建新剧集"""
        payload = {
            "project_id": project_id,
            "episode_number": episode_number,
            "title": title,
            "summary": summary,
            "status": "draft",
            "canvas_data": {},
            "storyboard_shot_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.post(
            f"{self._rest_url}/episodes",
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else payload

    async def get_episode(self, episode_id: str) -> dict[str, Any] | None:
        """获取剧集详情"""
        response = await self._client.get(
            f"{self._rest_url}/episodes",
            params={"episode_id": f"eq.{episode_id}", "select": "*"},
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None

    async def update_episode(
        self,
        episode_id: str,
        title: str | None = None,
        summary: str | None = None,
        script_text: str | None = None,
        novel_content: str | None = None,
    ) -> dict[str, Any]:
        """更新剧集信息"""
        payload = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if title is not None:
            payload["title"] = title
        if summary is not None:
            payload["summary"] = summary
        if script_text is not None:
            payload["script_text"] = script_text
        if novel_content is not None:
            payload["novel_content"] = novel_content
            # 更新字数统计
            payload["word_count"] = len(novel_content) if novel_content else 0

        response = await self._client.patch(
            f"{self._rest_url}/episodes",
            params={"episode_id": f"eq.{episode_id}"},
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()

        # 返回更新后的数据
        return await self.get_episode(episode_id) or payload

    async def delete_episode(self, episode_id: str) -> bool:
        """删除剧集（级联删除分镜、场景、连线）"""
        # 先删除关联的分镜（会级联删除连线）
        await self._client.delete(
            f"{self._rest_url}/shot_nodes",
            params={"episode_id": f"eq.{episode_id}"},
        )

        # 删除场景
        await self._client.delete(
            f"{self._rest_url}/scenes",
            params={"episode_id": f"eq.{episode_id}"},
        )

        # 删除剧集
        response = await self._client.delete(
            f"{self._rest_url}/episodes",
            params={"episode_id": f"eq.{episode_id}"},
        )
        return response.status_code in (200, 204)

    # ===== v6.0 Canvas Management =====

    async def get_episode_canvas(self, episode_id: str) -> dict[str, Any] | None:
        """获取剧集画布数据"""
        response = await self._client.get(
            f"{self._rest_url}/episodes",
            params={"episode_id": f"eq.{episode_id}", "select": "canvas_data"},
        )
        response.raise_for_status()
        result = response.json()
        if result and result[0].get("canvas_data"):
            canvas_data = result[0]["canvas_data"]
            canvas_data["episode_id"] = episode_id
            return canvas_data
        return None

    async def save_episode_canvas(
        self,
        episode_id: str,
        canvas_data: dict[str, Any],
    ) -> dict[str, Any]:
        """保存剧集画布数据"""
        payload = {
            "canvas_data": canvas_data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.patch(
            f"{self._rest_url}/episodes",
            params={"episode_id": f"eq.{episode_id}"},
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()
        return canvas_data

    async def update_episode_viewport(
        self,
        episode_id: str,
        x: float,
        y: float,
        zoom: float,
    ) -> dict[str, Any]:
        """仅更新视口状态"""
        # 获取现有画布数据
        existing = await self.get_episode_canvas(episode_id)

        if existing:
            existing["viewport"] = {"x": x, "y": y, "zoom": zoom}
            return await self.save_episode_canvas(episode_id, existing)
        else:
            # 创建新的画布数据
            new_canvas = {
                "episode_id": episode_id,
                "viewport": {"x": x, "y": y, "zoom": zoom},
                "nodes": [],
                "connections": [],
            }
            return await self.save_episode_canvas(episode_id, new_canvas)

    async def sync_shot_nodes_from_canvas(
        self,
        episode_id: str,
        nodes: list[dict[str, Any]],
    ) -> None:
        """同步画布节点到 shot_nodes 表"""
        # 这个方法在保存画布后调用，确保 shot_nodes 表与画布一致
        # 实际实现可能需要根据具体需求调整
        logger.info(
            "Syncing shot nodes from canvas",
            episode_id=episode_id,
            node_count=len(nodes),
        )
        # 注：实际同步逻辑可能需要更复杂的实现

    # ===== v6.0 Shot Nodes CRUD =====

    async def list_shot_nodes(
        self,
        episode_id: str,
        scene_id: str | None = None,
        node_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取剧集的所有分镜节点"""
        params: dict[str, Any] = {
            "episode_id": f"eq.{episode_id}",
            "select": "*",
            "order": "shot_number.asc",
        }

        if scene_id:
            params["scene_id"] = f"eq.{scene_id}"
        if node_type:
            params["node_type"] = f"eq.{node_type}"

        response = await self._client.get(
            f"{self._rest_url}/shot_nodes",
            params=params,
        )
        response.raise_for_status()
        return response.json() or []

    async def get_next_shot_number(self, episode_id: str) -> int:
        """获取下一个分镜编号"""
        response = await self._client.get(
            f"{self._rest_url}/shot_nodes",
            params={
                "episode_id": f"eq.{episode_id}",
                "select": "shot_number",
                "order": "shot_number.desc",
                "limit": 1,
            },
        )
        response.raise_for_status()
        result = response.json()
        if result:
            return result[0].get("shot_number", 0) + 1
        return 1

    async def create_shot_node(
        self,
        episode_id: str,
        node_type: str,
        shot_number: int,
        title: str,
        subtitle: str | None = None,
        position_x: float = 0,
        position_y: float = 0,
        scene_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建分镜节点"""
        payload = {
            "episode_id": episode_id,
            "scene_id": scene_id,
            "node_type": node_type,
            "shot_number": shot_number,
            "title": title,
            "subtitle": subtitle,
            "position_x": position_x,
            "position_y": position_y,
            "status": "pending",
            "details": details or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.post(
            f"{self._rest_url}/shot_nodes",
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json()

        # 更新剧集的分镜计数
        await self._update_episode_shot_count(episode_id)

        return result[0] if result else payload

    async def batch_create_shot_nodes(
        self,
        episode_id: str,
        shots_data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """批量创建分镜节点"""
        # 获取起始编号
        start_number = await self.get_next_shot_number(episode_id)

        payloads = []
        for idx, shot_data in enumerate(shots_data):
            payload = {
                "episode_id": episode_id,
                "node_type": shot_data.get("node_type", "shot"),
                "shot_number": start_number + idx,
                "title": shot_data.get("title", f"Shot {start_number + idx}"),
                "subtitle": shot_data.get("subtitle"),
                "position_x": shot_data.get("position_x", 0),
                "position_y": shot_data.get("position_y", 0),
                "scene_id": shot_data.get("scene_id"),
                "status": "pending",
                "details": shot_data.get("details", {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            payloads.append(payload)

        # 批量插入
        response = await self._client.post(
            f"{self._rest_url}/shot_nodes",
            json=payloads,
            headers=self._headers,
        )
        response.raise_for_status()

        # 更新剧集的分镜计数
        await self._update_episode_shot_count(episode_id)

        return response.json() or payloads

    async def get_shot_node(self, shot_id: str) -> dict[str, Any] | None:
        """获取分镜详情"""
        response = await self._client.get(
            f"{self._rest_url}/shot_nodes",
            params={"shot_id": f"eq.{shot_id}", "select": "*"},
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None

    async def update_shot_node(
        self,
        shot_id: str,
        title: str | None = None,
        subtitle: str | None = None,
        status: str | None = None,
        position_x: float | None = None,
        position_y: float | None = None,
        thumbnail_url: str | None = None,
        image_url: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """更新分镜节点"""
        payload = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if title is not None:
            payload["title"] = title
        if subtitle is not None:
            payload["subtitle"] = subtitle
        if status is not None:
            payload["status"] = status
        if position_x is not None:
            payload["position_x"] = position_x
        if position_y is not None:
            payload["position_y"] = position_y
        if thumbnail_url is not None:
            payload["thumbnail_url"] = thumbnail_url
        if image_url is not None:
            payload["image_url"] = image_url
        if details is not None:
            payload["details"] = details

        response = await self._client.patch(
            f"{self._rest_url}/shot_nodes",
            params={"shot_id": f"eq.{shot_id}"},
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()

        # 获取 episode_id 以更新计数
        shot = await self.get_shot_node(shot_id)
        if shot:
            await self._update_episode_shot_count(shot["episode_id"])

        return await self.get_shot_node(shot_id) or payload

    async def batch_update_shot_positions(
        self,
        episode_id: str,
        positions: dict[str, tuple[float, float]],
    ) -> None:
        """批量更新节点位置"""
        for shot_id, (x, y) in positions.items():
            await self.update_shot_node(
                shot_id=shot_id,
                position_x=x,
                position_y=y,
            )

    async def delete_shot_node(self, shot_id: str) -> bool:
        """删除分镜节点"""
        # 获取 episode_id 以更新计数
        shot = await self.get_shot_node(shot_id)
        episode_id = shot.get("episode_id") if shot else None

        # 删除关联的连线
        await self._client.delete(
            f"{self._rest_url}/shot_connections",
            params={
                "or": f"(source_shot_id.eq.{shot_id},target_shot_id.eq.{shot_id})",
            },
        )

        # 删除分镜
        response = await self._client.delete(
            f"{self._rest_url}/shot_nodes",
            params={"shot_id": f"eq.{shot_id}"},
        )

        # 更新剧集计数
        if episode_id:
            await self._update_episode_shot_count(episode_id)

        return response.status_code in (200, 204)

    async def _update_episode_shot_count(self, episode_id: str) -> None:
        """更新剧集的分镜计数"""
        # 统计分镜数量
        response = await self._client.get(
            f"{self._rest_url}/shot_nodes",
            params={
                "episode_id": f"eq.{episode_id}",
                "select": "shot_id",
            },
            headers={**self._headers, "Prefer": "count=exact"},
        )
        count_header = response.headers.get("content-range", "0-0/0")
        try:
            count = int(count_header.split("/")[1])
        except (ValueError, IndexError):
            count = len(response.json() or [])

        # 更新剧集
        await self._client.patch(
            f"{self._rest_url}/episodes",
            params={"episode_id": f"eq.{episode_id}"},
            json={
                "storyboard_shot_count": count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            headers=self._headers,
        )

    # ===== v6.0 Scenes CRUD =====

    async def list_scenes(self, episode_id: str) -> list[dict[str, Any]]:
        """获取剧集的所有场景"""
        response = await self._client.get(
            f"{self._rest_url}/scenes",
            params={
                "episode_id": f"eq.{episode_id}",
                "select": "*",
                "order": "scene_number.asc",
            },
        )
        response.raise_for_status()
        return response.json() or []

    async def get_next_scene_number(self, episode_id: str) -> int:
        """获取下一个场景编号"""
        response = await self._client.get(
            f"{self._rest_url}/scenes",
            params={
                "episode_id": f"eq.{episode_id}",
                "select": "scene_number",
                "order": "created_at.desc",
                "limit": 1,
            },
        )
        response.raise_for_status()
        result = response.json()
        if result:
            # 从 S01 格式提取数字
            scene_num = result[0].get("scene_number", "S00")
            try:
                return int(scene_num[1:]) + 1
            except (ValueError, IndexError):
                return 1
        return 1

    async def create_scene(
        self,
        episode_id: str,
        scene_number: str,
        location: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """创建场景"""
        payload = {
            "episode_id": episode_id,
            "scene_number": scene_number,
            "location": location,
            "description": description,
            "shot_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.post(
            f"{self._rest_url}/scenes",
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else payload

    async def get_scene(self, scene_id: str) -> dict[str, Any] | None:
        """获取场景详情"""
        response = await self._client.get(
            f"{self._rest_url}/scenes",
            params={"scene_id": f"eq.{scene_id}", "select": "*"},
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None

    async def update_scene(
        self,
        scene_id: str,
        location: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """更新场景信息"""
        payload = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if location is not None:
            payload["location"] = location
        if description is not None:
            payload["description"] = description

        response = await self._client.patch(
            f"{self._rest_url}/scenes",
            params={"scene_id": f"eq.{scene_id}"},
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()
        return await self.get_scene(scene_id) or payload

    async def update_scene_master(self, scene_id: str, master_node_id: str) -> None:
        """更新场景的 Master 节点 ID"""
        await self._client.patch(
            f"{self._rest_url}/scenes",
            params={"scene_id": f"eq.{scene_id}"},
            json={
                "master_node_id": master_node_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            headers=self._headers,
        )

    async def delete_scene(self, scene_id: str) -> bool:
        """删除场景"""
        response = await self._client.delete(
            f"{self._rest_url}/scenes",
            params={"scene_id": f"eq.{scene_id}"},
        )
        return response.status_code in (200, 204)

    async def _update_scene_shot_count(self, scene_id: str) -> None:
        """更新场景的分镜计数"""
        response = await self._client.get(
            f"{self._rest_url}/shot_nodes",
            params={
                "scene_id": f"eq.{scene_id}",
                "select": "shot_id",
            },
            headers={**self._headers, "Prefer": "count=exact"},
        )
        count_header = response.headers.get("content-range", "0-0/0")
        try:
            count = int(count_header.split("/")[1])
        except (ValueError, IndexError):
            count = len(response.json() or [])

        await self._client.patch(
            f"{self._rest_url}/scenes",
            params={"scene_id": f"eq.{scene_id}"},
            json={
                "shot_count": count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            headers=self._headers,
        )

    # ===== v6.0 Shot Connections CRUD =====

    async def list_shot_connections(self, episode_id: str) -> list[dict[str, Any]]:
        """获取剧集的所有连线"""
        response = await self._client.get(
            f"{self._rest_url}/shot_connections",
            params={
                "episode_id": f"eq.{episode_id}",
                "select": "*",
                "order": "created_at.asc",
            },
        )
        response.raise_for_status()
        return response.json() or []

    async def create_shot_connection(
        self,
        episode_id: str,
        source_shot_id: str,
        target_shot_id: str,
        connection_type: str = "sequence",
    ) -> dict[str, Any]:
        """创建连线"""
        payload = {
            "episode_id": episode_id,
            "source_shot_id": source_shot_id,
            "target_shot_id": target_shot_id,
            "connection_type": connection_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        response = await self._client.post(
            f"{self._rest_url}/shot_connections",
            json=payload,
            headers=self._headers,
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else payload

    async def delete_shot_connection(self, connection_id: str) -> bool:
        """删除连线"""
        response = await self._client.delete(
            f"{self._rest_url}/shot_connections",
            params={"connection_id": f"eq.{connection_id}"},
        )
        return response.status_code in (200, 204)

    # ===== Market Reports (Market Analysis Caching) =====

    async def create_market_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """创建市场分析报告"""
        payload = {
            "report_type": data.get("report_type", "weekly"),
            "genres": data.get("genres", []),
            "tones": data.get("tones", []),
            "insights": data.get("insights", ""),
            "target_audience": data.get("target_audience", ""),
            "search_queries": data.get("search_queries", []),
            "raw_search_results": data.get("raw_search_results", ""),
            "valid_until": data.get("valid_until"),
            "is_active": data.get("is_active", True),
        }

        response = await self._client.post(
            f"{self._rest_url}/market_reports", json=payload, headers=self._headers
        )
        response.raise_for_status()
        result = response.json()
        return result[0] if result else payload

    async def get_latest_market_report(self) -> dict[str, Any] | None:
        """获取最新的有效市场分析报告"""
        from datetime import datetime, timezone

        # 查询最新的活跃报告
        response = await self._client.get(
            f"{self._rest_url}/market_reports",
            params={
                "is_active": "eq.true",
                "valid_until": f"gte.{datetime.now(timezone.utc).isoformat()}",
                "order": "created_at.desc",
                "limit": 1,
                "select": "*",
            },
        )
        response.raise_for_status()
        result = response.json()

        if result and len(result) > 0:
            return result[0]
        return None


# ===== Singleton Factory =====

_db_service: DatabaseService | None = None


async def init_db_service() -> DatabaseService:
    """初始化数据库服务"""
    global _db_service

    if _db_service is None:
        _db_service = DatabaseService(
            base_url=settings.supabase_url,
            service_key=settings.supabase_key,
        )
        logger.info("Database service initialized", url=settings.supabase_url)

    return _db_service


def get_db_service() -> DatabaseService:
    """获取数据库服务实例"""
    if _db_service is None:
        raise RuntimeError("Database service not initialized. Call init_db_service() first.")
    return _db_service
