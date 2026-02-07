from typing import Optional
from langchain_core.tools import tool
from backend.services.database import get_db_service

@tool
def load_genre_context(genre_id: str, include_tropes: bool = True, include_hooks: bool = True) -> str:
    """
    Skill: 加载指定题材的完整上下文信息。
    
    返回格式化的题材指导文本，包含核心公式、推荐元素、避雷指南等。
    可直接注入 Agent 的 System Prompt 中。
    
    Args:
        genre_id: 题材ID，可选值: revenge(复仇), sweet(甜宠), suspense(悬疑), 
                 fantasy(玄幻), urban(都市), workplace(职场) 等
        include_tropes: 是否包含推荐元素列表
        include_hooks: 是否包含钩子模板
    
    Returns:
        格式化的题材指导文本，包含以下章节:
        - 题材基本信息
        - 核心公式 (Setup → Rising → Climax → Resolution)
        - 目标受众
        - 推荐元素 (Tropes)
        - 情绪钩子 (Hooks)
        - 写作关键词
        - 视觉风格
        - 避雷清单
        - 市场趋势
    
    Example:
        >>> context = load_genre_context("revenge")
        >>> print(context)
        ## 题材指导：复仇逆袭
        
        ### 核心公式
        - Setup: 极端羞辱或背叛
        - Rising: 积累实力/隐藏身份
        - Climax: 身份揭露+打脸
        - Resolution: 正义伸张
        ...
    """
    db = get_db_service()
    
    # 查询题材基础信息
    genre = db.query(
        "themes",
        filters={"slug": genre_id, "status": "active"},
        include=["elements", "trends"]
    )
    
    if not genre:
        return f"错误：找不到题材 '{genre_id}'"
    
    # 构建返回文本
    sections = []
    
    # 章节 1: 基本信息
    sections.append(f"""
## 题材指导：{genre['name']}

{genre.get('description', '')}

**一句话总结**: {genre.get('summary', '')}
""")
    
    # 章节 2: 核心公式
    formula = genre.get('core_formula', {})
    sections.append(f"""
### 核心公式 (Core Formula)

1. **铺垫 (Setup)**: {formula.get('setup', 'N/A')}
2. **升级 (Rising)**: {formula.get('rising', 'N/A')}
3. **高潮 (Climax)**: {formula.get('climax', 'N/A')}
4. **结局 (Resolution)**: {formula.get('resolution', 'N/A')}

**情绪弧线**: {genre.get('emotional_arc', 'N/A')}
""")
    
    # 章节 3: 目标受众
    target = genre.get('target_audience', {})
    sections.append(f"""
### 目标受众

- **年龄段**: {target.get('age_range', 'N/A')}
- **性别倾向**: {target.get('gender', 'N/A')}
- **兴趣标签**: {', '.join(target.get('interests', []))}
- **观看习惯**: {target.get('viewing_habits', 'N/A')}
""")
    
    # 章节 4: 推荐元素 (Tropes)
    if include_tropes:
        tropes = db.query(
            "theme_elements",
            filters={
                "theme_id": genre['id'],
                "element_type": "trope",
                "is_active": True
            },
            order_by="weight DESC",
            limit=5
        )
        
        trope_text = "\n".join([
            f"  - **{t['name']}**: {t.get('description', '')} (权重: {t.get('weight', 1.0)})"
            for t in tropes
        ])
        
        sections.append(f"""
### 推荐元素 (Tropes)

{trope_text}

**使用建议**: 选择 2-3 个元素组合，避免堆砌。
""")
    
    # 章节 5: 钩子模板 (Hooks)
    if include_hooks:
        hooks = db.query(
            "theme_elements",
            filters={
                "theme_id": genre['id'],
                "element_type": "hook",
                "is_active": True
            },
            limit=3
        )
        
        hook_text = "\n".join([
            f"  - **{h['name']}** ({h.get('hook_type', '通用')}): {h.get('template', '')}"
            for h in hooks
        ])
        
        sections.append(f"""
### 钩子模板 (Hooks) - 用于前3秒留存

{hook_text}

**使用时机**: 前3秒必须抛出钩子，否则完播率会大幅下降。
""")
    
    # 章节 6: 写作关键词
    keywords = genre.get('keywords', {})
    writing_kw = keywords.get('writing', [])
    sections.append(f"""
### 写作关键词 (Writing Keywords)

用于指导 Novel Writer 的文风：
{', '.join(writing_kw)}

**使用方式**: 在 System Prompt 中强调这些关键词的使用。
""")
    
    # 章节 7: 视觉风格
    visual_kw = keywords.get('visual', [])
    visual_style = genre.get('visual_style', [])
    sections.append(f"""
### 视觉风格 (Visual Style)

**关键词**: {', '.join(visual_kw)}

**画面风格**: {', '.join(visual_style)}

**使用方式**: 用于指导 Storyboard Director 和 Asset Inspector。
""")
    
    # 章节 8: 避雷清单
    avoid = genre.get('avoid_patterns', [])
    sections.append(f"""
### ⚠️ 避雷清单 (Avoid Patterns)

以下套路在当前题材中已被观众厌倦，应避免使用：

{chr(10).join([f"  - ❌ {pattern}" for pattern in avoid])}

**替代方案**: 使用推荐元素中的创新组合。
""")
    
    # 章节 9: 市场趋势
    trends = genre.get('trends', {})
    sections.append(f"""
### 📊 市场趋势

- **热门度**: {genre.get('popularity_score', 0)}/100
- **成功率**: {genre.get('success_rate', 0)}%
- **趋势方向**: {trends.get('direction', 'stable')}
- **推荐度**: {'⭐⭐⭐⭐⭐' if genre.get('is_featured') else '⭐⭐⭐'}
""")
    
    return "\n---\n".join(sections)