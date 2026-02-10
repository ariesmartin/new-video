"""
Story Planner Agent - Level 2 故事策划

使用 create_react_agent 创建，Prompt 从文件加载。
需要读取缓存的市场分析报告并注入到 Prompt 中。
"""

from pathlib import Path
from typing import Optional
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.services.market_analysis import get_market_analysis_service
from backend.schemas.model_config import TaskType

# ✅ 使用 Skills
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes,
    get_hooks,
    get_character_archetypes,
    get_writing_keywords,
)
from backend.skills.writing_assistant import (
    get_sensory_guide,
    get_pacing_rules,
    get_trending_combinations,
)
import structlog

logger = structlog.get_logger(__name__)


def _get_background_context(background: str) -> str:
    """
    获取背景设定的上下文描述。

    注意：此函数不再限制AI的题材选择，只提供背景参考信息。
    AI可以自由组合任何题材元素，不受背景限制。
    """
    background_contexts = {
        "现代都市": "背景设定在现代城市，可以包含职场、豪门、校园等元素",
        "古装仙侠": "背景设定在古代或仙侠世界，可以包含宫廷、江湖、修仙等元素",
        "民国传奇": "背景设定在民国时期，可以包含军阀、谍战、宅门等元素",
        "未来科幻": "背景设定在未来或科幻世界，可以包含高科技、星际、末世等元素",
    }
    return background_contexts.get(background, f"背景设定：{background}")


# 保留向后兼容的函数，但不再强制映射
def _genre_to_slug(genre: str) -> Optional[str]:
    """
    【已弃用】不再强制映射题材。
    请使用 _get_background_context() 获取背景信息。
    为了保持兼容性，此函数返回 None，由调用方处理。
    """
    # 返回 None 表示不再强制映射，AI 可以自由选择
    return None


async def _get_all_theme_slugs() -> list[str]:
    """从数据库动态获取所有可用主题的slug列表"""
    try:
        from backend.services.database import get_db_service

        db = get_db_service()
        themes = await db.get_all_themes(active_only=True)
        slugs = [theme["slug"] for theme in themes if theme.get("is_active", True)]
        logger.info(f"Dynamically loaded {len(slugs)} themes from database")
        return slugs
    except Exception as e:
        logger.warning("Failed to load themes from DB, using fallback", error=str(e))
        # 回退方案：返回所有已知主题（硬编码作为fallback）
        return [
            "revenge",
            "romance",
            "suspense",
            "transmigration",
            "family_urban",
            "infinite_flow",
            "apocalypse",
            "rules_horror",
            "cyberpunk",
            "business_war",
            "medical_drama",
            "sports",
            "food_culture",
        ]


async def _load_story_planner_prompt(
    market_report: Optional[dict] = None,
    episode_count: int = 80,
    episode_duration: float = 1.5,
    genre: str = "现代都市",
    setting: str = "modern",
) -> str:
    """从文件加载 Story Planner 的 System Prompt"""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "2_Story_Planner.md"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 Markdown 内容
        lines = content.split("\n")
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith("#"):
                start_idx = i
                break

        prompt = "\n".join(lines[start_idx:]).strip()

        # 注入市场分析报告（如果存在）
        if market_report:
            market_context = _format_market_report(market_report)
            prompt = prompt.replace("{market_report}", market_context)
        else:
            # 使用默认市场数据
            prompt = prompt.replace("{market_report}", _get_default_market_report())

        # 清空融合请求占位符（由 Master Router 处理意图）
        prompt = prompt.replace("{fusion_request}", "")

        # 注入剧集配置信息
        prompt = prompt.replace("{episode_count}", str(episode_count))
        prompt = prompt.replace("{episode_duration}", str(episode_duration))
        # ✅ 重要：genre参数只作为参考，不限制AI的题材选择
        prompt = prompt.replace("{genre}", genre)
        prompt = prompt.replace("{setting}", setting)

        # ✅ 注入主题库数据 - 动态加载所有主题供AI自由组合
        try:
            # 动态获取所有主题slug
            all_theme_slugs = await _get_all_theme_slugs()

            # ✅ 随机选择5-8个主题加载（增加多样性，避免总是加载全部）
            import random

            num_themes = random.randint(5, min(8, len(all_theme_slugs)))
            selected_slugs = random.sample(all_theme_slugs, k=num_themes)

            # ✅ 加载选中题材的完整数据
            all_themes_context = []
            for slug in selected_slugs:
                try:
                    theme_context = await load_genre_context.ainvoke({"genre_id": slug})
                    all_themes_context.append(f"\n{'=' * 50}\n{theme_context}\n{'=' * 50}")
                except Exception as e:
                    logger.warning(f"Failed to load theme {slug}", error=str(e))
                    continue

            if all_themes_context:
                full_theme_data = "\n".join(all_themes_context)
                # ✅ 显示全部主题列表，但只详细加载选中部分
                available_themes_info = f"""
## 📚 题材库信息

### 全部可用题材（{len(all_theme_slugs)}个）
{", ".join(all_theme_slugs)}

### 详细加载的题材（{len(selected_slugs)}个）
以下题材的完整信息已加载，供您优先参考：
{", ".join(selected_slugs)}

**说明**：您可以选择任意2-3个题材进行融合创新。如果需要了解其他未加载题材的详细信息，可以调用 `load_genre_context()` 工具获取。

### 题材选择建议
1. **热门题材**（market_score > 85）：revenge, transmigration, infinite_flow, romance, rules_horror
2. **新兴题材**（market_score 75-85）：cyberpunk, business_war, medical_drama, sports, food_culture
3. **推荐策略**：选择1个热门 + 1个新兴 + 1个创新元素
"""
                prompt = prompt.replace(
                    "{theme_library_data}", available_themes_info + full_theme_data
                )
                logger.info(
                    "Injected themes library data",
                    total_themes=len(all_theme_slugs),
                    loaded_themes=len(all_themes_context),
                    selected_slugs=selected_slugs,
                )
            else:
                prompt = prompt.replace(
                    "{theme_library_data}",
                    "## 题材库\n系统包含13大题材，包括复仇逆袭、甜宠恋爱、悬疑推理、穿越重生、家庭伦理、无限流、末世求生、规则怪谈、赛博朋克、职场商战、医疗剧、体育竞技、美食文化等。",
                )

            # 清空跨主题占位符（已整合到主数据中）
            prompt = prompt.replace("{all_themes_data}", "")

        except Exception as e:
            logger.warning("Failed to load theme library", error=str(e))
            prompt = prompt.replace(
                "{theme_library_data}",
                "## 题材库\n系统包含13大题材，包括复仇逆袭、甜宠恋爱、悬疑推理、穿越重生、家庭伦理、无限流、末世求生、规则怪谈、赛博朋克、职场商战、医疗剧、体育竞技、美食文化等。",
            )
            prompt = prompt.replace("{all_themes_data}", "")

        # 注入推荐元素 - 从所有主题中随机选择，增加多样性
        try:
            import random

            # ✅ 从所有主题中动态获取并随机选择2-3个，混合推荐
            all_theme_slugs = await _get_all_theme_slugs()
            selected_themes = random.sample(all_theme_slugs, k=min(3, len(all_theme_slugs)))
            all_tropes = []
            for theme in selected_themes:
                try:
                    tropes = await get_tropes.ainvoke({"genre_id": theme, "limit": 3})
                    # ✅ Fix: 确保 tropes 是字符串类型
                    if isinstance(tropes, list):
                        tropes = "\n".join(str(t) for t in tropes)
                    elif not isinstance(tropes, str):
                        tropes = str(tropes)
                    if tropes and "错误" not in tropes:
                        all_tropes.append(f"【{theme}】{tropes}")
                except Exception as e:
                    logger.warning(f"Failed to get tropes for {theme}", error=str(e))
                    continue

            if all_tropes:
                combined_tropes = "\n\n".join(all_tropes)
                prompt = prompt.replace("{recommended_tropes}", combined_tropes)
                logger.info("Injected mixed tropes from multiple themes", themes=selected_themes)
            else:
                prompt = prompt.replace(
                    "{recommended_tropes}", "调用 `get_tropes()` 获取推荐元素。"
                )
        except Exception as e:
            logger.warning("Failed to load tropes", error=str(e))
            prompt = prompt.replace("{recommended_tropes}", "调用 `get_tropes()` 获取推荐元素。")

        # 注入市场趋势 - 获取所有题材的市场概览
        try:
            from backend.skills.theme_library import get_market_trends

            trends = await get_market_trends.ainvoke({})  # 不传genre_id获取所有题材概览
            prompt = prompt.replace("{market_trends}", trends)
        except Exception as e:
            logger.warning("Failed to load market trends", error=str(e))
            prompt = prompt.replace("{market_trends}", "调用 `get_market_trends()` 获取市场数据。")

        logger.debug(
            "Loaded Story Planner prompt from file",
            path=str(prompt_path),
            episode_count=episode_count,
            episode_duration=episode_duration,
            genre=genre,
        )
        return prompt

    except Exception as e:
        logger.error("Failed to load Story Planner prompt", error=str(e))
        return """你是短剧故事策划专家。基于市场趋势生成3个不同维度的故事方案。"""


def _format_market_report(report: dict) -> str:
    """格式化市场分析报告为 Prompt 可用的字符串（软性引导版）"""
    lines = ["## 💡 市场趋势参考（创意建议）"]

    # ✅ 优化：以软性引导方式呈现热点元素
    hot_elements = report.get("hot_elements", {})
    if hot_elements:
        lines.append("\n### 🔥 当前市场热门趋势（供参考）")

        # 热门元素
        tropes = hot_elements.get("hot_tropes", [])
        if tropes:
            lines.append("\n**近期观众关注的元素**（可作为创意灵感）：")
            for i, trope in enumerate(tropes[:8], 1):
                lines.append(f"{i}. {trope}")

        # 热门背景
        settings = hot_elements.get("hot_settings", [])
        if settings:
            lines.append("\n**受欢迎的故事背景**：")
            for setting in settings[:5]:
                lines.append(f"- {setting}")

        # 热门人设
        characters = hot_elements.get("hot_character_types", [])
        if characters:
            lines.append("\n**讨喜的角色人设**：")
            for char in characters[:6]:
                lines.append(f"- {char}")

        # 新兴组合
        emerging = hot_elements.get("emerging_combinations", [])
        if emerging:
            lines.append("\n**🆕 新兴组合**（创新方向，推荐尝试）：")
            for combo in emerging[:5]:
                lines.append(f"- {combo}")

        # 过度使用的套路
        overused = hot_elements.get("overused_tropes", [])
        if overused:
            lines.append("\n**🚫 已过度使用**（谨慎使用或避免）：")
            for trope in overused[:5]:
                lines.append(f"- ❌ {trope}")

        # 参考爆款剧
        works = hot_elements.get("specific_works", [])
        if works:
            lines.append("\n**🎬 参考爆款剧**（了解市场热点）：")
            for work in works[:5]:
                lines.append(f"- 《{work}》")

        # 添加创意建议（软性引导）
        lines.append("\n" + "=" * 50)
        lines.append("💡 **创意建议**（参考而非限制）：")
        lines.append("• 融合1-2个市场热点元素，可能提升观众接受度")
        lines.append("• 尝试新兴组合，创造差异化的故事体验")
        if overused:
            lines.append("• 【已过度使用】的元素建议谨慎使用或增加创新 twist")
        lines.append("• 参考【爆款剧】了解当前市场偏好，但不必模仿")
        lines.append("• **最重要的是：保持创意独特性！**")
        lines.append("=" * 50)

    # 原有的题材趋势
    genres = report.get("genres", [])
    if genres:
        lines.append("\n### 热门题材趋势")
        for g in genres:
            trend_emoji = {"hot": "🔥", "up": "📈", "stable": "➡️", "down": "📉"}.get(
                g.get("trend"), "•"
            )
            lines.append(f"{trend_emoji} {g.get('name', 'N/A')}: {g.get('description', '')}")

    # 添加调性
    tones = report.get("tones", [])
    if tones:
        lines.append(f"\n### 推荐调性\n{', '.join(tones)}")

    # 添加洞察
    insights = report.get("insights", "")
    if insights:
        lines.append(f"\n### 市场洞察\n{insights}")

    # 添加受众
    audience = report.get("audience", "")
    if audience:
        lines.append(f"\n### 目标受众\n{audience}")

    return "\n".join(lines)


def _get_default_market_report() -> str:
    """获取默认市场报告（当缓存不存在时使用）"""
    return """## 默认市场参考
- 逆袭复仇题材持续热门
- 现代都市爱情稳定需求
- 用户偏好：快节奏、强情绪、反套路
"""


async def create_story_planner_agent(
    user_id: str,
    project_id: Optional[str] = None,
    episode_count: int = 80,
    episode_duration: float = 1.5,
    genre: str = "现代都市",
    setting: str = "modern",
    is_regenerate: bool = False,
    variation_seed: Optional[int] = None,
):
    """
    创建 Story Planner Agent

    🌡️ 温度建议（Temperature）:
    - 首次生成：建议使用 temperature=0.85-0.9
      平衡创意性和合理性，适合跨题材融合

    - 重新生成（regenerate）：建议使用 temperature=0.9-0.95
      更高的发散性，确保与上次生成明显不同

    - 普通任务：temperature=0.7（默认）

    请在模型映射配置中调整 Story Planner 任务的 temperature 参数。
    """
    # 1. 获取缓存的市场分析报告
    try:
        market_service = get_market_analysis_service()
        market_report = await market_service.get_latest_analysis()
        logger.info(
            "Loaded market report for Story Planner",
            has_report=bool(market_report),
            user_id=user_id,
        )

        # 如果没有缓存，创建一个提示信息返回给用户
        if not market_report:
            logger.warning("No market report cache found")
            # 返回一个特殊的消息，让前端知道缺少缓存
            from langchain_core.messages import AIMessage

            return {
                "messages": [
                    AIMessage(
                        content="⚠️ **系统提示**：市场分析报告尚未生成。请联系管理员先执行市场分析缓存任务，或稍后再试。"
                    )
                ],
                "story_plans": "",
                "last_successful_node": "story_planner_no_cache",
            }
    except Exception as e:
        logger.error("Failed to load market report", error=str(e))
        # 发生错误时返回错误信息
        from langchain_core.messages import AIMessage

        return {
            "messages": [
                AIMessage(content=f"⚠️ **系统错误**：无法加载市场分析报告。错误信息：{str(e)}")
            ],
            "story_plans": "",
            "last_successful_node": "story_planner_error",
        }

    # 2. 获取去重上下文（如果是重新生成）
    dedup_context = ""
    if is_regenerate:
        try:
            from backend.services.plan_deduplication import get_dedup_service

            dedup_service = get_dedup_service()
            dedup_context = await dedup_service.get_dedup_context_for_prompt(user_id, days=7)
            if dedup_context:
                logger.info("Loaded dedup context for regeneration", user_id=user_id)
        except Exception as e:
            logger.warning("Failed to load dedup context", error=str(e))

    # 3. 获取配置好的模型
    router = get_model_router()
    model = await router.get_model(
        user_id=user_id, task_type=TaskType.STORY_PLANNER, project_id=project_id
    )

    # 4. 加载基础prompt
    base_prompt = await _load_story_planner_prompt(
        market_report=market_report,
        episode_count=episode_count,
        episode_duration=episode_duration,
        genre=genre,
        setting=setting,
    )

    # 5. 如果有去重上下文，追加到prompt
    if dedup_context:
        base_prompt = base_prompt + "\n\n" + dedup_context

    # 6. 创建 Agent（使用 Skills）
    agent = create_react_agent(
        model=model,
        tools=[
            # ✅ Theme Library Skills
            load_genre_context,  # 加载题材上下文
            get_tropes,  # 获取推荐元素
            get_hooks,  # 获取钩子模板
            get_character_archetypes,  # 获取角色原型
            get_writing_keywords,  # 获取写作关键词
            # ✅ Writing Assistant Skills
            get_sensory_guide,  # 获取五感指导
            get_pacing_rules,  # 获取节奏规则
            get_trending_combinations,  # 获取热门组合
        ],
        prompt=base_prompt,
    )

    return agent


# 导出
__all__ = ["create_story_planner_agent"]
