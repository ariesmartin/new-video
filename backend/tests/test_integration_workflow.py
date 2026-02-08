"""
集成测试：工作流端到端流程

测试 Master Router + Workflow Plan + Router 的完整流程
使用 Mock LLM 进行测试（无需 API Key）

Usage:
    cd /Users/ariesmartin/Documents/new-video
    python -m backend.tests.test_integration_workflow
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.schemas.agent_state import AgentState, create_initial_state, WorkflowStep
from backend.agents.master_router import (
    master_router_node,
    _extract_routing_decision,
    _check_workflow_continuation,
)
from backend.graph.router import route_after_master, route_after_agent_execution


class MockLLMResponse:
    """Mock LLM 响应生成器"""

    @staticmethod
    def single_step():
        """单步骤响应"""
        return """
        {
          "thought_process": "用户想要进行市场分析",
          "target_agent": "Market_Analyst",
          "function_name": "analyze_market",
          "parameters": {},
          "ui_feedback": "正在分析市场趋势..."
        }
        """

    @staticmethod
    def multi_step_storyboard_image():
        """分镜+生图 多步骤响应"""
        return """
        {
          "intent_analysis": "用户希望将第一章进行分镜拆分，然后为分镜生成预览图片。这是一个两步任务。",
          "workflow_plan": [
            {
              "step_id": "step_1",
              "agent": "Storyboard_Director",
              "task": "将第一章剧本转换为分镜描述",
              "depends_on": [],
              "input_mapping": {"script_data": "novel_content"},
              "output_mapping": "storyboard"
            },
            {
              "step_id": "step_2",
              "agent": "Image_Generator",
              "task": "为分镜生成预览图片",
              "depends_on": ["step_1"],
              "input_mapping": {"shots": "storyboard"},
              "output_mapping": "shot_images"
            }
          ],
          "ui_feedback": "我将为您：1) 分析第一章并生成分镜 2) 为每个分镜生成预览图",
          "estimated_steps": 2
        }
        """

    @staticmethod
    def multi_step_full_pipeline():
        """全文处理（剧本+分镜+生图）"""
        return """
        {
          "intent_analysis": "用户希望进行全文处理",
          "workflow_plan": [
            {
              "step_id": "step_1",
              "agent": "Script_Adapter",
              "task": "提取剧本",
              "depends_on": [],
              "input_mapping": {"novel_content": "novel_content"},
              "output_mapping": "script_data"
            },
            {
              "step_id": "step_2",
              "agent": "Storyboard_Director",
              "task": "生成分镜",
              "depends_on": ["step_1"],
              "input_mapping": {"script_data": "script_data"},
              "output_mapping": "storyboard"
            },
            {
              "step_id": "step_3",
              "agent": "Image_Generator",
              "task": "生成图片",
              "depends_on": ["step_2"],
              "input_mapping": {"shots": "storyboard"},
              "output_mapping": "shot_images"
            }
          ],
          "ui_feedback": "全文处理：剧本→分镜→图片",
          "estimated_steps": 3
        }
        """


async def test_single_step_workflow():
    """测试单步骤工作流"""
    print("\n" + "=" * 60)
    print("测试 1: 单步骤工作流")
    print("=" * 60)

    # 创建初始状态
    state = create_initial_state("user_1", "proj_1")
    state["messages"] = [MagicMock(type="human", content="分析一下市场趋势")]

    # Mock LLM 响应 - 修复 async mock
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=MagicMock(content=MockLLMResponse.single_step()))

    mock_router_instance = MagicMock()
    mock_router_instance.get_model = AsyncMock(return_value=mock_model)

    with patch(
        "backend.graph.agents.master_router.get_model_router", return_value=mock_router_instance
    ):
        # 执行 Master Router
        result = await master_router_node(state)

    print(f"✓ Master Router 执行完成")
    print(f"  - routed_agent: {result['routed_agent']}")
    print(f"  - ui_feedback: {result['ui_feedback']}")
    print(f"  - workflow_plan: {len(result.get('workflow_plan', []))} 步骤")

    # 验证路由
    assert result["routed_agent"] == "Market_Analyst"
    assert len(result.get("workflow_plan", [])) == 0  # 单步骤没有 workflow_plan

    # 模拟 Router 决策
    state.update(result)
    next_node = route_after_master(state)
    print(f"✓ Router 决策: {next_node}")
    assert next_node == "market_analyst"

    return True


async def test_multi_step_workflow():
    """测试多步骤工作流"""
    print("\n" + "=" * 60)
    print("测试 2: 多步骤工作流 (分镜+生图)")
    print("=" * 60)

    # 创建初始状态（模拟已有第一章小说）
    state = create_initial_state("user_1", "proj_1")
    state["current_stage"] = "ModA"
    state["novel_content"] = "第一章内容..."
    state["messages"] = [MagicMock(type="human", content="将第一章进行分镜并生成分镜图片")]

    # Mock LLM 响应
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(
        return_value=MagicMock(content=MockLLMResponse.multi_step_storyboard_image())
    )

    mock_router_instance = MagicMock()
    mock_router_instance.get_model = AsyncMock(return_value=mock_model)

    with patch(
        "backend.graph.agents.master_router.get_model_router", return_value=mock_router_instance
    ):
        # 执行 Master Router
        result = await master_router_node(state)

    print(f"✓ Master Router 执行完成")
    print(f"  - intent_analysis: {result['intent_analysis'][:50]}...")
    print(f"  - workflow_plan: {len(result['workflow_plan'])} 步骤")
    print(f"  - current_step_idx: {result['current_step_idx']}")
    print(f"  - routed_agent: {result['routed_agent']}")

    # 验证
    assert len(result["workflow_plan"]) == 2
    assert result["current_step_idx"] == 0
    assert result["routed_agent"] == "Storyboard_Director"  # 第一步
    assert result["workflow_plan"][0]["step_id"] == "step_1"
    assert result["workflow_plan"][1]["step_id"] == "step_2"
    assert result["workflow_plan"][1]["depends_on"] == ["step_1"]

    # 模拟 Router 决策 - 第一步
    state.update(result)
    next_node = route_after_master(state)
    print(f"✓ Router 决策 (Step 1): {next_node}")
    assert next_node == "module_c"  # Storyboard_Director 映射到 module_c

    # 模拟第一步完成后的状态
    print(f"\n  --- 模拟 Step 1 完成 ---")
    state["workflow_results"] = {"step_1": {"storyboard": [...]}}
    state["storyboard"] = [{"shot_id": "S01-01"}, {"shot_id": "S01-02"}]

    # 模拟 Router 检查是否需要继续
    continuation = _check_workflow_continuation(state)
    if continuation:
        print(f"✓ 工作流继续")
        print(f"  - 下一步 idx: {continuation['current_step_idx']}")
        print(f"  - 下一步 agent: {continuation['routed_agent']}")
        state.update(continuation)

        # 验证第二步
        assert continuation["routed_agent"] == "Image_Generator"
        assert continuation["current_step_idx"] == 1

    # 模拟第二步完成
    print(f"\n  --- 模拟 Step 2 完成 ---")
    state["workflow_results"]["step_2"] = {"images": ["url1", "url2"]}
    state["shot_images"] = ["url1", "url2"]

    # 检查工作流是否完成
    end_check = _check_workflow_continuation(state)
    if end_check:
        print(f"✓ 工作流完成")
        print(f"  - 最终状态: {end_check['routed_agent']}")
        assert end_check["routed_agent"] == "end"

    return True


async def test_full_pipeline_workflow():
    """测试全流程（剧本+分镜+生图）"""
    print("\n" + "=" * 60)
    print("测试 3: 全流程工作流 (剧本→分镜→生图)")
    print("=" * 60)

    # 创建初始状态
    state = create_initial_state("user_1", "proj_1")
    state["current_stage"] = "ModA"
    state["novel_content"] = "完整小说内容..."
    state["messages"] = [MagicMock(type="human", content="全文处理")]

    # Mock LLM 响应
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(
        return_value=MagicMock(content=MockLLMResponse.multi_step_full_pipeline())
    )

    mock_router_instance = MagicMock()
    mock_router_instance.get_model = AsyncMock(return_value=mock_model)

    with patch(
        "backend.graph.agents.master_router.get_model_router", return_value=mock_router_instance
    ):
        result = await master_router_node(state)

    print(f"✓ Master Router 执行完成")
    print(f"  - workflow_plan: {len(result['workflow_plan'])} 步骤")

    # 验证 3 步骤
    assert len(result["workflow_plan"]) == 3

    # 验证步骤顺序和依赖
    steps = result["workflow_plan"]
    print(f"\n  工作流步骤:")
    for i, step in enumerate(steps, 1):
        deps = step["depends_on"] if step["depends_on"] else "无"
        print(f"    Step {i}: {step['agent']}")
        print(f"      任务: {step['task']}")
        print(f"      依赖: {deps}")

    assert steps[0]["agent"] == "Script_Adapter"
    assert steps[0]["depends_on"] == []
    assert steps[1]["agent"] == "Storyboard_Director"
    assert steps[1]["depends_on"] == ["step_1"]
    assert steps[2]["agent"] == "Image_Generator"
    assert steps[2]["depends_on"] == ["step_2"]

    return True


async def test_workflow_resume():
    """测试工作流恢复（从 Checkpoint）"""
    print("\n" + "=" * 60)
    print("测试 4: 工作流恢复")
    print("=" * 60)

    # 模拟从 checkpoint 恢复的状态（正在进行 Step 2）
    state = create_initial_state("user_1", "proj_1")
    state["workflow_plan"] = [
        WorkflowStep(
            step_id="step_1",
            agent="Storyboard_Director",
            task="生成分镜",
            depends_on=[],
            input_mapping={},
            output_mapping="storyboard",
        ),
        WorkflowStep(
            step_id="step_2",
            agent="Image_Generator",
            task="生成图片",
            depends_on=["step_1"],
            input_mapping={},
            output_mapping="shot_images",
        ),
    ]
    state["current_step_idx"] = 1  # 已经在 Step 2
    state["workflow_results"] = {"step_1": {"status": "completed", "output": "storyboard_data"}}
    state["storyboard"] = [{"shot_id": "S01-01"}]

    # Mock 用户确认继续
    state["messages"] = [MagicMock(type="human", content="继续")]

    # 这种情况下 Master Router 应该检测到工作流并继续到下一步
    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="{}"))

    mock_router_instance = MagicMock()
    mock_router_instance.get_model = AsyncMock(return_value=mock_model)

    with patch(
        "backend.graph.agents.master_router.get_model_router", return_value=mock_router_instance
    ):
        result = await master_router_node(state)

    print(f"✓ 工作流恢复")
    print(f"  - 从 Step {state['current_step_idx'] + 1} 继续")
    print(f"  - routed_agent: {result['routed_agent']}")

    # 注意：current_step_idx=1 表示我们正在 Step 2
    # Master Router 应该直接执行 workflow_plan[1]，然后结束（因为这是最后一步）
    # 或者，如果 LLM 返回了新的决策，使用 LLM 的决策
    # 由于我们 mock 了 LLM 返回空 JSON，Master Router 会检查工作流状态
    # 如果工作流有 2 步，current_step_idx=1，执行完这步后应该结束
    assert result["routed_agent"] in ["Image_Generator", "end"]

    return True


async def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试 5: 错误处理")
    print("=" * 60)

    # 测试 1: JSON 解析失败
    print("\n  测试 JSON 解析失败:")
    invalid_response = "这不是有效的 JSON"
    result = _extract_routing_decision(invalid_response)
    print(f"    ✓ 优雅降级到 end")
    assert result["routed_agent"] == "end"

    # 测试 2: 无效 Agent
    print("\n  测试无效 Agent:")
    invalid_agent_response = """
    {
      "intent_analysis": "测试",
      "workflow_plan": [
        {
          "step_id": "step_1",
          "agent": "NonExistent_Agent",
          "task": "无效任务",
          "depends_on": [],
          "input_mapping": {},
          "output_mapping": "output"
        }
      ],
      "ui_feedback": "测试"
    }
    """
    result = _extract_routing_decision(invalid_agent_response)
    print(f"    ✓ 检测到无效 Agent，降级处理")
    assert result["routed_agent"] == "end"  # 应该降级

    return True


async def test_sse_event_simulation():
    """模拟 SSE 事件流"""
    print("\n" + "=" * 60)
    print("测试 6: SSE 事件流模拟")
    print("=" * 60)

    print("\n  模拟用户输入: '将第一章进行分镜并生图'")
    print("  ---")

    events = [
        ("node_start", "master_router", "分析意图..."),
        ("workflow_planned", "", "计划: 2 步骤"),
        ("node_start", "Storyboard_Director", "步骤 1/2: 生成分镜..."),
        ("tool_call", "generate_storyboard", "生成 5 个分镜"),
        ("node_end", "Storyboard_Director", "分镜生成完成"),
        ("workflow_progress", "", "步骤 1/2 完成"),
        ("node_start", "Image_Generator", "步骤 2/2: 生成图片..."),
        ("tool_call", "generate_images", "生成 5 张图片"),
        ("node_end", "Image_Generator", "图片生成完成"),
        ("workflow_completed", "", "所有步骤完成！"),
    ]

    for event_type, detail, message in events:
        icon = {
            "node_start": "▶️",
            "node_end": "✅",
            "tool_call": "🔧",
            "workflow_planned": "📋",
            "workflow_progress": "⏳",
            "workflow_completed": "🎉",
        }.get(event_type, "•")
        print(f"    {icon} [{event_type:20}] {message}")

    print("  ---")
    print("✓ SSE 事件流模拟完成")

    return True


async def main():
    """运行所有集成测试"""
    print("\n" + "=" * 60)
    print("工作流集成测试套件 (Mock LLM)")
    print("=" * 60)
    print("\n注意: 本测试使用 Mock LLM，无需 API Key")
    print("用于验证流程完整性和数据流正确性")

    results = []

    try:
        results.append(("单步骤工作流", await test_single_step_workflow()))
        results.append(("多步骤工作流", await test_multi_step_workflow()))
        results.append(("全流程工作流", await test_full_pipeline_workflow()))
        results.append(("工作流恢复", await test_workflow_resume()))
        results.append(("错误处理", await test_error_handling()))
        results.append(("SSE 事件流", await test_sse_event_simulation()))
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有集成测试通过！")
        print("\n下一步:")
        print("  1. 运行真实 LLM 测试: python -m backend.tests.test_real_llm")
        print("  2. 启动服务进行端到端测试: python -m backend.main")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
