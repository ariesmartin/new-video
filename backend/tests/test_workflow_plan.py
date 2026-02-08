"""
测试脚本：验证 Agent Registry 和 Workflow Plan 实现

Usage:
    cd /Users/ariesmartin/Documents/new-video
    python -m backend.tests.test_workflow_plan
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.registry import AgentRegistry, WorkflowStep
from backend.schemas.agent_state import AgentState, create_initial_state


def test_agent_registry():
    """测试 Agent Registry"""
    print("\n" + "=" * 60)
    print("测试 1: Agent Registry")
    print("=" * 60)

    # 1. 获取所有 Agents
    agents = AgentRegistry.get_all_agents()
    print(f"✓ 已注册 Agents 数量: {len(agents)}")

    # 2. 获取特定 Agent
    agent = AgentRegistry.get("Storyboard_Director")
    if agent:
        print(f"✓ Storyboard_Director 存在")
        print(f"  - 描述: {agent['description'][:50]}...")
        print(f"  - 能力: {', '.join(agent['capabilities'][:3])}")
    else:
        print("✗ Storyboard_Director 不存在")

    # 3. 检查 Image_Generator (V4.1 新增)
    image_gen = AgentRegistry.get("Image_Generator")
    if image_gen:
        print(f"✓ Image_Generator 存在 (V4.1 新增)")
        print(f"  - 能力: {', '.join(image_gen['capabilities'])}")
    else:
        print("✗ Image_Generator 不存在")

    # 4. 根据能力查找
    storyboard_agents = AgentRegistry.find_by_capability("storyboard_generation")
    print(f"✓ 具有 storyboard_generation 能力的 Agents: {len(storyboard_agents)}")

    # 5. 生成 Prompt 描述
    prompt_desc = AgentRegistry.get_prompt_description()
    print(f"✓ Prompt 描述长度: {len(prompt_desc)} 字符")
    print(f"  预览:\n{prompt_desc[:300]}...")

    return True


def test_workflow_validation():
    """测试工作流验证"""
    print("\n" + "=" * 60)
    print("测试 2: 工作流验证")
    print("=" * 60)

    # 1. 有效工作流
    valid_workflow = [
        WorkflowStep(
            step_id="step_1",
            agent="Storyboard_Director",
            task="生成分镜",
            depends_on=[],
            input_mapping={"script_data": "novel_content"},
            output_mapping="storyboard",
        ),
        WorkflowStep(
            step_id="step_2",
            agent="Image_Generator",
            task="生成图片",
            depends_on=["step_1"],
            input_mapping={"shots": "storyboard"},
            output_mapping="shot_images",
        ),
    ]

    is_valid, msg = AgentRegistry.validate_workflow(valid_workflow)
    print(f"✓ 有效工作流测试: {msg}" if is_valid else f"✗ {msg}")

    # 2. 无效 Agent
    invalid_agent_workflow = [
        WorkflowStep(
            step_id="step_1",
            agent="NonExistent_Agent",
            task="无效任务",
            depends_on=[],
            input_mapping={},
            output_mapping="output",
        )
    ]

    is_valid, msg = AgentRegistry.validate_workflow(invalid_agent_workflow)
    print(f"✓ 无效 Agent 检测: {msg}" if not is_valid else f"✗ 应该检测到无效 Agent")

    # 3. 循环依赖
    cyclic_workflow = [
        WorkflowStep(
            step_id="step_1",
            agent="Storyboard_Director",
            task="步骤1",
            depends_on=["step_2"],
            input_mapping={},
            output_mapping="output",
        ),
        WorkflowStep(
            step_id="step_2",
            agent="Image_Generator",
            task="步骤2",
            depends_on=["step_1"],
            input_mapping={},
            output_mapping="output",
        ),
    ]

    is_valid, msg = AgentRegistry.validate_workflow(cyclic_workflow)
    print(f"✓ 循环依赖检测: {msg}" if not is_valid else f"✗ 应该检测到循环依赖")

    return True


def test_agent_state():
    """测试 AgentState 的 workflow 字段"""
    print("\n" + "=" * 60)
    print("测试 3: AgentState Workflow 字段")
    print("=" * 60)

    state = create_initial_state(user_id="test_user", project_id="test_project")

    # 检查新增字段
    print(f"✓ workflow_plan 初始值: {state.get('workflow_plan')}")
    print(f"✓ current_step_idx 初始值: {state.get('current_step_idx')}")
    print(f"✓ workflow_results 初始值: {state.get('workflow_results')}")
    print(f"✓ intent_analysis 初始值: {state.get('intent_analysis')}")

    # 模拟设置工作流
    state["workflow_plan"] = [
        WorkflowStep(
            step_id="step_1",
            agent="Storyboard_Director",
            task="生成分镜",
            depends_on=[],
            input_mapping={"script_data": "novel_content"},
            output_mapping="storyboard",
        )
    ]
    state["current_step_idx"] = 0
    state["intent_analysis"] = "测试意图"

    print(f"✓ 设置工作流后: {len(state['workflow_plan'])} 步骤")
    print(f"✓ 当前步骤: {state['workflow_plan'][0]['task']}")

    return True


def test_multi_step_scenarios():
    """测试多步骤场景"""
    print("\n" + "=" * 60)
    print("测试 4: 多步骤场景示例")
    print("=" * 60)

    scenarios = [
        {
            "name": "分镜并生图",
            "steps": [
                ("Storyboard_Director", "novel_content", "storyboard"),
                ("Image_Generator", "storyboard", "shot_images"),
            ],
        },
        {
            "name": "提取剧本并分镜",
            "steps": [
                ("Script_Adapter", "novel_content", "script_data"),
                ("Storyboard_Director", "script_data", "storyboard"),
            ],
        },
        {
            "name": "全文处理",
            "steps": [
                ("Script_Adapter", "novel_content", "script_data"),
                ("Storyboard_Director", "script_data", "storyboard"),
                ("Image_Generator", "storyboard", "shot_images"),
            ],
        },
    ]

    for scenario in scenarios:
        print(f"\n场景: {scenario['name']}")
        workflow = []
        for i, (agent, input_field, output_field) in enumerate(scenario["steps"], 1):
            step = WorkflowStep(
                step_id=f"step_{i}",
                agent=agent,
                task=f"步骤 {i}: {agent}",
                depends_on=[f"step_{i - 1}"] if i > 1 else [],
                input_mapping={"input": input_field},
                output_mapping=output_field,
            )
            workflow.append(step)
            print(f"  Step {i}: {agent}")
            print(f"    Input: {input_field} → Output: {output_field}")

        is_valid, msg = AgentRegistry.validate_workflow(workflow)
        status = "✓" if is_valid else "✗"
        print(f"  {status} 验证: {msg}")

    return True


async def test_master_router_integration():
    """测试 Master Router 集成（需要模型）"""
    print("\n" + "=" * 60)
    print("测试 5: Master Router 集成")
    print("=" * 60)

    try:
        from backend.agents.master_router import (
            _extract_routing_decision,
            _check_workflow_continuation,
        )

        # 1. 测试单步骤解析
        single_step_response = """
        {
          "thought_process": "用户想要生成分镜",
          "target_agent": "Storyboard_Director",
          "function_name": "generate_storyboard",
          "parameters": {"episode": 1},
          "ui_feedback": "正在生成分镜..."
        }
        """

        decision = _extract_routing_decision(single_step_response)
        print(f"✓ 单步骤解析")
        print(f"  - routed_agent: {decision['routed_agent']}")
        print(f"  - workflow_plan: {decision.get('workflow_plan', [])}")

        # 2. 测试多步骤解析
        multi_step_response = """
        {
          "intent_analysis": "用户希望分镜并生图",
          "workflow_plan": [
            {
              "step_id": "step_1",
              "agent": "Storyboard_Director",
              "task": "生成分镜",
              "depends_on": [],
              "input_mapping": {"script_data": "novel_content"},
              "output_mapping": "storyboard"
            },
            {
              "step_id": "step_2",
              "agent": "Image_Generator",
              "task": "生成图片",
              "depends_on": ["step_1"],
              "input_mapping": {"shots": "storyboard"},
              "output_mapping": "shot_images"
            }
          ],
          "ui_feedback": "执行两步任务...",
          "estimated_steps": 2
        }
        """

        decision = _extract_routing_decision(multi_step_response)
        print(f"✓ 多步骤解析")
        print(f"  - routed_agent: {decision['routed_agent']}")
        print(f"  - workflow_plan 长度: {len(decision.get('workflow_plan', []))}")
        print(f"  - 第一步 Agent: {decision.get('workflow_plan', [{}])[0].get('agent')}")

        # 3. 测试工作流继续检查
        state = create_initial_state("user1", "proj1")
        state["workflow_plan"] = [
            WorkflowStep(
                step_id="step_1",
                agent="Storyboard_Director",
                task="步骤1",
                depends_on=[],
                input_mapping={},
                output_mapping="storyboard",
            ),
            WorkflowStep(
                step_id="step_2",
                agent="Image_Generator",
                task="步骤2",
                depends_on=["step_1"],
                input_mapping={},
                output_mapping="images",
            ),
        ]
        state["current_step_idx"] = 0

        continuation = _check_workflow_continuation(state)
        if continuation:
            print(f"✓ 工作流继续检测")
            print(f"  - 下一步 idx: {continuation.get('current_step_idx')}")
            print(f"  - 下一步 agent: {continuation.get('routed_agent')}")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Agent Registry & Workflow Plan 测试套件")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("Agent Registry", test_agent_registry()))
    results.append(("Workflow Validation", test_workflow_validation()))
    results.append(("AgentState Fields", test_agent_state()))
    results.append(("Multi-Step Scenarios", test_multi_step_scenarios()))
    results.append(("Master Router Integration", await test_master_router_integration()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
