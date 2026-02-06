"""
Sync Service

将 LangGraph AgentState 中的产物同步到业务数据库表 (story_nodes)。
这是连接 Graph 状态和 Canvas 画布的关键桥梁。

架构遵循: 系统架构文档.md Section 3.2 (Data Flow & Persistence)
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from backend.services.database import DatabaseService
from backend.schemas.node import NodeCreate, NodeType, NodeLayoutUpdate
from backend.schemas.agent_state import AgentState, StoryPlan, SceneData, ShotData, EpisodeOutline

logger = structlog.get_logger(__name__)


class SyncService:
    """
    状态同步服务

    负责将 LangGraph 的运行时状态持久化到业务表中，
    使 Canvas 画布能够读取和展示生成的内容。
    """

    def __init__(self, db: DatabaseService):
        self._db = db

    async def sync_story_plans(
        self,
        project_id: str,
        plans: list[StoryPlan],
        clear_existing: bool = True,
    ) -> list[str]:
        """
        同步故事方案到 story_nodes 表

        Args:
            project_id: 项目 ID
            plans: 故事方案列表 (通常 3-5 个)
            clear_existing: 是否清除现有的方案节点

        Returns:
            创建的节点 ID 列表
        """
        logger.info("Syncing story plans", project_id=project_id, count=len(plans))

        # 可选：清除现有方案
        if clear_existing:
            existing_nodes = await self._db.list_nodes(project_id, node_type="story_plan")
            for node in existing_nodes:
                await self._db.delete_node(str(node.id))

        created_ids = []
        for i, plan in enumerate(plans):
            node_data = NodeCreate(
                project_id=uuid.UUID(project_id),
                type=NodeType.STORY_PLAN,
                content={
                    "plan_id": plan.get("plan_id", f"plan_{i + 1}"),
                    "title": plan.get("title", f"方案 {i + 1}"),
                    "logline": plan.get("logline", ""),
                    "protagonist": plan.get("protagonist", {}),
                    "deuteragonist": plan.get("deuteragonist", {}),
                    "core_appeal": plan.get("core_appeal", []),
                    "anti_cliche_applied": plan.get("anti_cliche_applied", False),
                },
            )

            # 计算画布位置 (水平排列)
            layout = NodeLayoutUpdate(
                canvas_tab="planning",
                position_x=100 + i * 400,
                position_y=200,
            )

            node = await self._db.create_node(node_data, layout)
            created_ids.append(str(node.id))

        logger.info("Story plans synced", created_count=len(created_ids))
        return created_ids

    async def sync_beat_sheet(
        self,
        project_id: str,
        beat_sheet: list[EpisodeOutline],
    ) -> list[str]:
        """
        同步分集大纲到 story_nodes 表

        Args:
            project_id: 项目 ID
            beat_sheet: 分集大纲列表

        Returns:
            创建的节点 ID 列表
        """
        logger.info("Syncing beat sheet", project_id=project_id, count=len(beat_sheet))

        created_ids = []
        for i, episode in enumerate(beat_sheet):
            node_data = NodeCreate(
                project_id=uuid.UUID(project_id),
                type=NodeType.EPISODE_OUTLINE,
                content={
                    "episode_id": episode.get("episode_id", f"ep_{i + 1}"),
                    "episode_number": episode.get("episode_number", i + 1),
                    "title": episode.get("title", f"第 {i + 1} 集"),
                    "summary": episode.get("summary", ""),
                    "key_scenes": episode.get("key_scenes", []),
                    "cliffhanger": episode.get("cliffhanger", ""),
                },
            )

            layout = NodeLayoutUpdate(
                canvas_tab="planning",
                position_x=100,
                position_y=500 + i * 150,
            )

            node = await self._db.create_node(node_data, layout)
            created_ids.append(str(node.id))

        return created_ids

    async def sync_novel_content(
        self,
        project_id: str,
        episode_number: int,
        content: str,
        parent_id: str | None = None,
    ) -> str:
        """
        同步小说章节内容

        Args:
            project_id: 项目 ID
            episode_number: 集数
            content: 小说正文
            parent_id: 父节点 ID (如 episode outline)

        Returns:
            创建的节点 ID
        """
        logger.info("Syncing novel content", project_id=project_id, episode=episode_number)

        node_data = NodeCreate(
            project_id=uuid.UUID(project_id),
            parent_id=uuid.UUID(parent_id) if parent_id else None,
            type=NodeType.NOVEL_CHAPTER,
            content={
                "episode_number": episode_number,
                "text": content,
                "word_count": len(content),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        layout = NodeLayoutUpdate(
            canvas_tab="novel",
            position_x=100,
            position_y=100 + (episode_number - 1) * 300,
        )

        node = await self._db.create_node(node_data, layout)
        return str(node.id)

    async def sync_script_data(
        self,
        project_id: str,
        scenes: list[SceneData],
        parent_id: str | None = None,
    ) -> list[str]:
        """
        同步剧本场景数据

        Args:
            project_id: 项目 ID
            scenes: 场景列表
            parent_id: 父节点 ID (如 novel chapter)

        Returns:
            创建的节点 ID 列表
        """
        logger.info("Syncing script data", project_id=project_id, count=len(scenes))

        created_ids = []
        for i, scene in enumerate(scenes):
            node_data = NodeCreate(
                project_id=uuid.UUID(project_id),
                parent_id=uuid.UUID(parent_id) if parent_id else None,
                type=NodeType.SCRIPT_SCENE,
                content={
                    "scene_id": scene.get("scene_id", f"scene_{i + 1}"),
                    "scene_number": scene.get("scene_number", f"S{i + 1:02d}"),
                    "location": scene.get("location", ""),
                    "visual_description": scene.get("visual_description", ""),
                    "elements": scene.get("elements", []),
                },
            )

            layout = NodeLayoutUpdate(
                canvas_tab="script",
                position_x=100 + (i % 3) * 400,
                position_y=100 + (i // 3) * 350,
            )

            node = await self._db.create_node(node_data, layout)
            created_ids.append(str(node.id))

        return created_ids

    async def sync_storyboard(
        self,
        project_id: str,
        shots: list[ShotData],
        parent_id: str | None = None,
    ) -> list[str]:
        """
        同步分镜数据

        Args:
            project_id: 项目 ID
            shots: 分镜列表
            parent_id: 父节点 ID (如 script scene)

        Returns:
            创建的节点 ID 列表
        """
        logger.info("Syncing storyboard", project_id=project_id, count=len(shots))

        created_ids = []
        for i, shot in enumerate(shots):
            node_data = NodeCreate(
                project_id=uuid.UUID(project_id),
                parent_id=uuid.UUID(parent_id) if parent_id else None,
                type=NodeType.STORYBOARD_SHOT,
                content={
                    "shot_id": shot.get("shot_id", f"shot_{i + 1}"),
                    "shot_number": shot.get("shot_number", f"S01-{i + 1:02d}"),
                    "shot_type": shot.get("shot_type", "中景"),
                    "camera_movement": shot.get("camera_movement", "固定"),
                    "subject": shot.get("subject", ""),
                    "action": shot.get("action", ""),
                    "visual_description": shot.get("visual_description", ""),
                    "nano_banana_prompt": shot.get("nano_banana_prompt", ""),
                },
            )

            layout = NodeLayoutUpdate(
                canvas_tab="storyboard",
                position_x=100 + (i % 4) * 350,
                position_y=100 + (i // 4) * 500,
            )

            node = await self._db.create_node(node_data, layout)
            created_ids.append(str(node.id))

        return created_ids

    async def sync_from_state(
        self,
        state: AgentState,
        sync_plans: bool = True,
        sync_beat_sheet: bool = True,
        sync_novel: bool = True,
        sync_script: bool = True,
        sync_storyboard: bool = True,
    ) -> dict[str, list[str]]:
        """
        从 AgentState 批量同步所有产物

        Args:
            state: LangGraph 状态
            sync_*: 控制同步哪些内容

        Returns:
            各类型同步的节点 ID 字典
        """
        project_id = state.get("project_id")
        if not project_id:
            raise ValueError("AgentState missing project_id")

        result: dict[str, list[str]] = {}

        # 同步故事方案
        if sync_plans and state.get("story_plans"):
            result["story_plans"] = await self.sync_story_plans(project_id, state["story_plans"])

        # 同步分集大纲
        if sync_beat_sheet and state.get("beat_sheet"):
            result["beat_sheet"] = await self.sync_beat_sheet(project_id, state["beat_sheet"])

        # 同步小说内容
        if sync_novel and state.get("novel_content"):
            node_id = await self.sync_novel_content(
                project_id,
                state.get("current_episode", 1),
                state["novel_content"],
            )
            result["novel"] = [node_id]

        # 同步剧本
        if sync_script and state.get("script"):
            result["script"] = await self.sync_script_data(project_id, state["script"])

        # 同步分镜
        if sync_storyboard and state.get("storyboard"):
            result["storyboard"] = await self.sync_storyboard(project_id, state["storyboard"])

        logger.info("State synced to DB", project_id=project_id, result=result)
        return result


# ===== Factory =====

_sync_service: SyncService | None = None


def get_sync_service(db: DatabaseService) -> SyncService:
    """获取同步服务实例"""
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService(db)
    return _sync_service
