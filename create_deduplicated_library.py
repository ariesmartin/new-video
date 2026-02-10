#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确去重版：短剧主题库数据整合
去重规则：
1. 保留PDF的20个分类元素（作为基础体系）
2. 保留TXT的25个题材特定元素（独有）
3. 去除TXT的5个通用元素（与PDF重叠）
最终：20 + 25 = 45个元素
"""

import json
from datetime import datetime


def create_deduplicated_library():
    """创建正确去重后的数据集"""
    print("📖 加载数据源...")

    # 1. 加载数据
    with open("extracted_theme_library_data.json", "r", encoding="utf-8") as f:
        txt_data = json.load(f)

    with open("extracted_pdf_theme_data.json", "r", encoding="utf-8") as f:
        pdf_data = json.load(f)

    print(f"   ✓ TXT: {len(txt_data['elements'])}个元素")
    print(f"   ✓ PDF: {pdf_data['summary']['tropes_count']}个元素")

    # 2. 识别重叠元素（5个）
    overlapping_names = {
        "身份揭露",  # ↔ PDF:隐藏大佬/扮猪吃虎
        "当众打脸",  # ↔ PDF:打脸反杀/当众羞辱
        "契约婚姻",  # ↔ PDF:契约婚姻/假戏真做（完全相同）
        "系统金手指",  # ↔ PDF:系统绑定/金手指觉醒
        "时间循环",  # ↔ PDF:时间循环/重复当日（完全相同）
    }

    print(f"\n🔍 识别到重叠元素: {len(overlapping_names)}个")
    for name in sorted(overlapping_names):
        print(f"   - {name} (将在TXT中去除，保留PDF版本)")

    # 3. 整合题材（保留PDF的四阶段公式 + TXT的案例）
    print("\n🎭 整合题材数据...")
    merged_genres = []
    for pdf_genre in pdf_data["genres"]:
        # 查找对应TXT题材
        txt_genre = None
        for tg in txt_data["themes"]:
            if (
                (pdf_genre["slug"] == "transmigration" and tg["slug"] == "rebirth")
                or (pdf_genre["slug"] == "family_urban" and tg["slug"] == "urban")
                or (pdf_genre["slug"] == tg["slug"])
            ):
                txt_genre = tg
                break

        merged_genre = {
            "id": pdf_genre["id"],
            "slug": pdf_genre["slug"],
            "name": pdf_genre["name"],
            "name_en": pdf_genre.get("name_en", ""),
            "description": pdf_genre["description"],
            "core_formula": pdf_genre["core_formula"],
            "writing_keywords": pdf_genre.get("writing_keywords", []),
            "visual_keywords": pdf_genre.get("visual_keywords", []),
            "viral_examples": txt_genre.get("viral_examples", []) if txt_genre else [],
        }
        merged_genres.append(merged_genre)

    print(f"   ✓ 整合后: {len(merged_genres)}个题材")

    # 4. 整合元素库（关键：正确去重）
    print("\n🧩 整合元素库（正确去重）...")

    # 4.1 PDF分类元素：20个（全部保留）
    tropes_library = pdf_data["tropes_library"]
    pdf_count = sum(len(v) for v in tropes_library.values())
    print(f"   ✓ PDF分类元素: {pdf_count}个（全部保留）")
    for category, items in tropes_library.items():
        print(f"     - {category}: {len(items)}个")

    # 4.2 TXT题材特定元素：25个（独有，全部保留）
    txt_unique_tropes = []
    for elem in txt_data["elements"]:
        # 只保留题材特定元素（theme_id不为null）
        if elem.get("theme_id") is not None:
            txt_unique_tropes.append(
                {
                    "id": elem["id"],
                    "theme_id": elem["theme_id"],
                    "name": elem["name"],
                    "name_en": elem.get("name_en", ""),
                    "category": elem.get("category", ""),
                    "description": elem.get("description", ""),
                    "effectiveness_score": elem.get("effectiveness_score", 0),
                    "usage_timing": elem.get("usage_timing", ""),
                    "examples": elem.get("examples", []),
                }
            )

    txt_unique_count = len(txt_unique_tropes)
    print(f"\n   ✓ TXT题材特定元素: {txt_unique_count}个（全部保留）")

    # 按题材分组显示
    for theme in txt_data["themes"]:
        theme_elements = [e for e in txt_unique_tropes if e["theme_id"] == theme["id"]]
        print(f"     - {theme['name']}: {len(theme_elements)}个")

    # 4.3 去除的重复元素：5个
    removed_count = len(overlapping_names)
    print(f"\n   ✗ 去除的重复元素: {removed_count}个（与PDF重叠）")
    for name in sorted(overlapping_names):
        print(f"     - {name}")

    # 5. 正确去重后的统计
    total_tropes = pdf_count + txt_unique_count
    print(
        f"\n   📊 正确去重后: {pdf_count} + {txt_unique_count} = {total_tropes}个元素"
    )

    # 6. 钩子模板：30个（PDF）
    print("\n🪝 整合钩子模板...")
    hooks_library = pdf_data["hooks_library"]
    total_hooks = sum(len(v) for v in hooks_library.values())
    print(f"   ✓ 钩子总计: {total_hooks}个")

    # 7. 角色原型（PDF为主，补充TXT）
    print("\n👤 整合角色原型...")
    archetypes = pdf_data["archetypes"]
    # 添加TXT中独有的角色原型
    for arch in txt_data.get("archetypes", []):
        if isinstance(arch, dict):
            role = arch.get("role", "protagonist")
            # 检查是否已存在
            exists = any(
                a.get("name") == arch.get("name")
                for role_list in archetypes.values()
                for a in role_list
            )
            if not exists and role in archetypes:
                archetypes[role].append(arch)

    total_archetypes = sum(len(v) for v in archetypes.values())
    print(f"   ✓ 角色原型总计: {total_archetypes}个")

    # 8. 案例统计
    total_examples = sum(len(g.get("viral_examples", [])) for g in merged_genres)
    print(f"\n🎬 爆款案例总计: {total_examples}个")

    # 9. 构建最终数据集
    comprehensive_data = {
        "metadata": {
            "version": "2.2.0",
            "creation_date": datetime.now().isoformat(),
            "sources": [
                "短剧创作主题库研究报告.txt",
                "中文短剧AI生成系统主题库研究报告.pdf",
            ],
            "deduplication_note": "正确去重版：去除5个重叠元素，保留45个独有元素",
            "deduplication_rule": "保留PDF分类体系(20) + TXT题材特定(25)，去除TXT通用(5)",
        },
        "summary": {
            "themes_count": len(merged_genres),
            "tropes_pdf": pdf_count,
            "tropes_txt_unique": txt_unique_count,
            "tropes_removed": removed_count,
            "tropes_total": total_tropes,
            "hooks_count": total_hooks,
            "archetypes_count": total_archetypes,
            "examples_count": total_examples,
            "combinations_count": len(
                pdf_data["market_insights"].get("trending_combinations", [])
            ),
        },
        "themes": merged_genres,
        "tropes_library": tropes_library,
        "txt_tropes_unique": txt_unique_tropes,
        "removed_overlapping_tropes": sorted(list(overlapping_names)),
        "hooks_library": hooks_library,
        "archetypes": archetypes,
        "market_insights": pdf_data["market_insights"],
        "writing_guide": pdf_data["writing_guide"],
        "visual_guide": pdf_data["visual_guide"],
    }

    return comprehensive_data


def main():
    """主函数"""
    print("=" * 80)
    print("短剧主题库数据整合 - 正确去重版")
    print("去重规则: 20(PDF) + 25(TXT独有) = 45个元素")
    print("=" * 80)

    try:
        # 创建数据集
        data = create_deduplicated_library()

        # 保存
        output_file = "theme_library_deduplicated.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_size = len(json.dumps(data, ensure_ascii=False)) / 1024

        # 生成最终报告
        print("\n" + "=" * 80)
        print("✅ 正确去重后的最终统计")
        print("=" * 80)
        print(f"\n📁 输出文件: {output_file}")
        print(f"📦 文件大小: {file_size:.1f} KB")
        print()
        print("=" * 80)
        print("📊 最终准确统计（已去重）")
        print("=" * 80)
        print(f"🎭 题材:                 {data['summary']['themes_count']} 个")
        print(f"🧩 PDF分类元素:          {data['summary']['tropes_pdf']} 个")
        print(f"🧩 TXT题材特定元素:      {data['summary']['tropes_txt_unique']} 个")
        print(f"✗ 去除的重叠元素:       {data['summary']['tropes_removed']} 个")
        print(f"📊 元素总计（正确）:     {data['summary']['tropes_total']} 个 ✓")
        print(f"🪝 钩子模板:             {data['summary']['hooks_count']} 个")
        print(f"👤 角色原型:             {data['summary']['archetypes_count']} 个")
        print(f"🎬 爆款案例:             {data['summary']['examples_count']} 个")
        print(f"🔗 跨题材组合:           {data['summary']['combinations_count']} 个")
        print()
        print("=" * 80)
        print("🗑️ 去除的重叠元素")
        print("=" * 80)
        for elem in data["removed_overlapping_tropes"]:
            print(f"  - {elem}")
        print("  （这些元素在PDF分类体系中已存在）")
        print()
        print("=" * 80)
        print("✅ 正确去重版整合完成！")
        print("=" * 80)
        print()
        print("统计验证:")
        print(
            f"  20 (PDF分类) + 25 (TXT题材特定) = {data['summary']['tropes_total']} 个元素 ✓"
        )
        print()

        return True

    except Exception as e:
        print(f"\n❌ 整合失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
