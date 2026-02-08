"""
Graph Agents Package

LangGraph Agent 定义，使用 create_react_agent 创建。

每个 Agent 是一个完整的智能体，具备：
- 自主决策能力
- Tool 调用能力
- 多轮推理能力

Usage:
    from backend.agents import (
        master_router_node,
        create_market_analyst_agent,
        create_storyboard_director_agent,
    )

    # Master Router 直接使用
    result = await master_router_node(state)

    # 其他 Agent 需要创建
    agent = await create_market_analyst_agent(user_id, project_id)
    result = await agent.ainvoke({"messages": [...]})
"""

# Level 0: 总控中枢 (直接调用 LLM，不使用 create_react_agent)
from backend.agents.master_router import master_router_node

# Level 1-3: 核心创作流程 (使用 create_react_agent)
from backend.agents.market_analyst import create_market_analyst_agent
from backend.agents.story_planner import create_story_planner_agent

# Level 3: 骨架构建 (Skeleton Builder + Editor + Refiner)
from backend.agents.skeleton_builder import (
    create_skeleton_builder_agent,
    skeleton_builder_node,
)
from backend.agents.quality_control.editor import (
    create_editor_agent,
    editor_node,
)
from backend.agents.quality_control.refiner import (
    create_refiner_agent,
    refiner_node,
)

# Module B: 剧本提取
from backend.agents.script_adapter import create_script_adapter_agent

# Module C: 分镜生成
from backend.agents.storyboard_director import create_storyboard_director_agent
from backend.agents.image_generator import create_image_generator_agent

__all__ = [
    # Level 0
    "master_router_node",
    # Level 1
    "create_market_analyst_agent",
    # Level 2
    "create_story_planner_agent",
    # Level 3: Skeleton Builder
    "create_skeleton_builder_agent",
    "skeleton_builder_node",
    # Level 3: Quality Control
    "create_editor_agent",
    "editor_node",
    "create_refiner_agent",
    "refiner_node",
    # Module B
    "create_script_adapter_agent",
    # Module C
    "create_storyboard_director_agent",
    "create_image_generator_agent",
]
