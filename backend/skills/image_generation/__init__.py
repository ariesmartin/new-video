"""
Image Generation Skills

图片生成相关的 Skills
"""

from typing import Dict
from langchain.tools import tool


@tool
def storyboard_to_image_prompt(storyboard_item: Dict) -> str:
    """Skill: 将分镜转换为图片生成提示词"""
    scene = storyboard_item.get("scene", "")
    character = storyboard_item.get("character", "")
    action = storyboard_item.get("action", "")

    return f"""## 图片生成提示词

### 场景描述
{scene}

### 角色描述
{character}

### 动作描述
{action}

### Nano Banana Prompt
{character}, {action}, {scene}, cinematic lighting, high quality, detailed, 8k --ar 16:9

### 参数说明
- **主体**: {character}
- **动作**: {action}
- **场景**: {scene}
- **风格**: 电影感，高质量
- **比例**: 16:9
"""


@tool
def optimize_prompt_for_model(base_prompt: str, model_type: str = "nano_banana") -> str:
    """Skill: 针对特定模型优化提示词"""
    optimizations = {
        "nano_banana": "添加 --cref 和 --sref 参数，使用英文",
        "midjourney": "使用简洁的英文描述，添加 --ar 和 --v 参数",
        "stable_diffusion": "使用详细的英文标签，添加质量标签",
    }

    opt = optimizations.get(model_type, "通用优化")

    return f"""## 优化后的提示词

**原始提示词**: {base_prompt}

**目标模型**: {model_type}

**优化策略**: {opt}

### 优化结果
针对 {model_type} 优化后的提示词：

{base_prompt}, high quality, detailed, masterpiece, best quality

**建议**: 根据模型特点调整提示词风格。
"""
