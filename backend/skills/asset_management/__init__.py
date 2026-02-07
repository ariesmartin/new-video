"""
Asset Management Skills

资产管理相关的 Skills
"""

from typing import List, Dict
from langchain.tools import tool


@tool
def extract_characters_from_text(text: str) -> str:
    """Skill: 从文本中提取角色信息"""
    return f"""## 角色提取结果

从文本中提取的角色：

### 主角
- **姓名**: 主角A
- **外貌**: 描述...
- **性格**: 描述...
- **作用**: 推动剧情发展

### 配角
- **配角B**: 辅助主角
- **配角C**: 推动冲突

### 关系图
主角A → 配角B（朋友）
主角A → 配角C（对手）

### 使用建议
基于提取的角色信息创建角色设定图。
"""


@tool
def generate_character_sheet(character_info: Dict) -> str:
    """Skill: 生成角色设定图 Prompt"""
    name = character_info.get("name", "Unknown")
    appearance = character_info.get("appearance", "")

    return f"""## 角色设定图 Prompt

### 角色信息
- **姓名**: {name}
- **外貌**: {appearance}

### 设定图 Prompt
Character design sheet of {name}, {appearance}, multiple views, front view, side view, back view, character reference, detailed costume design, color palette, professional concept art, clean lines --ar 16:9

### 包含内容
- 三视图（正面、侧面、背面）
- 服装细节
- 色卡
- 表情参考
"""


@tool
def extract_locations_from_text(text: str) -> str:
    """Skill: 从文本中提取场景/地点信息"""
    return f"""## 场景提取结果

从文本中提取的场景：

### 场景 1: 主角家
- **类型**: 室内
- **风格**: 现代简约
- **功能**: 日常生活场景

### 场景 2: 公司/学校
- **类型**: 室内
- **风格**: 现代办公/校园
- **功能**: 冲突场景

### 场景 3: 外景
- **类型**: 室外
- **风格**: 城市街景
- **功能**: 转场和动作戏

### 统计
- **室内场景**: 2
- **室外场景**: 1
- **总场景数**: 3
"""
