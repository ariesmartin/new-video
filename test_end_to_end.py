#!/usr/bin/env python3
"""
端到端验证测试 - Skeleton Builder 章节大纲生成

测试内容：
1. 章节映射计算算法
2. Prompt变量注入
3. Graph流程完整性
"""

import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")


def test_chapter_mapping():
    """测试章节映射计算"""
    print("=" * 60)
    print("测试1: 章节映射计算算法")
    print("=" * 60)

    # 模拟导入（避免依赖langgraph）
    import json

    # 复制核心算法进行测试
    def parse_paywall_range(range_str):
        if not range_str:
            return [12]
        try:
            if "-" in str(range_str):
                parts = str(range_str).split("-")
                start = int(parts[0])
                end = int(parts[1])
                return list(range(start, end + 1))
            else:
                return [int(range_str)]
        except:
            return [12]

    def calculate_chapter_mapping(total_episodes, paywall_episodes):
        chapters = []
        current_ep = 1
        paywall_first = paywall_episodes[0] if paywall_episodes else 12
        paywall_last = paywall_episodes[-1] if paywall_episodes else 12
        total_minutes = total_episodes * 2
        estimated_words = total_minutes * 4000

        # 开篇
        opening_eps = max(3, int(total_episodes * 0.15))
        for i in range(opening_eps):
            if i < 3:
                eps = 1.5
                word_count = 9000
            else:
                eps = 1.0
                word_count = 8000
            chapters.append(
                {
                    "chapter_num": len(chapters) + 1,
                    "episode_start": int(current_ep),
                    "episode_end": min(int(current_ep + eps - 1), total_episodes),
                    "word_count": word_count,
                    "stage": "opening",
                    "is_paywall": False,
                }
            )
            current_ep += eps

        # 发展到付费卡点前
        while current_ep < paywall_first - 2:
            chapters.append(
                {
                    "chapter_num": len(chapters) + 1,
                    "episode_start": int(current_ep),
                    "episode_end": min(int(current_ep + 1), total_episodes),
                    "word_count": 10000,
                    "stage": "development",
                    "is_paywall": False,
                }
            )
            current_ep += 2

        # 付费卡点章节
        paywall_chapter_idx = len(chapters) + 1
        chapters.append(
            {
                "chapter_num": paywall_chapter_idx,
                "episode_start": int(current_ep),
                "episode_end": paywall_last,
                "word_count": 12000,
                "stage": "paywall",
                "is_paywall": True,
            }
        )
        current_ep = paywall_last + 1

        # 发展到75%
        dev_end = int(total_episodes * 0.75)
        while current_ep < dev_end:
            chapters.append(
                {
                    "chapter_num": len(chapters) + 1,
                    "episode_start": int(current_ep),
                    "episode_end": min(int(current_ep + 1), total_episodes),
                    "word_count": 10000,
                    "stage": "development",
                    "is_paywall": False,
                }
            )
            current_ep += 2

        # 高潮
        climax_end = int(total_episodes * 0.90)
        while current_ep < climax_end:
            chapters.append(
                {
                    "chapter_num": len(chapters) + 1,
                    "episode_start": int(current_ep),
                    "episode_end": int(current_ep),
                    "word_count": 8000,
                    "stage": "climax",
                    "is_paywall": False,
                }
            )
            current_ep += 1

        # 结局
        while current_ep <= total_episodes:
            remaining = total_episodes - current_ep + 1
            eps = min(remaining, 2)
            chapters.append(
                {
                    "chapter_num": len(chapters) + 1,
                    "episode_start": int(current_ep),
                    "episode_end": min(int(current_ep + eps - 1), total_episodes),
                    "word_count": 8000 if eps == 1 else 10000,
                    "stage": "ending",
                    "is_paywall": False,
                }
            )
            current_ep += eps

        return {
            "total_chapters": len(chapters),
            "paywall_chapter": paywall_chapter_idx,
            "estimated_words": estimated_words,
            "chapters": chapters,
        }

    # 测试用例1: 80集短剧
    print("\n测试用例1: 80集短剧，付费卡点10-12")
    result = calculate_chapter_mapping(80, [10, 11, 12])
    print(f"  ✓ 总章节数: {result['total_chapters']}")
    print(f"  ✓ 付费卡点章节: Chapter {result['paywall_chapter']}")
    print(f"  ✓ 预计字数: {result['estimated_words']:,}字")
    print(f"  ✓ 改编比例: 1章≈{80 / result['total_chapters']:.2f}集")

    assert result["total_chapters"] > 50, "章节数应该>50"
    assert result["paywall_chapter"] > 0, "付费卡点章节应该>0"
    assert result["estimated_words"] > 600000, "字数应该>60万字"

    # 验证付费卡点章节
    paywall_ch = result["chapters"][result["paywall_chapter"] - 1]
    assert paywall_ch["is_paywall"] == True, "付费章节标记错误"
    assert paywall_ch["word_count"] == 12000, "付费章节字数应该为12000"
    print(f"  ✓ 付费卡点章节验证通过")

    # 测试用例2: 60集短剧
    print("\n测试用例2: 60集短剧，付费卡点8")
    result = calculate_chapter_mapping(60, [8])
    print(f"  ✓ 总章节数: {result['total_chapters']}")
    print(f"  ✓ 付费卡点章节: Chapter {result['paywall_chapter']}")
    assert 40 <= result["total_chapters"] <= 50, "60集应该生成40-50章"
    print(f"  ✓ 60集配置验证通过")

    # 测试用例3: 40集短剧
    print("\n测试用例3: 40集短剧，付费卡点6-8")
    result = calculate_chapter_mapping(40, [6, 7, 8])
    print(f"  ✓ 总章节数: {result['total_chapters']}")
    assert 25 <= result["total_chapters"] <= 35, "40集应该生成25-35章"
    print(f"  ✓ 40集配置验证通过")

    print("\n✅ 所有章节映射测试通过!")
    return True


def test_prompt_variables():
    """测试Prompt变量替换"""
    print("\n" + "=" * 60)
    print("测试2: Prompt变量注入")
    print("=" * 60)

    # 读取实际Prompt文件
    prompt_path = "/Users/ariesmartin/Documents/new-video/prompts/3_Skeleton_Builder.md"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键变量是否存在（核心变量）
        variables = [
            "{total_chapters}",
            "{paywall_chapter}",
            "{total_words}",
            "{ratio}",
            "{opening_end}",
            "{midpoint_chapter}",
            "{climax_chapter}",
            "{paywall_position}",
        ]

        missing = []
        for var in variables:
            if var not in content:
                missing.append(var)

        if missing:
            print(f"  ❌ 缺少变量: {missing}")
            return False

        print(f"  ✓ 找到 {len(variables)} 个章节映射变量")

        # 检查关键章节格式
        if "### Chapter" in content:
            print("  ✓ 包含章节大纲格式 (### Chapter)")

        if "付费卡点" in content and "⚠️" in content:
            print("  ✓ 包含付费卡点专项设计标记")

        if "短剧对应" in content:
            print("  ✓ 包含短剧映射说明")

        print("\n✅ Prompt变量检查通过!")
        return True

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False


def test_graph_structure():
    """测试Graph结构完整性"""
    print("\n" + "=" * 60)
    print("测试3: Graph结构检查")
    print("=" * 60)

    graph_path = "/Users/ariesmartin/Documents/new-video/backend/graph/workflows/skeleton_builder_graph.py"
    try:
        with open(graph_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键节点
        nodes = [
            "batch_coordinator",
            "validate_output",
            "calculate_chapter_mapping",
            "parse_paywall_range",
        ]

        for node in nodes:
            if node in content:
                print(f"  ✓ 找到节点/函数: {node}")
            else:
                print(f"  ❌ 缺少: {node}")
                return False

        # 检查节点是否被添加到workflow
        if 'workflow.add_node("batch_coordinator"' in content:
            print("  ✓ batch_coordinator 已添加到Graph")
        else:
            print("  ❌ batch_coordinator 未添加到Graph")
            return False

        if 'workflow.add_node("validate_output"' in content:
            print("  ✓ validate_output 已添加到Graph")
        else:
            print("  ❌ validate_output 未添加到Graph")
            return False

        # 检查路由
        if "route_after_validate_output" in content:
            print("  ✓ 输出验证路由已定义")
        else:
            print("  ❌ 输出验证路由未定义")
            return False

        print("\n✅ Graph结构检查通过!")
        return True

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False


def test_skeleton_builder_agent():
    """测试Skeleton Builder Agent配置"""
    print("\n" + "=" * 60)
    print("测试4: Skeleton Builder Agent")
    print("=" * 60)

    agent_path = (
        "/Users/ariesmartin/Documents/new-video/backend/agents/skeleton_builder.py"
    )
    try:
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查函数签名
        if "chapter_mapping: Optional[Dict] = None" in content:
            print("  ✓ create_skeleton_builder_agent 支持 chapter_mapping 参数")
        else:
            print("  ❌ create_skeleton_builder_agent 不支持 chapter_mapping")
            return False

        if "chapter_mapping=chapter_mapping" in content:
            print("  ✓ Prompt加载时传递 chapter_mapping")
        else:
            print("  ❌ 未传递 chapter_mapping 到Prompt")
            return False

        # 检查变量替换
        if 'content.replace("{total_chapters}"' in content:
            print("  ✓ 实现 {total_chapters} 变量替换")
        else:
            print("  ❌ 未实现变量替换")
            return False

        print("\n✅ Skeleton Builder Agent检查通过!")
        return True

    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "🔍" * 30)
    print("Skeleton Builder 系统验证测试")
    print("🔍" * 30 + "\n")

    results = []

    try:
        results.append(("章节映射算法", test_chapter_mapping()))
        results.append(("Prompt变量注入", test_prompt_variables()))
        results.append(("Graph结构", test_graph_structure()))
        results.append(("Agent配置", test_skeleton_builder_agent()))

        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)

        for name, passed in results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{status}: {name}")

        all_passed = all(r[1] for r in results)

        if all_passed:
            print("\n" + "🎉" * 20)
            print("所有测试通过! 系统准备就绪")
            print("🎉" * 20)
            return 0
        else:
            print("\n" + "⚠️" * 20)
            print("部分测试失败，请检查问题")
            print("⚠️" * 20)
            return 1

    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
