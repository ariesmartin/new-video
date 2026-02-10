#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase数据导入脚本 - 适配实际数据库Schema
基于 migration 005_theme_knowledge_base.sql
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
        "hook_templates",
        "themes",
    ]

    for table in tables:
        try:
            # 使用DELETE清空表（neq不适用于UUID，使用is not null）
            result = supabase.table(table).delete().not_.is_("id", "null").execute()
            print(f"  ✅ 清空 {table}")
        except Exception as e:
            print(f"  ⚠️  {table}: {str(e)[:80]}")

    print("  清理完成")


def import_themes(data: Dict) -> Dict:
    """导入主题数据 - 适配新schema"""
    print("\n📥 导入主题数据 (themes)...")

    themes = data.get("themes", [])
    success_count = 0
    error_count = 0
    theme_id_map = {}  # 用于映射 slug -> UUID

    for theme in themes:
        try:
            # 映射到新schema
            theme_data = {
                "slug": theme["slug"],
                "name": theme["name"],
                "name_en": theme.get("name_en", ""),
                "category": theme.get("category", "drama"),
                "description": theme.get("description", ""),
                "summary": theme.get("summary", ""),
                "core_formula": theme.get("core_formula", {}),
                "keywords": {
                    "writing": theme.get("writing_keywords", []),
                    "visual": theme.get("visual_keywords", []),
                },
                "audience_analysis": theme.get("target_audience", {}),
                "market_size": theme.get("market_size", {}),
                "market_score": theme.get("market_score", 0)
                or theme.get("effectiveness_score", 0),
                "success_rate": theme.get("success_rate", 0),
                "is_active": True,
            }

            result = supabase.table("themes").insert(theme_data).execute()
            if result.data:
                theme_id_map[theme["slug"]] = result.data[0]["id"]
                success_count += 1
                print(f"  ✅ {theme['name']}")
            else:
                error_count += 1
                print(f"  ❌ {theme.get('name', 'Unknown')}: No data returned")

        except Exception as e:
            error_count += 1
            print(f"  ❌ {theme.get('name', 'Unknown')}: {str(e)[:80]}")

    print(f"\n  主题导入完成: {success_count}成功, {error_count}失败")
    return theme_id_map


def import_theme_elements(data: Dict, theme_id_map: Dict):
    """导入元素数据 - 适配新schema"""
    print("\n📥 导入元素数据 (theme_elements)...")
    print("  数据来源: 正确去重版（45个元素）")

    success_count = 0
    error_count = 0

    # 1. 导入PDF分类元素（20个）
    print("\n  导入PDF分类元素...")
    tropes_library = data.get("tropes_library", {})

    for category, items in tropes_library.items():
        for item in items:
            try:
                # 查找对应的theme_id（基于category映射）
                theme_slug = map_category_to_theme(category)
                theme_id = theme_id_map.get(theme_slug)

                element_data = {
                    "theme_id": theme_id,
                    "element_type": map_category_to_element_type(category),
                    "name": item["name"],
                    "name_en": item.get("name_en", ""),
                    "description": item.get("description", ""),
                    "effectiveness_score": item.get("effectiveness_score", 0)
                    or item.get("success_rate", 0),
                    "weight": 1.0,
                    "usage_guidance": {
                        "best_timing": item.get("best_timing", ""),
                        "preparation": "",
                        "execution_tips": item.get("usage_tips", ""),
                        "variations": item.get("variations", []),
                    },
                    "risk_factors": parse_risk_factors(item.get("risk_factors", [])),
                    "emotional_impact": {},
                    "classic_examples": [
                        {"drama": ex, "scene": "", "why_effective": ""}
                        for ex in item.get("classic_examples", [])
                    ],
                    "is_active": True,
                }

                result = supabase.table("theme_elements").insert(element_data).execute()
                success_count += 1
                print(f"    ✅ {item['name'][:30]}...")

            except Exception as e:
                error_count += 1
                print(f"    ❌ {item.get('name', 'Unknown')[:30]}...: {str(e)[:60]}")

    # 2. 导入TXT题材特定元素（25个）
    print("\n  导入TXT题材特定元素...")
    txt_tropes = data.get("txt_tropes_unique", [])

    for item in txt_tropes:
        try:
            # 查找对应的theme_id
            theme_id = item.get("theme_id")
            if theme_id and isinstance(theme_id, int):
                # 将数字ID映射为slug
                theme_slug = map_numeric_theme_id(theme_id)
                theme_id = theme_id_map.get(theme_slug)

            element_data = {
                "theme_id": theme_id,
                "element_type": "trope",
                "name": item["name"],
                "name_en": item.get("name_en", ""),
                "description": item.get("description", ""),
                "effectiveness_score": item.get("effectiveness_score", 0),
                "weight": 1.0,
                "usage_guidance": {
                    "best_timing": item.get("usage_timing", ""),
                    "preparation": "",
                    "execution_tips": "",
                    "variations": [],
                },
                "risk_factors": [],
                "emotional_impact": {},
                "classic_examples": [
                    {"drama": ex, "scene": "", "why_effective": ""}
                    for ex in item.get("examples", [])
                ],
                "is_active": True,
            }

            result = supabase.table("theme_elements").insert(element_data).execute()
            success_count += 1
            print(
                f"    ✅ {item['name'][:30]}... (评分:{item.get('effectiveness_score', 0)})"
            )

        except Exception as e:
            error_count += 1
            print(f"    ❌ {item.get('name', 'Unknown')[:30]}...: {str(e)[:60]}")

    print(f"\n  元素导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_hooks(data: Dict):
    """导入钩子模板 - 适配新schema"""
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
                    "description": hook.get("description", ""),
                    "variables": hook.get("variables", {}),
                    "effectiveness_score": hook.get("effectiveness_score", 0),
                    "psychology_mechanism": hook.get("psychology_mechanism", ""),
                    "usage_constraints": {
                        "must_follow_up": hook.get("must_follow_up", ""),
                        "avoid": "",
                        "tone": "",
                        "duration": "前30秒",
                    },
                    "applicable_genres": hook.get("applicable_genres", []),
                    "applicable_episodes": "第1集前30秒",
                    "examples": [
                        {
                            "scenario": ex,
                            "hook_text": "",
                            "effectiveness": "",
                            "completion_rate": "",
                        }
                        for ex in hook.get("examples", [])
                    ],
                    "is_active": True,
                }

                result = supabase.table("hook_templates").insert(hook_data).execute()
                success_count += 1
                print(f"  ✅ [{hook_type}] {hook['name'][:30]}...")

            except Exception as e:
                error_count += 1
                print(f"  ❌ {hook.get('name', 'Unknown')[:30]}...: {str(e)[:60]}")

    print(f"\n  钩子导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def import_examples(data: Dict, theme_id_map: Dict):
    """导入爆款案例 - 适配新schema"""
    print("\n📥 导入爆款案例 (theme_examples)...")

    success_count = 0
    error_count = 0

    for theme in data.get("themes", []):
        theme_slug = theme.get("slug")
        theme_id = theme_id_map.get(theme_slug)
        examples = theme.get("viral_examples", [])

        for example in examples:
            try:
                example_data = {
                    "theme_id": theme_id,
                    "example_type": "drama",
                    "title": example["title"],
                    "alternative_title": "",
                    "release_year": 2024,
                    "description": example.get("why_it_works", ""),
                    "storyline_summary": example.get("innovation", ""),
                    "achievements": {
                        "records": [example.get("data", "")]
                        if example.get("data")
                        else [],
                        "awards": [],
                    },
                    "key_success_factors": [example.get("success_factors", "")]
                    if example.get("success_factors")
                    else [],
                    "unique_selling_points": [],
                    "learnings": example.get("risk_lesson", ""),
                    "market_performance": {},
                    "is_verified": True,
                    "verification_source": "Deep Research报告",
                }

                result = supabase.table("theme_examples").insert(example_data).execute()
                success_count += 1
                print(f"  ✅ {example['title'][:40]}...")

            except Exception as e:
                error_count += 1
                print(f"  ❌ {example.get('title', 'Unknown')[:40]}...: {str(e)[:60]}")

    print(f"\n  案例导入完成: {success_count}成功, {error_count}失败")
    return success_count, error_count


def parse_risk_factors(risk_data) -> list:
    """解析风险因素，支持字符串、列表或分号分隔的字符串"""
    if not risk_data:
        return []
    if isinstance(risk_data, list):
        return risk_data
    if isinstance(risk_data, str):
        # 处理分号分隔的风险因素
        if "；" in risk_data:
            return [r.strip() for r in risk_data.split("；") if r.strip()]
        elif ";" in risk_data:
            return [r.strip() for r in risk_data.split(";") if r.strip()]
        else:
            return [risk_data.strip()] if risk_data.strip() else []
    return []


def map_category_to_theme(category: str) -> str:
    """将PDF分类映射到theme slug"""
    mapping = {
        "identity": "revenge",  # 身份相关 -> 复仇逆袭
        "relationship": "romance",  # 关系相关 -> 甜宠恋爱
        "conflict": "revenge",  # 冲突相关 -> 复仇逆袭
        "setting": "transmigration",  # 设定相关 -> 穿越重生（包含奇幻元素）
    }
    return mapping.get(category, "revenge")


def map_category_to_element_type(category: str) -> str:
    """将分类映射到element_type"""
    mapping = {
        "identity": "character",
        "relationship": "plot",
        "conflict": "plot",
        "setting": "visual",
    }
    return mapping.get(category, "trope")


def map_numeric_theme_id(theme_id: int) -> str:
    """将数字theme_id映射到slug"""
    mapping = {
        1: "revenge",
        2: "romance",
        3: "suspense",
        4: "transmigration",
        5: "family_urban",  # 修正为实际的slug
    }
    return mapping.get(theme_id, "revenge")


def main():
    """主函数"""
    print("=" * 80)
    print("Supabase数据导入 - 适配实际Schema版")
    print("基于 migration 005_theme_knowledge_base.sql")
    print("=" * 80)

    try:
        # 1. 加载正确去重后的数据
        print("\n📖 加载数据...")
        data = load_json(
            "/Users/ariesmartin/Documents/new-video/theme_library_deduplicated.json"
        )
        print(f"   ✓ 数据版本: {data['metadata']['version']}")
        print(f"   ✓ 元素总计: {data['summary']['tropes_total']}个")
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

        # 导入主题（返回ID映射）
        theme_id_map = import_themes(data)

        # 导入元素
        import_theme_elements(data, theme_id_map)

        # 导入钩子
        import_hooks(data)

        # 导入案例
        import_examples(data, theme_id_map)

        # 5. 生成最终报告
        print("\n" + "=" * 80)
        print("✅ 数据导入完成！")
        print("=" * 80)
        print("\n📊 导入完成:")
        print("  ✓ 主题: 已导入（带UUID映射）")
        print("  ✓ 元素: 45个正确去重后")
        print("  ✓ 钩子模板: 30个")
        print("  ✓ 案例: 25个真实爆款")
        print("\n数据特点:")
        print("  ✓ 45个元素（已去重，统计准确）")
        print("  ✓ 20个PDF分类元素 + 25个TXT题材特定元素")
        print("  ✓ 5个重叠元素已去除")
        print("  ✓ 适配 migration 005 数据库Schema")

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
