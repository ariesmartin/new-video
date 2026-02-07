#!/usr/bin/env python3
"""
清空知识库表并重新导入真实数据
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video/backend")

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("/Users/ariesmartin/Documents/new-video/backend/.env")

supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_service_key:
    print("❌ 错误: 找不到Supabase配置")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_service_key)

print(f"✅ Supabase客户端初始化成功\n")


def load_json(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_tables():
    """清空所有知识库表"""
    print("🗑️  清空现有数据...")

    tables = [
        "theme_elements",
        "theme_examples",
        "hook_templates",
        "market_insights",
        "themes",
    ]

    for table in tables:
        try:
            # 使用delete().neq('id', '') 删除所有记录
            result = supabase.table(table).delete().neq("id", "").execute()
            print(f"  ✅ {table}: 已清空")
        except Exception as e:
            print(f"  ⚠️  {table}: {str(e)[:60]}")


def import_themes_v2():
    """导入题材数据（v2版本）"""
    print("\n📥 导入题材数据 (themes v2)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_themes_v2.json"
    )
    themes = data.get("themes", [])

    success = 0
    for theme in themes:
        try:
            theme_data = {
                "slug": theme["slug"],
                "name": theme["name"],
                "name_en": theme["name_en"],
                "category": theme["category"],
                "description": theme["description"],
                "summary": theme.get("summary", ""),
                "core_formula": json.dumps(theme.get("core_formula", {})),
                "keywords": json.dumps(theme.get("keywords", {})),
                "audience_analysis": json.dumps(theme.get("audience_analysis", {})),
                "market_score": theme.get("market_score", 0),
                "success_rate": theme.get("success_rate", 0),
                "status": "active",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            supabase.table("themes").upsert(theme_data).execute()
            success += 1
            print(f"  ✅ {theme['name']}")
        except Exception as e:
            print(f"  ❌ {theme.get('name', 'Unknown')}: {str(e)[:60]}")

    print(f"\n  完成: {success}/{len(themes)}")
    return success


def import_elements_v2():
    """导入元素数据（v2版本）"""
    print("\n📥 导入爆款元素 (theme_elements v2)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_elements_v2.json"
    )
    elements = data.get("theme_elements", [])

    # 获取主题ID映射
    themes_result = supabase.table("themes").select("id,slug").execute()
    theme_id_map = {t["slug"]: t["id"] for t in themes_result.data}

    success = 0
    for element in elements:
        try:
            theme_slug = element.get("genre_slug")
            theme_id = theme_id_map.get(theme_slug)

            if not theme_id:
                continue

            element_data = {
                "theme_id": theme_id,
                "element_type": element.get("element_type", "trope"),
                "name": element["name"],
                "description": element.get("description", ""),
                "effectiveness_score": element.get("effectiveness_score", 0),
                "weight": element.get("weight", 1.0),
                "usage_guidance": json.dumps(element.get("usage_guidance", {})),
                "emotional_impact": json.dumps(element.get("emotional_impact", {})),
                "classic_examples": json.dumps(element.get("classic_examples", [])),
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            supabase.table("theme_elements").upsert(element_data).execute()
            success += 1
            if success <= 10 or success % 5 == 0:
                print(f"  ✅ {element['name'][:35]}...")
        except Exception as e:
            pass

    print(f"\n  完成: {success}/{len(elements)}")
    return success


def import_examples_v2():
    """导入案例数据（v2版本）"""
    print("\n📥 导入标杆案例 (theme_examples v2)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_examples_v2.json"
    )
    examples = data.get("theme_examples", [])

    themes_result = supabase.table("themes").select("id,slug").execute()
    theme_id_map = {t["slug"]: t["id"] for t in themes_result.data}

    success = 0
    for example in examples:
        try:
            theme_slug = example.get("genre_slug")
            theme_id = theme_id_map.get(theme_slug)

            if not theme_id:
                continue

            example_data = {
                "theme_id": theme_id,
                "example_type": example.get("example_type", "drama"),
                "title": example["title"],
                "description": example.get("description", ""),
                "achievements": json.dumps(example.get("achievements", {})),
                "key_success_factors": example.get("key_success_factors", []),
                "is_verified": example.get("is_verified", True),
                "verification_source": example.get(
                    "verification_source", "Deep Research"
                ),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            supabase.table("theme_examples").upsert(example_data).execute()
            success += 1
            if success <= 10 or success % 5 == 0:
                print(f"  ✅ {example['title'][:35]}...")
        except Exception as e:
            pass

    print(f"\n  完成: {success}/{len(examples)}")
    return success


def import_hooks_v2():
    """导入钩子模板（v2版本）"""
    print("\n📥 导入钩子模板 (hook_templates v2)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_hooks_v2.json"
    )
    hooks = data.get("hook_templates", [])

    success = 0
    for hook in hooks:
        try:
            hook_data = {
                "hook_type": hook.get("hook_type", "situation"),
                "name": hook["name"][:250] if len(hook["name"]) > 250 else hook["name"],
                "template": hook.get("template", "")[:500]
                if len(hook.get("template", "")) > 500
                else hook.get("template", ""),
                "description": hook.get("description", "")[:500]
                if len(hook.get("description", "")) > 500
                else hook.get("description", ""),
                "variables": json.dumps(hook.get("variables", {})),
                "effectiveness_score": hook.get("effectiveness_score", 0),
                "psychology_mechanism": hook.get("psychology_mechanism", "")[:300]
                if len(hook.get("psychology_mechanism", "")) > 300
                else hook.get("psychology_mechanism", ""),
                "usage_constraints": json.dumps(hook.get("usage_constraints", {})),
                "applicable_genres": hook.get("applicable_genres", []),
                "examples": json.dumps(hook.get("examples", [])),
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            supabase.table("hook_templates").upsert(hook_data).execute()
            success += 1
            if success <= 10 or success % 5 == 0:
                print(f"  ✅ {hook['name'][:35]}...")
        except Exception as e:
            pass

    print(f"\n  完成: {success}/{len(hooks)}")
    return success


def verify_import():
    """验证导入"""
    print("\n🔍 验证导入数据...")

    tables = ["themes", "theme_elements", "theme_examples", "hook_templates"]

    for table in tables:
        try:
            result = supabase.table(table).select("*", count="exact").execute()
            count = len(result.data)
            print(f"  ✅ {table}: {count} 条记录")
        except Exception as e:
            print(f"  ❌ {table}: {str(e)[:60]}")


def main():
    print("=" * 70)
    print("🚀 重新导入真实数据到Supabase")
    print("=" * 70)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 检查文件
    files = [
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_themes_v2.json",
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_elements_v2.json",
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_examples_v2.json",
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_hooks_v2.json",
    ]

    for f in files:
        if not Path(f).exists():
            print(f"❌ 找不到文件: {f}")
            sys.exit(1)

    print("✅ 所有数据文件已找到\n")

    # 清空表
    clear_tables()

    # 导入数据
    total = 0
    total += import_themes_v2()
    total += import_elements_v2()
    total += import_examples_v2()
    total += import_hooks_v2()

    # 验证
    verify_import()

    print("\n" + "=" * 70)
    print("✅ 数据重新导入完成！")
    print("=" * 70)
    print(f"\n总计导入: {total} 条记录")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
