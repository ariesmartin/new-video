#!/usr/bin/env python3
"""
Story Planner 流程测试脚本

测试步骤：
1. 模拟用户选择分类（select_genre）
2. 验证是否正确路由到 Story Planner
3. 验证是否进入方案生成（而非重新显示分类选择）

使用方法：
    cd /Users/ariesmartin/Documents/new-video/backend
    python test_story_planner_flow.py
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加后端目录到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.schemas.agent_state import AgentState
from backend.graph.main_graph import create_main_graph
from langchain_core.messages import HumanMessage


async def test_select_genre_flow():
    """测试选择分类后的完整流程"""

    print("=" * 80)
    print("🧪 测试 Story Planner 流程")
    print("=" * 80)

    # 创建图
    print("\n1. 创建 Main Graph...")
    graph = create_main_graph()
    print("   ✅ Graph 创建成功")

    # 测试场景 1: 用户点击"赛博现实主义"按钮
    print("\n2. 模拟用户选择分类...")
    thread_id = "test-thread-001"

    # 构建初始状态（模拟用户点击按钮后的状态）
    state = {
        "user_id": "test-user",
        "project_id": "test-project",
        "thread_id": thread_id,
        "messages": [
            HumanMessage(
                content=json.dumps(
                    {
                        "action": "select_genre",
                        "payload": {"genre": "赛博现实主义", "setting": "future"},
                    }
                )
            )
        ],
        "user_config": {},  # 初始为空
        "detected_action": "select_genre",
        "action_payload": {"genre": "赛博现实主义", "setting": "future"},
    }

    print(f"   - Action: select_genre")
    print(f"   - Payload: {state['action_payload']}")
    print(f"   - User Config (初始): {state['user_config']}")

    # 运行图
    print("\n3. 执行 Graph...")
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await graph.ainvoke(state, config)
        print("   ✅ Graph 执行完成")

        # 验证结果
        print("\n4. 验证结果...")
        print(f"   - Last Successful Node: {result.get('last_successful_node')}")
        print(f"   - Routed Agent: {result.get('routed_agent')}")
        print(f"   - Routed Parameters: {result.get('routed_parameters')}")
        print(f"   - User Config (最终): {result.get('user_config')}")

        # 检查 ui_interaction
        ui = result.get("ui_interaction")
        if ui:
            print(f"\n   - UI Interaction Block:")
            if hasattr(ui, "title"):
                print(f"     Title: {ui.title}")
            if hasattr(ui, "buttons"):
                print(f"     Buttons: {len(ui.buttons)} 个")
                for btn in ui.buttons[:3]:
                    if hasattr(btn, "label"):
                        print(f"       - {btn.label}")

        # 关键验证点
        print("\n5. 关键验证...")

        # 验证 1: routed_agent 应该是 story_planner
        routed_agent = result.get("routed_agent")
        if routed_agent == "story_planner":
            print("   ✅ routed_agent 正确: story_planner")
        else:
            print(f"   ❌ routed_agent 错误: {routed_agent} (期望: story_planner)")

        # 验证 2: routed_parameters 应该包含 genre
        routed_params = result.get("routed_parameters", {})
        if routed_params.get("genre") == "赛博现实主义":
            print("   ✅ routed_parameters 包含 genre")
        else:
            print(f"   ❌ routed_parameters 缺失 genre: {routed_params}")

        # 验证 3: 不应该再次显示分类选择 UI
        if ui and hasattr(ui, "title"):
            if "方案" in ui.title or "Plan" in ui.title:
                print(f"   ✅ 显示方案选择 UI: {ui.title}")
            elif "背景" in ui.title or "分类" in ui.title or "Category" in ui.title:
                print(f"   ❌ 仍然显示分类选择 UI: {ui.title}")
                print("      问题: genre 没有正确传递到 Story Planner!")
            else:
                print(f"   ⚠️  未知 UI: {ui.title}")

        # 验证 4: 检查消息内容
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "content"):
                content = str(last_msg.content)[:100]
                print(f"\n   - 最后消息内容: {content}...")

                if "方案" in content or "Plan" in content:
                    print("   ✅ 消息内容表明进入方案生成")
                elif "背景" in content or "分类" in content:
                    print("   ❌ 消息内容仍然在选择分类")

        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


async def test_story_planner_node_directly():
    """直接测试 _story_planner_node 逻辑"""

    print("\n" + "=" * 80)
    print("🧪 直接测试 _story_planner_node")
    print("=" * 80)

    # 模拟状态：已选择 genre
    state = {
        "user_id": "test-user",
        "project_id": "test-project",
        "user_config": {},  # 初始为空
        "routed_parameters": {"genre": "赛博现实主义", "setting": "future"},
        "messages": [],
    }

    print(f"\n输入状态:")
    print(f"  user_config: {state['user_config']}")
    print(f"  routed_parameters: {state['routed_parameters']}")

    # 模拟 _story_planner_node 开头的逻辑
    user_config = state.get("user_config", {}).copy()
    routed_params = state.get("routed_parameters", {})

    print(f"\n逻辑执行:")
    print(f"  1. 获取 user_config: {user_config}")
    print(f"  2. 获取 routed_params: {routed_params}")

    if routed_params.get("genre"):
        user_config["genre"] = routed_params["genre"]
        user_config["setting"] = routed_params.get("setting", "modern")
        state["user_config"] = user_config
        print(f"  3. 更新 user_config: {user_config}")
        print(f"     ✅ 成功更新!")
    else:
        print(f"  3. routed_params 中没有 genre")
        print(f"     ❌ 不会更新 user_config")

    genre = user_config.get("genre")
    print(f"\n结果:")
    print(f"  genre: {genre}")

    if genre:
        print(f"  ✅ 会进入方案生成流程")
    else:
        print(f"  ❌ 会显示分类选择 UI")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 先直接测试节点逻辑
    asyncio.run(test_story_planner_node_directly())

    # 再测试完整流程
    print("\n\n")
    asyncio.run(test_select_genre_flow())
