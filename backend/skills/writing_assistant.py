from langchain_core.tools import tool
from backend.services.database import get_db_service

@tool
def get_sensory_guide(scene_type: str, emotion: Optional[str] = None) -> str:
    """
    Skill: 获取五感描写指导。
    
    帮助 Novel Writer 增强场景质感。
    
    Args:
        scene_type: 场景类型 (conflict-冲突, romance-浪漫, suspense-悬疑, daily-日常)
        emotion: 情绪基调 (可选)
    
    Returns:
        五感描写词汇和技巧指导。
    """
    sensory_db = {
        "conflict": {
            "visual": ["青筋暴起", "眼神锐利", "破碎的玻璃", "晃动的阴影"],
            "auditory": ["沉重的呼吸", "瓷器碎裂", "心跳加速", "怒吼"],
            "tactile": ["掌心出汗", "肌肉紧绷", "灼热感", "冰冷的触感"],
            "olfactory": ["火药味", "血腥味", "焦糊味"],
            "gustatory": ["铁锈味", "苦涩"]
        },
        "romance": {
            "visual": ["柔和光线", "眼神交汇", "微笑", "靠近的身影"],
            "auditory": ["低声细语", "心跳声", "轻笑", "沉默"],
            "tactile": ["指尖触碰", "温暖", "颤抖", "拥抱"],
            "olfactory": ["香水味", "阳光味", "花香"],
            "gustatory": ["甜味", "微苦"]
        }
    }
    
    guide = sensory_db.get(scene_type, {})
    
    return f"""
## {scene_type.upper()} 场景五感描写指导

**视觉 (Visual)**:
{', '.join(guide.get('visual', []))}

**听觉 (Auditory)**:
{', '.join(guide.get('auditory', []))}

**触觉 (Tactile)**:
{', '.join(guide.get('tactile', []))}

**嗅觉 (Olfactory)**:
{', '.join(guide.get('olfactory', []))}

**味觉 (Gustatory)**:
{', '.join(guide.get('gustatory', []))}

**使用技巧**: 
- 每段描写至少包含2种感官
- 根据情绪基调选择合适词汇
- 避免堆砌，自然融入叙事
"""


@tool
def get_pacing_rules(genre_id: str, episode_position: str) -> str:
    """
    Skill: 获取节奏控制规则。
    
    Args:
        genre_id: 题材ID
        episode_position: 剧集位置 (opening-开局, middle-中段, climax-高潮, ending-结局)
    
    Returns:
        节奏控制建议。
    """
    rules = {
        "opening": {
            "scene_count": "3-5个场景",
            "hook_timing": "前3秒必须抛出钩子",
            "pace": "快节奏，迅速建立冲突",
            "key_elements": ["主角亮相", "核心冲突", "悬念建立"]
        },
        "middle": {
            "scene_count": "5-8个场景",
            "hook_timing": "每3分钟一个小高潮",
            "pace": "快慢交替，保持张力",
            "key_elements": ["冲突升级", "关系发展", "伏笔铺设"]
        },
        "climax": {
            "scene_count": "3-5个场景",
            "hook_timing": "全程高能",
            "pace": "极快，情绪爆发",
            "key_elements": ["矛盾总爆发", "身份揭露", "打脸时刻"]
        },
        "ending": {
            "scene_count": "2-3个场景",
            "hook_timing": "收尾要有余韵",
            "pace": "由快到慢，归于平静",
            "key_elements": ["问题解决", "情感收束", "未来展望"]
        }
    }
    
    rule = rules.get(episode_position, {})
    
    return f"""
## 节奏控制规则 - {episode_position.upper()}

**场景数量**: {rule.get('scene_count', 'N/A')}

**钩子时机**: {rule.get('hook_timing', 'N/A')}

**整体节奏**: {rule.get('pace', 'N/A')}

**必须包含元素**:
{chr(10).join(['- ' + e for e in rule.get('key_elements', [])])}

**节奏曲线参考**:
- 开场: ████████░░░░░░░░░░ 快起
- 中段: ███░░████░░███░░██ 起伏
- 高潮: ██████████████████ 全程高能
- 结局: ██████░░░░░░░░░░░░ 渐收
"""


@tool
def get_trending_combinations(genre_id: Optional[str] = None) -> str:
    """
    Skill: 获取热门题材组合。
    
    用于 Concept Generator 的逆向工程方法论。
    
    Args:
        genre_id: 题材ID (可选)
    
    Returns:
        热门组合列表。
    """
    db = get_db_service()
    
    # 查询热门组合
    combinations = db.query(
        "theme_combinations",
        filters={"heat_score": {"gte": 80}},
        order_by="heat_score DESC",
        limit=5
    )
    
    sections = ["## 🔥 热门题材组合\n"]
    
    for combo in combinations:
        sections.append(f"""
**{combo['name']}**
- 组合: {' + '.join(combo['genres'])}
- 热度: {combo['heat_score']}/100
- 示例: {combo['example']}
- 成功要素: {combo.get('success_factors', 'N/A')}
""")
    
    sections.append("""
**逆向工程建议**:
分析以上热门组合的共性：
1. 违和感设计（传统+现代）
2. 身份落差（表象vs真实）
3. 情绪价值明确
""")
    
    return "\n".join(sections)