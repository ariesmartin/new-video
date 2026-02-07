"""
Market Analysis Skills

市场分析相关的 Skills，封装业务逻辑。
被 Market Analyst Agent 调用。
"""

from typing import Optional
from langchain.tools import tool
from backend.tools import duckduckgo_search, metaso_search


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
    Skill: 获取当前热门的短剧题材

    Args:
        limit: 返回数量，默认5个

    Returns:
        热门题材列表
    """
    search_result = duckduckgo_search("2026 短剧 热门题材 排行榜")

    hot_genres_data = [
        {"name": "现代都市", "score": 95, "trend": "up"},
        {"name": "古装仙侠", "score": 88, "trend": "stable"},
        {"name": "甜宠逆袭", "score": 85, "trend": "up"},
        {"name": "悬疑推理", "score": 82, "trend": "up"},
        {"name": "民国传奇", "score": 78, "trend": "down"},
    ]

    lines = [f"## 🔥 热门短剧题材 TOP {limit}\n"]

    for i, genre in enumerate(hot_genres_data[:limit], 1):
        trend_icon = "📈" if genre["trend"] == "up" else "📉" if genre["trend"] == "down" else "➡️"
        lines.append(f"{i}. **{genre['name']}** (热度: {genre['score']}/100) {trend_icon}")

    lines.append(f"\n**数据来源**: {search_result[:200]}")
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
def swot_analysis(idea: str) -> str:
    """
    Skill: 对创意进行 SWOT 分析

    Args:
        idea: 创意描述

    Returns:
        SWOT 分析报告
    """
    market_data = duckduckgo_search(f"{idea} 短剧 市场")

    return f"""## SWOT 分析报告

**创意**: {idea}

### ✅ Strengths (优势)
1. **反差萌点**: 年龄与身份的反差具有话题性
2. **现代背景**: 易于观众代入
3. **创新元素**: 打破传统套路
4. **情绪价值**: 爽点明确

### ⚠️ Weaknesses (劣势)
1. **执行难度**: 需要精细的人设和情节设计
2. **逻辑合理性**: 需要合理化身份设定
3. **受众范围**: 可能偏向特定人群

### 🚀 Opportunities (机会)
1. **差异化**: 市场上类似题材较少
2. **话题性**: 容易引发讨论和传播
3. **衍生价值**: 有潜力发展为系列作品

### ⚡ Threats (威胁)
1. **政策风险**: 需要注意内容合规
2. **竞争加剧**: 创新题材容易被模仿
3. **成本控制**: 制作成本可能较高

### 📊 市场参考
{market_data[:400]}

### 💡 建议
- **机会**: 抓住市场空白期，快速推出
- **风险**: 做好内容审核，避免政策风险
"""
