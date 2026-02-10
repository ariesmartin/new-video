#!/usr/bin/env python3
"""
直接测试 Quality Control Graph
不依赖 skeleton_builder，直接调用审阅功能
"""

import asyncio
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.graph.workflows.quality_control_graph import (
    run_quality_review,
    run_chapter_review,
)

# 测试数据
TEST_USER_ID = "test-user-001"
TEST_PROJECT_ID = "test-project-001"
TEST_CHAPTER_ID = "ep_001"


async def test_global_review():
    """测试全局审阅"""
    print("=" * 60)
    print("🧪 测试全局审阅 (run_quality_review)")
    print("=" * 60)

    # 测试大纲文本
    content = """
# 重生之我在异世界开餐馆

## 故事简介
顶级厨师意外穿越到魔法世界，用美食征服异世界，却卷入王国权力斗争。

## 第1集：穿越与第一道菜
主角李明在车祸中穿越到异世界，醒来发现自己在一个破旧的小餐馆里。他决定用现代烹饪技术做出第一道菜——红烧肉。这道菜香气四溢，吸引了路过的冒险者。

主要情节：
1. 李明穿越到异世界
2. 发现破旧餐馆
3. 制作红烧肉
4. 吸引冒险者

## 第2集：冒险者的订单
冒险者队长被红烧肉征服，决定带全队来吃饭。李明面临食材不足的困境，必须想办法解决。

主要情节：
1. 冒险者队长品尝美食
2. 决定带全队前来
3. 李明面临食材危机
4. 寻找解决方案

## 第3集：贵族的试探
当地贵族听说这家餐馆的美味，派管家前来试探。李明必须应对贵族的挑剔口味。

## 第4集：魔法食材的秘密
李明发现这个世界的食材含有魔法元素，可以做出具有特殊效果的料理。他开始研究如何将魔法融入烹饪。

## 第5集：厨神大赛的邀请
王国举办厨神大赛，李明的餐馆收到邀请。他必须在大赛中证明自己的实力。
"""

    print(f"\n📄 测试大纲长度: {len(content)} 字符")
    print(f"   用户ID: {TEST_USER_ID}")
    print(f"   项目ID: {TEST_PROJECT_ID}")
    print(f"   内容类型: outline")

    try:
        result = await run_quality_review(
            user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
            content=content,
            content_type="outline",
        )

        print(f"\n✅ 全局审阅成功!")
        print(f"\n📊 质量评分: {result.get('quality_score', 'N/A')}/100")

        # 审阅报告
        report = result.get("review_report", {})
        if report:
            print(f"\n📋 审阅报告:")
            print(f"   总体评分: {report.get('overall_score', 'N/A')}/100")

            # 分类评分
            scores = report.get("scores", {})
            if scores:
                print(f"\n   分类评分:")
                for category, score in scores.items():
                    print(f"      • {category}: {score}/100")

            # 问题列表
            issues = report.get("issues", [])
            if issues:
                print(f"\n   ⚠️ 发现 {len(issues)} 个问题:")
                for i, issue in enumerate(issues[:5], 1):
                    print(
                        f"      {i}. [{issue.get('severity', 'N/A')}] {issue.get('category', 'N/A')}: {issue.get('description', '')[:50]}..."
                    )
            else:
                print(f"\n   ✅ 未发现明显问题")

            # 改进建议
            suggestions = report.get("suggestions", [])
            if suggestions:
                print(f"\n   💡 改进建议 ({len(suggestions)} 条):")
                for i, suggestion in enumerate(suggestions[:3], 1):
                    print(f"      {i}. {suggestion[:70]}...")

            # 张力曲线
            tension_curve = report.get("tension_curve", [])
            if tension_curve:
                print(f"\n   📈 张力曲线:")
                print(f"      点数: {len(tension_curve)}")
                print(
                    f"      范围: {min(tension_curve):.2f} - {max(tension_curve):.2f}"
                )

        return True, result

    except Exception as e:
        print(f"\n❌ 全局审阅失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None


async def test_chapter_review():
    """测试章节审阅"""
    print("\n" + "=" * 60)
    print("🧪 测试章节审阅 (run_chapter_review)")
    print("=" * 60)

    # 单章内容
    content = """
第1集：穿越与第一道菜

主角李明在车祸中穿越到异世界，醒来发现自己在一个破旧的小餐馆里。他决定用现代烹饪技术做出第一道菜——红烧肉。这道菜香气四溢，吸引了路过的冒险者。

场景1：穿越
李明原本是一位顶级厨师，在现代都市拥有自己的米其林餐厅。一场意外的车祸让他失去了意识，当他醒来时，发现自己躺在了一个陌生的世界里。

场景2：发现餐馆
这是一间破旧的小餐馆，桌椅陈旧，厨房设备简陋。但李明看到了机会——这个世界的人从未尝过真正的美食。

场景3：第一道菜
李明决定用有限的食材制作红烧肉。他利用异世界的魔法火焰，结合现代的烹饪技巧，创造出了前所未有的美味。

场景4：吸引顾客
红烧肉的香气飘散出去，吸引了一支冒险者队伍。队长尝了一口后，眼睛都亮了。
"""

    print(f"\n📄 测试章节长度: {len(content)} 字符")
    print(f"   用户ID: {TEST_USER_ID}")
    print(f"   项目ID: {TEST_PROJECT_ID}")
    print(f"   章节ID: {TEST_CHAPTER_ID}")

    try:
        result = await run_chapter_review(
            user_id=TEST_USER_ID,
            project_id=TEST_PROJECT_ID,
            chapter_id=TEST_CHAPTER_ID,
            content=content,
            content_type="outline",
        )

        print(f"\n✅ 章节审阅成功!")
        print(f"\n📊 质量评分: {result.get('quality_score', 'N/A')}/100")
        print(f"   章节ID: {result.get('chapter_id', 'N/A')}")

        # 审阅报告
        report = result.get("review_report", {})
        if report:
            print(f"\n📋 章节审阅详情:")

            # 章节审阅结果（Editor Agent 输出）
            chapter_review = report.get("chapter_review", {})
            if chapter_review:
                print(f"   章节评分: {chapter_review.get('score', 'N/A')}/100")
                print(f"   状态: {chapter_review.get('status', 'N/A')}")

                comment = chapter_review.get("comment", "")
                if comment:
                    print(f"\n   📝 评语: {comment[:150]}...")

                issues = chapter_review.get("issues", [])
                if issues:
                    print(f"\n   ⚠️ 章节问题 ({len(issues)} 个):")
                    for i, issue in enumerate(issues[:3], 1):
                        print(
                            f"      {i}. [{issue.get('severity', 'N/A')}] {issue.get('description', '')[:60]}..."
                        )

            # 张力数据
            tension_data = report.get("tension_data", {})
            if tension_data:
                print(f"\n   📈 张力数据:")
                for key, value in tension_data.items():
                    print(f"      • {key}: {value}")

        return True, result

    except Exception as e:
        print(f"\n❌ 章节审阅失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None


async def main():
    """主测试函数"""
    print("\n" + "🧪" * 30)
    print("   Quality Control Graph - 端到端测试")
    print("🧪" * 30)

    results = []

    # 测试 1: 全局审阅
    success1, global_result = await test_global_review()
    results.append(("全局审阅", success1))

    # 测试 2: 章节审阅
    success2, chapter_result = await test_chapter_review()
    results.append(("章节审阅", success2))

    # 测试报告
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
        print("\n🎉 所有测试通过！质量控制系统工作正常。")
    else:
        print(f"\n⚠️ {total - passed} 项测试失败。")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
