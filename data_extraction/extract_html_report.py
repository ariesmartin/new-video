#!/usr/bin/env python3
"""
Deep Research HTML 报告提取工具
将HTML格式的研究报告转换为结构化的JSON数据
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class StageFormula:
    """四阶段公式"""

    stage_name: str
    episodes: str
    task: str
    key_elements: List[str]


@dataclass
class TropeElement:
    """爆款元素"""

    name: str
    score: int
    description: str = ""
    usage_timing: str = ""


@dataclass
class BenchmarkExample:
    """标杆案例"""

    title: str
    achievements: str
    description: str = ""


@dataclass
class GenreData:
    """题材数据"""

    slug: str
    name: str
    name_en: str
    category: str
    description: str
    summary: str
    core_formula: Dict[str, Any]
    tropes: List[TropeElement]
    examples: List[BenchmarkExample]
    keywords: Dict[str, List[str]]
    market_score: float
    success_rate: float


class HTMLReportExtractor:
    """HTML报告提取器"""

    def __init__(self, html_content: str):
        self.html = html_content
        self.data = {
            "metadata": {
                "version": "1.0.0",
                "extracted_at": datetime.now().isoformat(),
                "source": "Deep Research Report",
            },
            "genres": [],
            "tropes": [],
            "hooks": [],
            "examples": [],
            "market_insights": {},
        }

    def extract_all(self) -> Dict:
        """提取所有数据"""
        self.extract_genres()
        self.extract_market_insights()
        return self.data

    def extract_genres(self):
        """提取5大核心题材数据"""

        # 复仇逆袭
        revenge = GenreData(
            slug="revenge",
            name="复仇逆袭",
            name_en="Revenge & Comeback",
            category="drama",
            description="主角遭受不公，通过努力或隐藏身份实现逆袭打脸",
            summary="悲情开局，隐忍蓄力，层层反击，最终复仇成功",
            core_formula={
                "setup": {
                    "episodes": "第1-5集（10-15%）",
                    "task": "悲情渲染与仇恨种子埋设",
                    "key_elements": ["至亲被害", "财产被夺", "当众羞辱", "信任崩塌"],
                    "emotional_goal": "让观众产生强烈同情和愤怒",
                    "avoid": "不要过度虐待主角（不超过3集无反击）",
                },
                "rising": {
                    "episodes": "第6-30集（30-40%）",
                    "task": "隐忍蓄力与身份/能力提升",
                    "key_elements": ["隐藏身份", "获取金手指", "建立盟友", "小试牛刀"],
                    "pacing": "每3集一个小打脸，保持爽感",
                    "tension_building": "逐渐揭露主角真实实力的线索",
                },
                "climax": {
                    "episodes": "第31-70集（40-50%）",
                    "task": "层层反击与终极对决",
                    "key_elements": ["身份揭露", "证据公开", "权力碾压", "当众打脸"],
                    "satisfaction_curve": "身份揭露→打脸1→打脸2→打脸3（递进式）",
                    "visual_requirements": "必须使用特写、慢动作、强烈对比",
                },
                "resolution": {
                    "episodes": "第71-80+集（10-15%）",
                    "task": "复仇完成与新身份确立",
                    "key_elements": ["反派下场", "情感收束", "主题升华", "新生活开始"],
                    "avoid": "圣母原谅（主角必须彻底胜利）",
                },
            },
            tropes=[
                TropeElement(
                    "隐藏大佬/扮猪吃虎", 95, "表面是底层，实则是顶层大佬", "贯穿全剧"
                ),
                TropeElement(
                    "身份揭露/当众打脸",
                    90,
                    "真实身份在关键时刻暴露，震惊全场",
                    "第10-15集",
                ),
                TropeElement(
                    "法律复仇/智取型", 92, "通过法律手段或智慧复仇，非暴力", "第20-40集"
                ),
                TropeElement(
                    "金手指/系统绑定", 88, "获得特殊能力或系统辅助", "第3-5集"
                ),
            ],
            examples=[
                BenchmarkExample(
                    "《黑莲花上位手册》",
                    "24小时充值破2000万",
                    "因极端暴力被下架，但商业成功不可否认",
                ),
                BenchmarkExample(
                    "《幸得相遇离婚时》", "分账8000万创纪录", "前5秒留存率62%，行业标杆"
                ),
            ],
            keywords={
                "writing": ["红眼", "掐腰", "居高临下", "冷笑", "颤抖", "咬牙", "攥拳"],
                "visual": [
                    "破碎感",
                    "逆光",
                    "高对比",
                    "权力象征",
                    "阴影",
                    "破碎的玻璃",
                ],
            },
            market_score=95.5,
            success_rate=88.0,
        )

        # 甜宠恋爱
        romance = GenreData(
            slug="sweet_romance",
            name="甜宠恋爱",
            name_en="Sweet Romance",
            category="romance",
            description="高糖度恋爱故事，强调宠溺、保护和甜蜜互动",
            summary="从相遇到暧昧到确认关系，全程发糖的甜蜜旅程",
            core_formula={
                "setup": {
                    "episodes": "第1-8集",
                    "task": "快速建立相遇场景",
                    "key_elements": ["职业差异", "意外事件", "一见钟情", "被迫同居"],
                    "emotional_goal": "建立好感，制造心动瞬间",
                },
                "rising": {
                    "episodes": "第9-35集",
                    "task": "建立关系纽带",
                    "key_elements": ["契约婚姻", "同居场景", "护短行为", "暧昧推拉"],
                    "pacing": "每3-5集一个糖点，保持甜度",
                },
                "climax": {
                    "episodes": "第36-65集",
                    "task": "制造重大考验",
                    "key_elements": ["重大误会", "外部阻力", "追妻火葬场", "双向奔赴"],
                    "satisfaction_curve": "误会→解释→和解→确认关系",
                },
                "resolution": {
                    "episodes": "第66-80+集",
                    "task": "消除障碍，确认关系",
                    "key_elements": ["求婚婚礼", "公开关系", "共同事业", "甜蜜日常"],
                    "avoid": "狗血误会（不能超过1集不解开）",
                },
            },
            tropes=[
                TropeElement(
                    "契约婚姻/假戏真做", 94, "被迫结婚，但在相处中产生真情", "第5-15集"
                ),
                TropeElement(
                    "追妻/追夫火葬场", 93, "前期冷漠，后期疯狂追求", "第30-50集"
                ),
                TropeElement("双向暗恋", 90, "双方都喜欢但都不敢表白", "第10-25集"),
                TropeElement("霸道总裁爱上我", 88, "高富帅爱上平凡女孩", "贯穿全剧"),
            ],
            examples=[
                BenchmarkExample(
                    "《我在八零年代当后妈》", "分账破亿", "穿越+甜宠+年代，创新组合"
                ),
            ],
            keywords={
                "writing": ["宠溺", "温柔", "耳语", "拥抱", "额头吻", "护短", "独占欲"],
                "visual": ["柔光", "暖色调", "花瓣", "阳光", "暖色滤镜", "柔焦"],
            },
            market_score=88.0,
            success_rate=85.0,
        )

        # 悬疑推理
        mystery = GenreData(
            slug="mystery",
            name="悬疑推理",
            name_en="Mystery & Suspense",
            category="thriller",
            description="谜题设计、悬念维持、逻辑严密的推理故事",
            summary="抛出谜团，多线调查，层层反转，最终揭晓真相",
            core_formula={
                "setup": {
                    "episodes": "第1-6集",
                    "task": "抛出核心谜团",
                    "key_elements": ["离奇案件", "关键符号", "多视角碎片", "悬念建立"],
                    "emotional_goal": "激发好奇心和探索欲",
                },
                "rising": {
                    "episodes": "第7-30集",
                    "task": "多线推进调查",
                    "key_elements": [
                        "新嫌疑人",
                        "红鲱鱼误导",
                        "关系网展开",
                        "线索交织",
                    ],
                    "pacing": "每3-5集一个新线索或误导",
                },
                "climax": {
                    "episodes": "第31-60集",
                    "task": "核心谜题解答",
                    "key_elements": ["核心证据", "真凶反转", "动机解读", "真相揭露"],
                    "satisfaction_curve": "线索回收→真相揭露→动机解释",
                },
                "resolution": {
                    "episodes": "第61-80+集",
                    "task": "完整解答谜题",
                    "key_elements": ["伏笔回收", "主题升华", "开放式结局", "人物归宿"],
                    "avoid": "逻辑漏洞（所有线索必须有解释）",
                },
            },
            tropes=[
                TropeElement(
                    "符号隐喻系统", 93, "如《隐秘的角落》笛卡尔符号", "贯穿全剧"
                ),
                TropeElement("多螺旋叙事", 90, "不同线索如螺旋交织", "全剧结构"),
                TropeElement(
                    "不可靠叙述者", 88, "主角或旁白信息有限或误导", "关键反转"
                ),
                TropeElement("时间线诡计", 85, "非线性叙事制造悬念", "中段使用"),
            ],
            examples=[
                BenchmarkExample(
                    "《隐秘的角落》", "现象级爆款", "笛卡尔符号系统，多螺旋叙事典范"
                ),
            ],
            keywords={
                "writing": ["谜团", "线索", "反转", "真相", "悬疑", "推理", "揭秘"],
                "visual": ["冷色调", "阴影", "特写", "快速剪辑", "暗调", "紧张氛围"],
            },
            market_score=82.0,
            success_rate=78.0,
        )

        # 穿越重生
        transmigration = GenreData(
            slug="transmigration",
            name="穿越重生",
            name_en="Transmigration & Rebirth",
            category="fantasy",
            description="主角穿越到古代或重生回到过去，利用现代知识改变命运",
            summary="死亡/穿越→适应新世界→运用现代知识→改变命运→选择归留",
            core_formula={
                "setup": {
                    "episodes": "第1-5集",
                    "task": "完成死亡-穿越-觉醒",
                    "key_elements": [
                        "现代死亡",
                        "穿越触发",
                        "新身份认知",
                        "新世界规则",
                    ],
                    "emotional_goal": "建立身份落差和期待感",
                },
                "rising": {
                    "episodes": "第6-25集",
                    "task": "探索新世界规则",
                    "key_elements": ["世界观获取", "关键人物", "首次金手指", "小冲突"],
                    "pacing": "逐渐展示现代知识的威力",
                },
                "climax": {
                    "episodes": "第26-60集",
                    "task": "运用现代知识改变命运",
                    "key_elements": [
                        "现代知识降维",
                        "历史事件干预",
                        "身份地位提升",
                        "敌人打脸",
                    ],
                    "satisfaction_curve": "小成功→大成功→身份确立",
                },
                "resolution": {
                    "episodes": "第61-80+集",
                    "task": "处理归留抉择",
                    "key_elements": ["回归机会", "情感羁绊", "身份整合", "最终选择"],
                    "avoid": "强行回到现代（除非必要）",
                },
            },
            tropes=[
                TropeElement(
                    "系统绑定/任务驱动", 94, "系统发布任务，奖励能力", "第2-3集"
                ),
                TropeElement(
                    "读心术/心声外泄", 91, "2025新趋势：全家偷听心声", "第5-10集"
                ),
                TropeElement(
                    "现代知识降维", 88, "用现代知识在古代/过去取得优势", "贯穿全剧"
                ),
                TropeElement("历史人物互动", 85, "与真实历史人物产生交集", "中段使用"),
            ],
            examples=[
                BenchmarkExample(
                    "《全家偷听我心声》",
                    "2025新趋势代表",
                    "从个人逆袭扩展到家庭共同成长",
                ),
            ],
            keywords={
                "writing": ["穿越", "重生", "现代", "古代", "金手指", "系统", "心声"],
                "visual": ["古今对比", "时空扭曲", "系统界面", "现代服装", "古装"],
            },
            market_score=90.0,
            success_rate=86.0,
        )

        # 家庭伦理/都市现实
        family = GenreData(
            slug="family",
            name="家庭伦理",
            name_en="Family & Urban Reality",
            category="drama",
            description="聚焦家庭关系、代际冲突、都市现实问题的短剧",
            summary="矛盾潜伏→冲突爆发→危机顶点→和解/重建",
            core_formula={
                "setup": {
                    "episodes": "第1-10集",
                    "task": "铺陈关系网络，埋下矛盾种子",
                    "key_elements": ["代际差异", "财产隐患", "婚姻张力", "职场压力"],
                    "emotional_goal": "建立代入感和共鸣",
                },
                "rising": {
                    "episodes": "第11-40集",
                    "task": "矛盾公开化，冲突升级",
                    "key_elements": ["遗产争夺", "赡养纠纷", "职场PUA", "婚姻危机"],
                    "pacing": "每5-8集一个冲突高潮",
                },
                "climax": {
                    "episodes": "第41-65集",
                    "task": "冲突达到顶点",
                    "key_elements": ["离婚断绝", "失业崩塌", "健康危机", "关系破裂"],
                    "satisfaction_curve": "危机→觉醒→改变",
                },
                "resolution": {
                    "episodes": "第66-80+集",
                    "task": "完成个人成长，重建关系",
                    "key_elements": ["自我和解", "关系修复", "新生活方式", "主题升华"],
                    "avoid": "强行大团圆（要真实）",
                },
            },
            tropes=[
                TropeElement("职场PUA/反PUA", 90, "职场不公与反抗", "第10-30集"),
                TropeElement("婆媳矛盾/和解", 88, "传统家庭冲突", "贯穿全剧"),
                TropeElement("重组家庭张力", 85, "继父母、继子女关系", "第15-40集"),
                TropeElement("养老困境", 82, "赡养老人引发的家庭矛盾", "第20-50集"),
            ],
            examples=[
                BenchmarkExample(
                    "《杜小慧》", "话题营销典范", "#职场PUA有多隐蔽# 48小时阅读32亿"
                ),
            ],
            keywords={
                "writing": ["家庭", "矛盾", "和解", "成长", "现实", "职场", "代际"],
                "visual": ["日常场景", "烟火气", "菜市场", "社区医院", "家庭餐桌"],
            },
            market_score=75.0,
            success_rate=72.0,
        )

        # 转换所有题材为字典并添加到数据
        for genre in [revenge, romance, mystery, transmigration, family]:
            genre_dict = asdict(genre)
            # 转换dataclass列表为字典列表
            genre_dict["tropes"] = [asdict(t) for t in genre.tropes]
            genre_dict["examples"] = [asdict(e) for e in genre.examples]
            self.data["genres"].append(genre_dict)

            # 同时添加到tropes列表（全局）
            for trope in genre.tropes:
                self.data["tropes"].append(
                    {
                        "genre_slug": genre.slug,
                        "genre_name": genre.name,
                        **asdict(trope),
                    }
                )

            # 添加到examples列表（全局）
            for example in genre.examples:
                self.data["examples"].append(
                    {
                        "genre_slug": genre.slug,
                        "genre_name": genre.name,
                        **asdict(example),
                    }
                )

    def extract_market_insights(self):
        """提取市场洞察数据"""
        self.data["market_insights"] = {
            "overview": {
                "market_size_2024": "504.4亿元",
                "market_size_2025_forecast": "634亿元",
                "user_count_2024": "6.62亿",
                "user_count_2025_forecast": "6.96亿",
                "growth_rate": "25.7%",
            },
            "key_findings": [
                "情绪先行优于逻辑完备——短剧本质是情绪生意",
                "信息差是爽感核心机制——身份揭露、能力隐藏",
                "钩子密度决定免费模式成败——15秒冲突、30秒推进",
                "免费模式以66.3%占比成为主流",
                "头部效应加剧——仅1.38%短剧贡献18%总热度值",
            ],
            "genre_rankings": [
                {
                    "rank": 1,
                    "genre": "revenge",
                    "heat_score": 95.5,
                    "market_share": "25%",
                },
                {
                    "rank": 2,
                    "genre": "transmigration",
                    "heat_score": 90.0,
                    "market_share": "20%",
                },
                {
                    "rank": 3,
                    "genre": "sweet_romance",
                    "heat_score": 88.0,
                    "market_share": "18%",
                },
                {
                    "rank": 4,
                    "genre": "mystery",
                    "heat_score": 82.0,
                    "market_share": "15%",
                },
                {
                    "rank": 5,
                    "genre": "family",
                    "heat_score": 75.0,
                    "market_share": "12%",
                },
            ],
            "trending_combinations": [
                {
                    "name": "复仇+甜宠",
                    "genres": ["revenge", "sweet_romance"],
                    "heat_score": 92,
                    "example": "《我在八零年代当后妈》",
                },
                {
                    "name": "穿越+系统",
                    "genres": ["transmigration"],
                    "heat_score": 91,
                    "example": "《全家偷听我心声》",
                },
                {
                    "name": "悬疑+现实",
                    "genres": ["mystery", "family"],
                    "heat_score": 85,
                    "example": "《隐秘的角落》",
                },
            ],
        }

    def extract_hook_templates(self):
        """提取钩子模板"""
        hooks = [
            {
                "type": "situation",
                "name": "极限羞辱",
                "template": "主角正在遭受[羞辱类型]，倒计时[3,2,1]即将[反击方式]",
                "variables": {
                    "羞辱类型": [
                        "被当众退婚",
                        "被经理泼咖啡",
                        "被亲戚嘲讽",
                        "被同学霸凌",
                    ],
                    "反击方式": ["暴露真实身份", "展示隐藏实力", "神秘人物出场"],
                },
                "effectiveness_score": 95,
                "psychology": "利用观众对不公的愤怒和对反转的期待",
                "applicable_genres": ["revenge"],
                "duration": "前30秒",
                "examples": [
                    {
                        "scenario": "被当众退婚",
                        "hook_text": "林家当众退婚，羞辱叶辰不配。叶辰冷笑：'三年之期未到，你们林家高攀不起。'",
                        "effectiveness": "极高",
                    }
                ],
            },
            {
                "type": "question",
                "name": "悬念提问",
                "template": "[反常识陈述/直接提问]，引发观众好奇",
                "variables": {
                    "提问方式": [
                        "她竟然是我未来的婆婆？",
                        "这个乞丐竟然是 billionaire？",
                    ]
                },
                "effectiveness_score": 88,
                "psychology": "信息差引发好奇心",
                "applicable_genres": ["sweet_romance", "revenge"],
                "duration": "前3秒",
                "examples": [],
            },
            {
                "type": "visual",
                "name": "视觉奇观",
                "template": "展示[违背常理的画面/极端对比]，立即抓住眼球",
                "variables": {
                    "奇观类型": [
                        "古代皇帝拿出iPhone",
                        "丧尸排队买咖啡",
                        "少女跪在棺材前眼神沧桑",
                    ]
                },
                "effectiveness_score": 90,
                "psychology": "违和感和陌生化制造猎奇",
                "applicable_genres": ["transmigration", "mystery"],
                "duration": "前3秒",
                "examples": [],
            },
        ]

        self.data["hooks"] = hooks


def save_json(data: Dict, output_path: str):
    """保存JSON文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据已保存到: {output_path}")


def main():
    """主函数"""
    print("🚀 开始提取Deep Research报告数据...")

    # 创建提取器（这里可以传入实际的HTML内容）
    # 目前使用内置的数据结构
    extractor = HTMLReportExtractor("")

    # 提取所有数据
    data = extractor.extract_all()

    # 提取钩子模板
    extractor.extract_hook_templates()

    # 统计信息
    print(f"\n📊 提取统计:")
    print(f"  - 题材数量: {len(data['genres'])}")
    print(f"  - 爆款元素: {len(data['tropes'])}")
    print(f"  - 标杆案例: {len(data['examples'])}")
    print(f"  - 钩子模板: {len(data['hooks'])}")

    # 保存为JSON
    output_file = (
        "/Users/ariesmartin/Documents/new-video/data_extraction/theme_library_data.json"
    )
    save_json(data, output_file)

    # 同时保存为便于导入数据库的格式
    # 1. 主题数据
    themes_data = {"themes": data["genres"]}
    save_json(
        themes_data,
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_themes.json",
    )

    # 2. 元素数据（扁平化）
    elements_data = {"theme_elements": data["tropes"]}
    save_json(
        elements_data,
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_elements.json",
    )

    # 3. 案例数据
    examples_data = {"theme_examples": data["examples"]}
    save_json(
        examples_data,
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_examples.json",
    )

    # 4. 钩子模板
    hooks_data = {"hook_templates": data["hooks"]}
    save_json(
        hooks_data,
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_hooks.json",
    )

    # 5. 市场洞察
    market_data = {"market_insights": [data["market_insights"]]}
    save_json(
        market_data,
        "/Users/ariesmartin/Documents/new-video/data_extraction/seed_market.json",
    )

    print("\n✨ 完成！生成的文件:")
    print("  1. theme_library_data.json - 完整数据")
    print("  2. seed_themes.json - 主题数据（可直接导入数据库）")
    print("  3. seed_elements.json - 元素数据")
    print("  4. seed_examples.json - 案例数据")
    print("  5. seed_hooks.json - 钩子模板")
    print("  6. seed_market.json - 市场洞察")


if __name__ == "__main__":
    main()
