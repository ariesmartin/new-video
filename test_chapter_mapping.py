"""
测试章节映射计算算法
"""

import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.graph.workflows.skeleton_builder_graph import (
    parse_paywall_range,
    calculate_chapter_mapping,
)


def test_parse_paywall_range():
    """测试付费卡点范围解析"""
    print("=== 测试 parse_paywall_range ===")

    # 测试范围格式
    result = parse_paywall_range("10-12")
    assert result == [10, 11, 12], f"期望[10, 11, 12], 实际{result}"
    print("✅ 范围格式 '10-12' 解析正确")

    # 测试单集格式
    result = parse_paywall_range("12")
    assert result == [12], f"期望[12], 实际{result}"
    print("✅ 单集格式 '12' 解析正确")

    # 测试空值
    result = parse_paywall_range("")
    assert result == [12], f"期望默认值[12], 实际{result}"
    print("✅ 空值使用默认值[12]")

    print()


def test_calculate_chapter_mapping():
    """测试章节映射计算"""
    print("=== 测试 calculate_chapter_mapping ===")

    # 测试80集短剧
    result = calculate_chapter_mapping(80, [12])
    print(f"80集短剧 → {result['total_chapters']}章")
    print(f"付费卡点: Chapter {result['paywall_chapter']}")
    print(f"预计字数: {result['estimated_words']}字")
    print(f"改编比例: 1章≈{result['adaptation_ratio']}集")

    assert result["total_chapters"] > 50, "章节数应该>50"
    assert result["paywall_chapter"] > 0, "付费卡点章节应该>0"
    assert result["estimated_words"] > 500000, "预计字数应该>50万字"
    print("✅ 80集配置计算正确")

    # 验证章节连续性
    chapters = result["chapters"]
    for i, ch in enumerate(chapters):
        assert ch["chapter_num"] == i + 1, f"章节号错误: {ch['chapter_num']}"
        assert ch["word_count"] >= 6000, f"字数过低: {ch['word_count']}"
        assert ch["word_count"] <= 15000, f"字数过高: {ch['word_count']}"
    print(f"✅ 所有{len(chapters)}章验证通过")

    # 验证付费卡点章节
    paywall_ch = chapters[result["paywall_chapter"] - 1]
    assert paywall_ch["is_paywall"] == True, "付费卡点章节标记错误"
    assert paywall_ch["word_count"] >= 10000, "付费卡点章节字数应该>=10000"
    print(f"✅ 付费卡点章节(Chapter {result['paywall_chapter']})验证通过")

    print()

    # 测试60集短剧
    result = calculate_chapter_mapping(60, [10])
    print(f"60集短剧 → {result['total_chapters']}章")
    assert 40 <= result["total_chapters"] <= 50, "60集应该生成40-50章"
    print("✅ 60集配置计算正确")

    print()

    # 测试40集短剧
    result = calculate_chapter_mapping(40, [8])
    print(f"40集短剧 → {result['total_chapters']}章")
    assert 25 <= result["total_chapters"] <= 35, "40集应该生成25-35章"
    print("✅ 40集配置计算正确")

    print()


if __name__ == "__main__":
    try:
        test_parse_paywall_range()
        test_calculate_chapter_mapping()
        print("=" * 50)
        print("🎉 所有测试通过!")
        print("=" * 50)
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
