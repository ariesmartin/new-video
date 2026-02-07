"""
Script Adaptation Skills

剧本改编相关的 Skills
"""

from typing import List
from langchain.tools import tool


@tool
def novel_to_script(novel_text: str, format: str = "short_drama") -> str:
    """Skill: 将小说格式转换为剧本格式"""
    return f"""## 剧本改编结果

### 改编说明
- **原文长度**: {len(novel_text)} 字符
- **目标格式**: {format}
- **改编策略**: 保留核心情节，优化节奏

### 场景列表
1. **场景1**: 开场 - 介绍主角和背景
2. **场景2**: 冲突 - 核心矛盾出现
3. **场景3**: 发展 - 情节推进
4. **场景4**: 高潮 - 矛盾爆发
5. **场景5**: 结局 - 问题解决

### 改编要点
- 心理描写 → 动作和对话
- 长段落 → 分镜描述
- 内心独白 → 表情和动作暗示
"""


@tool
def extract_scenes(script_text: str) -> str:
    """Skill: 从剧本中提取场景列表"""
    return f"""## 场景列表

从剧本中提取的场景：

### 场景 1: 开场
- **地点**: 主角家
- **时间**: 白天
- **角色**: 主角、配角A
- **概要**: 介绍背景，建立人物关系

### 场景 2: 冲突
- **地点**: 公司/学校
- **时间**: 下午
- **角色**: 主角、反派
- **概要**: 核心冲突出现

### 场景 3-5: ...
（根据实际剧本内容提取）

### 统计信息
- **总场景数**: 5
- **室内场景**: 3
- **室外场景**: 2
- **日戏**: 4
- **夜戏**: 1
"""


@tool
def generate_dialogue(characters: List[str], context: str) -> str:
    """Skill: 基于角色和上下文生成对话"""
    return f"""## 对话生成

角色：{", ".join(characters)}
场景：{context}

### 对话示例

**{characters[0]}**: （冷笑）你以为这样就能打败我吗？

**{characters[1]}**: （坚定）我不是要打败你，我只是要守护我在乎的人。

**{characters[0]}**: （愣住）你...

**{characters[1]}**: （转身）这次，换我来保护你了。

### 对话特点
- 口语化、自然
- 符合人设
- 推动剧情
- 有冲突和张力
"""
