#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版：整合所有数据源 - 创建完整的短剧主题库数据集
修复：确保所有30个TXT元素都被正确整合
"""

import json
from datetime import datetime


def create_corrected_comprehensive_library():
    """创建修正后的完整数据集"""
    print("📖 加载所有数据源...")

    # 1. 加载TXT数据
    with open("extracted_theme_library_data.json", "r", encoding="utf-8") as f:
        txt_data = json.load(f)

    # 2. 加载PDF数据
    with open("extracted_pdf_theme_data.json", "r", encoding="utf-8") as f:
        pdf_data = json.load(f)

    print(
        f"   ✓ TXT数据: {len(txt_data['themes'])}题材, {len(txt_data['elements'])}元素"
    )
    print(
        f"   ✓ PDF数据: {len(pdf_data['genres'])}题材, {pdf_data['summary']['tropes_count']}元素"
    )

    # 3. 整合题材（以PDF的四阶段公式为主，补充TXT的案例）
    print("\n🎭 整合题材数据...")
    merged_genres = []
    for pdf_genre in pdf_data["genres"]:
        # 查找对应的TXT题材
        txt_genre = None
        for tg in txt_data["themes"]:
            if (
                (pdf_genre["slug"] == "transmigration" and tg["slug"] == "rebirth")
                or (pdf_genre["slug"] == "family_urban" and tg["slug"] == "urban")
                or (pdf_genre["slug"] == tg["slug"])
            ):
                txt_genre = tg
                break

        # 合并数据
        merged_genre = {
            "id": pdf_genre["id"],
            "slug": pdf_genre["slug"],
            "name": pdf_genre["name"],
            "name_en": pdf_genre.get("name_en", ""),
            "description": pdf_genre["description"],
            "core_formula": pdf_genre["core_formula"],
            "writing_keywords": pdf_genre.get("writing_keywords", []),
            "visual_keywords": pdf_genre.get("visual_keywords", []),
            "tropes": pdf_genre.get("tropes", []),
            "viral_examples": txt_genre.get("viral_examples", []) if txt_genre else [],
        }
        merged_genres.append(merged_genre)

    print(f"   ✓ 整合后: {len(merged_genres)}个题材")

    # 4. 整合元素库（关键修正：确保所有30个TXT元素都被包含）
    print("\n🧩 整合元素库...")

    # PDF的分类元素库（20个）
    tropes_library = pdf_data["tropes_library"]

    # TXT的30个元素（25个题材特定 + 5个通用）
    txt_elements_by_genre = {}
    txt_universal_elements = []

    for elem in txt_data["elements"]:
        theme_id = elem.get("theme_id")
        if theme_id:
            # 题材特定元素
            if theme_id not in txt_elements_by_genre:
                txt_elements_by_genre[theme_id] = []
            txt_elements_by_genre[theme_id].append(
                {
                    "name": elem["name"],
                    "description": elem.get("description", ""),
                    "effectiveness_score": elem.get("effectiveness_score", 0),
                    "usage_timing": elem.get("usage_timing", ""),
                    "examples": elem.get("examples", []),
                }
            )
        else:
            # 通用元素
            txt_universal_elements.append(
                {
                    "name": elem["name"],
                    "category": elem.get("category", ""),
                    "description": elem.get("description", ""),
                    "effectiveness_score": elem.get("effectiveness_score", 0),
                }
            )

    # 创建详细的题材特定元素列表
    genre_specific_tropes = []
    for theme_id, elements in txt_elements_by_genre.items():
        theme_name = (
            txt_data["themes"][theme_id - 1]["name"]
            if theme_id <= len(txt_data["themes"])
            else f"Theme {theme_id}"
        )
        genre_specific_tropes.append(
            {"theme_id": theme_id, "theme_name": theme_name, "elements": elements}
        )

    total_tropes = (
        sum(len(v) for v in tropes_library.values())
        + len(txt_universal_elements)
        + sum(len(g["elements"]) for g in genre_specific_tropes)
    )
    print(f"   ✓ PDF分类元素: {sum(len(v) for v in tropes_library.values())}个")
    print(f"   ✓ TXT通用元素: {len(txt_universal_elements)}个")
    print(
        f"   ✓ TXT题材特定元素: {sum(len(g['elements']) for g in genre_specific_tropes)}个"
    )
    print(f"   ✓ 元素总计: {total_tropes}个")

    # 5. 钩子模板（PDF的30个）
    print("\n🪝 整合钩子模板...")
    hooks_library = pdf_data["hooks_library"]
    total_hooks = sum(len(v) for v in hooks_library.values())
    print(f"   ✓ 钩子总计: {total_hooks}个")

    # 6. 角色原型（PDF的15个 + TXT的5个补充）
    print("\n👤 整合角色原型...")
    archetypes = pdf_data["archetypes"]
    # 添加TXT中的角色原型
    for arch in txt_data.get("archetypes", []):
        if isinstance(arch, dict):
            # 检查是否已存在
            exists = any(
                a.get("name") == arch.get("name")
                for role_list in archetypes.values()
                for a in role_list
            )
            if not exists:
                # 根据role类型添加到对应列表
                role = arch.get("role", "protagonist")
                if role in archetypes:
                    archetypes[role].append(arch)

    total_archetypes = sum(len(v) for v in archetypes.values())
    print(f"   ✓ 角色原型总计: {total_archetypes}个")

    # 7. 案例统计
    total_examples = sum(len(g.get("viral_examples", [])) for g in merged_genres)
    print(f"\n🎬 爆款案例总计: {total_examples}个")

    # 8. 构建最终数据集
    comprehensive_data = {
        "metadata": {
            "version": "2.1.0",
            "creation_date": datetime.now().isoformat(),
            "sources": [
                "短剧创作主题库研究报告.txt",
                "中文短剧AI生成系统主题库研究报告.pdf",
                "google-deepresearch.html",
            ],
            "total_sources": 3,
            "correction_note": "修正版：确保所有30个TXT元素都被正确整合",
        },
        "summary": {
            "themes_count": len(merged_genres),
            "tropes_library_count": sum(len(v) for v in tropes_library.values()),
            "txt_universal_tropes_count": len(txt_universal_elements),
            "txt_genre_specific_tropes_count": sum(
                len(g["elements"]) for g in genre_specific_tropes
            ),
            "total_tropes_count": total_tropes,
            "hooks_count": total_hooks,
            "archetypes_count": total_archetypes,
            "examples_count": total_examples,
            "combinations_count": len(
                pdf_data["market_insights"].get("trending_combinations", [])
            ),
        },
        "themes": merged_genres,
        "tropes_library": tropes_library,
        "txt_universal_tropes": txt_universal_elements,
        "txt_genre_specific_tropes": genre_specific_tropes,
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
    print("短剧主题库数据整合工具 - 修正版")
    print("确保所有30个TXT元素都被正确整合")
    print("=" * 80)

    try:
        # 创建完整数据集
        data = create_corrected_comprehensive_library()

        # 保存
        output_file = "comprehensive_theme_library_v2.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_size = len(json.dumps(data, ensure_ascii=False)) / 1024

        # 生成报告
        print("\n" + "=" * 80)
        print("📊 修正后的完整统计")
        print("=" * 80)
        print(f"\n✅ 数据整合完成！")
        print(f"\n📁 输出文件: {output_file}")
        print(f"📦 文件大小: {file_size:.1f} KB")
        print()
        print("=" * 80)
        print("📈 准确数据统计")
        print("=" * 80)
        print(f"🎭 题材:                 {data['summary']['themes_count']} 个")
        print(f"🧩 分类元素(PDF):        {data['summary']['tropes_library_count']} 个")
        print(
            f"🧩 通用元素(TXT):        {data['summary']['txt_universal_tropes_count']} 个"
        )
        print(
            f"🧩 题材特定元素(TXT):    {data['summary']['txt_genre_specific_tropes_count']} 个"
        )
        print(f"📊 元素总计:             {data['summary']['total_tropes_count']} 个")
        print(f"🪝 钩子模板:             {data['summary']['hooks_count']} 个")
        print(f"👤 角色原型:             {data['summary']['archetypes_count']} 个")
        print(f"🎬 爆款案例:             {data['summary']['examples_count']} 个")
        print(f"🔗 跨题材组合:           {data['summary']['combinations_count']} 个")
        print()
        print("=" * 80)
        print("✨ 数据源")
        print("=" * 80)
        for i, source in enumerate(data["metadata"]["sources"], 1):
            print(f"{i}. {source}")
        print()
        print("=" * 80)
        print("🎉 修正版整合完成！")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ 数据整合失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
