"""
方案去重服务

检测新生成的方案是否与历史方案重复，提供去重建议。
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class PlanDeduplicationService:
    """方案去重服务"""

    def __init__(self, db_service=None):
        from backend.services.database import get_db_service

        self.db = db_service or get_db_service()

    async def check_similarity(
        self, user_id: str, new_plan: Dict[str, Any], threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        检查新方案与历史方案的相似度

        Args:
            user_id: 用户ID
            new_plan: 新方案数据
            threshold: 相似度阈值（超过则认为重复）

        Returns:
            {
                "is_duplicate": bool,
                "similarity_score": float,
                "similar_plans": List[Dict],
                "suggestions": List[str]  # 去重建议
            }
        """
        # 1. 获取用户最近生成的方案（30天内）
        recent_plans = await self._get_recent_plans(user_id, days=30)

        if not recent_plans:
            return {
                "is_duplicate": False,
                "similarity_score": 0.0,
                "similar_plans": [],
                "suggestions": [],
            }

        # 2. 计算相似度
        similarities = []
        for plan in recent_plans:
            score = self._calculate_similarity(new_plan, plan)
            similarities.append({"plan": plan, "score": score})

        # 3. 找出最相似的
        similarities.sort(key=lambda x: x["score"], reverse=True)
        max_similarity = similarities[0]["score"] if similarities else 0

        # 4. 判断是否重复
        is_duplicate = max_similarity >= threshold

        # 5. 生成建议
        suggestions = []
        if is_duplicate:
            similar = similarities[0]["plan"]
            suggestions = self._generate_dedup_suggestions(new_plan, similar)

        return {
            "is_duplicate": is_duplicate,
            "similarity_score": max_similarity,
            "similar_plans": [s["plan"] for s in similarities[:3]],
            "suggestions": suggestions,
        }

    def _calculate_similarity(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> float:
        """计算两个方案的相似度（0-1）"""
        scores = []

        # 1. 标题相似度（简单字符串匹配）
        title1 = plan1.get("title", "").lower()
        title2 = plan2.get("title", "").lower()
        if title1 and title2:
            # Jaccard相似度
            set1 = set(title1)
            set2 = set(title2)
            jaccard = len(set1 & set2) / len(set1 | set2) if set1 | set2 else 0
            scores.append(jaccard * 0.2)  # 权重20%

        # 2. 核心元素重叠度
        tropes1 = set(plan1.get("core_tropes", []))
        tropes2 = set(plan2.get("core_tropes", []))
        if tropes1 and tropes2:
            overlap = len(tropes1 & tropes2) / len(tropes1 | tropes2) if tropes1 | tropes2 else 0
            scores.append(overlap * 0.4)  # 权重40%

        # 3. 题材组合相似度
        genres1 = set(plan1.get("genre_combination", []))
        genres2 = set(plan2.get("genre_combination", []))
        if genres1 and genres2:
            genre_overlap = (
                len(genres1 & genres2) / len(genres1 | genres2) if genres1 | genres2 else 0
            )
            scores.append(genre_overlap * 0.3)  # 权重30%

        # 4. 背景设定相似度
        setting1 = plan1.get("background_setting", "").lower()
        setting2 = plan2.get("background_setting", "").lower()
        if setting1 and setting2:
            setting_sim = 1.0 if setting1 == setting2 else 0.0
            scores.append(setting_sim * 0.1)  # 权重10%

        return sum(scores) / len(scores) if scores else 0.0

    def _generate_dedup_suggestions(
        self, new_plan: Dict[str, Any], similar_plan: Dict[str, Any]
    ) -> List[str]:
        """生成去重建议"""
        suggestions = []

        # 1. 替换核心元素
        new_tropes = set(new_plan.get("core_tropes", []))
        similar_tropes = set(similar_plan.get("core_tropes", []))
        common_tropes = new_tropes & similar_tropes

        if common_tropes:
            suggestions.append(f"尝试替换这些核心元素：{', '.join(list(common_tropes)[:3])}")

        # 2. 改变题材组合
        new_genres = set(new_plan.get("genre_combination", []))
        similar_genres = set(similar_plan.get("genre_combination", []))

        if new_genres == similar_genres:
            suggestions.append("尝试完全不同的题材组合，至少更换1个题材")

        # 3. 改变背景设定
        if new_plan.get("background_setting") == similar_plan.get("background_setting"):
            suggestions.append(f"更换背景设定：从'{new_plan.get('background_setting')}'改为其他")

        # 4. 添加创新元素
        suggestions.append("引入1-2个市场上尚未出现的新元素")

        return suggestions

    async def _get_recent_plans(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取用户最近生成的方案"""
        try:
            # 使用数据库服务查询
            recent_plans = await self.db.get_recent_plans(user_id, days=days)
            return recent_plans
        except Exception as e:
            logger.error("Failed to get recent plans", error=str(e))
            return []

    async def save_plan(self, user_id: str, project_id: str, plan_data: Dict[str, Any]):
        """保存生成的方案到历史记录"""
        try:
            # 提取核心元素
            content = plan_data.get("content", "")
            core_tropes = self._extract_tropes_from_content(content)

            # 计算相似度哈希
            similarity_hash = self._calculate_similarity_hash(
                plan_data.get("title", ""), core_tropes, plan_data.get("genres", [])
            )

            # 构建记录
            record = {
                "user_id": user_id,
                "project_id": project_id,
                "plan_title": plan_data.get("title", ""),
                "plan_summary": plan_data.get("summary", ""),
                "core_tropes": json.dumps(core_tropes),
                "genre_combination": json.dumps(plan_data.get("genres", [])),
                "background_setting": plan_data.get("setting", ""),
                "total_episodes": plan_data.get("total_episodes", 80),
                "episode_duration": plan_data.get("episode_duration", 1.5),
                "plan_data": json.dumps(plan_data),
                "similarity_hash": similarity_hash,
                "generated_at": datetime.now().isoformat(),
            }

            # 保存到数据库
            result = await self.db.save_plan_history(record)
            if result:
                logger.info(
                    "Saved plan to history",
                    user_id=user_id,
                    project_id=project_id,
                    title=plan_data.get("title", "")[:50],
                    record_id=result.get("id", "unknown"),
                )
            else:
                logger.warning(
                    "Failed to save plan history", user_id=user_id, project_id=project_id
                )

        except Exception as e:
            logger.error("Failed to save plan", error=str(e))

    def _extract_tropes_from_content(self, content: str) -> List[str]:
        """从方案内容中提取核心元素"""
        # 常见的短剧元素关键词
        common_tropes = [
            "复仇",
            "甜宠",
            "穿越",
            "重生",
            "悬疑",
            "推理",
            "霸总",
            "太奶奶",
            "逆袭",
            "打脸",
            "身份互换",
            "契约婚姻",
            "失忆",
            "误会",
            "守护",
            "暗恋",
            "无限流",
            "末世",
            "规则怪谈",
            "赛博朋克",
            "商战",
            "医疗",
            "体育",
            "美食",
            "仙侠",
            "科幻",
            "古装",
        ]

        found = []
        content_lower = content.lower()
        for trope in common_tropes:
            if trope in content_lower:
                found.append(trope)

        return found[:10]  # 最多返回10个

    def _calculate_similarity_hash(self, title: str, tropes: List[str], genres: List[str]) -> str:
        """计算方案相似度哈希"""
        hash_input = f"{title.lower()}::{json.dumps(sorted(tropes))}::{json.dumps(sorted(genres))}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    async def get_dedup_context_for_prompt(self, user_id: str, days: int = 7) -> str:
        """
        获取去重上下文，用于注入到Prompt中

        Returns:
            去重提示文本
        """
        try:
            recent_plans = await self._get_recent_plans(user_id, days=days)

            if not recent_plans:
                return ""

            # 提取已使用的元素
            used_tropes = set()
            used_combinations = []
            used_titles = []

            for plan in recent_plans[:5]:  # 只取最近5个
                used_tropes.update(plan.get("core_tropes", []))
                used_combinations.append(plan.get("genre_combination", []))
                used_titles.append(plan.get("plan_title", ""))

            # 构建去重上下文
            context = f"""
## 🚫 去重提醒（重新生成时必须遵循）

根据您最近{len(recent_plans)}天内生成的方案，以下元素已被使用过：

**已使用核心元素**：{", ".join(list(used_tropes)[:15])}

**已使用题材组合**：
"""
            for i, combo in enumerate(used_combinations[:3], 1):
                context += f"{i}. {' + '.join(combo)}\n"

            context += """
### 强制去重规则：
1. **严禁**使用与最近3个方案相同的核心元素组合（相似度>70%）
2. **必须**尝试至少1个全新的题材（未在最近方案中使用过）
3. **必须**从市场热点数据中选择未使用过的元素
4. **避免**生成与以下标题相似的方案：
"""
            for title in used_titles[:3]:
                context += f"   - {title}\n"

            context += """
### 创新建议：
- 尝试完全不同的题材组合（如之前用了复仇+甜宠，这次尝试悬疑+美食）
- 更换主角设定（如之前是太奶奶，这次尝试AI机器人或末世幸存者）
- 改变故事背景（如之前是现代都市，这次尝试赛博朋克或无限流副本）
- 引入全新的冲突类型（如规则怪谈式的诡异逻辑）

如果不确定是否重复，请先进行自我检查：
- [ ] 这个方案的标题与之前的完全不同？
- [ ] 核心元素组合与之前<30%重叠？
- [ ] 至少引入1个从未使用过的新题材？
"""

            return context

        except Exception as e:
            logger.error("Failed to get dedup context", error=str(e))
            return ""


# 全局实例
_dedup_service = None


def get_dedup_service() -> PlanDeduplicationService:
    """获取去重服务实例"""
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = PlanDeduplicationService()
    return _dedup_service
