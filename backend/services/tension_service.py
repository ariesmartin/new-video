"""
Tension Service

负责张力曲线计算和关键节点识别
"""

from typing import List, Dict, Tuple
import math


def generate_standard_curve(total_episodes: int) -> List[float]:
    """
    生成标准戏剧性张力曲线

    基于经典三幕结构 + 短剧特性调整：
    - 第一幕 (0-25%): 建立 + 激励事件，张力逐步上升
    - 第二幕 (25-75%): 对抗升级，张力波动上升
    - 第三幕 (75-100%): 高潮 + 结局，张力快速上升后回落

    Args:
        total_episodes: 总集数

    Returns:
        每集的张力值列表 (0-100)
    """
    values = []

    for i in range(total_episodes):
        position = i / total_episodes if total_episodes > 0 else 0

        if position < 0.03:  # 前3%：超级钩子 (95-100)
            # 开篇必须强钩子
            tension = 95 + (position / 0.03) * 5
        elif position < 0.10:  # 3-10%：激励事件后 (75-90)
            # 激励事件后张力回落再上升
            progress = (position - 0.03) / 0.07
            tension = 75 + math.sin(progress * math.pi) * 15
        elif position < 0.25:  # 10-25%：第一幕发展 (60-75)
            # 稳步建立，小波动
            progress = (position - 0.10) / 0.15
            tension = 60 + progress * 15 + math.sin(progress * 8) * 5
        elif position < 0.50:  # 25-50%：第二幕前半 (65-80)
            # 对抗开始，逐步升级
            progress = (position - 0.25) / 0.25
            tension = 65 + progress * 15 + math.sin(progress * 6) * 8
        elif position < 0.75:  # 50-75%：第二幕后半 (70-88)
            # 接近高潮，张力快速上升
            progress = (position - 0.50) / 0.25
            tension = 70 + progress * 18 + math.sin(progress * 4) * 5
        elif position < 0.875:  # 75-87.5%：第三幕高潮前 (85-95)
            # 高潮前冲刺
            progress = (position - 0.75) / 0.125
            tension = 85 + progress * 10
        elif position < 0.95:  # 87.5-95%：高潮 (92-98)
            # 高潮峰值，必须90+
            progress = (position - 0.875) / 0.075
            tension = 92 + progress * 6
        else:  # 95-100%：结局回落 (85-70)
            # 结局回落，但保持一定张力
            progress = (position - 0.95) / 0.05
            tension = 85 - progress * 15

        values.append(round(tension, 1))

    return values


def generate_tension_curve(total_episodes: int, curve_type: str = "standard") -> Dict:
    """
    生成张力曲线数据

    Args:
        total_episodes: 总集数
        curve_type: 曲线类型 ("standard", "fast", "slow")
            - standard: 标准戏剧性结构
            - fast: 快节奏，前10集张力更高
            - slow: 慢热型，中段开始发力

    Returns:
        {
            "total_points": int,  # 总点数
            "values": List[float],  # 张力值列表 (0-100)
            "key_points": {
                "opening_hook": int,  # 开篇钩子位置 (第1集)
                "inciting_incident": int,  # 激励事件 (10%位置)
                "midpoint": int,  # 中点转折 (50%位置)
                "climax": int,  # 高潮 (87.5%位置)
                "paywall": int,  # 付费卡点 (~12集或15%位置)
                "resolution": int  # 结局
            },
            "curve_type": str  # 曲线类型
        }
    """
    # 计算关键节点位置
    key_points = {
        "opening_hook": 0,  # 第1集（索引0）
        "inciting_incident": max(2, int(total_episodes * 0.10)),
        "midpoint": int(total_episodes * 0.50),
        "climax": int(total_episodes * 0.875),
        "paywall": min(12, int(total_episodes * 0.15))
        if total_episodes >= 12
        else int(total_episodes * 0.20),
        "resolution": total_episodes - 1,  # 最后一集
    }

    # 根据类型生成曲线
    if curve_type == "fast":
        # 快节奏：前段张力更高
        values = _generate_fast_curve(total_episodes)
    elif curve_type == "slow":
        # 慢热型：中段开始发力
        values = _generate_slow_curve(total_episodes)
    else:
        # 标准曲线
        values = generate_standard_curve(total_episodes)

    return {
        "total_points": total_episodes,
        "values": values,
        "key_points": key_points,
        "curve_type": curve_type,
    }


def _generate_fast_curve(total_episodes: int) -> List[float]:
    """生成快节奏曲线（适合爽文）"""
    values = []
    for i in range(total_episodes):
        position = i / total_episodes
        # 前20集保持高张力
        if position < 0.25:
            tension = 85 + math.sin(position * 20) * 10
        else:
            # 后面按标准曲线
            tension = 70 + position * 20 + math.sin(position * 10) * 8
        values.append(round(tension, 1))
    return values


def _generate_slow_curve(total_episodes: int) -> List[float]:
    """生成慢热型曲线（适合悬疑、成长型）"""
    values = []
    for i in range(total_episodes):
        position = i / total_episodes
        # 前30%保持中低张力，铺垫
        if position < 0.30:
            tension = 60 + position * 30 + math.sin(position * 15) * 5
        else:
            # 后面快速拉升
            tension = 70 + (position - 0.30) * 35 + math.sin(position * 8) * 8
        values.append(round(min(tension, 98), 1))
    return values


def calculate_curve_deviation(
    actual_values: List[float], target_values: List[float]
) -> Tuple[float, List[Dict]]:
    """
    计算实际曲线与目标曲线的偏差

    Args:
        actual_values: 实际张力值列表
        target_values: 目标张力值列表

    Returns:
        (平均偏差, 偏差较大的点列表)

    Example:
        >>> avg_dev, issues = calculate_curve_deviation([80, 75, 90], [85, 80, 85])
        >>> print(f"平均偏差: {avg_dev}")
    """
    if len(actual_values) != len(target_values):
        raise ValueError("实际值和目标值长度必须相同")

    deviations = []
    issues = []

    for i, (actual, target) in enumerate(zip(actual_values, target_values)):
        deviation = abs(actual - target)
        deviations.append(deviation)

        # 记录偏差较大的点
        if deviation > 15:  # 偏差超过15分
            issues.append(
                {
                    "episode": i + 1,
                    "actual": actual,
                    "target": target,
                    "deviation": deviation,
                    "severity": "high" if deviation > 25 else "medium",
                }
            )

    avg_deviation = sum(deviations) / len(deviations) if deviations else 0

    return round(avg_deviation, 2), issues


def get_tension_requirements(episode_number: int, total_episodes: int) -> Dict:
    """
    获取指定集数的张力要求

    Args:
        episode_number: 集数（1-based）
        total_episodes: 总集数

    Returns:
        {
            "min_tension": float,  # 最低张力要求
            "target_tension": float,  # 目标张力
            "description": str  # 该位置的叙事要求
        }
    """
    position = (episode_number - 1) / total_episodes if total_episodes > 1 else 0

    if episode_number == 1:
        return {
            "min_tension": 85,
            "target_tension": 95,
            "description": "开篇钩子 - 必须强冲击，前3秒抓住观众",
        }
    elif position < 0.10:
        return {
            "min_tension": 70,
            "target_tension": 80,
            "description": "激励事件后 - 建立冲突，引发好奇",
        }
    elif position < 0.50:
        return {
            "min_tension": 60,
            "target_tension": 75,
            "description": "发展部分 - 稳步升级，保持兴趣",
        }
    elif position < 0.875:
        return {
            "min_tension": 75,
            "target_tension": 88,
            "description": "升级部分 - 快速推进，接近高潮",
        }
    elif position < 0.95:
        return {
            "min_tension": 90,
            "target_tension": 95,
            "description": "高潮部分 - 必须达到峰值，最大冲突",
        }
    else:
        return {
            "min_tension": 65,
            "target_tension": 75,
            "description": "结局部分 - 合理收尾，情感释放",
        }


# Skill Review Matrix 定义（微观补充层）
SKILL_REVIEW_MATRIX = {
    "S_Protocol": {
        "label": "协议合规性",
        "applies_to": ["script", "storyboard"],
        "checks": ["格式规范", "字段完整", "命名规范"],
    },
    "S_Logic": {
        "label": "逻辑卫士",
        "applies_to": ["novel", "script"],
        "checks": ["因果检查", "弧光检查", "吃书检查"],
    },
    "S_Engagement": {
        "label": "吸引力",
        "applies_to": ["novel", "script"],
        "checks": ["爽点密度", "钩子检查", "情绪曲线"],
    },
    "S_Texture": {
        "label": "文学质感",
        "applies_to": ["novel"],  # 仅小说
        "checks": ["五感描写", "共情能力", "环境投射"],
    },
    "S_Human": {
        "label": "拟真度",
        "applies_to": ["novel", "script"],
        "checks": ["对话自然", "反套路", "潜台词"],
    },
}


def get_skill_checks(content_type: str) -> Dict[str, List[str]]:
    """
    获取指定内容类型的 Skill Review 检查点

    Args:
        content_type: 内容类型 ("novel", "script", "storyboard")

    Returns:
        适用的 Skill 检查点
    """
    checks = {}
    for skill, config in SKILL_REVIEW_MATRIX.items():
        if content_type in config["applies_to"]:
            checks[skill] = config["checks"]
    return checks
