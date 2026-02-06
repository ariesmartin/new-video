"""
真实LLM测试：验证Master Router的意图识别和多步骤工作流规划

使用真实OpenAI API调用和Supabase配置

Prerequisites:
- Supabase已配置（model_mappings, llm_providers表）
- .env文件中有有效的Supabase和OpenAI配置
- 数据库中有ROUTER或NOVEL_WRITER的模型配置

Usage:
    cd /Users/ariesmartin/Documents/new-video/backend
    python tests/test_real_llm.py
"""

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

import structlog
from langchain_core.messages import HumanMessage

from backend.config import settings
from backend.schemas.agent_state import create_initial_state
from backend.graph.agents.master_router import master_router_node
from backend.graph.agents.registry import AgentRegistry
from backend.services.model_router import init_model_router, get_model_router
from backend.services.database import DatabaseService

logger = structlog.get_logger(__name__)


# 使用真实UUID
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # 示例UUID


# 测试用例
TEST_CASES = [
    {
        "name": "单步骤-市场分析",
        "user_input": "分析一下当前短剧市场趋势",
        "expected_mode": "single",
        "expected_agent": "Market_Analyst",
        "context": {"current_stage": "L1"},
    },
    {
        "name": "多步骤-分镜并生图",
        "user_input": "将第一章进行分镜并生成分镜图片",
        "expected_mode": "multi",
        "expected_steps": 2,
        "context": {"current_stage": "ModA", "novel_content": "第一章：夜幕降临，主角走出房门..."},
    },
    {
        "name": "多步骤-全文处理",
        "user_input": "全文处理",
        "expected_mode": "multi",
        "expected_steps": 3,
        "context": {"current_stage": "ModA", "novel_content": "完整的小说第一章内容..."},
    },
]


def init_services():
    """初始化服务"""
    print("\n" + "=" * 60)
    print("初始化服务...")
    print("=" * 60)

    try:
        # 直接初始化Database Service
        db_service = DatabaseService(settings.supabase_url, settings.supabase_key)
        print(f"✓ Database Service 初始化成功")
        print(f"  - Supabase URL: {settings.supabase_url}")

        # 初始化Model Router
        init_model_router(db_service)
        print("✓ Model Router 初始化成功")

        return True

    except Exception as e:
        print(f"✗ 服务初始化失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def create_test_state(test_case: Dict) -> Dict:
    """创建测试状态"""
    state = create_initial_state(TEST_USER_ID, str(uuid.uuid4()))

    # 添加测试上下文
    context = test_case.get("context", {})
    for key, value in context.items():
        state[key] = value

    # 添加用户消息
    state["messages"] = [HumanMessage(content=test_case["user_input"])]

    return state


async def run_single_test(test_case: Dict) -> Dict[str, Any]:
    """运行单个测试用例"""
    print(f"\n{'=' * 60}")
    print(f"测试: {test_case['name']}")
    print(f'输入: "{test_case["user_input"]}"')
    print(f"预期: {'多步骤' if test_case['expected_mode'] == 'multi' else '单步骤'}")
    print("=" * 60)

    # 创建状态
    state = create_test_state(test_case)

    try:
        # 执行Master Router
        result = await master_router_node(state)

        # 分析结果
        workflow_plan = result.get("workflow_plan", [])
        is_multi_step = len(workflow_plan) > 0

        print(f"\n✓ Master Router 执行成功")
        print(f"  意图分析: {result.get('intent_analysis', 'N/A')[:60]}...")
        print(f"  检测模式: {'多步骤' if is_multi_step else '单步骤'}")
        print(f"  UI反馈: {result.get('ui_feedback', 'N/A')}")

        if is_multi_step:
            print(f"\n  工作流步骤 ({len(workflow_plan)} 步):")
            for i, step in enumerate(workflow_plan, 1):
                print(f"    Step {i}: {step['agent']}")
        else:
            print(f"  目标Agent: {result.get('routed_agent')}")

        # 验证
        success = True
        errors = []

        if test_case["expected_mode"] == "multi" and not is_multi_step:
            success = False
            errors.append(f"预期多步骤，但得到单步骤")
        elif test_case["expected_mode"] == "single" and is_multi_step:
            success = False
            errors.append(f"预期单步骤，但得到多步骤({len(workflow_plan)}步)")

        if "expected_steps" in test_case and is_multi_step:
            if len(workflow_plan) != test_case["expected_steps"]:
                success = False
                errors.append(f"预期{test_case['expected_steps']}步，实际{len(workflow_plan)}步")

        if success:
            print(f"\n✅ 验证通过")
        else:
            print(f"\n❌ 验证失败:")
            for error in errors:
                print(f"  - {error}")

        return {
            "name": test_case["name"],
            "success": success,
            "errors": errors,
            "is_multi_step": is_multi_step,
            "step_count": len(workflow_plan),
        }

    except Exception as e:
        logger.error(f"测试执行失败", error=str(e))
        print(f"\n❌ 测试执行失败: {e}")
        return {
            "name": test_case["name"],
            "success": False,
            "errors": [str(e)],
            "is_multi_step": False,
            "step_count": 0,
        }


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("真实LLM测试 - Master Router Workflow Plan")
    print("=" * 60)
    print(f"\n测试用户ID: {TEST_USER_ID}")
    print("注意: 这将调用真实的OpenAI API\n")

    # 初始化服务
    if not init_services():
        return False

    # 运行所有测试
    results = []
    for test_case in TEST_CASES:
        result = await run_single_test(test_case)
        results.append(result)

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")

    print("\n详细结果:")
    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        mode = f"{'多' if r['is_multi_step'] else '单'}步骤({r['step_count']}步)"
        print(f"  {status}: {r['name']:<25} [{mode}]")

    success_rate = (passed / len(results)) * 100
    print(f"\n成功率: {success_rate:.1f}%")

    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试套件失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
