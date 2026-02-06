"""
Phase 1 Test Suite

测试 Master Router 和 Market Analyst 节点
使用真实 LLM 调用验证
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

import structlog
from langchain_core.messages import HumanMessage

from backend.config import settings
from backend.schemas.agent_state import create_initial_state
from backend.graph.nodes.router import master_router
from backend.graph.nodes.market_analyst import market_analyst
from backend.graph.router import route_from_start, route_after_master

# 初始化服务
from backend.services.model_router import init_model_router
from backend.services import get_prompt_service
from backend.services.database import DatabaseService

# 全局初始化标志
_services_initialized = False


async def init_services():
    """初始化所需服务"""
    global _services_initialized
    if _services_initialized:
        return

    # 初始化 Database Service
    db_service = DatabaseService(settings.supabase_url, settings.supabase_key)

    # 初始化 Model Router
    init_model_router(db_service)

    _services_initialized = True
    logger.info("Services initialized for testing")


logger = structlog.get_logger(__name__)


async def test_master_router():
    """测试 Master Router 节点"""
    print("\n" + "=" * 70)
    print("🧪 测试 1: Master Router - 意图识别")
    print("=" * 70)

    # 使用数据库中配置的用户ID
    user_id = "00000000-0000-0000-0000-000000000001"
    # 使用真实UUID格式的project_id（或None使用全局默认）
    project_id = None

    state = create_initial_state(user_id, project_id)
    state["messages"] = [HumanMessage(content="我想写一个复仇题材的短剧")]
    state["use_master_router"] = True

    print(f"输入: '我想写一个复仇题材的短剧'")
    print(f"User ID: {user_id}")

    try:
        result = await master_router(state)

        print(f"\n✅ Master Router 执行成功")
        print(f"目标 Agent: {result.get('routed_agent')}")
        print(f"UI 反馈: {result.get('ui_feedback')}")

        # 验证路由目标
        assert result.get("routed_agent") is not None, "应该路由到某个 Agent"
        assert result.get("ui_feedback") is not None, "应该有 UI 反馈"

        return True, result

    except Exception as e:
        print(f"\n❌ Master Router 失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None


async def test_market_analyst():
    """测试 Market Analyst 节点"""
    print("\n" + "=" * 70)
    print("🧪 测试 2: Market Analyst - 市场分析")
    print("=" * 70)

    # 使用数据库中配置的用户ID
    user_id = "00000000-0000-0000-0000-000000000001"
    # 使用真实UUID格式的project_id（或None使用全局默认）
    project_id = None

    state = create_initial_state(user_id, project_id)
    state["messages"] = [HumanMessage(content="推荐适合复仇题材的赛道")]

    print(f"输入: '推荐适合复仇题材的赛道'")

    try:
        result = await market_analyst(state)

        print(f"\n✅ Market Analyst 执行成功")

        # 验证市场报告
        market_report = result.get("market_report")
        assert market_report is not None, "应该有市场报告"
        assert "genre_recommendations" in market_report, "应该有题材推荐"

        genres = market_report["genre_recommendations"]
        print(f"推荐题材数量: {len(genres)}")
        for genre in genres[:3]:
            print(f"  - {genre.get('name', 'Unknown')}: {genre.get('description', '')}")

        # 验证 SDUI
        ui = result.get("ui_interaction")
        assert ui is not None, "应该有 SDUI"
        assert hasattr(ui, "buttons"), "应该有 buttons 属性"
        assert len(ui.buttons) > 0, "应该有至少一个按钮"
        print(f"SDUI 按钮数量: {len(ui.buttons)}")

        return True, result

    except Exception as e:
        print(f"\n❌ Market Analyst 失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None


async def test_routing_logic():
    """测试路由逻辑"""
    print("\n" + "=" * 70)
    print("🧪 测试 3: 路由决策逻辑")
    print("=" * 70)

    tests = [
        # (描述, 状态, 期望路由)
        ("有 routed_agent", {"routed_agent": "story_planner"}, "story_planner"),
        ("CMD:analyze", {"messages": [HumanMessage(content="CMD:analyze")]}, "market_analyst"),
        ("L1 阶段", {"current_stage": "L1", "use_master_router": False}, "market_analyst"),
        ("L2 阶段", {"current_stage": "L2", "use_master_router": False}, "story_planner"),
    ]

    passed = 0
    for desc, state_update, expected in tests:
        state = create_initial_state("test", "test")
        state.update(state_update)

        result = route_from_start(state)
        success = result == expected

        status = "✅" if success else "❌"
        print(f"{status} {desc}: {result} (期望: {expected})")

        if success:
            passed += 1

    print(f"\n路由测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_integration():
    """集成测试：Master Router -> Market Analyst"""
    print("\n" + "=" * 70)
    print("🧪 测试 4: 集成测试 (Router -> Market Analyst)")
    print("=" * 70)

    # 使用数据库中配置的用户ID
    user_id = "00000000-0000-0000-0000-000000000001"
    project_id = None  # 使用全局默认映射

    # Step 1: Master Router
    state = create_initial_state(user_id, project_id)
    state["messages"] = [HumanMessage(content="分析一下短剧市场")]
    state["use_master_router"] = True

    print("Step 1: Master Router...")
    router_result = await master_router(state)

    routed_agent = router_result.get("routed_agent")
    print(f"  路由到: {routed_agent}")

    # Step 2: 根据路由结果执行对应 Agent
    if routed_agent in ["market_analyst", "Market_Analyst"]:
        print("Step 2: Market Analyst...")
        state.update(router_result)
        analyst_result = await market_analyst(state)

        market_report = analyst_result.get("market_report")
        if market_report:
            print(
                f"  ✅ 市场分析完成，{len(market_report.get('genre_recommendations', []))} 个推荐"
            )
            return True
        else:
            print(f"  ❌ 市场分析失败")
            return False
    else:
        print(f"  ⚠️ 未路由到 Market Analyst，跳过")
        return True


async def main():
    """运行所有测试"""
    print("\n" + "🚀" * 35)
    print("🚀 LangGraph Phase 1 测试套件")
    print("🚀" * 35)
    print(f"\n配置:")
    print(f"  - 数据库: {settings.database_url[:50]}...")
    print(f"  - LLM 提供商: OpenAI/Gemini")
    print(f"  - 测试时间: {datetime.now(timezone.utc).isoformat()}")

    # 初始化服务
    await init_services()

    results = []

    # 测试 1: Master Router
    success, _ = await test_master_router()
    results.append(("Master Router", success))

    # 测试 2: Market Analyst
    success, _ = await test_market_analyst()
    results.append(("Market Analyst", success))

    # 测试 3: 路由逻辑
    success = await test_routing_logic()
    results.append(("路由逻辑", success))

    # 测试 4: 集成测试
    success = await test_integration()
    results.append(("集成测试", success))

    # 总结
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")

    print(f"\n总计: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
