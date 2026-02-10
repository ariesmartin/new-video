"""
验证主题库数据导入完整性
"""
import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

async def verify_import():
    """验证数据导入情况"""
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("🔍 正在验证主题库数据导入...\n")
    
    # 1. 检查 themes 表
    themes_response = supabase.table('themes').select('*').execute()
    themes = themes_response.data
    print(f"✅ Themes 表: {len(themes)} 条记录")
    for theme in themes:
        print(f"   - {theme['name']} (slug: {theme['slug']}, category: {theme['category']})")
    
    # 2. 检查 theme_elements 表
    elements_response = supabase.table('theme_elements').select('*').execute()
    elements = elements_response.data
    print(f"\n✅ Theme Elements 表: {len(elements)} 条记录")
    
    # 按主题分组统计
    theme_element_counts = {}
    for elem in elements:
        theme_id = elem.get('theme_id')
        if theme_id:
            theme_element_counts[theme_id] = theme_element_counts.get(theme_id, 0) + 1
    
    # 获取主题名称映射
    theme_names = {t['id']: t['name'] for t in themes}
    for theme_id, count in theme_element_counts.items():
        theme_name = theme_names.get(theme_id, 'Unknown')
        print(f"   - {theme_name}: {count} 个元素")
    
    # 3. 检查 hook_templates 表
    hooks_response = supabase.table('hook_templates').select('*').execute()
    hooks = hooks_response.data
    print(f"\n✅ Hook Templates 表: {len(hooks)} 条记录")
    
    # 按类型分组
    hook_types = {}
    for hook in hooks:
        hook_type = hook.get('hook_type', 'unknown')
        hook_types[hook_type] = hook_types.get(hook_type, 0) + 1
    for hook_type, count in hook_types.items():
        print(f"   - {hook_type}: {count} 个模板")
    
    # 4. 检查 theme_examples 表
    examples_response = supabase.table('theme_examples').select('*').execute()
    examples = examples_response.data
    print(f"\n✅ Theme Examples 表: {len(examples)} 条记录")
    
    # 按主题分组
    example_counts = {}
    for ex in examples:
        theme_id = ex.get('theme_id')
        if theme_id:
            example_counts[theme_id] = example_counts.get(theme_id, 0) + 1
    for theme_id, count in example_counts.items():
        theme_name = theme_names.get(theme_id, 'Unknown')
        print(f"   - {theme_name}: {count} 个案例")
    
    # 5. 验证数据完整性
    print("\n📊 数据完整性检查:")
    
    # 检查是否有孤立的元素
    theme_ids = {t['id'] for t in themes}
    orphaned_elements = [e for e in elements if e.get('theme_id') not in theme_ids]
    if orphaned_elements:
        print(f"   ⚠️  发现 {len(orphaned_elements)} 个孤立的元素 (无对应主题)")
    else:
        print("   ✅ 所有元素都有对应的主题")
    
    # 检查是否有孤立的案例
    orphaned_examples = [e for e in examples if e.get('theme_id') not in theme_ids]
    if orphaned_examples:
        print(f"   ⚠️  发现 {len(orphaned_examples)} 个孤立的案例 (无对应主题)")
    else:
        print("   ✅ 所有案例都有对应的主题")
    
    # 6. 验证数据质量
    print("\n📈 数据质量检查:")
    
    # 检查元素的有效性评分范围
    invalid_scores = [e for e in elements if e.get('effectiveness_score', 0) < 0 or e.get('effectiveness_score', 0) > 100]
    if invalid_scores:
        print(f"   ⚠️  发现 {len(invalid_scores)} 个元素的有效性评分超出范围 (0-100)")
    else:
        print("   ✅ 所有元素的有效性评分都在有效范围内")
    
    # 检查钩子模板的有效性评分
    invalid_hook_scores = [h for h in hooks if h.get('effectiveness_score', 0) < 0 or h.get('effectiveness_score', 0) > 100]
    if invalid_hook_scores:
        print(f"   ⚠️  发现 {len(invalid_hook_scores)} 个钩子模板的有效性评分超出范围")
    else:
        print("   ✅ 所有钩子模板的有效性评分都在有效范围内")
    
    # 7. 抽样检查
    print("\n🔍 抽样检查 (随机选取一个主题查看详细信息):")
    if themes:
        sample_theme = themes[0]
        print(f"\n   主题: {sample_theme['name']}")
        print(f"   - 描述: {sample_theme['description'][:100]}...")
        print(f"   - 核心公式: {sample_theme.get('core_formula', 'N/A')}")
        print(f"   - 关键词: {sample_theme.get('keywords', [])}")
        
        # 获取该主题的元素
        theme_elements = [e for e in elements if e.get('theme_id') == sample_theme['id']]
        print(f"   - 关联元素数: {len(theme_elements)}")
        if theme_elements:
            sample_elem = theme_elements[0]
            print(f"   - 示例元素: {sample_elem['name']} (有效性: {sample_elem.get('effectiveness_score')})")
    
    print("\n✨ 验证完成!")
    
    # 返回统计信息
    return {
        "themes": len(themes),
        "elements": len(elements),
        "hooks": len(hooks),
        "examples": len(examples),
        "orphaned_elements": len(orphaned_elements) if orphaned_elements else 0,
        "orphaned_examples": len(orphaned_examples) if orphaned_examples else 0,
    }

if __name__ == "__main__":
    stats = asyncio.run(verify_import())
    
    print("\n" + "="*50)
    print("📋 导入统计摘要")
    print("="*50)
    print(f"主题 (Themes): {stats['themes']}")
    print(f"元素 (Elements): {stats['elements']}")
    print(f"钩子模板 (Hooks): {stats['hooks']}")
    print(f"案例 (Examples): {stats['examples']}")
    print(f"孤立元素: {stats['orphaned_elements']}")
    print(f"孤立案例: {stats['orphaned_examples']}")
    
    # 判断导入是否成功
    if stats['themes'] == 5 and stats['elements'] >= 45 and stats['hooks'] >= 30 and stats['examples'] >= 25:
        print("\n✅ 数据导入验证通过!")
    else:
        print("\n⚠️  数据导入可能不完整，请检查")
