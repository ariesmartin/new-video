"""
Review Service

负责审阅逻辑：权重计算、检查点定义、严重程度分级
"""

from typing import Dict, List

# 6大分类定义 - 统一审阅框架
# 将 Skill Review Matrix 的指标归纳进 6 大分类中
# 根据 content_type 动态启用/禁用某些检查点
REVIEW_CATEGORIES = {
    "logic": {
        "label": "逻辑/设定",
        "icon": "🧠",
        "color": "#3B82F6",
        "description": "检查故事逻辑是否自洽、设定是否前后一致（整合 S_Logic）",
        "skills": ["S_Logic"],  # 关联的 Skill Review 指标
        "checkpoints": {
            "outline": [
                "大纲结构完整",
                "世界观一致性（S_Logic）",
                "时间线合理性",
                "因果关系清晰",
            ],
            "novel": [
                "因果逻辑通顺",
                "无吃书现象（S_Logic-吃书检查）",
                "设定前后一致（S_Logic-设定一致性）",
                "伏笔合理回收",
            ],
            "script": [
                "场景逻辑合理",
                "道具一致性",
                "转场流畅",
                "台词符合情境",
            ],
            "storyboard": [
                "镜头逻辑连贯",
                "跳轴检查",
                "空间一致性",
                "时间线清晰",
            ],
        },
    },
    "pacing": {
        "label": "节奏/张力",
        "icon": "📈",
        "color": "#F97316",
        "description": "检查叙事节奏、张力曲线、爽点密度（整合 S_Engagement）",
        "skills": ["S_Engagement"],
        "checkpoints": {
            "outline": [
                "整体节奏曲线合理",
                "高潮位置在87.5%",
                "付费卡点张力≥90",
                "开篇钩子强度≥85",
            ],
            "novel": [
                "每章爽点密度适中（S_Engagement-爽点密度）",
                "情绪高低起伏自然（S_Engagement-情绪曲线）",
                "无拖沓段落",
                "转折点位置恰当",
            ],
            "script": [
                "每集节奏紧凑",
                "场景时长分配合理",
                "转场节奏流畅",
                "对白节奏明快",
            ],
            "storyboard": [
                "镜头时长合适",
                "剪辑节奏流畅",
                "视觉张力充足",
                "动作场面有冲击力",
            ],
        },
    },
    "character": {
        "label": "人设/角色",
        "icon": "👤",
        "color": "#A855F7",
        "description": "检查角色塑造、人设一致性、成长弧光（整合 S_Human）",
        "skills": ["S_Human"],
        "checkpoints": {
            "outline": [
                "角色小传完整",
                "极致美丽达标",
                "B-Story存在",
                "拒绝工具人",
                "成长弧光清晰（S_Logic-弧光检查）",
            ],
            "novel": [
                "行为符合人设",
                "性格有层次",
                "台词符合身份（S_Human-对话自然）",
                "情感变化自然（S_Human-潜台词）",
            ],
            "script": [
                "表演指导明确",
                "情绪层次丰富",
                "角色关系动态变化",
                "性格特征鲜明",
            ],
            "storyboard": [
                "角色造型一致",
                "表情神态到位",
                "动作设计符合性格",
                "视觉辨识度高",
            ],
        },
    },
    "conflict": {
        "label": "冲突/事件",
        "icon": "⚔️",
        "color": "#EF4444",
        "description": "检查冲突设计、事件推动、情绪冲击（整合 S_Engagement）",
        "skills": ["S_Engagement"],
        "checkpoints": {
            "outline": [
                "核心冲突明确",
                "冲突升级路径清晰",
                "爽点分布均匀（S_Engagement-爽点密度）",
                "反转设计巧妙",
            ],
            "novel": [
                "冲突持续升级",
                "反转合理意外",
                "爽点密度充足（S_Engagement）",
                "无冗余事件",
            ],
            "script": [
                "戏剧冲突强烈",
                "场景张力饱满",
                "高潮呈现精彩",
                "冲突解决合理",
            ],
            "storyboard": [
                "动作设计精彩",
                "冲突可视化强",
                "视觉冲击力强",
                "战斗场面有层次感",
            ],
        },
    },
    "world": {
        "label": "世界/规则",
        "icon": "🌍",
        "color": "#22C55E",
        "description": "检查世界观完整性、规则一致性（整合 S_Logic）",
        "skills": ["S_Logic"],
        "checkpoints": {
            "outline": [
                "3条铁律明确",
                "战力平衡",
                "规则一致性（S_Logic-世界观一致性）",
                "世界观有深度",
            ],
            "novel": [
                "规则严格遵守",
                "设定细节一致（S_Logic-设定一致性）",
                "无战力崩坏",
                "世界细节丰富",
            ],
            "script": [
                "场景设定清晰",
                "特效可行性",
                "逻辑自洽",
                "氛围营造到位",
            ],
            "storyboard": [
                "场景细节准确",
                "道具准确性",
                "环境氛围统一",
                "时代特征明显",
            ],
        },
    },
    "hook": {
        "label": "钩子/悬念",
        "icon": "🪝",
        "color": "#EAB308",
        "description": "检查钩子设计、悬念维持（整合 S_Engagement）",
        "skills": ["S_Engagement"],
        "checkpoints": {
            "outline": [
                "前3秒钩子强度≥90",
                "每集cliffhanger",
                "付费卡点悬念强",
                "伏笔合理分布（S_Engagement-钩子检查）",
            ],
            "novel": [
                "章节结尾有悬念",
                "悬念留存自然",
                "情绪高点结束",
                "章评引导到位",
            ],
            "script": [
                "镜头钩子抓人",
                "转场有悬念",
                "情绪峰值突出",
                "卡点张力强",
            ],
            "storyboard": [
                "视觉冲击力强",
                "构图吸引力强",
                "色彩情绪到位",
                "画面有故事性",
            ],
        },
    },
    "protocol": {
        "label": "协议/格式",
        "icon": "📋",
        "color": "#6366F1",
        "description": "检查格式规范、字段完整（仅 Script/Storyboard）",
        "skills": ["S_Protocol"],
        "content_types": ["script", "storyboard"],  # 仅特定类型启用
        "checkpoints": {
            "script": [
                "格式规范（S_Protocol-格式规范）",
                "字段完整（S_Protocol-字段完整）",
                "命名规范（S_Protocol-命名规范）",
            ],
            "storyboard": [
                "格式规范（S_Protocol）",
                "字段完整（S_Protocol）",
                "命名规范（S_Protocol）",
            ],
        },
    },
    "texture": {
        "label": "文学质感",
        "icon": "✨",
        "color": "#EC4899",
        "description": "检查文学性、五感描写、共情能力（仅 Novel）",
        "skills": ["S_Texture"],
        "content_types": ["novel"],  # 仅 Novel 启用
        "checkpoints": {
            "novel": [
                "五感描写丰富（S_Texture-五感描写）",
                "共情能力强（S_Texture-共情能力）",
                "环境投射到位（S_Texture-环境投射）",
                "文学性达标",
            ],
        },
    },
}

# 基础权重表（单题材）
BASE_WEIGHTS = {
    "revenge": {  # 复仇爽剧
        "logic": 0.10,
        "pacing": 0.30,
        "character": 0.10,
        "conflict": 0.25,
        "world": 0.05,
        "hook": 0.20,
    },
    "romance": {  # 甜宠
        "logic": 0.10,
        "pacing": 0.20,
        "character": 0.30,
        "conflict": 0.10,
        "world": 0.05,
        "hook": 0.25,
    },
    "suspense": {  # 悬疑
        "logic": 0.30,
        "pacing": 0.20,
        "character": 0.05,
        "conflict": 0.05,
        "world": 0.15,
        "hook": 0.25,
    },
    "transmigration": {  # 穿越重生
        "logic": 0.20,
        "pacing": 0.25,
        "character": 0.15,
        "conflict": 0.20,
        "world": 0.10,
        "hook": 0.10,
    },
    "family": {  # 家庭伦理
        "logic": 0.20,
        "pacing": 0.05,
        "character": 0.30,
        "conflict": 0.15,
        "world": 0.25,
        "hook": 0.05,
    },
}

# 严重程度分级
SEVERITY_LEVELS = {
    "critical": {
        "label": "致命",
        "color": "#DC2626",
        "icon": "🔴",
        "editor_comment": "这也能播?立刻给我改!",
        "score_threshold": 0,  # 0-59分
        "examples": ["结局逻辑崩坏", "主角人设全崩", "付费卡点无力"],
    },
    "high": {
        "label": "严重",
        "color": "#EA580C",
        "icon": "🟠",
        "editor_comment": "问题很大,不想被骂就改!",
        "score_threshold": 60,  # 60-74分
        "examples": ["连续5集平淡", "核心冲突模糊", "人设工具人"],
    },
    "medium": {
        "label": "警告",
        "color": "#EAB308",
        "icon": "🟡",
        "editor_comment": "小问题,但影响质感。",
        "score_threshold": 75,  # 75-84分
        "examples": ["某集钩子弱", "细节逻辑漏洞", "节奏稍慢"],
    },
    "low": {
        "label": "提示",
        "color": "#6B7280",
        "icon": "⚪",
        "editor_comment": "挑刺的话可以说,但问题不大。",
        "score_threshold": 85,  # 85-100分
        "examples": ["某句台词可以更精炼", "某场景可删减"],
    },
}


def calculate_weights(genre_combination: List[str]) -> Dict[str, float]:
    """
    根据题材组合计算6大分类权重

    例如: ["revenge", "romance"] → 复仇甜宠组合
    计算方式: 加权平均后归一化

    Args:
        genre_combination: 题材组合列表，如 ["revenge", "romance"]

    Returns:
        6大分类的权重字典，总和为1.0

    Example:
        >>> calculate_weights(["revenge", "romance"])
        {'logic': 0.10, 'pacing': 0.25, 'character': 0.20,
         'conflict': 0.175, 'world': 0.05, 'hook': 0.225}
    """
    if not genre_combination:
        # 默认使用复仇权重
        return BASE_WEIGHTS["revenge"].copy()

    # 初始化权重
    combined = {key: 0.0 for key in BASE_WEIGHTS["revenge"].keys()}

    # 加权平均
    for genre in genre_combination:
        weights = BASE_WEIGHTS.get(genre, BASE_WEIGHTS["revenge"])
        for key in combined:
            combined[key] += weights[key] / len(genre_combination)

    # 归一化（确保总和为1.0）
    total = sum(combined.values())
    if total > 0:
        return {k: round(v / total, 2) for k, v in combined.items()}

    return combined


def get_checkpoints(content_type: str) -> Dict[str, List[str]]:
    """
    获取指定内容类型的检查点（统一审阅框架）

    根据 content_type 动态启用/禁用某些分类：
    - 6大基础分类：所有类型通用
    - protocol（协议/格式）：仅 script/storyboard
    - texture（文学质感）：仅 novel

    Args:
        content_type: 内容类型 ("outline", "novel", "script", "storyboard")

    Returns:
        适用的分类及其检查点列表
    """
    checkpoints = {}
    for category, config in REVIEW_CATEGORIES.items():
        # 检查该分类是否适用于当前 content_type
        applicable_types = config.get("content_types")
        if applicable_types is not None:
            # 有明确限制的分类（protocol, texture）
            if content_type not in applicable_types:
                continue  # 跳过不适用的分类

        # 获取该分类在当前 content_type 下的检查点
        category_checkpoints = config["checkpoints"].get(content_type, [])
        if category_checkpoints:
            checkpoints[category] = category_checkpoints

    return checkpoints


def get_applicable_categories(content_type: str) -> Dict[str, Dict]:
    """
    获取适用于指定内容类型的所有分类配置

    Args:
        content_type: 内容类型

    Returns:
        分类配置字典（包含权重计算所需的分类）
    """
    applicable = {}
    for category, config in REVIEW_CATEGORIES.items():
        applicable_types = config.get("content_types")
        if applicable_types is None or content_type in applicable_types:
            applicable[category] = config
    return applicable


def calculate_weights_unified(genre_combination: List[str], content_type: str) -> Dict[str, float]:
    """
    计算统一审阅框架下的权重（含动态分类）

    Args:
        genre_combination: 题材组合
        content_type: 内容类型（影响哪些分类参与计算）

    Returns:
        各分类权重（仅包含适用的分类）
    """
    # 获取基础权重（6大分类）
    base_weights = calculate_weights(genre_combination)

    # 获取适用的分类
    applicable_categories = get_applicable_categories(content_type)

    # 为动态分类分配权重
    unified_weights = {}
    total_weight = 0

    for category in applicable_categories.keys():
        if category in base_weights:
            unified_weights[category] = base_weights[category]
        elif category == "protocol":
            # 协议/格式权重（较低，因为是合规性检查）
            unified_weights[category] = 0.05
        elif category == "texture":
            # 文学质感权重（较高，因为是novel核心）
            unified_weights[category] = 0.15
        total_weight += unified_weights[category]

    # 归一化
    if total_weight > 0 and total_weight != 1.0:
        unified_weights = {k: round(v / total_weight, 2) for k, v in unified_weights.items()}

    return unified_weights


def determine_severity(score: float, weight: float) -> str:
    """
    根据分数和权重确定严重程度

    Args:
        score: 该项得分 (0-100)
        weight: 该项权重 (影响严重程度判断)

    Returns:
        严重程度级别: "critical", "high", "medium", "low"
    """
    # 权重越高，对分数的要求越严格
    adjusted_score = score * (1 + weight * 0.5)

    for severity, config in SEVERITY_LEVELS.items():
        if adjusted_score < config["score_threshold"] + 15:  # 缓冲区间
            return severity

    return "low"


def get_severity_config(severity: str) -> Dict:
    """
    获取严重程度的配置信息

    Args:
        severity: 严重程度级别

    Returns:
        配置字典，包含label、color、icon等
    """
    return SEVERITY_LEVELS.get(severity, SEVERITY_LEVELS["medium"])


# 常见题材组合权重参考
COMMON_COMBINATIONS = {
    "复仇+甜宠": {
        "pacing": 0.25,
        "hook": 0.225,
        "character": 0.20,
        "conflict": 0.175,
        "logic": 0.10,
        "world": 0.05,
    },
    "悬疑+甜宠": {
        "logic": 0.20,
        "hook": 0.25,
        "character": 0.175,
        "pacing": 0.20,
        "conflict": 0.10,
        "world": 0.075,
    },
    "复仇+悬疑": {
        "logic": 0.20,
        "pacing": 0.25,
        "conflict": 0.15,
        "hook": 0.225,
        "character": 0.075,
        "world": 0.10,
    },
    "穿越+甜宠": {
        "character": 0.225,
        "pacing": 0.225,
        "hook": 0.175,
        "logic": 0.15,
        "conflict": 0.125,
        "world": 0.10,
    },
    "家庭+甜宠": {
        "character": 0.30,
        "world": 0.15,
        "logic": 0.15,
        "conflict": 0.15,
        "pacing": 0.10,
        "hook": 0.05,
    },
}
