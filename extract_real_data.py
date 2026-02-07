#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短剧主题库数据提取脚本 - 从TXT和PDF报告提取真实数据
"""

import json
import re
import os
from datetime import datetime

# 添加项目路径
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")
os.chdir("/Users/ariesmartin/Documents/new-video")

# 导入数据库配置
try:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "database", "servers/douyin-specialist/database.py"
    )
    db_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_module)
    SessionLocal = db_module.SessionLocal
    init_db = db_module.init_db

    spec2 = importlib.util.spec_from_file_location(
        "models", "servers/douyin-specialist/models.py"
    )
    models_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(models_module)
    Theme = models_module.Theme
    ThemeElement = models_module.ThemeElement
    ThemeExample = models_module.ThemeExample
    HookTemplate = models_module.HookTemplate
    CharacterArchetype = models_module.CharacterArchetype

    DB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  数据库模块导入失败: {e}")
    DB_AVAILABLE = False


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


def extract_themes_from_txt(data):
    """从TXT数据提取题材"""
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

        # 构建四阶段公式JSON
        core_formula = {
            "setup": genre_data["core_formula"]["setup"],
            "rising": genre_data["core_formula"]["rising"],
            "climax": genre_data["core_formula"]["climax"],
            "resolution": genre_data["core_formula"]["resolution"],
        }

        theme = {
            "slug": slug,
            "name": name,
            "description": genre_data["core_formula"]["setup"][:100] + "...",
            "core_formula": core_formula,
            "emotional_arc": genre_data["emotional_arc"],
            "writing_keywords": genre_data["writing_keywords"],
            "visual_keywords": genre_data["visual_keywords"],
            "target_audience": genre_data["target_audience"],
            "avoid_patterns": genre_data["avoid_patterns"],
        }
        themes.append(theme)

    return themes


def extract_elements_from_txt(data):
    """从TXT数据提取元素"""
    elements = []
    element_id = 1

    # 1. 从题材中提取元素
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
                "id": element_id,
                "theme_id": theme_id,
                "name": trope["name"],
                "name_en": "",
                "category": "genre_specific",
                "description": trope["description"],
                "effectiveness_score": trope["effectiveness_score"],
                "usage_timing": trope["usage_timing"],
                "examples": json.dumps(trope["examples"], ensure_ascii=False),
            }
            elements.append(element)
            element_id += 1

    # 2. 从通用tropes中提取元素
    for trope_key, trope_data in data.get("tropes", {}).items():
        element = {
            "id": element_id,
            "theme_id": None,  # 通用元素
            "name": trope_data["name"],
            "name_en": trope_data.get("name_en", ""),
            "category": trope_data["category"],
            "description": trope_data["description"],
            "effectiveness_score": trope_data["success_rate"],
            "usage_timing": json.dumps(
                trope_data.get("usage_guidelines", {}), ensure_ascii=False
            ),
            "examples": json.dumps(
                [ex["drama"] for ex in trope_data.get("classic_examples", [])],
                ensure_ascii=False,
            ),
        }
        elements.append(element)
        element_id += 1

    return elements


def extract_examples_from_txt(data):
    """从TXT数据提取案例"""
    examples = []
    example_id = 1

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
                "id": example_id,
                "theme_id": theme_id,
                "title": viral_ex["title"],
                "why_it_works": viral_ex["why_it_works"],
            }
            examples.append(example)
            example_id += 1

    return examples


def extract_hooks_from_txt(data):
    """从TXT数据提取钩子模板"""
    hooks = []
    hook_id = 1

    # 处理三类钩子
    hook_categories = [
        ("situation_hooks", "situation"),
        ("question_hooks", "question"),
        ("visual_hooks", "visual"),
    ]

    for category_key, category_name in hook_categories:
        for hook_data in data.get("hooks", {}).get(category_key, []):
            hook = {
                "id": hook_id,
                "hook_type": category_name,
                "name": hook_data["name"],
                "template": hook_data["template"],
                "variables": json.dumps(
                    hook_data.get("variables", {}), ensure_ascii=False
                ),
                "effectiveness_score": hook_data["effectiveness_score"],
                "examples": json.dumps(
                    hook_data.get("examples", []), ensure_ascii=False
                ),
                "usage_tips": hook_data.get("usage_tips", ""),
            }
            hooks.append(hook)
            hook_id += 1

    return hooks


def extract_archetypes_from_txt(data):
    """从TXT数据提取角色原型"""
    archetypes = []

    for arch_key, arch_data in data.get("archetypes", {}).items():
        archetype = {
            "archetype_id": arch_key,
            "name": arch_data["name"],
            "name_en": arch_data.get("name_en", ""),
            "role": arch_data["role"],
            "core_traits": json.dumps(
                arch_data.get("core_traits", {}), ensure_ascii=False
            ),
            "motivation": json.dumps(
                arch_data.get("motivation", {}), ensure_ascii=False
            ),
            "character_arc": arch_data.get("character_arc", ""),
            "dialogue_style": json.dumps(
                arch_data.get("dialogue_style", {}), ensure_ascii=False
            ),
            "visual_markers": arch_data.get("visual_markers", []),
            "classic_examples": arch_data.get("classic_examples", []),
        }
        archetypes.append(archetype)

    return archetypes


def import_to_database(themes, elements, examples, hooks, archetypes):
    """将数据导入数据库"""
    if not DB_AVAILABLE:
        print("❌ 数据库模块不可用，跳过导入")
        return False

    print("\n💾 正在导入数据库...")

    try:
        # 初始化数据库
        init_db()

        db = SessionLocal()

        # 清空现有数据
        print("   清空现有数据...")
        db.query(ThemeElement).delete()
        db.query(ThemeExample).delete()
        db.query(HookTemplate).delete()
        db.query(CharacterArchetype).delete()
        db.query(Theme).delete()
        db.commit()

        # 1. 导入题材
        print(f"   导入 {len(themes)} 个题材...")
        for theme_data in themes:
            theme = Theme(
                slug=theme_data["slug"],
                name=theme_data["name"],
                description=theme_data["description"],
                core_formula=theme_data["core_formula"],
                emotional_arc=theme_data["emotional_arc"],
                writing_keywords=theme_data["writing_keywords"],
                visual_keywords=theme_data["visual_keywords"],
                target_audience=theme_data["target_audience"],
                avoid_patterns=theme_data["avoid_patterns"],
            )
            db.add(theme)
        db.commit()

        # 2. 导入元素
        print(f"   导入 {len(elements)} 个元素...")
        for elem_data in elements:
            element = ThemeElement(
                id=elem_data["id"],
                theme_id=elem_data["theme_id"],
                name=elem_data["name"],
                name_en=elem_data["name_en"],
                category=elem_data["category"],
                description=elem_data["description"],
                effectiveness_score=elem_data["effectiveness_score"],
                usage_timing=elem_data["usage_timing"],
                examples=elem_data["examples"],
            )
            db.add(element)
        db.commit()

        # 3. 导入案例
        print(f"   导入 {len(examples)} 个案例...")
        for ex_data in examples:
            example = ThemeExample(
                id=ex_data["id"],
                theme_id=ex_data["theme_id"],
                title=ex_data["title"],
                why_it_works=ex_data["why_it_works"],
            )
            db.add(example)
        db.commit()

        # 4. 导入钩子模板
        print(f"   导入 {len(hooks)} 个钩子模板...")
        for hook_data in hooks:
            hook = HookTemplate(
                id=hook_data["id"],
                hook_type=hook_data["hook_type"],
                name=hook_data["name"],
                template=hook_data["template"],
                variables=hook_data["variables"],
                effectiveness_score=hook_data["effectiveness_score"],
                examples=hook_data["examples"],
                usage_tips=hook_data["usage_tips"],
            )
            db.add(hook)
        db.commit()

        # 5. 导入角色原型
        print(f"   导入 {len(archetypes)} 个角色原型...")
        for arch_data in archetypes:
            archetype = CharacterArchetype(
                archetype_id=arch_data["archetype_id"],
                name=arch_data["name"],
                name_en=arch_data["name_en"],
                role=arch_data["role"],
                core_traits=arch_data["core_traits"],
                motivation=arch_data["motivation"],
                character_arc=arch_data["character_arc"],
                dialogue_style=arch_data["dialogue_style"],
                visual_markers=arch_data["visual_markers"],
                classic_examples=arch_data["classic_examples"],
            )
            db.add(archetype)
        db.commit()

        db.close()
        print("✅ 数据库导入完成！")
        return True

    except Exception as e:
        print(f"❌ 数据库导入失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def save_to_json(themes, elements, examples, hooks, archetypes):
    """保存为JSON文件（备用）"""
    output = {
        "themes": themes,
        "elements": elements,
        "examples": examples,
        "hooks": hooks,
        "archetypes": archetypes,
        "extraction_date": datetime.now().isoformat(),
    }

    with open("extracted_theme_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到 extracted_theme_data.json")


def main():
    """主函数"""
    print("=" * 60)
    print("短剧主题库数据提取工具")
    print("数据源: 短剧创作主题库研究报告.txt")
    print("=" * 60)

    try:
        # 1. 加载TXT数据
        txt_data = load_txt_data()

        # 2. 提取各类数据
        print("\n🔍 提取数据中...")

        themes = extract_themes_from_txt(txt_data)
        print(f"   ✓ 提取 {len(themes)} 个题材")

        elements = extract_elements_from_txt(txt_data)
        print(f"   ✓ 提取 {len(elements)} 个元素")

        examples = extract_examples_from_txt(txt_data)
        print(f"   ✓ 提取 {len(examples)} 个案例")

        hooks = extract_hooks_from_txt(txt_data)
        print(f"   ✓ 提取 {len(hooks)} 个钩子模板")

        archetypes = extract_archetypes_from_txt(txt_data)
        print(f"   ✓ 提取 {len(archetypes)} 个角色原型")

        # 3. 导入数据库
        success = import_to_database(themes, elements, examples, hooks, archetypes)

        # 4. 保存JSON备份
        save_to_json(themes, elements, examples, hooks, archetypes)

        # 5. 统计报告
        print("\n" + "=" * 60)
        print("📊 数据提取统计")
        print("=" * 60)
        print(f"题材: {len(themes)} 个")
        print(f"元素: {len(elements)} 个")
        print(f"案例: {len(examples)} 个")
        print(f"钩子: {len(hooks)} 个")
        print(f"角色原型: {len(archetypes)} 个")
        print("=" * 60)

        if success:
            print("✅ 全部数据已成功导入数据库！")
        else:
            print("⚠️  数据库导入失败，但JSON文件已保存")

        return True

    except Exception as e:
        print(f"❌ 数据提取失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
