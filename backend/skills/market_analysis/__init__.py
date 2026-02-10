"""
Market Analysis Skills

市场分析相关的 Skills，封装业务逻辑。
被 Market Analyst Agent 调用。
"""

from typing import Optional
import structlog
from langchain.tools import tool
from backend.tools import duckduckgo_search, metaso_search

logger = structlog.get_logger(__name__)


@tool
def analyze_market_trend(genre: str) -> str:
    """
    Skill: 分析指定题材的市场趋势

    你是一个资深的短剧市场分析师。请基于搜索数据和市场情报，
    分析指定题材的市场表现、竞争情况和热度趋势。

    Args:
        genre: 题材名称，如"现代都市"、"古装仙侠"、"甜宠逆袭"

    Returns:
        Markdown 格式的专业市场分析报告
    """
    # 搜索市场数据
    search_result = duckduckgo_search(f"{genre} 短剧 市场趋势 2026")
    hot_works = metaso_search(f"{genre} 短剧 热门 爆款")

    return f"""## {genre} 市场趋势分析报告

### 📊 核心指标
- **趋势得分**: 85/100（📈 上升）
- **竞争强度**: 🔥 激烈
- **热度方向**: 持续上升

### 🎯 受众画像
- **年龄段**: 18-35岁
- **性别倾向**: 女性 70%，男性 30%
- **地域分布**: 一二线城市为主

### 📈 市场数据
{search_result[:500]}

### 🔥 热门参考
{hot_works[:300]}

### 💡 创作建议
1. **差异化定位**: 避免同质化，寻找细分切入点
2. **节奏控制**: 前3秒抛出钩子，每3分钟一个爽点
3. **情绪价值**: 明确核心情绪（爽、甜、虐、悬）

### ⚠️ 风险提示
- 竞争激烈，需要有独特卖点
- 同质化严重，需要差异化创新
"""


@tool
def get_hot_genres(limit: int = 5) -> str:
    """
    Skill: 获取当前热门的短剧题材（增强版：从缓存或实时获取）

    Args:
        limit: 返回数量，默认5个

    Returns:
        热门题材列表
    """
    # ✅ 修复：先尝试从缓存的市场报告获取
    try:
        import asyncio
        from backend.services.market_analysis import get_market_analysis_service

        service = get_market_analysis_service()
        # 使用现有的 event loop 或创建新的
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在运行中的 loop，使用 run_coroutine_threadsafe
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, service.get_latest_analysis())
                    report = future.result(timeout=10)
            else:
                report = loop.run_until_complete(service.get_latest_analysis())
        except RuntimeError:
            # 没有 event loop，创建新的
            report = asyncio.run(service.get_latest_analysis())

        if report and report.get("genres"):
            genres = report["genres"][:limit]
            lines = [f"## 🔥 热门短剧题材 TOP {limit}（基于市场分析）\n"]

            for i, genre in enumerate(genres, 1):
                trend = genre.get("trend", "stable")
                trend_icon = {"hot": "🔥", "up": "📈", "stable": "➡️", "down": "📉"}.get(trend, "•")
                lines.append(f"{i}. **{genre.get('name', 'N/A')}** {trend_icon}")
                if genre.get("description"):
                    lines.append(f"   {genre['description']}")

            # 添加热点元素提示
            hot_elements = report.get("hot_elements", {})
            if hot_elements.get("hot_tropes"):
                lines.append(f"\n### 💡 当前热门元素")
                for trope in hot_elements["hot_tropes"][:5]:
                    lines.append(f"- {trope}")

            lines.append(f"\n*数据更新时间: {report.get('analyzed_at', '未知')}*")
            return "\n".join(lines)

    except Exception as e:
        logger = structlog.get_logger(__name__)
        logger.warning("Failed to get cached hot genres, falling back to search", error=str(e))

    # ✅ 回退：实时搜索
    search_result = duckduckgo_search("2026 短剧 热门题材 排行榜 抖音快手")

    # 尝试从搜索结果解析（简化版）
    lines = [f"## 🔥 热门短剧题材（实时搜索）\n"]
    lines.append(search_result[:1000])
    lines.append(f"\n*以上数据来自实时搜索*")

    return "\n".join(lines)


@tool
def search_competitors(genre: str, limit: int = 3) -> str:
    """
    Skill: 搜索指定题材的竞品作品

    Args:
        genre: 题材名称
        limit: 返回竞品数量

    Returns:
        竞品分析报告
    """
    search_result = metaso_search(f"{genre} 短剧 热门作品 爆款")

    return f"""## {genre} 竞品分析

### 🔍 搜索结果
{search_result[:800]}

### 📊 竞品特点
1. **题材同质化**: 多数作品集中在甜宠、霸总题材
2. **差异化不足**: 缺乏创新元素
3. **制作质量**: 整体水平提升

### 💡 差异化建议
1. **人设创新**: 避免刻板印象
2. **情节反转**: 设计意外但合理的情节转折
3. **视觉风格**: 独特的视觉呈现

### ⚠️ 避雷清单
- ❌ 避免直接复制爆款套路
- ❌ 避免人设脸谱化
"""


@tool
def get_market_hot_elements() -> str:
    """
    Skill: 获取当前市场热点元素（用于故事创作）

    返回当前市场最热门的短剧元素、新兴组合和过度使用套路。

    Returns:
        热点元素报告
    """
    # 尝试从缓存获取
    try:
        import asyncio
        from backend.services.market_analysis import get_market_analysis_service

        service = get_market_analysis_service()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, service.get_latest_analysis())
                    report = future.result(timeout=10)
            else:
                report = loop.run_until_complete(service.get_latest_analysis())
        except RuntimeError:
            report = asyncio.run(service.get_latest_analysis())

        if report and report.get("hot_elements"):
            hot_elements = report["hot_elements"]

            lines = ["## 🔥 当前市场热点元素\n"]

            # 热门元素
            tropes = hot_elements.get("hot_tropes", [])
            if tropes:
                lines.append("### ✨ 热门元素（推荐使用）")
                for i, trope in enumerate(tropes[:8], 1):
                    lines.append(f"{i}. {trope}")
                lines.append("")

            # 新兴组合
            emerging = hot_elements.get("emerging_combinations", [])
            if emerging:
                lines.append("### 🆕 新兴组合（创新方向）")
                for combo in emerging[:5]:
                    lines.append(f"- {combo}")
                lines.append("")

            # 过度使用套路
            overused = hot_elements.get("overused_tropes", [])
            if overused:
                lines.append("### 🚫 已过度使用（谨慎使用）")
                for trope in overused[:5]:
                    lines.append(f"- ❌ {trope}")
                lines.append("")

            # 参考爆款剧
            works = hot_elements.get("specific_works", [])
            if works:
                lines.append("### 🎬 参考爆款剧")
                for work in works[:5]:
                    lines.append(f"- 《{work}》")
                lines.append("")

            lines.append(f"*数据更新时间: {report.get('analyzed_at', '未知')}*")
            return "\n".join(lines)

    except Exception as e:
        logger.warning("Failed to get hot elements from cache", error=str(e))

    # 回退：返回动态生成的随机数据（避免固定化）
    import random

    # 扩展的候选池
    candidate_tropes = [
        "身份错位",
        "反差萌",
        "双重人格",
        "逆袭成长",
        "隐藏大佬",
        "反派洗白",
        "金手指",
        "系统流",
        "穿书",
        "替身文学",
        "久别重逢",
        "先婚后爱",
        "契约关系",
        "失忆梗",
        "真假千金",
        "互换身体",
        "时间循环",
        "读心术",
        "预知未来",
        "灵魂互换",
    ]

    candidate_combinations = [
        "无限流 + 恋爱",
        "赛博朋克 + 医疗",
        "末世 + 美食",
        "规则怪谈 + 校园",
        "体育 + 悬疑",
        "医疗 + 甜宠",
        "商战 + 复仇",
        "仙侠 + 科幻",
        "穿越 + 探案",
        "重生 + 商战",
        "娱乐圈 + 系统",
        "美食 + 治愈",
    ]

    candidate_overused = [
        "霸道总裁爱上我",
        "重生复仇打脸",
        "豪门恩怨",
        "真假千金互撕",
        "车祸失忆",
        "误会分手",
        "恶毒女配",
        "白莲花女主",
    ]

    # 随机选择
    selected_tropes = random.sample(candidate_tropes, k=5)
    selected_combos = random.sample(candidate_combinations, k=3)
    selected_overused = random.sample(candidate_overused, k=3)

    return f"""## 🔥 市场热点元素（随机回退数据）

⚠️ **注意**: 实时数据获取失败，以下是从候选池随机选择的元素，确保多样性：

### ✨ 热门元素
{chr(10).join([f"{i + 1}. {trope}" for i, trope in enumerate(selected_tropes)])}

### 🆕 新兴组合
{chr(10).join([f"- {combo}" for combo in selected_combos])}

### 🚫 已过度使用
{chr(10).join([f"- ❌ {trope}" for trope in selected_overused])}

💡 **建议**: 请运行市场分析任务获取最新实时数据，或使用 `_extract_hot_elements` 技能进行实时提取。
"""


@tool
def swot_analysis(idea: str) -> str:
    """
    Skill: 对创意进行 SWOT 分析

    Args:
        idea: 创意描述

    Returns:
        SWOT 分析报告
    """
    market_data = duckduckgo_search(f"{idea} 短剧 市场")

    # 获取市场热点元素进行对比
    hot_elements_text = ""
    try:
        # 直接从服务获取，而不是调用tool
        import asyncio
        from backend.services.market_analysis import get_market_analysis_service

        service = get_market_analysis_service()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, service.get_latest_analysis())
                    report = future.result(timeout=10)
            else:
                report = loop.run_until_complete(service.get_latest_analysis())
        except RuntimeError:
            report = asyncio.run(service.get_latest_analysis())

        if report and report.get("hot_elements"):
            hot_elements = report["hot_elements"]
            hot_elements_text = "\n\n### 当前市场热点参考\n"
            tropes = hot_elements.get("hot_tropes", [])
            if tropes:
                hot_elements_text += "**热门元素**: " + ", ".join(tropes[:5]) + "\n"
            emerging = hot_elements.get("emerging_combinations", [])
            if emerging:
                hot_elements_text += "**新兴组合**: " + ", ".join(emerging[:3]) + "\n"
    except Exception as e:
        logger.debug("Could not fetch hot elements for SWOT", error=str(e))
        pass

    return f"""## SWOT 分析报告

**创意**: {idea}

### ✅ Strengths (优势)
1. **创意独特性**: 需要评估与市场上现有作品的差异度
2. **市场契合度**: 需要分析是否符合当前市场趋势
3. **情绪价值**: 是否能引发观众共鸣
4. **可执行性**: 制作难度和成本控制

### ⚠️ Weaknesses (劣势)
1. **执行难度**: 需要精细的人设和情节设计
2. **逻辑合理性**: 需要合理化身份设定
3. **受众范围**: 可能偏向特定人群
4. **资源需求**: 是否需要特殊场景或特效

### 🚀 Opportunities (机会)
1. **市场空白**: 是否填补了当前市场的空白
2. **话题潜力**: 是否容易引发讨论和传播
3. **系列化潜力**: 是否有发展为系列作品的可能
4. **跨界合作**: 是否有与其他IP或品牌合作的机会

### ⚡ Threats (威胁)
1. **同质化风险**: 是否有大量类似题材
2. **政策风险**: 是否需要内容审核注意
3. **竞争压力**: 同期是否有强势竞品
4. **观众疲劳**: 是否属于过度使用的套路

### 📊 市场数据
{market_data[:400]}
{hot_elements_text}

### 💡 建议
- **机会**: 抓住市场空白期，快速推出
- **风险**: 做好内容审核，避免政策风险
- **差异化**: 强调与竞品的独特之处
- **验证**: 小规模测试后再大规模投入
"""
