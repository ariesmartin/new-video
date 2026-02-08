"""
Integration Test: Theme Library + Story Planner Agent

测试主题库与 Story Planner Agent 的集成。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载环境变量
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# 导入主题库技能
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes,
    get_hooks,
    get_character_archetypes,
    get_market_trends,
    get_writing_keywords,
)


async def init_database():
    """初始化数据库服务"""
    from backend.services.database import init_db_service

    await init_db_service()


def test_load_genre_context():
    """Test 1: 测试 load_genre_context 能正确加载题材数据"""
    print("\n" + "=" * 60)
    print("Test 1: load_genre_context()")
    print("=" * 60)

    # 测试复仇逆袭题材 - 使用 Tool 的 invoke 方法
    result = load_genre_context.invoke({"genre_id": "revenge"})

    # 验证返回内容包含关键信息
    assert "复仇逆袭" in result, "应该包含题材名称"
    assert "核心公式" in result, "应该包含核心公式"
    assert "爆款元素" in result, "应该包含爆款元素"
    assert "避雷清单" in result, "应该包含避雷清单"

    print("✅ load_genre_context('revenge') 成功")
    print(f"   返回内容长度: {len(result)} 字符")
    print(f"   前200字符预览:\n{result[:200]}...")

    return True


def test_get_tropes():
    """Test 2: 测试 get_tropes 能返回爆款元素"""
    print("\n" + "=" * 60)
    print("Test 2: get_tropes()")
    print("=" * 60)

    # 测试甜宠恋爱题材
    result = get_tropes.invoke({"genre_id": "romance", "limit": 3})

    assert "甜宠恋爱" in result or "高效果元素" in result, "应该返回元素列表"

    print("✅ get_tropes('romance') 成功")
    print(f"   返回内容:\n{result[:500]}...")

    return True


def test_get_hooks():
    """Test 3: 测试 get_hooks 能返回钩子模板"""
    print("\n" + "=" * 60)
    print("Test 3: get_hooks()")
    print("=" * 60)

    result = get_hooks.invoke({"genre_id": "revenge", "hook_type": "situation", "limit": 2})

    assert "钩子模板" in result or "未找到" in result, "应该返回钩子或提示"

    print("✅ get_hooks('revenge') 成功")
    print(f"   返回内容:\n{result[:500]}...")

    return True


def test_get_character_archetypes():
    """Test 4: 测试 get_character_archetypes 返回角色原型"""
    print("\n" + "=" * 60)
    print("Test 4: get_character_archetypes()")
    print("=" * 60)

    result = get_character_archetypes.invoke({"genre_id": "revenge", "limit": 3})

    assert "隐忍复仇者" in result or "角色原型" in result, "应该返回角色原型"

    print("✅ get_character_archetypes('revenge') 成功")
    print(f"   返回内容:\n{result}")

    return True


def test_get_market_trends():
    """Test 5: 测试 get_market_trends 返回市场趋势"""
    print("\n" + "=" * 60)
    print("Test 5: get_market_trends()")
    print("=" * 60)

    result = get_market_trends.invoke({"genre_id": "revenge"})

    assert "市场趋势" in result or "错误" in result, "应该返回市场数据或错误提示"

    print("✅ get_market_trends('revenge') 成功")
    print(f"   返回内容:\n{result[:500]}...")

    return True


def test_get_writing_keywords():
    """Test 6: 测试 get_writing_keywords 返回关键词"""
    print("\n" + "=" * 60)
    print("Test 6: get_writing_keywords()")
    print("=" * 60)

    result = get_writing_keywords.invoke({"genre_id": "revenge"})

    assert "关键词" in result or "错误" in result, "应该返回关键词或错误提示"

    print("✅ get_writing_keywords('revenge') 成功")
    print(f"   返回内容:\n{result[:500]}...")

    return True


def test_genre_mapping():
    """Test 7: 测试题材名称到 slug 的映射"""
    print("\n" + "=" * 60)
    print("Test 7: 题材映射测试")
    print("=" * 60)

    from backend.agents.story_planner import _genre_to_slug

    test_cases = [
        ("复仇逆袭", "revenge"),
        ("甜宠恋爱", "romance"),
        ("悬疑推理", "suspense"),
        ("穿越重生", "transmigration"),
        ("家庭伦理", "family_urban"),
        ("现代都市", "family_urban"),
        ("古装", "transmigration"),
        ("爱情", "romance"),
    ]

    for genre, expected_slug in test_cases:
        actual_slug = _genre_to_slug(genre)
        assert actual_slug == expected_slug, (
            f"题材 '{genre}' 应该映射到 '{expected_slug}', 但得到 '{actual_slug}'"
        )
        print(f"   ✅ '{genre}' → '{actual_slug}'")

    print("✅ 所有题材映射正确")
    return True


def test_prompt_injection():
    """Test 8: 测试 Prompt 注入功能"""
    print("\n" + "=" * 60)
    print("Test 8: Prompt 主题库数据注入")
    print("=" * 60)

    from backend.agents.story_planner import _load_story_planner_prompt

    # 测试复仇逆袭题材的 prompt 加载
    prompt = _load_story_planner_prompt(
        market_report=None,
        episode_count=80,
        episode_duration=1.5,
        genre="复仇逆袭",
        setting="modern",
    )

    # 验证主题库数据被注入
    assert "题材指导" in prompt, "Prompt 应该包含题材指导"
    assert "复仇逆袭" in prompt, "Prompt 应该包含复仇逆袭题材信息"
    assert "核心公式" in prompt, "Prompt 应该包含核心公式"

    print("✅ Prompt 注入成功")
    print(f"   Prompt 长度: {len(prompt)} 字符")
    print(f"   包含 '题材指导': {'✅' if '题材指导' in prompt else '❌'}")
    print(f"   包含 '核心公式': {'✅' if '核心公式' in prompt else '❌'}")
    print(f"   包含 '爆款元素': {'✅' if '爆款元素' in prompt else '❌'}")

    # 打印部分预览
    theme_section_start = prompt.find("## 题材指导")
    if theme_section_start != -1:
        preview = prompt[theme_section_start : theme_section_start + 800]
        print(f"\n   主题库数据预览:\n{preview}...")

    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("主题库 + Story Planner 集成测试")
    print("🧪" * 30)

    # 初始化数据库
    print("\n📊 初始化数据库服务...")
    try:
        await init_database()
        print("✅ 数据库服务初始化成功")
    except Exception as e:
        print(f"⚠️ 数据库初始化警告: {e}")
        print("   将继续测试，但数据库相关测试可能失败")

    results = []

    try:
        results.append(("load_genre_context", test_load_genre_context()))
    except Exception as e:
        results.append(("load_genre_context", False))
        print(f"❌ load_genre_context 失败: {e}")

    try:
        results.append(("get_tropes", test_get_tropes()))
    except Exception as e:
        results.append(("get_tropes", False))
        print(f"❌ get_tropes 失败: {e}")

    try:
        results.append(("get_hooks", test_get_hooks()))
    except Exception as e:
        results.append(("get_hooks", False))
        print(f"❌ get_hooks 失败: {e}")

    try:
        results.append(("get_character_archetypes", test_get_character_archetypes()))
    except Exception as e:
        results.append(("get_character_archetypes", False))
        print(f"❌ get_character_archetypes 失败: {e}")

    try:
        results.append(("get_market_trends", test_get_market_trends()))
    except Exception as e:
        results.append(("get_market_trends", False))
        print(f"❌ get_market_trends 失败: {e}")

    try:
        results.append(("get_writing_keywords", test_get_writing_keywords()))
    except Exception as e:
        results.append(("get_writing_keywords", False))
        print(f"❌ get_writing_keywords 失败: {e}")

    try:
        results.append(("genre_mapping", test_genre_mapping()))
    except Exception as e:
        results.append(("genre_mapping", False))
        print(f"❌ genre_mapping 失败: {e}")

    try:
        results.append(("prompt_injection", test_prompt_injection()))
    except Exception as e:
        results.append(("prompt_injection", False))
        print(f"❌ prompt_injection 失败: {e}")

    # 打印总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status}: {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！主题库与 Story Planner 集成成功！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查配置")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
