#!/usr/bin/env python3
"""
Story Planner 完整流程验证测试

验证用户选择分类后是否正确进入方案生成阶段
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# 设置测试环境
import os

os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://localhost/test"

from langchain_core.messages import HumanMessage, AIMessage


# 模拟 _story_planner_node 的核心逻辑
async def test_story_planner_logic():
    """直接测试 _story_planner_node 的核心逻辑"""

    print("=" * 80)
    print("🧪 测试 _story_planner_node 核心逻辑")
    print("=" * 80)

    # 场景 1: 用户已选择分类（通过 routed_parameters）
    print("\n【场景 1】用户通过按钮选择分类")
    state = {
        "user_id": "test-user",
        "project_id": "test-project",
        "user_config": {},  # 初始为空
        "routed_parameters": {"genre": "赛博现实主义", "setting": "future"},
        "messages": [],
    }

    print(f"输入状态:")
    print(f"  user_config: {state['user_config']}")
    print(f"  routed_parameters: {state['routed_parameters']}")

    # 执行 _story_planner_node 开头的逻辑
    user_config = state.get("user_config", {}).copy()
    routed_params = state.get("routed_parameters", {})

    if routed_params.get("genre"):
        user_config["genre"] = routed_params["genre"]
        user_config["setting"] = routed_params.get("setting", "modern")
        state["user_config"] = user_config
        print(f"\n✅ 更新 user_config: {user_config}")

    genre = user_config.get("genre")

    if genre:
        print(f"✅ genre 存在 ({genre})，应该进入方案生成")
        should_generate_plans = True
    else:
        print(f"❌ genre 不存在，会显示分类选择")
        should_generate_plans = False

    # 场景 2: 检查实际返回的 UI
    print("\n" + "=" * 80)
    print("【场景 2】验证返回的 UI 类型")
    print("=" * 80)

    # 模拟返回的 UI（分类选择）
    category_ui = {
        "block_type": "action_group",
        "title": "选择故事背景",
        "description": "请选择您想创作的故事背景：",
        "buttons": [
            {"label": "🏙️ 现代都市", "action": "select_genre"},
            {"label": "👘 古装仙侠", "action": "select_genre"},
        ],
    }

    # 模拟返回的 UI（方案选择）
    plan_ui = {
        "block_type": "action_group",
        "title": "选择故事方案",
        "description": "请选择一个方案继续创作：",
        "buttons": [
            {"label": "方案 A: xxx", "action": "select_plan"},
            {"label": "方案 B: xxx", "action": "select_plan"},
            {"label": "方案 C: xxx", "action": "select_plan"},
        ],
    }

    print("\n如果返回分类选择 UI:")
    print(f"  Title: {category_ui['title']}")
    print(
        f"  包含'背景'或'分类': {'背景' in category_ui['title'] or '分类' in category_ui['title']}"
    )

    print("\n如果返回方案选择 UI:")
    print(f"  Title: {plan_ui['title']}")
    print(f"  包含'方案'或'Plan': {'方案' in plan_ui['title'] or 'Plan' in plan_ui['title']}")

    # 场景 3: 检查截图中的问题
    print("\n" + "=" * 80)
    print("【场景 3】分析截图中的问题")
    print("=" * 80)
    print("""
根据截图分析：
1. 用户点击了"赛博现实主义"按钮
2. 显示了用户消息："选择：赛博现实主义" ✅
3. 然后又显示了分类选择 UI ❌

问题推断：
- routed_parameters 可能没有正确传递到 _story_planner_node
- 或者 state 在传递过程中被重置
- 或者 Master Router 没有正确设置 routed_parameters

需要验证的日志：
1. Master Router 是否设置了 routed_parameters？
2. _story_planner_node 是否收到了 routed_parameters？
3. 如果收到了，为什么 genre 仍然是空？
    """)

    print("\n" + "=" * 80)
    print("建议的调试日志")
    print("=" * 80)
    print("""
在以下位置添加日志：

1. backend/graph/agents/master_router.py (line 364)
   logger.info("Setting routed_parameters", params=routed_parameters)

2. backend/graph/main_graph.py _story_planner_node (line 137)
   logger.info("Received state", 
               routed_params=state.get("routed_parameters"),
               user_config=state.get("user_config"))

然后重新运行，查看日志输出。
    """)


if __name__ == "__main__":
    asyncio.run(test_story_planner_logic())
