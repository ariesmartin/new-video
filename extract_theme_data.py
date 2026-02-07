#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短剧主题库数据提取脚本 - 从TXT报告提取完整数据
输出: extracted_theme_library_data.json
"""

import json
import re
from datetime import datetime


def load_txt_data():
    """从TXT文件加载JSON数据"""
    print("📖 正在读取 TXT 报告...")
    with open("短剧创作主题库研究报告.txt", "r", encoding="utf-8") as f:
        content = f.read()

    # 提取JSON部分
    json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        data = json.loads(json_str)
        print(f"✅ 成功解析JSON数据")
        print(f"   - 题材数量: {data['research_metadata']['total_themes']}")
        print(f"   - 元素数量: {data['research_metadata']['total_tropes']}")
        print(f"   - 钩子数量: {data['research_metadata']['total_hooks']}")
        return data
    else:
        raise ValueError("未找到JSON数据块")


def extract_themes(data):
    """提取题材数据"""
    themes = []
    genre_mapping = {
        "revenge": ("复仇逆袭", "revenge"),
        "romance": ("甜宠恋爱", "romance"),
        "suspense": ("悬疑推理", "suspense"),
        "rebirth": ("穿越重生", "rebirth"),
        "urban": ("家庭伦理/都市现实", "urban"),
    }

    for genre_key, genre_data in data["genres"].items():
        name, slug = genre_mapping.get(genre_key, (genre_key, genre_key))

        theme = {
            "id": len(themes) + 1,
            "slug": slug,
            "name": name,
            "description": genre_data["core_formula"]["setup"][:150] + "...",
            "core_formula": genre_data["core_formula"],
            "emotional_arc": genre_data["emotional_arc"],
            "writing_keywords": genre_data["writing_keywords"],
            "visual_keywords": genre_data["visual_keywords"],
            "target_audience": genre_data["target_audience"],
            "avoid_patterns": genre_data["avoid_patterns"],
            "viral_examples": genre_data.get("viral_examples", []),
        }
        themes.append(theme)

    return themes


def extract_elements(data):
    """提取元素数据（包含题材特定元素和通用元素）"""
    elements = []

    # 1. 从题材中提取元素（25个）
    genre_mapping = {
        "revenge": 1,
        "romance": 2,
        "suspense": 3,
        "rebirth": 4,
        "urban": 5,
    }

    for genre_key, genre_data in data["genres"].items():
        theme_id = genre_mapping.get(genre_key, 1)

        for trope in genre_data["tropes"]:
            element = {
                "id": len(elements) + 1,
                "theme_id": theme_id,
                "theme_slug": genre_key,
                "name": trope["name"],
                "name_en": "",
                "category": "genre_specific",
                "description": trope["description"],
                "effectiveness_score": trope["effectiveness_score"],
                "usage_timing": trope["usage_timing"],
                "examples": trope["examples"],
            }
            elements.append(element)

    # 2. 从通用tropes中提取元素（5个）
    for trope_key, trope_data in data.get("tropes", {}).items():
        element = {
            "id": len(elements) + 1,
            "theme_id": None,
            "theme_slug": "universal",
            "name": trope_data["name"],
            "name_en": trope_data.get("name_en", ""),
            "category": trope_data["category"],
            "description": trope_data["description"],
            "effectiveness_score": trope_data.get("success_rate", 90),
            "usage_timing": trope_data.get("usage_guidelines", {}),
            "examples": [ex["drama"] for ex in trope_data.get("classic_examples", [])],
            "variations": trope_data.get("variations", []),
            "emotional_impact": trope_data.get("emotional_impact", {}),
            "risk_factors": trope_data.get("risk_factors", []),
        }
        elements.append(element)

    return elements


def extract_examples(data):
    """提取案例数据（25个）"""
    examples = []
    genre_mapping = {
        "revenge": 1,
        "romance": 2,
        "suspense": 3,
        "rebirth": 4,
        "urban": 5,
    }

    for genre_key, genre_data in data["genres"].items():
        theme_id = genre_mapping.get(genre_key, 1)

        for viral_ex in genre_data.get("viral_examples", []):
            example = {
                "id": len(examples) + 1,
                "theme_id": theme_id,
                "theme_slug": genre_key,
                "title": viral_ex["title"],
                "why_it_works": viral_ex["why_it_works"],
            }
            examples.append(example)

    return examples


def extract_hooks(data):
    """提取钩子模板数据（15个）"""
    hooks = []

    # 处理三类钩子
    hook_categories = [
        ("situation_hooks", "situation", "情境型"),
        ("question_hooks", "question", "问题型"),
        ("visual_hooks", "visual", "视觉型"),
    ]

    for category_key, category_slug, category_name in hook_categories:
        for hook_data in data.get("hooks", {}).get(category_key, []):
            hook = {
                "id": len(hooks) + 1,
                "hook_type": category_slug,
                "hook_type_cn": category_name,
                "name": hook_data["name"],
                "template": hook_data["template"],
                "variables": hook_data.get("variables", {}),
                "effectiveness_score": hook_data["effectiveness_score"],
                "examples": hook_data.get("examples", []),
                "usage_tips": hook_data.get("usage_tips", ""),
                "applicable_genres": hook_data.get("applicable_genres", []),
            }
            hooks.append(hook)

    return hooks


def extract_archetypes(data):
    """提取角色原型数据（6个）"""
    archetypes = []

    for arch_key, arch_data in data.get("archetypes", {}).items():
        archetype = {
            "id": len(archetypes) + 1,
            "archetype_key": arch_key,
            "name": arch_data["name"],
            "name_en": arch_data.get("name_en", ""),
            "role": arch_data["role"],
            "core_traits": arch_data.get("core_traits", {}),
            "motivation": arch_data.get("motivation", {}),
            "character_arc": arch_data.get("character_arc", ""),
            "dialogue_style": arch_data.get("dialogue_style", {}),
            "visual_markers": arch_data.get("visual_markers", []),
            "classic_examples": arch_data.get("classic_examples", []),
            "relationship_dynamics": arch_data.get("relationship_dynamics", {}),
        }
        archetypes.append(archetype)

    return archetypes


def extract_market_insights(data):
    """提取市场洞察数据"""
    return data.get("market_insights", {})


def extract_writing_guide(data):
    """提取写作指导数据"""
    return data.get("writing_guide", {})


def extract_visual_guide(data):
    """提取视觉指导数据"""
    return data.get("visual_guide", {})


def main():
    """主函数"""
    print("=" * 70)
    print("短剧主题库数据提取工具")
    print("数据源: 短剧创作主题库研究报告.txt")
    print("=" * 70)

    try:
        # 1. 加载数据
        txt_data = load_txt_data()

        # 2. 提取各类数据
        print("\n🔍 提取数据中...")

        themes = extract_themes(txt_data)
        print(f"   ✓ 提取 {len(themes)} 个题材")

        elements = extract_elements(txt_data)
        print(f"   ✓ 提取 {len(elements)} 个元素")

        examples = extract_examples(txt_data)
        print(f"   ✓ 提取 {len(examples)} 个案例")

        hooks = extract_hooks(txt_data)
        print(f"   ✓ 提取 {len(hooks)} 个钩子模板")

        archetypes = extract_archetypes(txt_data)
        print(f"   ✓ 提取 {len(archetypes)} 个角色原型")

        market_insights = extract_market_insights(txt_data)
        print(f"   ✓ 提取市场洞察数据")

        writing_guide = extract_writing_guide(txt_data)
        print(f"   ✓ 提取写作指导数据")

        visual_guide = extract_visual_guide(txt_data)
        print(f"   ✓ 提取视觉指导数据")

        # 3. 构建完整输出
        output = {
            "metadata": {
                "source_file": "短剧创作主题库研究报告.txt",
                "extraction_date": datetime.now().isoformat(),
                "version": "1.0.0",
            },
            "summary": {
                "themes_count": len(themes),
                "elements_count": len(elements),
                "examples_count": len(examples),
                "hooks_count": len(hooks),
                "archetypes_count": len(archetypes),
            },
            "themes": themes,
            "elements": elements,
            "examples": examples,
            "hooks": hooks,
            "archetypes": archetypes,
            "market_insights": market_insights,
            "writing_guide": writing_guide,
            "visual_guide": visual_guide,
        }

        # 4. 保存JSON文件
        output_file = "extracted_theme_library_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n💾 数据已保存到: {output_file}")

        # 5. 统计报告
        print("\n" + "=" * 70)
        print("📊 数据提取统计")
        print("=" * 70)
        print(f"题材:       {len(themes):3d} 个")
        print(f"元素:       {len(elements):3d} 个 (题材内25个 + 通用5个)")
        print(f"案例:       {len(examples):3d} 个")
        print(f"钩子模板:   {len(hooks):3d} 个 (情境5 + 问题5 + 视觉5)")
        print(f"角色原型:   {len(archetypes):3d} 个")
        print(f"市场洞察:   ✓")
        print(f"写作指导:   ✓")
        print(f"视觉指导:   ✓")
        print("=" * 70)
        print("✅ 全部数据提取完成！")
        print(f"\n文件位置: ./{output_file}")
        print(f"文件大小: {len(json.dumps(output, ensure_ascii=False)) / 1024:.1f} KB")

        return True

    except Exception as e:
        print(f"\n❌ 数据提取失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
