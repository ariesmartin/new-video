"""
Storyboard Skills

分镜设计相关的 Skills
"""

from typing import Dict
from langchain.tools import tool


@tool
def design_shots(scene_description: str) -> str:
    """Skill: 为场景设计镜头"""
    return f"""## 镜头设计方案

场景：{scene_description}

### 镜头 1: 远景 establishing shot
- **类型**: 远景
- **运镜**: 固定
- **时长**: 3秒
- **作用**: 建立场景空间

### 镜头 2: 中景 medium shot
- **类型**: 中景
- **运镜**: 推镜头
- **时长**: 5秒
- **作用**: 介绍人物关系

### 镜头 3: 特写 close-up
- **类型**: 特写
- **运镜**: 固定
- **时长**: 2秒
- **作用**: 表现情绪

### 运镜建议
- 情感戏: 缓慢推近
- 动作戏: 快速切换
- 悬疑戏: 晃动+快速剪辑
"""


@tool
def generate_nano_banana_prompt(shot_description: str, assets: Dict) -> str:
    """Skill: 生成分镜的 Nano Banana Prompt"""
    char_ref = assets.get("character_url", "")
    loc_ref = assets.get("location_url", "")

    return f"""## Nano Banana Prompt

### 英文 Prompt
{shot_description}, cinematic lighting, high quality, detailed, 8k --cref {char_ref} --sref {loc_ref} --ar 16:9

### 中文描述
{shot_description}

**Asset 引用**:
- 角色引用: {char_ref}
- 场景引用: {loc_ref}

**参数说明**:
- --cref: 角色一致性引用
- --sref: 场景风格引用
- --ar 16:9: 宽高比
"""


@tool
def generate_video_prompt(shot_description: str) -> str:
    """Skill: 生成分镜的 Video Generation Prompt"""
    return f"""## Video Generation Prompt

### 场景描述
{shot_description}

### 动态描述
- **镜头运动**: 缓慢推近
- **角色动作**: 主角向前迈步，眼神坚定
- **环境变化**: 光影渐变，营造氛围
- **时间流逝**: 5秒内完成动作

### 技术参数
- **时长**: 5秒
- **分辨率**: 1080p
- **帧率**: 24fps
- **风格**: 电影感
"""


@tool
def plan_shot_sequence(scenes: List[Dict]) -> str:
    """Skill: 规划镜头序列"""
    return f"""## 镜头序列规划

总场景数：{len(scenes)}

### 序列设计
1. **开场**: 远景 → 中景 → 特写
2. **对话**: 正反打镜头
3. **动作**: 多角度快速切换
4. **转场**: 匹配剪辑或渐变

### 节奏控制
- **快节奏**: 1-2秒/镜头
- **慢节奏**: 5-8秒/镜头
- **平均**: 3-4秒/镜头

### 情绪曲线
通过镜头时长和运镜控制情绪节奏。
"""
