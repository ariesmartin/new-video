#!/usr/bin/env python3
"""
Supabase数据导入脚本
将Deep Research提取的JSON数据导入到Supabase数据库
"""

import json
import os
import sys
from pathlib import Path
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


def import_themes():
    """导入主题数据"""
    print("\n📥 导入主题数据 (themes)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_themes.json"
    )
    themes = data.get("themes", [])

    success_count = 0
    error_count = 0

    for theme in themes:
        try:
            # 转换数据格式以匹配数据库schema（不指定id，让数据库自动生成）
            theme_data = {
                "slug": theme["slug"],
                "name": theme["name"],
                "name_en": theme["name_en"],
                "category": theme["category"],
                "description": theme["description"],
                "summary": theme.get("summary", ""),
                "core_formula": json.dumps(theme.get("core_formula", {})),
                "keywords": json.dumps(theme.get("keywords", {})),
                "market_score": theme.get("market_score", 0),
                "success_rate": theme.get("success_rate", 0),
                "status": "active",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            # 插入数据
            result = supabase.table("themes").upsert(theme_data).execute()
            success_count += 1
            print(f"  ✅ {theme['name']}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ {theme.get('name', 'Unknown')}: {str(e)}")

    print(f"\n  主题导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_theme_elements():
    """导入爆款元素数据"""
    print("\n📥 导入爆款元素 (theme_elements)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_elements.json"
    )
    elements = data.get("theme_elements", [])

    success_count = 0
    error_count = 0

    # 首先获取所有主题的ID映射
    themes_result = supabase.table("themes").select("id,slug").execute()
    theme_id_map = {t["slug"]: t["id"] for t in themes_result.data}

    for element in elements:
        try:
            theme_slug = element.get("genre_slug")
            theme_id = theme_id_map.get(theme_slug)

            if not theme_id:
                print(f"  ⚠️ 跳过: 找不到主题 {theme_slug}")
                continue

            element_data = {
                "theme_id": theme_id,
                "element_type": "trope",  # 默认为trope类型
                "name": element["name"],
                "description": element.get("description", ""),
                "effectiveness_score": element.get("score", 0),
                "usage_guidance": json.dumps(
                    {
                        "best_timing": element.get("usage_timing", ""),
                        "description": element.get("description", ""),
                    }
                ),
                "weight": 1.0,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = supabase.table("theme_elements").upsert(element_data).execute()
            success_count += 1
            print(f"  ✅ {element['name'][:30]}...")

        except Exception as e:
            error_count += 1
            print(f"  ❌ {element.get('name', 'Unknown')}: {str(e)}")

    print(f"\n  元素导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_theme_examples():
    """导入标杆案例数据"""
    print("\n📥 导入标杆案例 (theme_examples)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_examples.json"
    )
    examples = data.get("theme_examples", [])

    success_count = 0
    error_count = 0

    # 获取主题ID映射
    themes_result = supabase.table("themes").select("id,slug").execute()
    theme_id_map = {t["slug"]: t["id"] for t in themes_result.data}

    for example in examples:
        try:
            theme_slug = example.get("genre_slug")
            theme_id = theme_id_map.get(theme_slug)

            if not theme_id:
                print(f"  ⚠️ 跳过: 找不到主题 {theme_slug}")
                continue

            example_data = {
                "theme_id": theme_id,
                "example_type": "drama",
                "title": example["title"],
                "description": example.get("description", ""),
                "achievements": json.dumps(
                    {
                        "records": [example.get("achievements", "")],
                        "description": example.get("description", ""),
                    }
                ),
                "key_success_factors": [example.get("description", "")],
                "is_verified": True,
                "verification_source": "Deep Research Report",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = supabase.table("theme_examples").upsert(example_data).execute()
            success_count += 1
            print(f"  ✅ {example['title'][:30]}...")

        except Exception as e:
            error_count += 1
            print(f"  ❌ {example.get('title', 'Unknown')}: {str(e)}")

    print(f"\n  案例导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_hook_templates():
    """导入钩子模板数据"""
    print("\n📥 导入钩子模板 (hook_templates)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_hooks.json"
    )
    hooks = data.get("hook_templates", [])

    success_count = 0
    error_count = 0

    for hook in hooks:
        try:
            hook_data = {
                "hook_type": hook.get("type", "situation"),
                "name": hook["name"],
                "template": hook["template"],
                "variables": json.dumps(hook.get("variables", {})),
                "effectiveness_score": hook.get("effectiveness_score", 0),
                "psychology_mechanism": hook.get("psychology", ""),
                "usage_constraints": json.dumps(
                    {
                        "duration": hook.get("duration", ""),
                        "tips": hook.get("usage_tips", ""),
                    }
                ),
                "applicable_genres": hook.get("applicable_genres", []),
                "examples": json.dumps(hook.get("examples", [])),
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            result = supabase.table("hook_templates").upsert(hook_data).execute()
            success_count += 1
            print(f"  ✅ {hook['name']}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ {hook.get('name', 'Unknown')}: {str(e)}")

    print(f"\n  钩子模板导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_market_insights():
    """导入市场洞察数据"""
    print("\n📥 导入市场洞察 (market_insights)...")

    data = load_json(
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_market.json"
    )
    market_data = data.get("market_insights", [{}])[0]

    try:
        insight_data = {
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "period_type": "yearly",
            "market_overview": json.dumps(market_data.get("overview", {})),
            "genre_rankings": json.dumps(market_data.get("genre_rankings", [])),
            "trending_combinations": json.dumps(
                market_data.get("trending_combinations", [])
            ),
            "emerging_trends": market_data.get("key_findings", []),
            "data_sources": ["Deep Research Report", "DataEye", "艾瑞咨询"],
            "created_at": datetime.now().isoformat(),
        }

        result = supabase.table("market_insights").upsert(insight_data).execute()
        print(f"  ✅ 市场洞察导入成功")
        return 1, 0

    except Exception as e:
        print(f"  ❌ 市场洞察导入失败: {str(e)}")
        return 0, 1


def verify_import():
    """验证导入的数据"""
    print("\n🔍 验证导入数据...")

    tables = [
        "themes",
        "theme_elements",
        "theme_examples",
        "hook_templates",
        "market_insights",
    ]

    for table in tables:
        try:
            result = supabase.table(table).select("*", count="exact").execute()
            count = len(result.data)
            print(f"  ✅ {table}: {count} 条记录")
        except Exception as e:
            print(f"  ❌ {table}: 查询失败 - {str(e)}")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Deep Research 数据导入工具")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 检查JSON文件是否存在
    json_files = [
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_themes.json",
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_elements.json",
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_examples.json",
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_hooks.json",
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_market.json",
    ]

    for file_path in json_files:
        if not Path(file_path).exists():
            print(f"❌ 错误: 找不到文件 {file_path}")
            sys.exit(1)

    print("✅ 所有数据文件已找到\n")

    # 导入数据
    total_success = 0
    total_error = 0

    s, e = import_themes()
    total_success += s
    total_error += e

    s, e = import_theme_elements()
    total_success += s
    total_error += e

    s, e = import_theme_examples()
    total_success += s
    total_error += e

    s, e = import_hook_templates()
    total_success += s
    total_error += e

    s, e = import_market_insights()
    total_success += s
    total_error += e

    # 验证
    verify_import()

    # 总结
    print("\n" + "=" * 60)
    print("📊 导入完成统计")
    print("=" * 60)
    print(f"✅ 成功: {total_success}")
    print(f"❌ 失败: {total_error}")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if total_error == 0:
        print("🎉 所有数据导入成功！")
    else:
        print(f"⚠️ 有 {total_error} 条数据导入失败，请检查错误信息")


if __name__ == "__main__":
    main()
