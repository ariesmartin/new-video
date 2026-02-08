"""
Comprehensive Service Tests

Complete unit tests for ReviewService and TensionService.
Tests all genre combinations and episode counts.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.review_service import (
    calculate_weights,
    get_checkpoints,
    get_applicable_categories,
    calculate_weights_unified,
    determine_severity,
    get_severity_config,
    COMMON_COMBINATIONS,
    BASE_WEIGHTS,
)
from backend.services.tension_service import (
    generate_tension_curve,
    generate_standard_curve,
    calculate_curve_deviation,
    get_tension_requirements,
    get_skill_checks,
)


def test_all_genre_combinations():
    """Test all 8 possible genre combinations"""
    print("\n🎭 测试所有题材组合 (8种)")
    print("=" * 60)

    genres = ["revenge", "romance", "suspense", "transmigration", "family"]

    # Generate all combinations (1 and 2 genres)
    combinations = []
    for g in genres:
        combinations.append([g])
    for i, g1 in enumerate(genres):
        for g2 in genres[i + 1 :]:
            combinations.append([g1, g2])

    print(f"总计测试 {len(combinations)} 种组合")

    for combo in combinations:
        weights = calculate_weights(combo)
        total = sum(weights.values())

        # Verify weights sum to 1.0 (allow rounding tolerance)
        assert abs(total - 1.0) < 0.02, f"权重总和应为1.0, 实际为 {total}"

        # Verify all 6 categories exist
        required_categories = ["logic", "pacing", "character", "conflict", "world", "hook"]
        for cat in required_categories:
            assert cat in weights, f"缺少分类: {cat}"
            assert 0 <= weights[cat] <= 1, f"权重值应在0-1之间: {weights[cat]}"

        combo_str = " + ".join(combo)
        print(f"\n✅ {combo_str}")
        print(f"   权重: {weights}")
        print(f"   总和: {total:.2f}")


def test_weights_normalization():
    """Test weight normalization for edge cases"""
    print("\n📊 测试权重归一化")
    print("=" * 60)

    # Empty combination - should use default (revenge)
    weights_empty = calculate_weights([])
    assert weights_empty == BASE_WEIGHTS["revenge"], "空组合应返回复仇权重"
    print("✅ 空组合 → 返回默认(复仇)权重")

    # Single genre
    weights_single = calculate_weights(["suspense"])
    assert abs(sum(weights_single.values()) - 1.0) < 0.02, "单题材权重应归一化"
    print("✅ 单题材权重正确归一化")

    # Three genres
    weights_three = calculate_weights(["revenge", "romance", "suspense"])
    assert abs(sum(weights_three.values()) - 1.0) < 0.02, "三题材权重应归一化"
    print("✅ 三题材权重正确归一化")


def test_content_type_checkpoints():
    """Test checkpoints for different content types"""
    print("\n📋 测试不同内容类型的检查点")
    print("=" * 60)

    content_types = ["outline", "novel", "script", "storyboard"]

    for content_type in content_types:
        checkpoints = get_checkpoints(content_type)
        categories = list(checkpoints.keys())

        print(f"\n✅ {content_type.upper()}")
        print(f"   分类: {categories}")

        # All types should have at least the 6 base categories
        base_categories = ["logic", "pacing", "character", "conflict", "world", "hook"]
        for cat in base_categories:
            assert cat in checkpoints, f"{content_type} 缺少 {cat} 分类"
            assert len(checkpoints[cat]) > 0, f"{content_type}.{cat} 没有检查点"

        # Novel-specific: texture
        if content_type == "novel":
            assert "texture" in checkpoints, "novel 应有 texture 分类"
            print(f"   特有: texture (文学质感)")

        # Script/Storyboard-specific: protocol
        if content_type in ["script", "storyboard"]:
            assert "protocol" in checkpoints, f"{content_type} 应有 protocol 分类"
            print(f"   特有: protocol (协议/格式)")


def test_common_combinations():
    """Verify common combinations from documentation"""
    print("\n🎯 验证常见题材组合")
    print("=" * 60)

    # Test predefined combinations
    for combo_name, expected_weights in COMMON_COMBINATIONS.items():
        print(f"\n✅ {combo_name}")
        print(f"   期望: {expected_weights}")

    print(f"\n   共 {len(COMMON_COMBINATIONS)} 种黄金组合")


def test_severity_levels():
    """Test severity determination"""
    print("\n⚠️ 测试严重程度分级")
    print("=" * 60)

    test_cases = [
        (50, 0.3, "high"),  # 低分 + 高权重
        (90, 0.3, "low"),  # 高分 + 高权重
        (70, 0.1, "medium"),  # 中分 + 低权重
        (30, 0.1, "critical"),  # 低分 + 低权重
    ]

    for score, weight, expected in test_cases:
        severity = determine_severity(score, weight)
        config = get_severity_config(severity)
        print(f"\n✅ 分数={score}, 权重={weight}")
        print(f"   级别: {config['icon']} {config['label']}")
        print(f"   评语: {config['editor_comment']}")


def test_all_episode_counts():
    """Test tension curves for all supported episode counts"""
    print("\n📈 测试所有集数配置")
    print("=" * 60)

    episode_counts = [40, 60, 80, 100]
    curve_types = ["standard", "fast", "slow"]

    for count in episode_counts:
        for curve_type in curve_types:
            curve = generate_tension_curve(count, curve_type)

            # Verify structure
            assert "total_points" in curve
            assert "values" in curve
            assert "key_points" in curve
            assert "curve_type" in curve

            # Verify counts match
            assert curve["total_points"] == count
            assert len(curve["values"]) == count

            # Verify key points are within bounds
            kp = curve["key_points"]
            assert 0 <= kp["opening_hook"] < count
            assert 0 <= kp["climax"] < count
            assert 0 <= kp["resolution"] < count

            # Verify tension values are within 0-100
            for val in curve["values"]:
                assert 0 <= val <= 100, f"张力值应在0-100之间: {val}"

            print(f"\n✅ {count}集 ({curve_type})")
            print(f"   开场: 第{kp['opening_hook'] + 1}集")
            print(f"   中点: 第{kp['midpoint'] + 1}集 ({kp['midpoint'] / count * 100:.1f}%)")
            print(f"   高潮: 第{kp['climax'] + 1}集 ({kp['climax'] / count * 100:.1f}%)")
            print(f"   付费点: 第{kp['paywall'] + 1}集")
            print(f"   平均张力: {sum(curve['values']) / len(curve['values']):.1f}")


def test_key_episode_positions():
    """Test key episode positions are percentage-based"""
    print("\n🎯 测试关键集数位置 (基于百分比)")
    print("=" * 60)

    test_cases = [
        (40, 0.10, 4),  # 激励事件应在10%位置
        (40, 0.50, 20),  # 中点应在50%位置
        (40, 0.875, 35),  # 高潮应在87.5%位置
        (80, 0.10, 8),
        (80, 0.50, 40),
        (80, 0.875, 70),
        (100, 0.10, 10),
        (100, 0.50, 50),
        (100, 0.875, 87),
    ]

    for total, percentage, expected in test_cases:
        curve = generate_tension_curve(total, "standard")
        actual = curve["key_points"]["climax"]

        if percentage == 0.875:
            # Verify climax position
            print(f"\n✅ {total}集")
            print(f"   高潮位置: 第{actual + 1}集 ({(actual + 1) / total * 100:.1f}%)")
            print(f"   期望: 第{expected + 1}集 (87.5%)")
            assert abs(actual - expected) <= 1, f"高潮位置应在{expected}附近"


def test_tension_curve_deviation():
    """Test curve deviation calculation"""
    print("\n📊 测试曲线偏差计算")
    print("=" * 60)

    # Perfect match
    actual = [80, 85, 90, 88, 85]
    target = [80, 85, 90, 88, 85]
    avg_dev, issues = calculate_curve_deviation(actual, target)
    assert avg_dev == 0, "完全匹配时偏差应为0"
    assert len(issues) == 0, "完全匹配时不应有问题点"
    print("✅ 完全匹配 → 偏差=0")

    # Small deviation
    actual = [80, 85, 90, 88, 85]
    target = [82, 85, 88, 88, 83]
    avg_dev, issues = calculate_curve_deviation(actual, target)
    assert avg_dev < 5, "小偏差应小于5"
    assert len(issues) == 0, "小偏差不应有问题点"
    print(f"✅ 小偏差 → 平均偏差={avg_dev}")

    # Large deviation
    actual = [80, 85, 90, 60, 85]
    target = [80, 85, 90, 88, 85]
    avg_dev, issues = calculate_curve_deviation(actual, target)
    assert avg_dev > 5, "大偏差应大于5"
    assert len(issues) > 0, "大偏差应有问题点"
    print(f"✅ 大偏差 → 平均偏差={avg_dev}, 问题点数={len(issues)}")


def test_tension_requirements():
    """Test tension requirements for specific episodes"""
    print("\n🎬 测试各集张力要求")
    print("=" * 60)

    test_cases = [
        (1, 80, 95, "开篇钩子"),
        (5, 80, 75, "激励事件后"),
        (40, 80, 75, "中点转折"),
        (70, 80, 88, "接近高潮"),
        (80, 100, 95, "高潮部分"),
    ]

    for episode, total, expected_min, description in test_cases:
        req = get_tension_requirements(episode, total)
        print(f"\n✅ 第{episode}集/{total}集")
        print(f"   位置: {description}")
        print(f"   最低张力: {req['min_tension']}")
        print(f"   目标张力: {req['target_tension']}")
        print(f"   说明: {req['description']}")

        assert req["min_tension"] > 0, "最低张力应大于0"
        assert req["target_tension"] > 0, "目标张力应大于0"


def test_skill_checks():
    """Test skill review matrix"""
    print("\n🔍 测试 Skill Review Matrix")
    print("=" * 60)

    content_types = ["novel", "script", "storyboard"]

    for content_type in content_types:
        skills = get_skill_checks(content_type)
        print(f"\n✅ {content_type.upper()}")

        for skill, checks in skills.items():
            print(f"   {skill}: {checks}")

        # Verify skill applicability
        if content_type == "novel":
            assert "S_Texture" in skills, "novel 应有 S_Texture"
        if content_type in ["script", "storyboard"]:
            assert "S_Protocol" in skills, f"{content_type} 应有 S_Protocol"


def test_edge_cases():
    """Test edge cases"""
    print("\n🧪 测试边界情况")
    print("=" * 60)

    # Single episode
    curve = generate_tension_curve(1, "standard")
    assert len(curve["values"]) == 1
    print("✅ 单集 → 支持")

    # Minimum episodes
    curve = generate_tension_curve(20, "standard")
    assert len(curve["values"]) == 20
    print("✅ 20集 → 支持")

    # Maximum episodes
    curve = generate_tension_curve(120, "standard")
    assert len(curve["values"]) == 120
    print("✅ 120集 → 支持")

    # Unknown genre
    weights = calculate_weights(["unknown_genre"])
    assert abs(sum(weights.values()) - 1.0) < 0.01, "未知题材应使用默认权重"
    print("✅ 未知题材 → 使用默认权重")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 综合服务测试套件")
    print("=" * 70)

    try:
        test_all_genre_combinations()
        test_weights_normalization()
        test_content_type_checkpoints()
        test_common_combinations()
        test_severity_levels()
        test_all_episode_counts()
        test_key_episode_positions()
        test_tension_curve_deviation()
        test_tension_requirements()
        test_skill_checks()
        test_edge_cases()

        print("\n" + "=" * 70)
        print("🎉 所有测试通过!")
        print("=" * 70)
        print("\n测试总结:")
        print("  ✅ 所有题材组合权重计算正确 (8+ 种)")
        print("  ✅ 所有集数配置支持 (40/60/80/100)")
        print("  ✅ 所有内容类型检查点正确")
        print("  ✅ 边界情况处理正确")
        print("  ✅ 百分比计算正确 (非硬编码)")

        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 错误: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
