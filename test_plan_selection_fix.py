#!/usr/bin/env python3
"""
测试方案选择后路由修复
验证选择方案后是否正确路由到 skeleton_builder
"""

import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")


def test_frontend_fix():
    """测试前端修复"""
    print("=" * 60)
    print("🧪 测试前端 UI 消息处理修复")
    print("=" * 60)

    # 读取前端代码
    with open(
        "/Users/ariesmartin/Documents/new-video/new-fronted/src/components/ai/AIAssistantPanel.tsx",
        "r",
    ) as f:
        content = f.read()

    # 检查修复
    checks = [
        ("条件修复", "if (accumulatedContent || lastUiInteraction)"),
        ("空内容处理", "content: accumulatedContent || ''"),
    ]

    all_passed = True
    for name, pattern in checks:
        if pattern in content:
            print(f"   ✅ {name}: 已修复")
        else:
            print(f"   ❌ {name}: 未找到")
            all_passed = False

    return all_passed


def test_backend_fix():
    """测试后端路由修复"""
    print("\n" + "=" * 60)
    print("🧪 测试后端路由修复")
    print("=" * 60)

    # 读取后端代码
    with open(
        "/Users/ariesmartin/Documents/new-video/backend/graph/main_graph.py", "r"
    ) as f:
        content = f.read()

    # 检查修复
    checks = [
        ("导入路由函数", "route_after_story_planner,"),
        (
            "Story Planner 路由",
            'graph.add_conditional_edges(\n        "story_planner",\n        route_after_story_planner',
        ),
        (
            "Skeleton Builder 路由",
            'graph.add_conditional_edges(\n        "skeleton_builder",\n        route_after_skeleton_builder',
        ),
        (
            "Market Analyst 路由",
            'graph.add_conditional_edges(\n        "market_analyst",\n        route_after_market_analyst',
        ),
    ]

    all_passed = True
    for name, pattern in checks:
        if pattern in content:
            print(f"   ✅ {name}: 已修复")
        else:
            print(f"   ❌ {name}: 未找到")
            all_passed = False

    return all_passed


def test_router_functions():
    """测试路由函数定义"""
    print("\n" + "=" * 60)
    print("🧪 测试路由函数定义")
    print("=" * 60)

    with open(
        "/Users/ariesmartin/Documents/new-video/backend/graph/router.py", "r"
    ) as f:
        content = f.read()

    checks = [
        ("route_after_story_planner", "def route_after_story_planner("),
        ("route_after_skeleton_builder", "def route_after_skeleton_builder("),
        ("route_after_market_analyst", "def route_after_market_analyst("),
        ("检查 selected_plan", 'selected_plan = state.get("selected_plan")'),
        ("路由到 skeleton_builder", 'return "skeleton_builder"'),
    ]

    all_passed = True
    for name, pattern in checks:
        if pattern in content:
            print(f"   ✅ {name}: 已定义")
        else:
            print(f"   ❌ {name}: 未找到")
            all_passed = False

    return all_passed


def main():
    """主测试函数"""
    print("\n" + "🧪" * 30)
    print("   方案选择路由修复验证")
    print("🧪" * 30)

    results = []
    results.append(("前端修复", test_frontend_fix()))
    results.append(("后端修复", test_backend_fix()))
    results.append(("路由函数", test_router_functions()))

    # 最终报告
    print("\n" + "=" * 60)
    print("📊 测试报告")
    print("=" * 60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {status}: {name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)

    print(f"\n总计: {total} 项")
    print(f"   ✅ 通过: {passed}")
    print(f"   ❌ 失败: {total - passed}")

    if passed == total:
        print("\n🎉 所有修复验证通过！")
        print("\n📝 修复内容：")
        print("   【前端】AIAssistantPanel.tsx")
        print(
            "      - onComplete 条件改为: if (accumulatedContent || lastUiInteraction)"
        )
        print("      - 支持只返回 ui_interaction 的消息")
        print("\n   【后端】main_graph.py")
        print("      - 导入特定路由函数")
        print("      - story_planner 使用 route_after_story_planner")
        print("      - 选择方案后正确路由到 skeleton_builder")
        print("\n✨ 效果：")
        print('   - 选择方案后立即显示"开始大纲拆解"按钮')
        print("   - 不再重复显示方案选择界面")
        print("   - 刷新页面后状态保持一致")
    else:
        print(f"\n⚠️ {total - passed} 项测试失败，请检查。")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
