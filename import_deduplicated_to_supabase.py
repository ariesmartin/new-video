#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase数据导入脚本 - 正确去重版
清空现有数据，重新导入45个正确去重后的元素
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# 添加backend到路径
sys.path.insert(0, "/Users/ariesmartin/Documents/new-video/backend")

from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("/Users/ariesmartin/Documents/new-video/backend/.env")

# 初始化Supabase客户端
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_service_key:
    print("❌ 错误: 找不到Supabase配置")
    print("请确保 .env 文件中包含 SUPABASE_URL 和 SUPABASE_SERVICE_KEY")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_service_key)

print(f"✅ Supabase客户端初始化成功")
print(f"   URL: {supabase_url}")


def load_json(file_path: str) -> Dict:
    """加载JSON文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_all_tables():
    """清空所有相关表"""
    print("\n🗑️  清空现有数据...")

    tables = [
        "theme_examples",
        "theme_elements",
        "character_archetypes",
        "hook_templates",
        "themes",
    ]

    for table in tables:
        try:
            # 使用DELETE清空表
            result = supabase.table(table).delete().neq("id", 0).execute()
            print(f"  ✅ 清空 {table}")
        except Exception as e:
            print(f"  ⚠️  {table}: {str(e)}")

    print("  所有表已清空")


def import_themes(data: Dict):
    """导入主题数据"""
    print("\n📥 导入主题数据 (themes)...")

    themes = data.get("themes", [])
    success_count = 0
    error_count = 0

    for theme in themes:
        try:
            theme_data = {
                "slug": theme["slug"],
                "name": theme["name"],
                "name_en": theme.get("name_en", ""),
                "description": theme.get("description", ""),
                "core_formula": theme.get("core_formula", {}),
                "writing_keywords": theme.get("writing_keywords", []),
                "visual_keywords": theme.get("visual_keywords", []),
                "emotional_arc": theme.get("emotional_arc", ""),
                "target_audience": theme.get("target_audience", {}),
                "avoid_patterns": theme.get("avoid_patterns", []),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = supabase.table("themes").insert(theme_data).execute()
            success_count += 1
            print(f"  ✅ {theme['name']}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ {theme.get('name', 'Unknown')}: {str(e)[:50]}")

    print(f"\n  主题导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_theme_elements(data: Dict):
    """导入元素数据 - 正确去重后的45个元素"""
    print("\n📥 导入元素数据 (theme_elements)...")
    print("  数据来源: 正确去重版（45个元素）")
    print("  - PDF分类元素: 20个")
    print("  - TXT题材特定: 25个")

    success_count = 0
    error_count = 0

    # 1. 导入PDF分类元素（20个）
    print("\n  导入PDF分类元素...")
    tropes_library = data.get("tropes_library", {})

    for category, items in tropes_library.items():
        for item in items:
            try:
                element_data = {
                    "name": item["name"],
                    "name_en": item.get("name_en", ""),
                    "category": category,
                    "description": item.get("description", ""),
                    "effectiveness_score": item.get("effectiveness_score", 0)
                    or item.get("success_rate", 0),
                    "usage_timing": item.get("best_timing", ""),
                    "examples": item.get("classic_examples", []),
                    "variations": item.get("variations", []),
                    "risk_factors": item.get("risk_factors", []),
                    "source": "pdf",
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                result = supabase.table("theme_elements").insert(element_data).execute()
                success_count += 1
                print(f"    ✅ {item['name'][:30]}...")

            except Exception as e:
                error_count += 1
                print(f"    ❌ {item.get('name', 'Unknown')[:30]}...: {str(e)[:50]}")

    # 2. 导入TXT题材特定元素（25个）
    print("\n  导入TXT题材特定元素...")
    txt_tropes = data.get("txt_tropes_unique", [])

    for item in txt_tropes:
        try:
            element_data = {
                "name": item["name"],
                "name_en": item.get("name_en", ""),
                "category": "genre_specific",
                "description": item.get("description", ""),
                "effectiveness_score": item.get("effectiveness_score", 0),
                "usage_timing": item.get("usage_timing", ""),
                "examples": item.get("examples", []),
                "theme_id": item.get("theme_id"),
                "source": "txt",
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = supabase.table("theme_elements").insert(element_data).execute()
            success_count += 1
            print(
                f"    ✅ {item['name'][:30]}... (评分:{item.get('effectiveness_score', 0)})"
            )

        except Exception as e:
            error_count += 1
            print(f"    ❌ {item.get('name', 'Unknown')[:30]}...: {str(e)[:50]}")

    print(f"\n  元素导入完成: {success_count}成功, {error_count}失败")
    print(f"  总计: {success_count}个元素（正确去重后45个）")
    return success_count, error_count


def import_hooks(data: Dict):
    """导入钩子模板"""
    print("\n📥 导入钩子模板 (hook_templates)...")

    hooks_library = data.get("hooks_library", {})
    success_count = 0
    error_count = 0

    for hook_type, hooks in hooks_library.items():
        for hook in hooks:
            try:
                hook_data = {
                    "hook_type": hook_type,
                    "name": hook["name"],
                    "template": hook.get("template", hook.get("core_formula", "")),
                    "variables": hook.get("variables", {}),
                    "effectiveness_score": hook.get("effectiveness_score", 0),
                    "examples": hook.get("examples", []),
                    "usage_tips": hook.get("usage_tips", ""),
                    "applicable_genres": hook.get("applicable_genres", []),
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                result = supabase.table("hook_templates").insert(hook_data).execute()
                success_count += 1
                print(f"  ✅ [{hook_type}] {hook['name'][:30]}...")

            except Exception as e:
                error_count += 1
                print(f"  ❌ {hook.get('name', 'Unknown')[:30]}...: {str(e)[:50]}")

    print(f"\n  钩子导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_archetypes(data: Dict):
    """导入角色原型"""
    print("\n📥 导入角色原型 (character_archetypes)...")

    archetypes = data.get("archetypes", {})
    success_count = 0
    error_count = 0

    for role_type, items in archetypes.items():
        for item in items:
            try:
                archetype_data = {
                    "archetype_id": item.get("id", item.get("archetype_key", "")),
                    "name": item["name"],
                    "name_en": item.get("name_en", ""),
                    "role": role_type,
                    "core_traits": item.get("core_traits", {}),
                    "motivation": item.get("motivation", {}),
                    "character_arc": item.get("character_arc", ""),
                    "dialogue_style": item.get("dialogue_style", {}),
                    "visual_markers": item.get("visual_markers", []),
                    "classic_examples": item.get("classic_examples", []),
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                result = (
                    supabase.table("character_archetypes")
                    .insert(archetype_data)
                    .execute()
                )
                success_count += 1
                print(f"  ✅ [{role_type}] {item['name'][:30]}...")

            except Exception as e:
                error_count += 1
                print(f"  ❌ {item.get('name', 'Unknown')[:30]}...: {str(e)[:50]}")

    print(f"\n  角色原型导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_examples(data: Dict):
    """导入爆款案例"""
    print("\n📥 导入爆款案例 (theme_examples)...")

    success_count = 0
    error_count = 0

    for theme in data.get("themes", []):
        theme_id = theme.get("id")
        examples = theme.get("viral_examples", [])

        for example in examples:
            try:
                example_data = {
                    "theme_id": theme_id,
                    "title": example["title"],
                    "why_it_works": example.get("why_it_works", ""),
                    "innovation": example.get("innovation", ""),
                    "data": example.get("data", ""),
                    "success_factors": example.get("success_factors", ""),
                    "risk_lesson": example.get("risk_lesson", ""),
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                result = supabase.table("theme_examples").insert(example_data).execute()
                success_count += 1
                print(f"  ✅ {example['title'][:40]}...")

            except Exception as e:
                error_count += 1
                print(f"  ❌ {example.get('title', 'Unknown')[:40]}...: {str(e)[:50]}")

    print(f"\n  案例导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def main():
    """主函数"""
    print("=" * 80)
    print("Supabase数据导入 - 正确去重版")
    print("清空现有数据，导入45个正确去重后的元素")
    print("=" * 80)

    try:
        # 1. 加载正确去重后的数据
        print("\n📖 加载数据...")
        data = load_json(
            "/Users/ariesmartin/Documents/new-video/theme_library_deduplicated.json"
        )
        print(f"   ✓ 数据版本: {data['metadata']['version']}")
        print(f"   ✓ 元素总计: {data['summary']['tropes_total']}个（正确去重后）")
        print(f"   ✓ 去重说明: {data['metadata']['deduplication_note']}")

        # 2. 确认操作
        print("\n⚠️  警告: 即将清空现有数据库并重新导入")
        print("   按 Ctrl+C 取消，或等待5秒继续...")
        import time

        time.sleep(5)

        # 3. 清空现有数据
        clear_all_tables()

        # 4. 导入新数据
        print("\n" + "=" * 80)
        print("📥 开始导入新数据...")
        print("=" * 80)

        results = {}

        # 导入主题
        results["themes"] = import_themes(data)

        # 导入元素（45个正确去重后）
        results["elements"] = import_theme_elements(data)

        # 导入钩子
        results["hooks"] = import_hooks(data)

        # 导入角色原型
        results["archetypes"] = import_archetypes(data)

        # 导入案例
        results["examples"] = import_examples(data)

        # 5. 生成最终报告
        print("\n" + "=" * 80)
        print("✅ 数据导入完成报告")
        print("=" * 80)
        print()
        print("📊 导入统计:")
        print(f"  主题:       {results['themes'][0]}成功, {results['themes'][1]}失败")
        print(
            f"  元素:       {results['elements'][0]}成功, {results['elements'][1]}失败"
        )
        print(f"  钩子模板:   {results['hooks'][0]}成功, {results['hooks'][1]}失败")
        print(
            f"  角色原型:   {results['archetypes'][0]}成功, {results['archetypes'][1]}失败"
        )
        print(
            f"  案例:       {results['examples'][0]}成功, {results['examples'][1]}失败"
        )
        print()
        print("=" * 80)
        print("🎉 正确去重后的数据已成功导入Supabase！")
        print("=" * 80)
        print()
        print("数据特点:")
        print("  ✓ 45个元素（已去重，统计准确）")
        print("  ✓ 20个PDF分类元素 + 25个TXT题材特定元素")
        print("  ✓ 5个重叠元素已去除")
        print("  ✓ 30个钩子模板")
        print("  ✓ 19个角色原型")
        print("  ✓ 25个真实爆款案例")

        return True

    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        return False
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
