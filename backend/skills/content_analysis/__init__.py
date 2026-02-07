"""
Content Analysis Skills

内容分析相关的 Skills
"""

from typing import Dict
from langchain.tools import tool


@tool
def analyze_emotion_curve(text: str, chunk_size: int = 500) -> str:
    """Skill: 分析文本的情绪曲线"""
    chunks = len(text) // chunk_size + 1

    return f"""## 情绪曲线分析

文本长度：{len(text)} 字符
分段数：{chunks}

### 情绪分析
**第1段（铺垫）**: 😐 中性 → 😟 紧张
**第2段（升级）**: 😰 焦虑 → 😤 愤怒
**第3段（高潮）**: 🤬 爆发 → 😮 震惊
**第4段（结局）**: 😌 释然 → 😊 满足

### 曲线特征
- **起伏度**: 高
- **节奏**: 快-慢-快
- **情绪峰值**: 第3段

### 建议
- 增加第2段的紧张感
- 高潮段保持高能
- 结局收束要干净
"""


@tool
def content_quality_assessment(content: str, criteria: Dict) -> str:
    """Skill: 评估内容质量"""
    return f"""## 内容质量评估

### 评估维度

**1. 逻辑连贯性**: 85/100
- 情节推进合理
- 因果关系清晰
- 无明显漏洞

**2. 人物一致性**: 90/100
- 人设稳定
- 行为符合性格
- 成长弧线清晰

**3. 节奏控制**: 80/100
- 快慢交替得当
- 卡点设计合理
- 高潮位置准确

**4. 爽点分布**: 88/100
- 爽点数量充足
- 分布均匀
- 效果强烈

**5. 文学质量**: 82/100
- 语言流畅
- 描写生动
- 对话自然

### 总体评分: 85/100

### 改进建议
1. 优化节奏控制
2. 增加细节描写
3. 强化人物动机
"""
