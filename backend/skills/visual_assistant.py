from langchain_core.tools import tool

@tool
def get_camera_style(genre_id: str, scene_mood: str) -> str:
    """
    Skill: 获取镜头风格建议。
    
    用于 Storyboard Director。
    
    Args:
        genre_id: 题材ID
        scene_mood: 场景情绪 (tense-紧张, romantic-浪漫, action-动作, sad-悲伤)
    
    Returns:
        镜头风格建议。
    """
    styles = {
        "revenge": {
            "tense": {
                "shot_types": ["特写", "低角度", "手持"],
                "lighting": ["高对比", "侧光", "阴影"],
                "color": ["冷色调", "高饱和"],
                "techniques": ["快速剪辑", "跳切", "变焦"]
            },
            "action": {
                "shot_types": ["广角", "运动镜头", "俯视"],
                "lighting": ["硬光", "逆光"],
                "color": ["高对比", "饱和度+20%"],
                "techniques": ["慢动作", "快速切换", "环绕拍摄"]
            }
        },
        "sweet": {
            "romantic": {
                "shot_types": ["中景", "浅景深", "柔焦"],
                "lighting": ["柔光", "暖光", "逆光"],
                "color": ["暖色调", "粉色调", "柔光滤镜"],
                "techniques": ["慢推", "环绕", "长镜头"]
            }
        }
    }
    
    genre_style = styles.get(genre_id, {})
    mood_style = genre_style.get(scene_mood, {})
    
    return f"""
## 镜头风格 - {genre_id} + {scene_mood}

**景别选择**:
{', '.join(mood_style.get('shot_types', ['根据情境选择']))}

**灯光设计**:
{', '.join(mood_style.get('lighting', ['标准布光']))}

**色彩方案**:
{', '.join(mood_style.get('color', ['自然色']))}

**特殊技法**:
{', '.join(mood_style.get('techniques', ['无特殊要求']))}

**参考影片**:
{getattr(mood_style, 'references', '参考同题材热门短剧')}
"""


@tool
def get_visual_keywords(genre_id: str) -> str:
    """
    Skill: 获取视觉关键词。
    
    用于 Asset Inspector 检查资产风格。
    
    Args:
        genre_id: 题材ID
    
    Returns:
        视觉关键词列表。
    """
    db = get_db_service()
    
    theme = db.query("themes", filters={"slug": genre_id})
    if not theme:
        return f"错误：找不到题材 '{genre_id}'"
    
    keywords = theme.get("keywords", {})
    visual_kw = keywords.get("visual", [])
    
    return f"""
## {theme['name']} 视觉关键词

{', '.join(visual_kw)}

**应用场景**:
- 角色服装: 体现身份和性格
- 场景布置: 强化题材氛围
- 色调滤镜: 统一视觉风格
- 道具选择: 符合题材特征
"""