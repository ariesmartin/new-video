"""
Skeleton Builder API Routes

大纲构建相关的API端点
对接前端的大纲编辑页面
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog
import re
import json

from backend.schemas.agent_state import AgentState, create_initial_state
from backend.schemas.project import ProjectUpdate
from backend.services.database import get_db_service
from backend.graph.workflows.quality_control_graph import (
    build_quality_control_graph,
    run_quality_review,
    run_chapter_review,
    QualityControlState,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/skeleton", tags=["skeleton-builder"])


# ===== 数据模型 =====


class GenerateOutlineRequest(BaseModel):
    """生成大纲请求"""

    projectId: str
    planId: str
    userInput: Optional[str] = None


class UpdateNodeRequest(BaseModel):
    """更新节点请求"""

    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OutlineResponse(BaseModel):
    """大纲响应"""

    projectId: str
    episodes: List[Dict[str, Any]]
    totalEpisodes: int
    createdAt: str
    updatedAt: str


class OutlineNode(BaseModel):
    """大纲节点"""

    id: str
    type: str  # 'episode' | 'scene' | 'shot'
    title: str
    episodeNumber: Optional[int] = None
    sceneNumber: Optional[int] = None
    shotNumber: Optional[int] = None
    children: Optional[List["OutlineNode"]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfirmOutlineResponse(BaseModel):
    """确认大纲响应"""

    success: bool
    message: str
    nextStep: str = "novel_writer"
    project_converted: bool = False


# ===== 辅助函数 =====


def parse_skeleton_to_outline(skeleton_content: str, project_id: str) -> Dict[str, Any]:
    """
    解析骨架构建器的输出，转换为标准的 OutlineData 格式

    骨架构建器输出格式：
    - 包含 chapter_map, paywall_info, actions 等元数据
    - 也包含章节大纲的文本内容

    转换为：
    - OutlineData 格式，包含 episodes 数组
    """
    import json
    import re
    from datetime import datetime

    # 尝试从内容中提取 JSON 部分
    outline_data = {
        "projectId": project_id,
        "episodes": [],
        "totalEpisodes": 80,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
    }

    try:
        # 尝试解析 JSON 部分
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", skeleton_content)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接找 JSON 对象
            json_match = re.search(
                r'\{\s*"chapter_map"[\s\S]*?"actions"\s*:\s*\[[\s\S]*?\]\s*\}', skeleton_content
            )
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = "{}"

        metadata = json.loads(json_str)

        # 提取元数据
        chapter_map = metadata.get("chapter_map", [])
        paywall_info = metadata.get("paywall_info", {})

        # 从 chapter_map 构建 episodes
        if chapter_map:
            episodes = []
            for chapter_info in chapter_map:
                chapter_num = chapter_info.get("chapter", 0)
                episode_range = chapter_info.get("episodes", "")

                # 解析剧集范围
                episode_nums = []
                if episode_range:
                    # 处理格式如 "1-2" 或 "3"
                    if "-" in episode_range:
                        start, end = episode_range.split("-")
                        episode_nums = list(range(int(start), int(end) + 1))
                    else:
                        episode_nums = [int(episode_range)]

                # 为每个剧集创建 episode
                for ep_num in episode_nums:
                    episode_id = f"ep_{project_id}_{ep_num}"

                    # 检查是否是付费卡点
                    is_paid_wall = False
                    if paywall_info:
                        paywall_chapter = paywall_info.get("chapter")
                        if paywall_chapter and chapter_num == paywall_chapter:
                            is_paid_wall = True

                    # 查找章节大纲文本
                    chapter_title = f"第{chapter_num}章"
                    chapter_summary = ""

                    # 尝试从文本中提取章节标题和摘要
                    chapter_pattern = rf"Chapter\s*{chapter_num}[\s:：]+([^\n]+)"
                    chapter_match = re.search(chapter_pattern, skeleton_content, re.IGNORECASE)
                    if chapter_match:
                        chapter_title = chapter_match.group(1).strip()

                    # 提取摘要（查找摘要部分）
                    summary_pattern = rf"Chapter\s*{chapter_num}[^\n]*\n.*?摘要[\s:：]+([^\n]+)"
                    summary_match = re.search(
                        summary_pattern, skeleton_content, re.IGNORECASE | re.DOTALL
                    )
                    if summary_match:
                        chapter_summary = summary_match.group(1).strip()

                    # 尝试从文本中提取场景清单
                    scenes = []
                    # 查找该章节下的场景部分
                    scene_section_pattern = rf"Chapter\s*{chapter_num}[^\n]*\n.*?场景清单[\s:：]*\n([\s\S]*?)(?=Chapter|\Z)"
                    scene_section_match = re.search(
                        scene_section_pattern, skeleton_content, re.IGNORECASE | re.DOTALL
                    )

                    if scene_section_match:
                        scene_section = scene_section_match.group(1)
                        # 解析每个场景（格式如：1. **场景1**：地点 - 事件）
                        scene_pattern = r"(\d+)\.\s*\*\*([^*]+)\*\*\s*[:：]\s*([^\n]+)"
                        scene_matches = re.findall(scene_pattern, scene_section)

                        for idx, (scene_num, scene_title, scene_desc) in enumerate(
                            scene_matches[:5], 1
                        ):  # 最多5个场景
                            scene_id = f"scene_{project_id}_{ep_num}_{idx}"
                            scenes.append(
                                {
                                    "sceneId": scene_id,
                                    "sceneNumber": idx,
                                    "title": scene_title.strip(),
                                    "content": scene_desc.strip(),
                                    "shots": [],  # 镜头数据暂不解析
                                }
                            )

                    # 如果没有解析到场景，创建一个默认场景
                    if not scenes:
                        scenes.append(
                            {
                                "sceneId": f"scene_{project_id}_{ep_num}_1",
                                "sceneNumber": 1,
                                "title": "主要场景",
                                "content": chapter_summary or f"第{chapter_num}章主要场景",
                                "shots": [],
                            }
                        )

                    episode = {
                        "episodeId": episode_id,
                        "episodeNumber": ep_num,
                        "title": chapter_title,
                        "summary": chapter_summary,
                        "scenes": scenes,
                        "reviewStatus": "pending",
                        "isPaidWall": is_paid_wall,
                    }
                    episodes.append(episode)

            # 按剧集编号排序
            episodes.sort(key=lambda x: x["episodeNumber"])
            outline_data["episodes"] = episodes
            outline_data["totalEpisodes"] = len(episodes)

            # 从骨架内容中提取各个部分
            story_settings = extract_story_settings(skeleton_content)

            # 添加元数据
            outline_data["metadata"] = {
                "chapter_map": chapter_map,
                "paywall_info": paywall_info,
                "source": "skeleton_builder",
                "skeleton_content": skeleton_content,
                "story_settings": story_settings,
            }

            # 保存完整骨架内容，用于在编辑器中显示
            outline_data["content"] = skeleton_content
            outline_data["storySettings"] = story_settings

    except Exception as e:
        logger.error("Failed to parse skeleton content", error=str(e))
        # 返回基本结构

    return outline_data


def extract_story_settings(content: str) -> dict:
    """
    全面提取故事设定各部分，返回 Markdown 格式的内容用于 Tiptap 渲染
    """
    settings = {
        "metadata": extract_section_markdown(
            content, ["一、元数据", "1. 元数据"], ["二、核心设定", "2. 核心设定"]
        ),
        "coreSetting": extract_section_markdown(
            content, ["二、核心设定", "2. 核心设定"], ["三、人物体系", "3. 人物体系"]
        ),
        "characters": extract_characters_section(content),
        "plotArchitecture": extract_section_markdown(
            content,
            ["四、情节架构", "4. 情节架构"],
            ["五、章节大纲", "5. 章节大纲", "六、短剧映射表"],
        ),
        "adaptationMapping": extract_section_markdown(
            content,
            ["六、短剧映射表", "6. 短剧映射表", "六、改编映射"],
            ["七、创作指导", "7. 创作指导"],
        ),
        "writingGuidelines": extract_section_markdown(
            content, ["七、创作指导", "7. 创作指导"], ["八、", "8. "]
        ),
        "paywallDesign": extract_paywall_design(content),
        "tensionCurve": extract_tension_curve(content),
    }
    return settings


def extract_section_markdown(
    content: str, start_markers: List[str], end_markers: List[str]
) -> Dict[str, Any]:
    """提取指定部分的完整 Markdown 内容"""
    result = {"markdown": "", "parsed": {}}
    start_pattern = "|".join(re.escape(m) for m in start_markers)
    end_pattern = "|".join(re.escape(m) for m in end_markers) if end_markers else "$"
    regex = rf"(?:{start_pattern}).*?\n([\s\S]*?)(?=(?:{end_pattern})|$)"
    match = re.search(regex, content, re.IGNORECASE)
    if match:
        result["markdown"] = match.group(1).strip()
        result["parsed"] = parse_key_value_content(result["markdown"])
    return result


def extract_characters_section(content: str) -> List[Dict[str, str]]:
    """提取人物体系部分"""
    characters = []
    section = extract_section_markdown(
        content, ["三、人物体系", "3. 人物体系"], ["四、情节架构", "4. 情节架构"]
    )
    if not section["markdown"]:
        return characters

    char_text = section["markdown"]
    pattern = r"(?:^|\n)(?:#{1,4}\s*\*\*|#{1,4}\s+|\*\*)\s*([^\*\n#]+?)\s*(?:\*\*)?(?=\n|$)"
    char_positions = []
    for match in re.finditer(pattern, char_text, re.MULTILINE):
        name = match.group(1).strip()
        if name and len(name) < 50:
            char_positions.append((name, match.start(), match.end()))

    for i, (name, start, end) in enumerate(char_positions):
        if i < len(char_positions) - 1:
            desc_end = char_positions[i + 1][1] - len(char_positions[i + 1][0]) - 10
            description = char_text[end:desc_end].strip()
        else:
            description = char_text[end:].strip()

        description = description[:1000] if len(description) > 1000 else description
        characters.append(
            {"name": name, "description": description, "markdown": f"### {name}\n\n{description}"}
        )

    return characters[:15]


def extract_paywall_design(content: str) -> Dict[str, Any]:
    """提取付费卡点设计"""
    result = {"markdown": "", "parsed": {}}
    section = extract_section_markdown(
        content, ["一、元数据", "1. 元数据"], ["二、核心设定", "2. 核心设定"]
    )
    if section["markdown"]:
        for line in section["markdown"].split("\n"):
            if "付费卡点" in line and "：" in line:
                result["markdown"] += line + "\n"
                match = re.search(r"第\s*(\d+)(?:\s*-\s*(\d+))?\s*集", line)
                if match:
                    result["parsed"]["episodes"] = match.group(0)
    return result


def extract_tension_curve(content: str) -> Dict[str, Any]:
    """提取张力曲线数据"""
    result = {"markdown": "", "parsed": [], "dataPoints": []}
    section = extract_section_markdown(
        content, ["张力曲线", "张力值", "剧情张力"], ["### Chapter", "## "]
    )
    if section["markdown"]:
        result["markdown"] = section["markdown"]
        for line in section["markdown"].split("\n"):
            if "|" in line and "Chapter" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    try:
                        chapter = re.search(r"Chapter\s*(\d+)", parts[1])
                        tension = re.search(r"(\d+)", parts[-2])
                        if chapter and tension:
                            result["dataPoints"].append(
                                {"chapter": int(chapter.group(1)), "tension": int(tension.group(1))}
                            )
                    except (ValueError, IndexError):
                        pass
    return result


def parse_key_value_content(content: str) -> Dict[str, str]:
    """解析键值对格式的内容"""
    parsed = {}
    for line in content.split("\n"):
        line = line.strip()
        if "：" in line or ":" in line:
            parts = line.split("：", 1) if "：" in line else line.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip("- *")
                value = parts[1].strip()
                if key and value:
                    parsed[key] = value
    return parsed


def format_outline_for_review(outline_data: Dict[str, Any]) -> str:
    """
    将大纲数据格式化为审阅用的文本
    """
    lines = []
    lines.append(f"# {outline_data.get('title', '未命名大纲')}")
    lines.append(f"总集数: {outline_data.get('totalEpisodes', 0)}")
    lines.append("")

    for episode in outline_data.get("episodes", []):
        lines.append(f"## 第{episode.get('episodeNumber', 0)}集: {episode.get('title', '')}")
        lines.append(f"简介: {episode.get('summary', '')}")

        if episode.get("isPaidWall"):
            lines.append("【付费卡点】")

        for scene in episode.get("scenes", []):
            lines.append(f"### 场景 {scene.get('sceneNumber', 0)}: {scene.get('title', '')}")
            lines.append(scene.get("content", ""))

            for shot in scene.get("shots", []):
                lines.append(f"- 镜头 {shot.get('shotNumber', 0)}: {shot.get('description', '')}")

        lines.append("")

    return "\n".join(lines)


# ===== API 端点 =====


@router.post("/generate", response_model=OutlineResponse)
async def generate_outline(request: GenerateOutlineRequest):
    """
    生成大纲

    触发 skeleton_builder_graph 工作流生成大纲结构
    """
    try:
        logger.info(
            "Generating outline",
            project_id=request.projectId,
            plan_id=request.planId,
        )

        # 调用 skeleton_builder_graph
        from backend.graph.workflows.skeleton_builder_graph import (
            build_skeleton_builder_graph,
            run_skeleton_builder,
        )

        # 获取用户配置（从数据库或默认）
        db = get_db_service()
        user_config = await db.get_user_config(request.projectId)

        # 获取选中的方案（DB 行格式）
        db_plan = await db.get_plan(request.planId)
        if not db_plan:
            raise HTTPException(status_code=404, detail="方案不存在")

        # ✅ GAP-2 修复：将 DB 行格式转换为 skeleton_builder 期望的标准格式
        # DB 格式: {id, project_id, title, plan_data: {content, title, plan_id, label}, is_selected}
        # 标准格式: {id, title, label, content}
        raw_plan_data = db_plan.get("plan_data") or {}
        if isinstance(raw_plan_data, str):
            import json as _json

            try:
                raw_plan_data = _json.loads(raw_plan_data)
            except (ValueError, TypeError):
                raw_plan_data = {}

        selected_plan = {
            "id": db_plan.get("plan_id") or raw_plan_data.get("plan_id", ""),
            "title": db_plan.get("title") or raw_plan_data.get("title", ""),
            "label": raw_plan_data.get("label", ""),
            "content": raw_plan_data.get("content", ""),
        }

        if not selected_plan["content"]:
            logger.warning(
                "selected_plan content is empty after transformation",
                plan_id=request.planId,
                db_plan_keys=list(db_plan.keys()),
                plan_data_keys=list(raw_plan_data.keys())
                if isinstance(raw_plan_data, dict)
                else [],
            )

        # 运行 skeleton_builder_graph（启用 checkpoint）
        from backend.graph.checkpointer import get_checkpointer

        async with get_checkpointer() as checkpointer:
            result = await run_skeleton_builder(
                user_id=user_config.get("user_id", "default"),
                project_id=request.projectId,
                selected_plan=selected_plan,
                user_config=user_config,
                checkpointer=checkpointer,  # ✅ 启用持久化
            )

        # 检查 Graph 执行是否返回错误
        if result.get("error"):
            raise HTTPException(status_code=500, detail=f"大纲生成失败: {result['error']}")

        # 提取大纲内容
        skeleton_content = result.get("skeleton_content")
        if not skeleton_content:
            raise HTTPException(status_code=500, detail="大纲生成失败：无内容")

        # 解析骨架内容为标准 OutlineData 格式
        outline_data = parse_skeleton_to_outline(skeleton_content, request.projectId)

        # 保存到数据库
        await db.save_outline(request.projectId, outline_data)

        # 自动触发全局审阅
        try:
            await trigger_global_review(request.projectId, outline_data)
        except Exception as review_error:
            logger.error("自动审阅失败", error=str(review_error))
            # 审阅失败不阻止大纲返回

        return OutlineResponse(**outline_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate outline", error=str(e))
        raise HTTPException(status_code=500, detail=f"生成大纲失败: {str(e)}")


@router.get("/{project_id}", response_model=OutlineResponse)
async def get_outline(project_id: str):
    """
    获取大纲

    获取指定项目的大纲数据（包含审阅结果）
    """
    try:
        logger.info("Getting outline", project_id=project_id)

        # 从数据库加载
        db = get_db_service()
        outline = await db.get_outline(project_id)

        if not outline:
            raise HTTPException(status_code=404, detail="大纲不存在")

        return OutlineResponse(**outline)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get outline", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取大纲失败: {str(e)}")


@router.patch("/{project_id}/nodes/{node_id}")
async def update_node(project_id: str, node_id: str, request: UpdateNodeRequest):
    """
    更新大纲节点

    更新指定节点的标题、内容或元数据，并自动触发该章节的审阅
    """
    try:
        logger.info(
            "Updating outline node",
            project_id=project_id,
            node_id=node_id,
            updates=request.dict(exclude_none=True),
        )

        # 更新数据库
        db = get_db_service()
        await db.update_outline_node(project_id, node_id, request.dict(exclude_none=True))

        # 自动触发该章节的审阅
        try:
            await trigger_chapter_review(project_id, node_id)
        except Exception as review_error:
            logger.error("自动审阅失败", error=str(review_error))
            # 审阅失败不阻止更新返回

        return {
            "success": True,
            "message": "节点更新成功",
            "nodeId": node_id,
            "updatedFields": request.dict(exclude_none=True),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update node", error=str(e))
        raise HTTPException(status_code=500, detail=f"更新节点失败: {str(e)}")


@router.post("/{project_id}/review")
async def review_outline(project_id: str):
    """
    触发大纲全局审阅

    调用 Quality Control Graph 进行全局审阅（global_review 模式）
    """
    try:
        logger.info("Reviewing outline", project_id=project_id)

        # 1. 从数据库获取大纲内容
        db = get_db_service()
        outline_data = await db.get_outline(project_id)

        if not outline_data:
            raise HTTPException(status_code=404, detail="大纲不存在")

        # 2. 格式化大纲内容为文本
        outline_text = format_outline_for_review(outline_data)

        # 3. 调用全局审阅
        review_report = await trigger_global_review(project_id, outline_data, outline_text)

        return {
            "success": True,
            "message": "审阅完成",
            "review": review_report,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to review outline", error=str(e))
        raise HTTPException(status_code=500, detail=f"审阅失败: {str(e)}")


@router.post("/{project_id}/confirm", response_model=ConfirmOutlineResponse)
async def confirm_outline(project_id: str):
    """
    确认大纲

    用户确认大纲后：
    1. 更新项目状态为 outline_confirmed
    2. 如果是临时项目，根据大纲标题转正

    注意：此时不创建剧集(episodes)，剧集在剧本改编阶段创建
    """
    try:
        logger.info("Confirming outline", project_id=project_id)

        db = get_db_service()

        # 1. 获取大纲数据（用于提取标题）
        outline_data = await db.get_outline(project_id)
        if not outline_data:
            raise HTTPException(status_code=404, detail="大纲不存在，请先生成大纲")

        # 2. 更新项目状态
        await db.update_project_status(project_id, "outline_confirmed")
        logger.info("Project status updated to outline_confirmed", project_id=project_id)

        # 3. 项目转正逻辑：如果是临时项目，使用大纲标题转正
        project_converted = False
        try:
            project = await db.get_project(project_id)
            if project and project.is_temporary:
                # 获取大纲标题用于项目名称
                outline_title = outline_data.get("title", "")

                if outline_title:
                    # 检查项目名称是否需要更新（只有默认名称才自动更新）
                    current_name = project.name or ""
                    should_update_name = (
                        "临时项目" in current_name
                        or current_name.startswith("项目-")
                        or current_name == ""
                        or len(current_name) < 5
                    )

                    update_data = ProjectUpdate()
                    if should_update_name:
                        update_data.name = outline_title
                        logger.info(
                            "Auto-updating project name from temporary to formal",
                            old_name=current_name,
                            new_name=outline_title,
                            project_id=project_id,
                        )

                    # 执行转正
                    await db.save_temp_project(project_id, update_data)
                    project_converted = True
                    logger.info(
                        "Project converted from temporary to formal on outline confirmation",
                        project_id=project_id,
                        name_updated=should_update_name,
                    )
        except Exception as convert_error:
            logger.error(
                "Failed to convert temporary project to formal on outline confirmation",
                error=str(convert_error),
                project_id=project_id,
            )

        logger.info(
            "Outline confirmation completed",
            project_id=project_id,
            project_converted=project_converted,
        )

        return ConfirmOutlineResponse(
            success=True,
            message="大纲已确认，进入小说创作阶段",
            nextStep="novel_writer",
            project_converted=project_converted,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to confirm outline", error=str(e))
        raise HTTPException(status_code=500, detail=f"确认大纲失败: {str(e)}")


@router.get("/{project_id}/review", response_model=Dict[str, Any])
async def get_outline_review(project_id: str):
    """
    获取大纲审阅结果

    获取全局审阅报告
    """
    try:
        logger.info("Getting outline review", project_id=project_id)

        # 从数据库加载审阅结果
        db = get_db_service()
        review = await db.get_outline_review(project_id)

        if not review:
            raise HTTPException(status_code=404, detail="审阅结果不存在，请先触发审阅")

        return review

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get outline review", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取审阅结果失败: {str(e)}")


# ===== 内部辅助函数 =====


async def trigger_global_review(
    project_id: str, outline_data: Dict[str, Any], outline_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    触发全局审阅

    审阅整个大纲，返回包含 chapterReviews 的完整报告。
    实现真正的逐章审阅：先全局审阅，再逐章审阅每个剧集。
    """
    db = get_db_service()
    user_config = await db.get_user_config(project_id)
    user_id = user_config.get("user_id", "default")

    if outline_text is None:
        outline_text = format_outline_for_review(outline_data)

    # 第一步：全局审阅（获取整体评分和分类评分）
    logger.info("Starting global review", project_id=project_id)

    global_result = await run_quality_review(
        user_id=user_id,
        project_id=project_id,
        content=outline_text,
        content_type="outline",
    )

    global_review_report = global_result.get("review_report")
    if not global_review_report:
        raise Exception("全局审阅报告生成失败")

    # 第二步：逐章审阅（真正调用 Editor 审阅每个章节）
    logger.info("Starting chapter-by-chapter review", project_id=project_id)

    chapter_reviews = {}
    episodes = outline_data.get("episodes", [])

    for episode in episodes:
        ep_id = episode.get("episodeId")
        ep_number = episode.get("episodeNumber", 0)

        logger.info(f"Reviewing chapter {ep_number}", episode_id=ep_id)

        # 格式化单章内容
        chapter_text = format_chapter_for_review(episode)

        try:
            # 调用 Editor 审阅单章
            chapter_result = await run_chapter_review(
                user_id=user_id,
                project_id=project_id,
                chapter_id=ep_id,
                content=chapter_text,
                content_type="outline",
            )

            chapter_report = chapter_result.get("review_report", {})

            # 构建单章审阅结果
            chapter_reviews[ep_id] = {
                "score": chapter_report.get("overall_score", 80),
                "status": "passed" if chapter_report.get("overall_score", 80) >= 80 else "warning",
                "issues": chapter_report.get("issues", []),
                "comment": chapter_report.get("verdict", "审阅完成"),
                "episodeNumber": ep_number,
            }

        except Exception as e:
            logger.error(f"Failed to review chapter {ep_number}", episode_id=ep_id, error=str(e))
            # 审阅失败时，使用全局评分作为后备
            chapter_reviews[ep_id] = {
                "score": global_review_report.get("overall_score", 80),
                "status": "warning",
                "issues": [{"description": f"审阅失败: {str(e)}"}],
                "comment": "审阅过程出错",
                "episodeNumber": ep_number,
            }

    # 第三步：构建完整的全局审阅报告
    from backend.services.tension_service import generate_tension_curve
    from backend.services.review_service import calculate_weights

    total_episodes = outline_data.get("totalEpisodes", 80)
    genre_combination = user_config.get("sub_tags", ["revenge"])

    # 生成张力曲线
    tension_curve_data = generate_tension_curve(total_episodes, "standard")

    # 计算权重
    weights = calculate_weights(genre_combination)

    # 组装完整的全局审阅报告
    global_review = {
        "generatedAt": datetime.now().isoformat(),
        "overallScore": global_review_report.get("overall_score", 0),
        "categories": {
            category: {
                "score": global_review_report.get("categories", {})
                .get(category, {})
                .get("score", 80),
                "weight": weights.get(category, 0.16),
                "issues": global_review_report.get("categories", {})
                .get(category, {})
                .get("issues", []),
            }
            for category in ["logic", "pacing", "character", "conflict", "world", "hook"]
        },
        "tensionCurve": tension_curve_data.get("values", []),
        "chapterReviews": chapter_reviews,
        "summary": global_review_report.get("summary", "审阅完成"),
        "recommendations": global_review_report.get("recommendations", []),
    }

    # 保存到数据库
    await db.save_outline_review(project_id, global_review)

    logger.info(
        "Global review completed",
        project_id=project_id,
        overall_score=global_review["overallScore"],
        chapters_reviewed=len(chapter_reviews),
    )

    return global_review


async def trigger_chapter_review(project_id: str, chapter_id: str) -> Dict[str, Any]:
    """
    触发单章审阅

    审阅指定章节，返回单章审阅报告
    """
    db = get_db_service()

    # 获取章节内容
    chapter_data = await db.get_outline_node(project_id, chapter_id)
    if not chapter_data:
        raise HTTPException(status_code=404, detail="章节不存在")

    # 格式化章节内容
    chapter_text = format_chapter_for_review(chapter_data)

    # 调用 Quality Control Graph（单章审阅模式）
    user_config = await db.get_user_config(project_id)

    result = await run_chapter_review(
        user_id=user_config.get("user_id", "default"),
        project_id=project_id,
        chapter_id=chapter_id,
        content=chapter_text,
        content_type="outline",
    )

    review_report = result.get("review_report")
    if not review_report:
        raise Exception("审阅报告生成失败")

    # 构建单章审阅报告
    chapter_review = {
        "chapterId": chapter_id,
        "reviewedAt": datetime.now().isoformat(),
        "score": review_report.get("overall_score", 0),
        "issues": review_report.get("issues", []),
        "suggestions": review_report.get("recommendations", []),
    }

    # 保存到数据库
    await db.save_chapter_review(project_id, chapter_id, chapter_review)

    # 更新全局审阅中的该章节状态
    await update_global_review_chapter(project_id, chapter_id, chapter_review)

    return chapter_review


def format_chapter_for_review(chapter_data: Dict[str, Any]) -> str:
    """
    将章节数据格式化为审阅用的文本
    """
    lines = []
    lines.append(f"# {chapter_data.get('title', '未命名章节')}")
    lines.append("")

    if chapter_data.get("summary"):
        lines.append(f"简介: {chapter_data.get('summary')}")
        lines.append("")

    if chapter_data.get("content"):
        lines.append(chapter_data.get("content"))

    return "\n".join(lines)


async def update_global_review_chapter(
    project_id: str, chapter_id: str, chapter_review: Dict[str, Any]
):
    """
    更新全局审阅报告中的单章审阅结果
    """
    db = get_db_service()

    # 获取当前全局审阅
    global_review = await db.get_outline_review(project_id)
    if not global_review:
        return

    # 更新章节审阅
    if "chapterReviews" not in global_review:
        global_review["chapterReviews"] = {}

    global_review["chapterReviews"][chapter_id] = {
        "score": chapter_review.get("score", 0),
        "status": "passed" if chapter_review.get("score", 0) >= 80 else "warning",
        "issues": chapter_review.get("issues", []),
    }

    # 重新计算总分（简化版：取所有章节平均分）
    chapter_scores = [cr.get("score", 0) for cr in global_review["chapterReviews"].values()]
    if chapter_scores:
        global_review["overallScore"] = round(sum(chapter_scores) / len(chapter_scores))

    # 保存更新
    await db.save_outline_review(project_id, global_review)
