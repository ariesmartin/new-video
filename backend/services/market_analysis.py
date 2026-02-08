"""
Market Analysis Service

后台市场分析服务，每日执行搜索并保存结果。
不是 LangGraph 节点，而是独立的后台任务。
"""

from datetime import datetime, timezone
from typing import Any

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

    async def run_daily_analysis(self) -> dict[str, Any]:
        """
        执行每日市场分析

        1. 搜索短剧榜单和趋势
        2. LLM 分析数据
        3. 保存到数据库

        Returns:
            分析结果字典
        """
        logger.info("Starting daily market analysis")

        try:
            # 1. 搜索市场数据
            search_queries = [
                "2026年短剧热度榜 抖音快手",
                "短剧题材趋势 逆袭复仇 现代都市",
                "短剧用户画像 2026",
            ]

            search_results = []
            for query in search_queries:
                try:
                    result = await metaso_search(query)
                    search_results.append({"query": query, "result": result})
                    logger.info("Search completed", query=query)
                except Exception as e:
                    logger.error("Search failed", query=query, error=str(e))

            # 2. LLM 分析
            analysis = await self._analyze_with_llm(search_results)

            # 3. 保存到数据库
            await self._save_analysis(analysis)

            logger.info(
                "Daily market analysis completed", genre_count=len(analysis.get("genres", []))
            )

            return analysis

        except Exception as e:
            logger.error("Daily market analysis failed", error=str(e))
            raise

    async def _analyze_with_llm(self, search_results: list) -> dict:
        """使用 LLM 分析搜索结果"""
        from langchain_core.messages import HumanMessage, SystemMessage

        # 构建搜索上下文
        context = "\n\n".join(
            [f"搜索: {r['query']}\n结果: {r['result'][:500]}..." for r in search_results]
        )

        # 加载 Prompt
        system_prompt = self.prompt_service.get_raw_prompt("market_analyst")

        # 构建消息
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"分析以下市场数据：\n\n{context}"),
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
        """保存分析结果到数据库"""
        try:
            from datetime import datetime, timedelta, timezone

            # 计算有效期（7天）
            valid_until = datetime.now(timezone.utc) + timedelta(days=7)

            # 构建数据
            data = {
                "report_type": "weekly",
                "genres": analysis.get("genres", []),
                "tones": analysis.get("tones", []),
                "insights": analysis.get("insights", ""),
                "target_audience": analysis.get("audience", ""),
                "search_queries": analysis.get("search_queries", []),
                "raw_search_results": analysis.get("raw_results", "")[:5000],  # 限制长度
                "valid_until": valid_until.isoformat(),
                "is_active": True,
            }

            # 插入数据库
            result = await self.db.create_market_report(data)
            logger.info("Market analysis saved", report_id=result.get("id"))

        except Exception as e:
            logger.error("Failed to save market analysis", error=str(e))
            # 保存失败不影响主流程

    async def get_latest_analysis(self) -> dict | None:
        """获取最新的有效市场分析结果"""
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

            # 转换为标准格式
            return {
                "genres": report.get("genres", []),
                "tones": report.get("tones", []),
                "insights": report.get("insights", ""),
                "audience": report.get("target_audience", ""),
                "analyzed_at": report.get("created_at"),
                "report_id": report.get("id"),
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
