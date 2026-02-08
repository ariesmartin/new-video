from typing import Optional
from langchain_core.tools import tool
from backend.services.database import get_db_service


@tool
async def load_genre_context(
    genre_id: str,
    include_elements: bool = True,
    include_hooks: bool = True,
    include_examples: bool = True,
) -> str:
    """
    Skill: 加载指定题材的完整上下文信息。

    返回格式化的题材指导文本，包含核心公式、推荐元素、避雷指南等。
    可直接注入 Agent 的 System Prompt 中。

    Args:
        genre_id: 题材ID，可选值: revenge(复仇逆袭), romance(甜宠恋爱), suspense(悬疑推理),
                 transmigration(穿越重生), family_urban(家庭伦理/都市现实)
        include_elements: 是否包含爆款元素列表
        include_hooks: 是否包含钩子模板
        include_examples: 是否包含标杆案例

    Returns:
        格式化的题材指导文本，包含以下章节:
        - 题材基本信息
        - 核心公式 (Setup → Rising → Climax → Resolution)
        - 目标受众与市场分析
        - 推荐元素 (爆款元素)
        - 钩子模板 (Hooks) - 前3秒留存
        - 标杆案例参考
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

    # Query theme information
    try:
        import httpx

        response = await db._client.get(
            f"{db._rest_url}/themes", params={"slug": f"eq.{genre_id}", "select": "*"}
        )
        response.raise_for_status()
        themes = response.json()

        if not themes:
            return f"错误：找不到题材 '{genre_id}'"

        theme = themes[0]
        theme_uuid = theme["id"]

    except Exception as e:
        return f"错误：查询题材失败 - {str(e)}"

    # 构建返回文本
    sections = []

    # 章节 1: 基本信息
    sections.append(f"""
## 题材指导：{theme["name"]}

{theme.get("description", "")}

**一句话总结**: {theme.get("summary", "")}

**题材分类**: {theme.get("category", "N/A")}
""")

    # 章节 2: 核心公式
    core_formula = theme.get("core_formula", {})
    if isinstance(core_formula, dict) and core_formula:
        formula_text = []
        stage_order = ["setup", "rising", "climax", "resolution"]
        stage_names = {
            "setup": "铺垫 (Setup)",
            "rising": "升级 (Rising)",
            "climax": "高潮 (Climax)",
            "resolution": "结局 (Resolution)",
        }

        for stage in stage_order:
            if stage in core_formula:
                stage_data = core_formula[stage]
                if isinstance(stage_data, dict):
                    task = stage_data.get("task", "N/A")
                    episodes = stage_data.get("episodes", "N/A")
                    elements = stage_data.get("elements", [])
                    avoid = stage_data.get("avoid", "")

                    formula_text.append(f"""
**{stage_names.get(stage, stage)}** ({episodes})
- 任务: {task}
- 核心元素: {", ".join(elements) if elements else "N/A"}
- 避雷: {avoid}
""")

        sections.append(f"""
### 核心公式 (Core Formula)

{"".join(formula_text)}
""")

    # 章节 3: 目标受众与市场分析
    audience = theme.get("audience_analysis", {})
    market_size = theme.get("market_size", "N/A")
    market_score = theme.get("market_score", 0)
    success_rate = theme.get("success_rate", 0)

    sections.append(f"""
### 目标受众与市场分析

**市场规模**: {market_size}
**市场评分**: {market_score}/100
**成功率**: {success_rate}%

**受众画像**:
- 性别倾向: {audience.get("gender_preference", "N/A")}
- 年龄层: {audience.get("age_range", "N/A")}
- 观看场景: {audience.get("viewing_context", "N/A")}
- 付费意愿: {audience.get("payment_willingness", "N/A")}
""")

    # 章节 4: 爆款元素
    if include_elements:
        try:
            elements_response = await db._client.get(
                f"{db._rest_url}/theme_elements",
                params={
                    "theme_id": f"eq.{theme_uuid}",
                    "select": "*",
                    "order": "effectiveness_score.desc",
                    "limit": 10,
                },
            )
            elements_response.raise_for_status()
            elements = elements_response.json() or []

            if elements:
                elements_text = []
                for i, elem in enumerate(elements[:5], 1):  # 只显示前5个
                    name = elem.get("name", "N/A")
                    name_en = elem.get("name_en", "")
                    desc = elem.get("description", "")
                    score = elem.get("effectiveness_score", 0)
                    guidance = elem.get("usage_guidance", "")
                    emotional = elem.get("emotional_impact", "")

                    elements_text.append(f"""
**{i}. {name}** {f"({name_en})" if name_en else ""}
   - 有效性评分: {score}/100
   - 描述: {desc[:100]}...
   - 使用时机: {guidance[:80]}...
   - 情绪效果: {emotional}
""")

                sections.append(f"""
### 爆款元素 (Top Elements)

{"".join(elements_text)}

**使用建议**: 选择 2-3 个元素组合，避免堆砌。根据剧情阶段选择合适的元素。
""")
        except Exception as e:
            sections.append(f"\n### 爆款元素\n*获取元素列表失败: {str(e)}*\n")

    # 章节 5: 钩子模板
    if include_hooks:
        try:
            hooks_response = await db._client.get(
                f"{db._rest_url}/hook_templates",
                params={"select": "*", "order": "effectiveness_score.desc", "limit": 5},
            )
            hooks_response.raise_for_status()
            hooks = hooks_response.json() or []

            if hooks:
                hooks_text = []
                for hook in hooks[:3]:  # 只显示前3个
                    name = hook.get("name", "N/A")
                    hook_type = hook.get("hook_type", "通用")
                    template = hook.get("template", "")
                    score = hook.get("effectiveness_score", 0)
                    psychology = hook.get("psychology_mechanism", "")

                    hooks_text.append(f"""
**{name}** ({hook_type}) - 有效性: {score}/100
   模板: {template}
   心理机制: {psychology}
""")

                sections.append(f"""
### 钩子模板 (Hooks) - 用于前3秒留存

{"".join(hooks_text)}

**使用时机**: 前3秒必须抛出钩子，否则完播率会大幅下降。
**选择原则**: 根据题材特点选择最合适的前3秒钩子类型。
""")
        except Exception as e:
            sections.append(f"\n### 钩子模板\n*获取钩子模板失败: {str(e)}*\n")

    # 章节 6: 标杆案例
    if include_examples:
        try:
            examples_response = await db._client.get(
                f"{db._rest_url}/theme_examples",
                params={"theme_id": f"eq.{theme_uuid}", "select": "*", "limit": 3},
            )
            examples_response.raise_for_status()
            examples = examples_response.json() or []

            if examples:
                examples_text = []
                for ex in examples[:2]:  # 只显示前2个
                    title = ex.get("title", "N/A")
                    alt_title = ex.get("alternative_title", "")
                    year = ex.get("release_year", "N/A")
                    achievements = ex.get("achievements", "")
                    learnings = ex.get("learnings", "")

                    examples_text.append(f"""
**《{title}》** {f"({alt_title})" if alt_title else ""} - {year}
   成绩: {achievements[:100]}...
   可借鉴: {learnings[:100]}...
""")

                sections.append(f"""
### 标杆案例 (Reference Cases)

{"".join(examples_text)}

**学习建议**: 分析成功案例的元素组合和节奏把控，而非简单模仿剧情。
""")
        except Exception as e:
            sections.append(f"\n### 标杆案例\n*获取案例失败: {str(e)}*\n")

    # 章节 7: 关键词
    keywords = theme.get("keywords", {})
    if isinstance(keywords, dict):
        writing_kw = keywords.get("writing", [])
        visual_kw = keywords.get("visual", [])

        if writing_kw or visual_kw:
            sections.append(f"""
### 关键词 (Keywords)

**写作关键词**: {", ".join(writing_kw) if writing_kw else "N/A"}
**视觉关键词**: {", ".join(visual_kw) if visual_kw else "N/A"}

**使用方式**: 在 System Prompt 中强调这些关键词的使用，确保文风统一。
""")

    # 章节 8: 避雷清单
    risk_factors = []
    # 从元素中提取风险因素
    if include_elements:
        try:
            elements_response = await db._client.get(
                f"{db._rest_url}/theme_elements",
                params={
                    "theme_id": f"eq.{theme_uuid}",
                    "select": "risk_factors",
                },
            )
            elements_response.raise_for_status()
            elements = elements_response.json() or []

            all_risks = set()
            for elem in elements:
                risks = elem.get("risk_factors", [])
                if isinstance(risks, list):
                    all_risks.update(risks)
                elif isinstance(risks, str):
                    all_risks.add(risks)

            risk_factors = list(all_risks)[:5]  # 最多显示5个
        except:
            pass

    if risk_factors:
        sections.append(f"""
### ⚠️ 避雷清单 (Avoid Patterns)

以下套路在当前题材中需要谨慎使用或避免：

{chr(10).join([f"  - ❌ {risk}" for risk in risk_factors])}

**替代方案**: 使用推荐元素中的创新组合，避免观众审美疲劳。
""")

    # 章节 9: 市场趋势总结
    sections.append(f"""
### 📊 市场总结

- **题材名称**: {theme["name"]}
- **市场评分**: {market_score}/100
- **成功率**: {success_rate}%
- **推荐度**: {"⭐⭐⭐⭐⭐" if market_score >= 90 else "⭐⭐⭐⭐" if market_score >= 80 else "⭐⭐⭐"}

**适用场景**: 根据目标受众和平台特点选择此题材。
""")

    return "\n---\n".join(sections)


@tool
async def search_elements_by_effectiveness(
    theme_id: str, min_score: int = 85, limit: int = 5
) -> str:
    """
    Skill: 按有效性评分搜索高效果元素。

    用于快速找到特定题材中最有效的爆款元素。

    Args:
        theme_id: 题材ID (revenge, romance, suspense, transmigration, family_urban)
        min_score: 最低有效性评分 (0-100)
        limit: 返回元素数量

    Returns:
        格式化的元素列表
    """
    db = get_db_service()

    try:
        # 先获取主题UUID
        theme_response = await db._client.get(
            f"{db._rest_url}/themes", params={"slug": f"eq.{theme_id}", "select": "id,name"}
        )
        theme_response.raise_for_status()
        themes = theme_response.json()

        if not themes:
            return f"错误：找不到题材 '{theme_id}'"

        theme_uuid = themes[0]["id"]
        theme_name = themes[0]["name"]

        # 查询高评分元素
        elements_response = await db._client.get(
            f"{db._rest_url}/theme_elements",
            params={
                "theme_id": f"eq.{theme_uuid}",
                "effectiveness_score": f"gte.{min_score}",
                "select": "*",
                "order": "effectiveness_score.desc",
                "limit": limit,
            },
        )
        elements_response.raise_for_status()
        elements = elements_response.json() or []

        if not elements:
            return f"在题材 '{theme_name}' 中没有找到评分 ≥ {min_score} 的元素"

        result = [f"## {theme_name} - 高效果元素 (评分 ≥ {min_score})\\n"]

        for i, elem in enumerate(elements, 1):
            name = elem.get("name", "N/A")
            score = elem.get("effectiveness_score", 0)
            desc = elem.get("description", "")
            guidance = elem.get("usage_guidance", "")
            weight = elem.get("weight", 1.0)

            result.append(f"""
**{i}. {name}** (评分: {score}, 权重: {weight})
   描述: {desc}
   使用建议: {guidance}
""")

        return "\\n".join(result)

    except Exception as e:
        return f"搜索失败: {str(e)}"


@tool
async def get_hook_templates_by_type(hook_type: str, limit: int = 3) -> str:
    """
    Skill: 获取指定类型的钩子模板。

    Args:
        hook_type: 钩子类型 (situation-情境型, question-疑问型, visual-视觉型)
        limit: 返回模板数量

    Returns:
        格式化的钩子模板列表
    """
    db = get_db_service()

    try:
        response = await db._client.get(
            f"{db._rest_url}/hook_templates",
            params={
                "hook_type": f"eq.{hook_type}",
                "select": "*",
                "order": "effectiveness_score.desc",
                "limit": limit,
            },
        )
        response.raise_for_status()
        hooks = response.json() or []

        if not hooks:
            return f"未找到类型为 '{hook_type}' 的钩子模板"

        type_names = {
            "situation": "情境型钩子",
            "question": "疑问型钩子",
            "visual": "视觉型钩子",
        }

        result = [f"## {type_names.get(hook_type, hook_type)} 模板\n"]

        for i, hook in enumerate(hooks, 1):
            name = hook.get("name", "N/A")
            template = hook.get("template", "")
            score = hook.get("effectiveness_score", 0)
            psychology = hook.get("psychology_mechanism", "")
            constraints = hook.get("usage_constraints", "")

            result.append(f"""
**{i}. {name}** (有效性: {score}/100)
   模板: {template}
   心理机制: {psychology}
   使用限制: {constraints}
""")

        return "\\n".join(result)

    except Exception as e:
        return f"获取钩子模板失败: {str(e)}"


@tool
async def analyze_genre_compatibility(genre1: str, genre2: str) -> str:
    """
    Skill: 分析两种题材的兼容性，判断是否适合融合创作。

    Args:
        genre1: 第一种题材ID
        genre2: 第二种题材ID

    Returns:
        兼容性分析报告
    """
    db = get_db_service()

    try:
        # 获取两个题材的信息
        response = await db._client.get(
            f"{db._rest_url}/themes", params={"slug": f"in.({genre1},{genre2})", "select": "*"}
        )
        response.raise_for_status()
        themes = response.json() or []

        if len(themes) < 2:
            return f"错误：找不到指定的题材（{genre1} 或 {genre2}）"

        theme_data = {t["slug"]: t for t in themes}
        t1, t2 = theme_data.get(genre1), theme_data.get(genre2)

        if not t1 or not t2:
            return "错误：无法获取题材信息"

        # 简单的兼容性分析逻辑
        # 基于关键词重叠度和市场定位
        keywords1 = set(t1.get("keywords", {}).get("writing", []))
        keywords2 = set(t2.get("keywords", {}).get("writing", []))

        overlap = keywords1 & keywords2
        compatibility_score = len(overlap) * 10 + 50  # 基础分50 + 重叠度
        compatibility_score = min(100, compatibility_score)

        # 判断兼容性等级
        if compatibility_score >= 80:
            level = "高度兼容 ✅"
            suggestion = "非常适合融合创作，可以大胆结合两种题材的特色元素"
        elif compatibility_score >= 60:
            level = "中度兼容 ⚠️"
            suggestion = "可以融合，但需要谨慎平衡两种题材的节奏和情绪"
        else:
            level = "低度兼容 ❌"
            suggestion = "不建议强行融合，可能导致风格混乱"

        return f"""
## 题材兼容性分析

**题材A**: {t1["name"]} (市场评分: {t1.get("market_score", 0)})
**题材B**: {t2["name"]} (市场评分: {t2.get("market_score", 0)})

### 兼容性评分: {compatibility_score}/100
**等级**: {level}

### 共同关键词
{", ".join(overlap) if overlap else "无显著重叠"}

### 融合建议
{suggestion}

### 注意事项
1. 保持核心情绪的连贯性
2. 避免两种题材的避雷清单冲突
3. 确保目标受众群体有足够重叠
4. 建议先小规模测试市场反应
"""

    except Exception as e:
        return f"分析失败: {str(e)}"


# ============================================================================
# Backward Compatibility Functions (for existing agents)
# ============================================================================


@tool
async def get_tropes(genre_id: str, limit: int = 5) -> str:
    """
    Skill: 获取指定题材的常用套路(tropes)。

    这是 search_elements_by_effectiveness 的别名，保持向后兼容。

    Args:
        genre_id: 题材ID
        limit: 返回数量

    Returns:
        套路/元素列表
    """
    return await search_elements_by_effectiveness.ainvoke(
        {"theme_id": genre_id, "min_score": 80, "limit": limit}
    )


@tool
async def get_hooks(genre_id: str, hook_type: Optional[str] = None, limit: int = 3) -> str:
    """
    Skill: 获取钩子模板。

    这是 get_hook_templates_by_type 的包装，支持按题材筛选。

    Args:
        genre_id: 题材ID
        hook_type: 钩子类型 (situation/question/visual)
        limit: 返回数量

    Returns:
        钩子模板列表
    """
    db = get_db_service()

    try:
        params = {"select": "*", "order": "effectiveness_score.desc", "limit": limit}
        if hook_type:
            params["hook_type"] = f"eq.{hook_type}"

        response = await db._client.get(f"{db._rest_url}/hook_templates", params=params)
        response.raise_for_status()
        hooks = response.json() or []

        if not hooks:
            return "未找到钩子模板"

        result = ["## 钩子模板\n"]

        for i, hook in enumerate(hooks, 1):
            name = hook.get("name", "N/A")
            template = hook.get("template", "")
            h_type = hook.get("hook_type", "通用")
            score = hook.get("effectiveness_score", 0)

            result.append(f"""
**{i}. {name}** ({h_type}) - 有效性: {score}/100
   模板: {template}
""")

        return "\\n".join(result)

    except Exception as e:
        return f"获取钩子模板失败: {str(e)}"


@tool
async def get_character_archetypes(genre_id: str, limit: int = 5) -> str:
    """
    Skill: 获取角色原型/archetypes。

    注意: 角色原型数据尚未导入数据库，此函数返回基于题材的通用角色建议。

    Args:
        genre_id: 题材ID
        limit: 返回数量

    Returns:
        角色原型建议
    """
    archetypes_db = {
        "revenge": [
            {"name": "隐忍复仇者", "traits": ["冷静", "有谋略", "善于隐藏"], "role": "主角"},
            {"name": "嚣张反派", "traits": ["傲慢", "短视", "欺软怕硬"], "role": "对手"},
            {"name": "背叛者", "traits": ["自私", "机会主义", "虚伪"], "role": "转折点"},
        ],
        "romance": [
            {"name": "高冷男神", "traits": ["外表冷漠", "内心温柔", "能力强"], "role": "男主"},
            {"name": "甜美女主", "traits": ["善良", "坚韧", "可爱"], "role": "女主"},
            {"name": "助攻闺蜜", "traits": ["热心", "幽默", "情商高"], "role": "配角"},
        ],
        "suspense": [
            {"name": "敏锐侦探", "traits": ["观察力强", "逻辑思维", "执着"], "role": "主角"},
            {
                "name": "神秘嫌疑人",
                "traits": ["深藏不露", "多面性格", "关键线索"],
                "role": "关键人物",
            },
            {"name": "幕后黑手", "traits": ["高智商", "精心布局", "动机复杂"], "role": "反派"},
        ],
        "transmigration": [
            {"name": "穿越者", "traits": ["现代思维", "信息优势", "适应力强"], "role": "主角"},
            {"name": "原著反派", "traits": ["被误解", "命运多舛", "可改变"], "role": "可变角色"},
            {"name": "土著贵人", "traits": ["权势", "眼光独到", "关键助力"], "role": "盟友"},
        ],
        "family_urban": [
            {"name": "家庭主妇", "traits": ["牺牲精神", "觉醒意识", "坚韧"], "role": "主角"},
            {"name": "妈宝男", "traits": ["依赖", "缺乏主见", "成长期"], "role": "可变角色"},
            {"name": "恶婆婆", "traits": ["控制欲", "传统观念", "冲突源"], "role": "对手"},
        ],
    }

    archetypes = archetypes_db.get(genre_id, [])

    if not archetypes:
        return f"未找到题材 '{genre_id}' 的角色原型数据"

    result = [f"## {genre_id} - 推荐角色原型\n"]

    for i, arch in enumerate(archetypes[:limit], 1):
        name = arch.get("name", "N/A")
        traits = ", ".join(arch.get("traits", []))
        role = arch.get("role", "配角")

        result.append(f"""
**{i}. {name}** ({role})
   特征: {traits}
""")

    return "\\n".join(result)


@tool
async def get_market_trends(genre_id: Optional[str] = None) -> str:
    """
    Skill: 获取市场趋势分析。

    Args:
        genre_id: 可选，特定题材ID

    Returns:
        市场趋势报告
    """
    db = get_db_service()

    try:
        if genre_id:
            # 获取特定题材的市场数据
            response = await db._client.get(
                f"{db._rest_url}/themes",
                params={
                    "slug": f"eq.{genre_id}",
                    "select": "name,market_size,market_score,success_rate,trend_direction",
                },
            )
            response.raise_for_status()
            themes = response.json() or []

            if not themes:
                return f"未找到题材 '{genre_id}'"

            theme = themes[0]
            return f"""
## {theme["name"]} - 市场趋势

**市场规模**: {theme.get("market_size", "N/A")}
**市场评分**: {theme.get("market_score", 0)}/100
**成功率**: {theme.get("success_rate", 0)}%
**趋势方向**: {theme.get("trend_direction", "stable")}

**建议**: 根据当前市场数据调整创作策略。
"""
        else:
            # 获取所有题材的市场概览
            response = await db._client.get(
                f"{db._rest_url}/themes",
                params={
                    "select": "name,slug,market_score,success_rate",
                    "order": "market_score.desc",
                },
            )
            response.raise_for_status()
            themes = response.json() or []

            result = ["## 全题材市场概览\n"]

            for theme in themes:
                name = theme.get("name", "N/A")
                score = theme.get("market_score", 0)
                success = theme.get("success_rate", 0)
                result.append(f"- **{name}**: 评分 {score}/100, 成功率 {success}%\\n")

            return "\\n".join(result)

    except Exception as e:
        return f"获取市场趋势失败: {str(e)}"


@tool
async def get_writing_keywords(genre_id: str) -> str:
    """
    Skill: 获取写作关键词。

    Args:
        genre_id: 题材ID

    Returns:
        写作和视觉关键词列表
    """
    db = get_db_service()

    try:
        response = await db._client.get(
            f"{db._rest_url}/themes",
            params={"slug": f"eq.{genre_id}", "select": "name,keywords"},
        )
        response.raise_for_status()
        themes = response.json() or []

        if not themes:
            return f"未找到题材 '{genre_id}'"

        theme = themes[0]
        keywords = theme.get("keywords", {})

        writing_kw = keywords.get("writing", [])
        visual_kw = keywords.get("visual", [])

        return f"""
## {theme["name"]} - 关键词

**写作关键词**: {", ".join(writing_kw) if writing_kw else "N/A"}

**视觉关键词**: {", ".join(visual_kw) if visual_kw else "N/A"}

**使用建议**: 在剧本创作中自然融入这些关键词，保持文风一致性。
"""

    except Exception as e:
        return f"获取关键词失败: {str(e)}"
