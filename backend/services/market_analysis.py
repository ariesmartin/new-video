"""
Market Analysis Service

后台市场分析服务，每日执行搜索并保存结果。
不是 LangGraph 节点，而是独立的后台任务。
"""

from datetime import datetime, timezone, timedelta
from typing import Any, List
import random
import json

import structlog

from backend.services.model_router import ModelRouter, get_model_router
from backend.services.prompt_service import PromptService, get_prompt_service
from backend.services.database import DatabaseService, get_db_service
from backend.schemas.model_config import TaskType
from backend.tools.metaso_search import metaso_search

logger = structlog.get_logger(__name__)


class MarketAnalysisService:
    """
    市场分析服务

    后台定时任务使用，每日搜索短剧市场趋势并保存。
    """

    def __init__(
        self,
        model_router: ModelRouter = None,
        prompt_service: PromptService = None,
        db_service: DatabaseService = None,
    ):
        self.router = model_router or get_model_router()
        self.prompt_service = prompt_service or get_prompt_service()
        # DatabaseService 已修复 event loop 问题，可以直接缓存
        self.db = db_service or get_db_service()

    async def _get_search_queries(self) -> List[str]:
        """
        动态生成搜索查询，包含基础查询+轮换查询

        策略：
        1. 基础查询（每日必搜）：榜单类
        2. 轮换查询（随机选择）：题材趋势、社会热点、竞品分析
        """
        # 基础查询（每日必搜）
        base_queries = [
            "2026年短剧热度榜 抖音快手 日榜",
            "2026年短剧播放量排行 微信视频号",
            "2026年短剧爆款 小红书推荐",
        ]

        # 题材趋势查询池（轮换）
        genre_query_pool = [
            "2026年短剧新兴题材 无限流 规则怪谈",
            "2026年短剧创新元素 银发 穿越 重生",
            "2026年短剧热门人设 反差萌 身份错位",
            "2026年短剧热门背景 赛博朋克 末世 仙侠",
            "2026年短剧创新案例 爆款分析",
            "2026年短剧黑马作品 逆袭",
            "2026年短剧 niche 小众题材",
        ]

        # 社会热点查询池（轮换）
        social_query_pool = [
            "2026年热门话题 短剧改编",
            "2026年网络流行语 短剧",
            "2026年社会事件 短剧创作",
            "2026年抖音热门挑战 短剧",
            "2026年微博热搜 短剧",
        ]

        # 竞品分析查询池（轮换）
        competitor_query_pool = [
            "2026年短剧爆款剧名 播放量",
            "2026年短剧热门剧 商业模式",
            "2026年短剧创新案例 获奖作品",
            "2026年短剧新锐导演 作品",
            "2026年短剧平台竞争 抖音快手",
        ]

        # 随机选择，确保多样性
        selected_genre = random.sample(genre_query_pool, k=min(2, len(genre_query_pool)))
        selected_social = random.sample(social_query_pool, k=min(1, len(social_query_pool)))
        selected_competitor = random.sample(
            competitor_query_pool, k=min(1, len(competitor_query_pool))
        )

        all_queries = base_queries + selected_genre + selected_social + selected_competitor

        logger.info(
            "Generated search queries",
            base=len(base_queries),
            genre=len(selected_genre),
            social=len(selected_social),
            competitor=len(selected_competitor),
            total=len(all_queries),
        )

        return all_queries

    async def run_daily_analysis(self) -> dict[str, Any]:
        """
        执行每日市场分析

        1. 搜索短剧榜单和趋势
        2. 提取热点元素
        3. LLM 分析数据
        4. 保存到数据库

        Returns:
            分析结果字典（包含热点元素）
        """
        logger.info("Starting daily market analysis")

        try:
            # 1. 搜索市场数据
            search_queries = await self._get_search_queries()

            search_results = []
            for query in search_queries:
                try:
                    result = await metaso_search(query)
                    search_results.append({"query": query, "result": result})
                    logger.info("Search completed", query=query, result_length=len(result))
                except Exception as e:
                    logger.error("Search failed", query=query, error=str(e))

            # 2. 提取热点元素（新增）
            hot_elements = await self._extract_hot_elements(search_results)
            logger.info(
                "Extracted hot elements",
                tropes=len(hot_elements.get("hot_tropes", [])),
                emerging=len(hot_elements.get("emerging_combinations", [])),
                overused=len(hot_elements.get("overused_tropes", [])),
            )

            # 3. LLM 分析（传入热点元素）
            analysis = await self._analyze_with_llm(search_results, hot_elements)

            # 将热点元素加入分析结果
            analysis["hot_elements"] = hot_elements

            # 4. 保存到数据库
            await self._save_analysis(analysis)

            logger.info(
                "Daily market analysis completed",
                genre_count=len(analysis.get("genres", [])),
                hot_tropes_count=len(hot_elements.get("hot_tropes", [])),
            )

            return analysis

        except Exception as e:
            logger.error("Daily market analysis failed", error=str(e))
            raise

    async def _extract_hot_elements(self, search_results: list) -> dict:
        """
        使用LLM从搜索结果中提取具体的热点元素

        提取：热门元素、新兴组合、过度使用套路、具体爆款剧名
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        # 构建完整搜索上下文（增加长度限制到3000字符）
        context = "\n\n".join(
            [f"搜索: {r['query']}\n结果: {r['result'][:3000]}" for r in search_results]
        )

        # 提取提示词（优化版：更好地支持组合创新）
        extract_prompt = f"""你是一个专业的短剧市场数据提取专家。请深度分析以下搜索结果，提取2026年短剧市场的具体热点元素和创新趋势。

搜索结果：
{context}

请提取以下信息（必须返回JSON格式）：
{{
    "hot_tropes": ["元素1", "元素2", ...],  // 提取8-10个当前最热门的单元素（如："身份错位"、"无限流"、"反派洗白"）
    "hot_settings": ["背景1", "背景2", ...],  // 提取5个热门背景设定（如："现代职场"、"末世废墟"）
    "hot_character_types": ["人设1", "人设2", ...],  // 提取8个热门人设类型（如："隐藏大佬"、"双重人格"）
    "emerging_combinations": ["组合1", "组合2", ...],  // 提取5-8个新兴题材/元素组合（如："无限流+甜宠"、"赛博朋克+医疗"）
    "overused_tropes": ["套路1", "套路2", ...],  // 提取5个已过度使用的套路（如："霸道总裁爱上我"、"重生复仇打脸"）
    "specific_works": ["剧名1", "剧名2", ...]  // 提取8-10个具体的爆款短剧名称
}}

重要要求：
1. **元素与组合的区别**：
   - hot_tropes：单个元素（如"穿越"、"甜宠"）
   - emerging_combinations：两个或多个元素的组合（如"穿越+虐恋"、"无限流+恋爱"）
   
2. **组合创新**：
   - 从搜索结果中发现真实存在的题材组合
   - 找出"A题材+B题材"的融合案例
   - 提取那些"意料之外但情理之中"的创新搭配
   
3. **具体案例**：
   - 如果搜索提到《XX剧》，提取剧名和它的题材组合
   - 例如：《穿越到虐恋文看我如何自救》→ 提取为"穿越+虐恋"组合
   
4. **质量要求**：
   - 必须是具体的、可操作的元素
   - 每个元素/组合不超过15个字
   - 优先提取创新元素和组合
   - overused_tropes必须是已经出现多次、观众审美疲劳的套路
   - specific_works必须是真实存在的短剧名称
   - 确保所有信息来自搜索结果，而非编造

只返回JSON，不要其他解释。"""

        try:
            messages = [
                SystemMessage(content="你是一个专业的短剧市场数据提取助手。只返回JSON格式数据。"),
                HumanMessage(content=extract_prompt),
            ]

            model = await self.router.get_model(
                user_id="system",
                task_type=TaskType.MARKET_ANALYST,
                project_id=None,
            )

            response = await model.ainvoke(messages)
            content = response.content

            # 解析JSON
            import re

            # 尝试提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # 清理可能的额外字符
            content = content.strip()
            if content.startswith("{") and content.endswith("}"):
                parsed = json.loads(content)

                # 确保所有字段存在
                return {
                    "hot_tropes": parsed.get("hot_tropes", [])[:10],
                    "hot_settings": parsed.get("hot_settings", [])[:5],
                    "hot_character_types": parsed.get("hot_character_types", [])[:8],
                    "emerging_combinations": parsed.get("emerging_combinations", [])[:5],
                    "overused_tropes": parsed.get("overused_tropes", [])[:5],
                    "specific_works": parsed.get("specific_works", [])[:10],
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Failed to extract hot elements",
                error=error_msg,
            )

        # 如果提取失败，返回随机回退数据
        return self._generate_random_fallback()

    async def _analyze_with_llm(self, search_results: list, hot_elements: dict = {}) -> dict:
        """使用 LLM 分析搜索结果（增强版，包含热点元素）"""
        from langchain_core.messages import HumanMessage, SystemMessage

        # 构建搜索上下文（增加长度到3000字符）
        context = "\n\n".join(
            [f"搜索: {r['query']}\n结果: {r['result'][:3000]}" for r in search_results]
        )

        # 构建热点元素上下文
        hot_context = ""
        if hot_elements:
            hot_context = f"""

## 已提取的市场热点元素（必须参考）

### 🔥 热门元素
{chr(10).join([f"- {trope}" for trope in hot_elements.get("hot_tropes", [])[:8]])}

### 🆕 新兴组合
{chr(10).join([f"- {combo}" for combo in hot_elements.get("emerging_combinations", [])[:5]])}

### 🚫 已过度使用的元素（分析时标明）
{chr(10).join([f"- {trope}" for trope in hot_elements.get("overused_tropes", [])[:5]])}

### 🎬 参考爆款剧
{chr(10).join([f"- 《{work}》" for work in hot_elements.get("specific_works", [])[:5]])}
"""

        # 加载 Prompt
        system_prompt = self.prompt_service.get_raw_prompt("market_analyst")

        # 构建消息
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"分析以下市场数据：\n\n{context}\n\n{hot_context}"),
        ]

        # 调用 LLM
        model = await self.router.get_model(
            user_id="system",  # 系统任务
            task_type=TaskType.MARKET_ANALYST,
            project_id=None,
        )

        response = await model.ainvoke(messages)
        content = response.content

        # 解析 JSON
        return self._parse_analysis(content)

    def _generate_random_fallback(self) -> dict:
        """
        生成随机回退数据（避免硬编码固定化）

        当实时搜索失败时使用，从大的候选池随机选择
        确保每次返回不同的元素组合
        """
        import random

        # 扩展的候选池（确保多样性）
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

        candidate_settings = [
            "现代职场",
            "古代宫廷",
            "末世废墟",
            "赛博都市",
            "民国上海",
            "修仙界",
            "校园青春",
            "豪门世家",
            "娱乐圈",
            "美食街",
            "医院",
            "律所",
            "研究所",
            "军营",
            "异能学院",
        ]

        candidate_characters = [
            "霸总",
            "职场新人",
            "隐藏大佬",
            "反派洗白",
            "腹黑男主",
            "飒爽女主",
            "病娇",
            "奶狗",
            "御姐",
            "小透明",
            "天才少年",
            "废柴逆袭",
            "双重身份",
            "神秘来客",
            "失忆者",
        ]

        candidate_combinations = [
            "无限流+恋爱",
            "赛博朋克+医疗",
            "末世+美食",
            "规则怪谈+校园",
            "体育+悬疑",
            "医疗+甜宠",
            "商战+复仇",
            "仙侠+科幻",
            "穿越+探案",
            "重生+商战",
            "娱乐圈+系统",
            "美食+治愈",
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

        # 随机选择，确保每次返回都不同
        return {
            "hot_tropes": random.sample(candidate_tropes, k=min(6, len(candidate_tropes))),
            "hot_settings": random.sample(candidate_settings, k=min(4, len(candidate_settings))),
            "hot_character_types": random.sample(
                candidate_characters, k=min(6, len(candidate_characters))
            ),
            "emerging_combinations": random.sample(
                candidate_combinations, k=min(4, len(candidate_combinations))
            ),
            "overused_tropes": random.sample(candidate_overused, k=min(4, len(candidate_overused))),
            "specific_works": [],
            "_source": "random_fallback",  # 标记这是回退数据
            "_note": "实时搜索失败，使用随机回退数据。建议重新运行市场分析。",
        }

    def _parse_analysis(self, content: str) -> dict:
        """解析 LLM 返回的分析结果"""
        import json
        import re

        # 尝试提取 JSON
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)

            content_stripped = content.strip()
            if content_stripped.startswith("{") and content_stripped.endswith("}"):
                return json.loads(content_stripped)

            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                return json.loads(match.group())

        except (json.JSONDecodeError, IndexError):
            pass

        # 回退：返回默认
        return {
            "genres": [
                {
                    "id": "urban",
                    "name": "现代都市",
                    "description": "职场、爱情、生活",
                    "trend": "up",
                },
                {
                    "id": "revenge",
                    "name": "逆袭复仇",
                    "description": "打脸、爽文、重生",
                    "trend": "hot",
                },
                {
                    "id": "fantasy",
                    "name": "奇幻仙侠",
                    "description": "修仙、玄幻、系统",
                    "trend": "stable",
                },
            ],
            "tones": ["爽感", "甜宠", "悬疑", "治愈"],
            "insights": "基于当前市场趋势分析",
            "audience": "18-35岁女性用户",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _save_analysis(self, analysis: dict) -> None:
        """保存分析结果到数据库（增强版，包含热点元素）"""
        try:
            from datetime import datetime, timedelta, timezone

            # ✅ 修改：缓存有效期从7天缩短到1天
            valid_until = datetime.now(timezone.utc) + timedelta(days=1)

            # 构建数据（新增 hot_elements 字段）
            data = {
                "report_type": "daily",  # 改为daily，因为每天更新
                "genres": analysis.get("genres", []),
                "tones": analysis.get("tones", []),
                "insights": analysis.get("insights", ""),
                "target_audience": analysis.get("audience", ""),
                "search_queries": analysis.get("search_queries", []),
                "raw_search_results": analysis.get("raw_results", "")[:5000],
                "hot_elements": analysis.get("hot_elements", {}),  # 新增：热点元素
                "valid_until": valid_until.isoformat(),
                "is_active": True,
            }

            # 插入数据库
            result = await self.db.create_market_report(data)
            logger.info(
                "Market analysis saved",
                report_id=result.get("id"),
                valid_until=valid_until.isoformat(),
                hot_tropes_count=len(analysis.get("hot_elements", {}).get("hot_tropes", [])),
            )

        except Exception as e:
            logger.error("Failed to save market analysis", error=str(e))
            # 保存失败不影响主流程

    async def run_quick_analysis(self) -> dict:
        """
        快速市场分析（用于缓存缺失时）

        只搜索2-3个关键查询，快速提取热点元素，不经过完整LLM分析
        耗时：3-5秒（vs 完整分析的10-15秒）
        """
        logger.info("Running quick market analysis...")

        try:
            # 只搜索最关键的2个查询
            quick_queries = [
                "2026年短剧热门元素 爆款",
                "2026年短剧新兴题材 创新",
            ]

            search_results = []
            for query in quick_queries:
                try:
                    result = await metaso_search(query)
                    search_results.append({"query": query, "result": result})
                except Exception as e:
                    logger.warning("Quick search query failed", query=query, error=str(e))

            if not search_results:
                logger.warning("No quick search results, using fallback")
                return self._generate_random_fallback()

            # 快速提取热点元素（不经过LLM，直接解析）
            hot_elements = await self._extract_hot_elements(search_results)

            # 构建简化版分析结果
            quick_analysis = {
                "genres": [
                    {
                        "id": "trending",
                        "name": "当前热门",
                        "description": "基于实时搜索",
                        "trend": "hot",
                    }
                ],
                "tones": ["爽感", "创新", "反转"],
                "insights": "基于快速实时搜索的市场热点",
                "audience": "18-35岁",
                "hot_elements": hot_elements,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "_source": "quick_realtime",  # 标记这是快速实时数据
            }

            logger.info(
                "Quick analysis completed", hot_tropes_count=len(hot_elements.get("hot_tropes", []))
            )

            return quick_analysis

        except Exception as e:
            logger.error("Quick analysis failed", error=str(e))
            # 如果快速分析也失败，返回随机回退
            return self._generate_random_fallback()

    async def get_latest_analysis(self, allow_quick_realtime: bool = True) -> dict | None:
        """
        获取最新的有效市场分析结果（增强版，包含热点元素）

        Args:
            allow_quick_realtime: 如果缓存过期，是否允许触发快速实时搜索（默认True）
        """
        try:
            # 查询最新的有效报告
            report = await self.db.get_latest_market_report()

            if not report:
                logger.info("No cached market report found")
                return None

            # 检查是否过期
            from datetime import datetime, timezone

            valid_until = report.get("valid_until")
            if valid_until:
                if isinstance(valid_until, str):
                    valid_until = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))

                if datetime.now(timezone.utc) > valid_until:
                    logger.info("Cached market report expired", valid_until=valid_until)
                    return None

            # ✅ 转换为标准格式（新增 hot_elements）
            hot_elements = report.get("hot_elements", {})

            return {
                "genres": report.get("genres", []),
                "tones": report.get("tones", []),
                "insights": report.get("insights", ""),
                "audience": report.get("target_audience", ""),
                "hot_elements": hot_elements,  # 新增：热点元素
                "analyzed_at": report.get("created_at"),
                "report_id": report.get("id"),
                "valid_until": valid_until.isoformat() if valid_until else None,
            }

        except Exception as e:
            logger.error("Failed to get cached analysis", error=str(e))
            return None


# 全局服务实例
_market_analysis_service = None


def get_market_analysis_service() -> MarketAnalysisService:
    """获取市场分析服务实例"""
    global _market_analysis_service
    if _market_analysis_service is None:
        _market_analysis_service = MarketAnalysisService()
    return _market_analysis_service
