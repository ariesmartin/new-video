"""
Agent Registry - 动态 Agent 注册表

提供 Agent 的自动发现、能力注册和动态查询功能。
Master Router 通过此注册表了解所有可用 Agents。

Usage:
    from backend.graph.agents.registry import AgentRegistry

    # 获取所有可用 Agents
    agents = AgentRegistry.get_all_agents()

    # 根据能力查找 Agent
    agents = AgentRegistry.find_by_capability("generate_storyboard")

    # 获取 Agent 描述（用于 Prompt）
    description = AgentRegistry.get_prompt_description()
"""

from typing import TypedDict, List, Dict, Any, Callable, Optional
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class AgentCapability(str, Enum):
    """Agent 能力枚举"""

    # 市场分析
    MARKET_ANALYSIS = "market_analysis"
    TREND_RESEARCH = "trend_research"

    # 故事规划
    STORY_PLANNING = "story_planning"
    OUTLINE_GENERATION = "outline_generation"
    CHARACTER_DESIGN = "character_design"

    # 小说创作
    NOVEL_WRITING = "novel_writing"
    CONTENT_EDITING = "content_editing"
    CONTENT_REFINEMENT = "content_refinement"
    STYLE_ANALYSIS = "style_analysis"

    # 剧本处理
    SCRIPT_ADAPTATION = "script_adaptation"
    SCENE_EXTRACTION = "scene_extraction"
    DIALOGUE_GENERATION = "dialogue_generation"

    # 分镜生成
    STORYBOARD_GENERATION = "storyboard_generation"
    SHOT_DESIGN = "shot_design"
    CAMERA_PLANNING = "camera_planning"

    # 图片生成
    IMAGE_GENERATION = "image_generation"
    BATCH_IMAGE_GENERATION = "batch_image_generation"
    IMAGE_REFINEMENT = "image_refinement"

    # 视频生成
    VIDEO_GENERATION = "video_generation"

    # 资产管理
    ASSET_EXTRACTION = "asset_extraction"
    ASSET_MANAGEMENT = "asset_management"
    CHARACTER_INSPECTION = "character_inspection"

    # 分析
    EMOTION_ANALYSIS = "emotion_analysis"
    LOGIC_CHECK = "logic_check"
    QUALITY_REVIEW = "quality_review"


class AgentDefinition(TypedDict):
    """Agent 定义"""

    name: str  # Agent 名称（代码中使用）
    display_name: str  # 显示名称（UI 中使用）
    description: str  # 功能描述
    capabilities: List[str]  # 能力列表
    input_types: List[str]  # 接受的输入类型
    output_types: List[str]  # 产生的输出类型
    category: str  # 分类：L1/L2/L3/ModA/ModB/ModC/ModX
    requires_context: List[str]  # 必需的上下文字段


class WorkflowStep(TypedDict):
    """工作流步骤定义"""

    step_id: str  # 步骤唯一 ID
    agent: str  # Agent 名称
    task: str  # 任务描述
    depends_on: List[str]  # 依赖的步骤 ID 列表
    input_mapping: Dict[str, str]  # 输入映射：{参数名: state字段}
    output_mapping: str  # 输出写入的 state 字段


class WorkflowPlan(TypedDict):
    """工作流计划"""

    intent_analysis: str  # 意图分析
    workflow_plan: List[WorkflowStep]  # 步骤列表
    ui_feedback: str  # 用户反馈文本
    estimated_steps: int  # 预计步骤数


class AgentRegistry:
    """
    Agent 注册表

    管理所有可用 Agents 的元数据，支持：
    - Agent 注册
    - 能力查询
    - Prompt 生成
    - 工作流验证
    """

    _agents: Dict[str, AgentDefinition] = {}
    _initialized: bool = False

    @classmethod
    def _initialize(cls):
        """初始化注册表（自动调用）"""
        if cls._initialized:
            return

        # 注册所有内置 Agents
        cls._register_builtin_agents()
        cls._initialized = True

        logger.info("AgentRegistry initialized", agent_count=len(cls._agents))

    @classmethod
    def _register_builtin_agents(cls):
        """注册内置 Agents"""
        agents = [
            # Level 1: 市场分析
            AgentDefinition(
                name="Market_Analyst",
                display_name="市场分析师",
                description="分析短剧市场趋势、热门题材和用户偏好，提供数据驱动的赛道推荐",
                capabilities=[
                    AgentCapability.MARKET_ANALYSIS,
                    AgentCapability.TREND_RESEARCH,
                ],
                input_types=["user_config", "genre_hint"],
                output_types=["market_report"],
                category="L1",
                requires_context=["user_config"],
            ),
            # Level 2: 故事规划
            AgentDefinition(
                name="Story_Planner",
                display_name="故事规划师",
                description="基于市场分析生成多个故事方案，包含人设、Logline、核心爽点",
                capabilities=[
                    AgentCapability.STORY_PLANNING,
                    AgentCapability.CHARACTER_DESIGN,
                ],
                input_types=["market_report", "user_config"],
                output_types=["story_plans"],
                category="L2",
                requires_context=["market_report", "user_config"],
            ),
            # Level 3: 骨架构建
            AgentDefinition(
                name="Skeleton_Builder",
                display_name="骨架构建师",
                description="生成详细人设（Character Bible）和分集大纲（Beat Sheet）",
                capabilities=[
                    AgentCapability.OUTLINE_GENERATION,
                    AgentCapability.CHARACTER_DESIGN,
                ],
                input_types=["selected_plan", "user_config"],
                output_types=["character_bible", "beat_sheet"],
                category="L3",
                requires_context=["selected_plan"],
            ),
            # Module A: 小说创作
            AgentDefinition(
                name="Novel_Writer",
                display_name="小说创作师",
                description="撰写小说正文，支持续写、扩写、风格调整",
                capabilities=[
                    AgentCapability.NOVEL_WRITING,
                    AgentCapability.STYLE_ANALYSIS,
                ],
                input_types=["beat_sheet", "novel_content", "style_dna"],
                output_types=["novel_content"],
                category="ModA",
                requires_context=["beat_sheet"],
            ),
            AgentDefinition(
                name="Content_Editor",
                display_name="内容审阅师",
                description="审阅小说内容，评估质量并给出修改建议",
                capabilities=[
                    AgentCapability.QUALITY_REVIEW,
                    AgentCapability.LOGIC_CHECK,
                ],
                input_types=["novel_content"],
                output_types=["quality_score", "editor_feedback"],
                category="ModA",
                requires_context=["novel_content"],
            ),
            AgentDefinition(
                name="Content_Refiner",
                display_name="内容精修师",
                description="根据审阅反馈精修内容",
                capabilities=[
                    AgentCapability.CONTENT_REFINEMENT,
                ],
                input_types=["novel_content", "editor_feedback"],
                output_types=["novel_content"],
                category="ModA",
                requires_context=["novel_content", "editor_feedback"],
            ),
            # Module B: 剧本提取
            AgentDefinition(
                name="Script_Adapter",
                display_name="剧本改编师",
                description="将小说转换为结构化剧本，支持多种叙事模式",
                capabilities=[
                    AgentCapability.SCRIPT_ADAPTATION,
                    AgentCapability.SCENE_EXTRACTION,
                    AgentCapability.DIALOGUE_GENERATION,
                ],
                input_types=["novel_content", "narrative_mode"],
                output_types=["script"],
                category="ModB",
                requires_context=["novel_content"],
            ),
            # Module C: 分镜生成
            AgentDefinition(
                name="Storyboard_Director",
                display_name="分镜导演",
                description="将剧本转换为分镜设计，包含镜头类型、运镜方式、视觉描述",
                capabilities=[
                    AgentCapability.STORYBOARD_GENERATION,
                    AgentCapability.SHOT_DESIGN,
                    AgentCapability.CAMERA_PLANNING,
                ],
                input_types=["script", "visual_config"],
                output_types=["storyboard"],
                category="ModC",
                requires_context=["script"],
            ),
            # Module C+: 图片生成（新增）
            AgentDefinition(
                name="Image_Generator",
                display_name="图片生成师",
                description="为分镜生成预览图片，支持批量生成和风格定制",
                capabilities=[
                    AgentCapability.IMAGE_GENERATION,
                    AgentCapability.BATCH_IMAGE_GENERATION,
                    AgentCapability.IMAGE_REFINEMENT,
                ],
                input_types=["storyboard", "shot_description", "style_config"],
                output_types=["shot_images", "image_urls"],
                category="ModC",
                requires_context=["storyboard"],
            ),
            # Module X: 资产管理
            AgentDefinition(
                name="Asset_Inspector",
                display_name="资产探查员",
                description="从文本中提取角色、场景、道具等资产信息",
                capabilities=[
                    AgentCapability.ASSET_EXTRACTION,
                    AgentCapability.ASSET_MANAGEMENT,
                    AgentCapability.CHARACTER_INSPECTION,
                ],
                input_types=["any_text_content"],
                output_types=["asset_manifest", "asset_prompts"],
                category="ModX",
                requires_context=[],
            ),
            # Module A+: 分析实验室
            AgentDefinition(
                name="Analysis_Lab",
                display_name="分析实验室",
                description="分析情绪曲线、进行定向修文（Surgery）",
                capabilities=[
                    AgentCapability.EMOTION_ANALYSIS,
                    AgentCapability.STYLE_ANALYSIS,
                ],
                input_types=["novel_content"],
                output_types=["emotion_curve", "surgery_result"],
                category="ModA+",
                requires_context=["novel_content"],
            ),
        ]

        for agent in agents:
            cls._agents[agent["name"]] = agent

    @classmethod
    def register(cls, agent_def: AgentDefinition) -> None:
        """
        注册一个新的 Agent

        Args:
            agent_def: Agent 定义
        """
        cls._initialize()
        cls._agents[agent_def["name"]] = agent_def
        logger.info("Agent registered", agent_name=agent_def["name"])

    @classmethod
    def get(cls, name: str) -> Optional[AgentDefinition]:
        """
        获取 Agent 定义

        Args:
            name: Agent 名称

        Returns:
            AgentDefinition 或 None
        """
        cls._initialize()
        return cls._agents.get(name)

    @classmethod
    def get_all_agents(cls) -> List[AgentDefinition]:
        """
        获取所有已注册的 Agents

        Returns:
            Agent 定义列表
        """
        cls._initialize()
        return list(cls._agents.values())

    @classmethod
    def find_by_capability(cls, capability: str) -> List[AgentDefinition]:
        """
        根据能力查找 Agents

        Args:
            capability: 能力名称

        Returns:
            具有该能力的 Agent 列表
        """
        cls._initialize()
        return [agent for agent in cls._agents.values() if capability in agent["capabilities"]]

    @classmethod
    def find_by_category(cls, category: str) -> List[AgentDefinition]:
        """
        根据分类查找 Agents

        Args:
            category: 分类（L1/L2/L3/ModA/ModB/ModC/ModX）

        Returns:
            该分类的 Agent 列表
        """
        cls._initialize()
        return [agent for agent in cls._agents.values() if agent["category"] == category]

    @classmethod
    def get_prompt_description(cls) -> str:
        """
        生成用于 Prompt 的 Agent 描述文本

        Returns:
            格式化的描述文本
        """
        cls._initialize()

        lines = ["## 可用 Agents\n"]

        # 按分类分组
        categories = {
            "L1": "Level 1: 启动与配置",
            "L2": "Level 2: 故事规划",
            "L3": "Level 3: 骨架构建",
            "ModA": "Module A: 小说创作",
            "ModB": "Module B: 剧本提取",
            "ModC": "Module C: 分镜生成",
            "ModX": "Module X: 资产管理",
            "ModA+": "Module A+: 分析实验室",
        }

        for cat_key, cat_name in categories.items():
            agents = cls.find_by_category(cat_key)
            if agents:
                lines.append(f"\n### {cat_name}")
                for agent in agents:
                    lines.append(f"\n**{agent['name']}** ({agent['display_name']})")
                    lines.append(f"- 功能: {agent['description']}")
                    lines.append(f"- 能力: {', '.join(agent['capabilities'])}")
                    lines.append(f"- 输入: {', '.join(agent['input_types'])}")
                    lines.append(f"- 输出: {', '.join(agent['output_types'])}")

        return "\n".join(lines)

    @classmethod
    def validate_workflow(cls, workflow: List[WorkflowStep]) -> tuple[bool, str]:
        """
        验证工作流是否有效

        Args:
            workflow: 工作流步骤列表

        Returns:
            (是否有效, 错误信息)
        """
        cls._initialize()

        # 检查步骤 ID 唯一性
        step_ids = [step["step_id"] for step in workflow]
        if len(step_ids) != len(set(step_ids)):
            return False, "工作流中存在重复的步骤 ID"

        # 检查每个步骤
        for step in workflow:
            # 检查 Agent 是否存在
            agent = cls.get(step["agent"])
            if not agent:
                return False, f"步骤 {step['step_id']}: Agent '{step['agent']}' 未注册"

            # 检查依赖是否存在
            for dep in step["depends_on"]:
                if dep not in step_ids:
                    return False, f"步骤 {step['step_id']}: 依赖的步骤 '{dep}' 不存在"

        # 检查循环依赖（简化版）
        visited = set()

        def has_cyclic_dependency(step_id: str, path: set) -> bool:
            if step_id in path:
                return True
            if step_id in visited:
                return False

            path.add(step_id)
            step = next((s for s in workflow if s["step_id"] == step_id), None)
            if step:
                for dep in step["depends_on"]:
                    if has_cyclic_dependency(dep, path):
                        return True
            path.remove(step_id)
            visited.add(step_id)
            return False

        for step in workflow:
            if has_cyclic_dependency(step["step_id"], set()):
                return False, f"工作流存在循环依赖"

        return True, "验证通过"

    @classmethod
    def get_agent_dependencies(cls, workflow: List[WorkflowStep]) -> Dict[str, List[str]]:
        """
        分析工作流的依赖关系

        Args:
            workflow: 工作流步骤列表

        Returns:
            步骤 ID 到依赖步骤 ID 列表的映射
        """
        return {step["step_id"]: step["depends_on"] for step in workflow}


# 初始化注册表
AgentRegistry._initialize()
