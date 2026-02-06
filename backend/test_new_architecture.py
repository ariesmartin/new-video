"""
Test New Architecture

验证新的 Market Analyst 架构：
1. Market Analyst 按需调用（关键词触发搜索）
2. Story Planner 读取缓存的市场数据
3. 路由逻辑正确（Market Analyst 不再是必经节点）
"""

import asyncio
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

import structlog
from langchain_core.messages import HumanMessage

from backend.config import settings
from backend.schemas.agent_state import create_initial_state
from backend.graph.nodes.router import master_router
from backend.graph.nodes.market_analyst import market_analyst, should_search_realtime
from backend.graph.nodes.story_planner import story_planner
from backend.graph.router import route_from_start, route_after_master
from backend.services.model_router import init_model_router
from backend.services.database import DatabaseService

logger = structlog.get_logger(__name__)


async def init_services():
    """初始化服务"""
    from backend.services.database import init_db_service

    db_service = await init_db_service()
    init_model_router(db_service)
    logger.info("Services initialized")


async def test_keyword_detection():
    """测试关键词检测"""
    print("\n" + "=" * 70)
    print("🧪 测试 1: 关键词检测")
    print("=" * 70)

    test_cases = [
        ("帮我分析下复仇题材", True),
        ("搜索一下热门题材", True),
        ("调研市场趋势", True),
        ("查找最新爆款", True),
        ("推荐几个题材", False),
        ("我想写短剧", False),
        ("开始创作", False),
    ]

    passed = 0
    for text, expected in test_cases:
        result = should_search_realtime(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text[:20]}...' -> 搜索={result} (期望={expected})")
        if result == expected:
            passed += 1

    print(f"\n结果: {passed}/{len(test_cases)} 通过")
    return passed == len(test_cases)


async def test_market_analyst_realtime_search():
    """测试 Market Analyst 实时搜索"""
    print("\n" + "=" * 70)
    print("🧪 测试 2: Market Analyst 实时搜索")
    print("=" * 70)

    user_id = "00000000-0000-0000-0000-000000000001"

    # 场景 A: 触发实时搜索
    state = create_initial_state(user_id, None)
    state["messages"] = [HumanMessage(content="分析一下复仇题材的市场热度")]

    print("输入: '分析一下复仇题材的市场热度'（应触发实时搜索）")

    try:
        result = await market_analyst(state)

        market_report = result.get("market_report", {})
        is_realtime = market_report.get("is_realtime", False)

        print(f"✅ Market Analyst 执行成功")
        print(f"   是否实时搜索: {is_realtime}")
        print(f"   题材数量: {len(market_report.get('genre_recommendations', []))}")

        # 验证触发了实时搜索
        assert is_realtime, "应该触发实时搜索"

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_market_analyst_cached_data():
    """测试 Market Analyst 使用缓存数据"""
    print("\n" + "=" * 70)
    print("🧪 测试 3: Market Analyst 使用缓存")
    print("=" * 70)

    user_id = "00000000-0000-0000-0000-000000000001"

    # 场景 B: 不触发实时搜索
    state = create_initial_state(user_id, None)
    state["messages"] = [HumanMessage(content="推荐几个题材")]

    print("输入: '推荐几个题材'（应使用缓存）")

    try:
        result = await market_analyst(state)

        market_report = result.get("market_report", {})
        is_realtime = market_report.get("is_realtime", False)

        print(f"✅ Market Analyst 执行成功")
        print(f"   是否实时搜索: {is_realtime}")
        print(f"   题材数量: {len(market_report.get('genre_recommendations', []))}")

        # 验证使用了缓存
        assert not is_realtime, "应该使用缓存"

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_story_planner_uses_market_context():
    """测试 Story Planner 使用市场上下文"""
    print("\n" + "=" * 70)
    print("🧪 测试 4: Story Planner 使用市场上下文")
    print("=" * 70)

    user_id = "00000000-0000-0000-0000-000000000001"

    state = create_initial_state(user_id, None)
    state["messages"] = [HumanMessage(content="我想写个复仇题材的短剧")]
    state["user_config"] = {"genre": "revenge"}

    print("输入: '我想写个复仇题材的短剧'")

    try:
        result = await story_planner(state)

        story_plans = result.get("story_plans", [])

        print(f"✅ Story Planner 执行成功")
        print(f"   方案数量: {len(story_plans)}")

        if story_plans:
            print(f"   第一个方案: {story_plans[0].get('title', 'N/A')}")

        # 验证生成了方案
        assert len(story_plans) > 0, "应该生成至少一个方案"

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_routing_not_required():
    """测试 Market Analyst 不再是必经节点"""
    print("\n" + "=" * 70)
    print("🧪 测试 5: 路由逻辑（Market Analyst 非必经）")
    print("=" * 70)

    # 场景 A: 默认路由应该到 Story Planner
    state = create_initial_state("test", None)
    state["use_master_router"] = False  # 禁用 Master Router
    state["current_stage"] = "L2"

    result = route_from_start(state)

    print(f"默认路由（L2, use_master_router=False）: {result}")

    assert result == "story_planner", f"应该路由到 story_planner，但得到 {result}"

    # 场景 B: Master Router 后默认到 Story Planner
    state2 = create_initial_state("test", None)
    state2["routed_agent"] = None  # Master Router 没有识别到特定 Agent

    result2 = route_after_master(state2)

    print(f"Master Router 后（无 routed_agent）: {result2}")

    assert result2 == "story_planner", f"应该默认到 story_planner，但得到 {result2}"

    print("✅ 路由逻辑正确")
    return True


async def main():
    """运行所有测试"""
    print("\n" + "🚀" * 35)
    print("🚀 新架构测试套件")
    print("🚀" * 35)
    print(f"\n测试时间: {datetime.now(timezone.utc).isoformat()}")

    # 初始化服务
    await init_services()

    results = []

    # 测试 1: 关键词检测
    results.append(("关键词检测", await test_keyword_detection()))

    # 测试 2: 实时搜索
    results.append(("实时搜索", await test_market_analyst_realtime_search()))

    # 测试 3: 缓存数据
    results.append(("缓存数据", await test_market_analyst_cached_data()))

    # 测试 4: Story Planner 市场上下文
    results.append(("Story Planner 市场上下文", await test_story_planner_uses_market_context()))

    # 测试 5: 路由逻辑
    results.append(("路由逻辑", await test_routing_not_required()))

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
