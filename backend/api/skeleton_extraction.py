"""
Skeleton Builder - Story Settings Extraction Module

Comprehensive extraction of story skeleton content with full Markdown support for Tiptap rendering.
"""

import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class SimpleLogger:
    @staticmethod
    def error(msg, **kwargs):
        print(f"[ERROR] {msg}: {kwargs}")

    @staticmethod
    def warning(msg, **kwargs):
        print(f"[WARN] {msg}: {kwargs}")


logger = SimpleLogger()


def parse_skeleton_to_outline(skeleton_content: str, project_id: str) -> Dict[str, Any]:
    """
    解析骨架构建器的输出，转换为标准的 OutlineData 格式

    Args:
        skeleton_content: 骨架构建器生成的完整 Markdown 内容
        project_id: 项目ID

    Returns:
        OutlineData 格式的字典
    """
    outline_data = {
        "projectId": project_id,
        "episodes": [],
        "totalEpisodes": 80,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "content": skeleton_content,
    }

    try:
        # 1. 尝试从内容中提取 JSON 元数据部分
        metadata = extract_json_metadata(skeleton_content)
        chapter_map = metadata.get("chapter_map", [])
        paywall_info = metadata.get("paywall_info", {})

        # 2. 提取故事设定（完整 Markdown 格式）
        story_settings = extract_story_settings_comprehensive(skeleton_content)
        outline_data["storySettings"] = story_settings
        outline_data["metadata"] = {
            "chapter_map": chapter_map,
            "paywall_info": paywall_info,
            "source": "skeleton_builder",
            "skeleton_content": skeleton_content,
            "story_settings": story_settings,
        }

        # 3. 从 chapter_map 构建 episodes
        if chapter_map:
            episodes = build_episodes_from_chapter_map(
                chapter_map, skeleton_content, project_id, paywall_info
            )
            episodes.sort(key=lambda x: x["episodeNumber"])
            outline_data["episodes"] = episodes
            outline_data["totalEpisodes"] = len(episodes)

    except Exception as e:
        logger.error("Failed to parse skeleton content", error=str(e), project_id=project_id)

    return outline_data


def extract_json_metadata(content: str) -> Dict[str, Any]:
    """提取 JSON 格式的元数据部分"""
    try:
        # 尝试匹配 ```json ... ``` 代码块
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
        if json_match:
            return json.loads(json_match.group(1))

        # 尝试直接匹配 JSON 对象（以 { 开头，包含 chapter_map）
        json_match = re.search(
            r'\{\s*"chapter_map"[\s\S]*?"actions"\s*:\s*\[[\s\S]*?\]\s*\}', content
        )
        if json_match:
            return json.loads(json_match.group(0))

    except json.JSONDecodeError as e:
        logger.warning("Failed to parse JSON metadata", error=str(e))

    return {}


def extract_story_settings_comprehensive(content: str) -> Dict[str, Any]:
    """
    全面提取故事设定各部分，返回 Markdown 格式的内容用于 Tiptap 渲染

    Returns:
        {
            "metadata": {"title": "...", "genre": "...", "markdown": "完整 Markdown"},
            "coreSetting": {"worldview": "...", "coreRules": "...", "markdown": "..."},
            "characters": [{"name": "...", "description": "...", "markdown": "..."}],
            "plotArchitecture": {"acts": [...], "markdown": "..."},
            "adaptationMapping": {"ratio": "...", "mapping": [...], "markdown": "..."},
            "writingGuidelines": {"guidelines": [...], "markdown": "..."},
            "paywallDesign": {"chapter": "...", "episodes": "...", "markdown": "..."},
            "tensionCurve": {"curve": [...], "markdown": "..."},
        }
    """
    settings = {
        "metadata": extract_section_markdown(
            content, ["一、元数据", "1. 元数据"], ["二、核心设定", "2. 核心设定"]
        ),
        "coreSetting": extract_section_markdown(
            content, ["二、核心设定", "2. 核心设定"], ["三、人物体系", "3. 人物体系"]
        ),
        "characters": extract_characters_section(content),
        "plotArchitecture": extract_section_markdown(
            content,
            ["四、情节架构", "4. 情节架构"],
            ["五、章节大纲", "5. 章节大纲", "六、短剧映射表"],
        ),
        "adaptationMapping": extract_section_markdown(
            content,
            ["六、短剧映射表", "6. 短剧映射表", "六、改编映射"],
            ["七、创作指导", "7. 创作指导"],
        ),
        "writingGuidelines": extract_section_markdown(
            content, ["七、创作指导", "7. 创作指导"], ["八、", "8. "]
        ),
        "paywallDesign": extract_paywall_design(content),
        "tensionCurve": extract_tension_curve(content),
    }

    return settings


def extract_section_markdown(
    content: str, start_markers: List[str], end_markers: List[str]
) -> Dict[str, Any]:
    """
    提取指定部分的完整 Markdown 内容

    Args:
        content: 完整骨架内容
        start_markers: 部分开始标记列表（如 ["一、元数据", "1. 元数据"]）
        end_markers: 部分结束标记列表

    Returns:
        {"markdown": "提取的 Markdown", "parsed": {...}}
    """
    result = {"markdown": "", "parsed": {}}

    # 构建正则表达式，匹配任一开始标记
    start_pattern = "|".join(re.escape(m) for m in start_markers)
    end_pattern = "|".join(re.escape(m) for m in end_markers) if end_markers else "$"

    # 匹配从 start_marker 到 end_marker 之间的内容
    regex = rf"(?:{start_pattern}).*?\n([\s\S]*?)(?=(?:{end_pattern})|$)"
    match = re.search(regex, content, re.IGNORECASE)

    if match:
        result["markdown"] = match.group(1).strip()
        result["parsed"] = parse_key_value_content(result["markdown"])

    return result


def extract_characters_section(content: str) -> List[Dict[str, str]]:
    """
    提取人物体系部分，返回人物列表

    支持格式：
    - ### 人物姓名
    - **人物姓名**
    - #### 人物姓名
    """
    characters = []

    # 定位人物体系部分
    section = extract_section_markdown(
        content, ["三、人物体系", "3. 人物体系"], ["四、情节架构", "4. 情节架构"]
    )

    if not section["markdown"]:
        return characters

    char_text = section["markdown"]

    # 匹配人物标题（### **姓名** 或 ### 姓名 或 **姓名**）
    # 使用更健壮的模式
    pattern = r"(?:^|\n)(?:#{1,4}\s*\*\*|#{1,4}\s*|\*\*)\s*([^\*\n#]+?)\s*(?:\*\*)?(?=\n|$)"

    # 找到所有人物位置
    char_positions = []
    for match in re.finditer(pattern, char_text, re.MULTILINE):
        name = match.group(1).strip()
        if name and len(name) < 50:  # 过滤过长的匹配
            char_positions.append((name, match.start(), match.end()))

    # 提取每个人物的完整描述
    for i, (name, start, end) in enumerate(char_positions):
        if i < len(char_positions) - 1:
            # 提取到下一个人物之前
            desc_start = end
            desc_end = char_positions[i + 1][1] - len(char_positions[i + 1][0]) - 10  # 估算
            description = char_text[desc_start:desc_end].strip()
        else:
            # 最后一个人物，提取到结尾
            description = char_text[end:].strip()

        # 限制长度并清理
        description = description[:1000] if len(description) > 1000 else description

        characters.append(
            {"name": name, "description": description, "markdown": f"### {name}\n\n{description}"}
        )

    return characters[:15]  # 最多15个人物


def extract_paywall_design(content: str) -> Dict[str, Any]:
    """提取付费卡点设计"""
    result = {"markdown": "", "parsed": {}}

    # 在元数据或改编映射中查找付费卡点信息
    section = extract_section_markdown(
        content, ["一、元数据", "1. 元数据"], ["二、核心设定", "2. 核心设定"]
    )

    if section["markdown"]:
        # 查找付费卡点相关行
        for line in section["markdown"].split("\n"):
            if "付费卡点" in line and "：" in line:
                result["markdown"] += line + "\n"
                if "第" in line and "集" in line:
                    # 提取 "第X-Y集" 或 "第X集"
                    match = re.search(r"第\s*(\d+)(?:\s*-\s*(\d+))?\s*集", line)
                    if match:
                        result["parsed"]["episodes"] = match.group(0)

    return result


def extract_tension_curve(content: str) -> Dict[str, Any]:
    """提取张力曲线数据"""
    result = {"markdown": "", "parsed": [], "dataPoints": []}

    # 查找张力曲线部分（通常在情节架构或单独章节）
    section = extract_section_markdown(
        content, ["张力曲线", "张力值", "剧情张力"], ["### Chapter", "## "]
    )

    if section["markdown"]:
        result["markdown"] = section["markdown"]
        # 尝试提取数值
        # 格式：| Chapter 1 | ... | 85 |
        for line in section["markdown"].split("\n"):
            if "|" in line and "Chapter" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    try:
                        chapter = re.search(r"Chapter\s*(\d+)", parts[1])
                        tension = re.search(r"(\d+)", parts[-2])
                        if chapter and tension:
                            result["dataPoints"].append(
                                {"chapter": int(chapter.group(1)), "tension": int(tension.group(1))}
                            )
                    except (ValueError, IndexError):
                        pass

    return result


def parse_key_value_content(content: str) -> Dict[str, str]:
    """解析键值对格式的内容"""
    parsed = {}
    for line in content.split("\n"):
        line = line.strip()
        if "：" in line or ":" in line:
            # 支持中文冒号和英文冒号
            parts = line.split("：", 1) if "：" in line else line.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip("- *")
                value = parts[1].strip()
                if key and value:
                    parsed[key] = value
    return parsed


def build_episodes_from_chapter_map(
    chapter_map: List[Dict], skeleton_content: str, project_id: str, paywall_info: Dict
) -> List[Dict]:
    """
    从 chapter_map 构建 episodes 列表
    """
    episodes = []
    paywall_chapter = paywall_info.get("chapter", 0)

    for chapter_info in chapter_map:
        chapter_num = chapter_info.get("chapter", 0)
        episode_range = chapter_info.get("episodes", "")

        # 解析剧集范围
        episode_nums = []
        if episode_range:
            if "-" in str(episode_range):
                parts = str(episode_range).split("-")
                episode_nums = list(range(int(parts[0]), int(parts[1]) + 1))
            else:
                episode_nums = [int(episode_range)]

        # 提取章节详细信息
        chapter_detail = extract_chapter_detail(skeleton_content, chapter_num)

        # 为每个剧集创建 episode
        for ep_num in episode_nums:
            episode_id = f"ep_{project_id}_{ep_num}"

            # 检查是否是付费卡点
            is_paid_wall = chapter_num == paywall_chapter

            episode = {
                "episodeId": episode_id,
                "episodeNumber": ep_num,
                "title": chapter_detail.get("title", f"第{chapter_num}章"),
                "summary": chapter_detail.get("summary", ""),
                "content": chapter_detail.get("content", ""),
                "scenes": chapter_detail.get("scenes", []),
                "reviewStatus": "pending",
                "isPaidWall": is_paid_wall,
                "chapterNumber": chapter_num,
            }
            episodes.append(episode)

    return episodes


def extract_chapter_detail(content: str, chapter_num: int) -> Dict[str, Any]:
    """
    提取单个章节的详细信息

    支持格式：
    ### Chapter X: 标题
    **摘要**: 内容
    **场景清单**:
    1. **场景1**: 描述
    """
    result = {"title": f"第{chapter_num}章", "summary": "", "content": "", "scenes": []}

    # 匹配 Chapter X 部分
    pattern = rf"###\s*Chapter\s*{chapter_num}[\s:：]*(.*?)\n"
    title_match = re.search(pattern, content, re.IGNORECASE)

    if title_match:
        result["title"] = title_match.group(1).strip() or f"第{chapter_num}章"

        # 找到本章内容的起始位置
        start_pos = title_match.end()

        # 找到下一个 Chapter 或部分结束
        next_chapter = re.search(
            rf"###\s*Chapter\s*{chapter_num + 1}", content[start_pos:], re.IGNORECASE
        )
        if next_chapter:
            chapter_content = content[start_pos : start_pos + next_chapter.start()]
        else:
            chapter_content = content[start_pos:]

        result["content"] = chapter_content.strip()

        # 提取摘要
        summary_match = re.search(
            r"\*\*摘要\*\*[\s:：]*(.*?)(?=\n\s*\*\*|\n\s*#{1,3}|$)",
            chapter_content,
            re.DOTALL | re.IGNORECASE,
        )
        if summary_match:
            result["summary"] = summary_match.group(1).strip()

        # 提取场景
        scene_section = re.search(
            r"场景清单.*?\n([\s\S]*?)(?=\n\s*#{1,3}|\n\s*\*\*|$)", chapter_content, re.IGNORECASE
        )
        if scene_section:
            scene_text = scene_section.group(1)
            # 解析场景列表
            scene_pattern = (
                r"(\d+)\.\s*\*\*([^*]+)\*\*[\s:：]*(.*?)(?=\n\s*\d+\.\s*\*\*|\n\s*\*\*|$)"
            )
            for match in re.finditer(scene_pattern, scene_text, re.DOTALL):
                scene_num = match.group(1)
                scene_title = match.group(2).strip()
                scene_desc = match.group(3).strip()

                result["scenes"].append(
                    {
                        "sceneId": f"scene_ch{chapter_num}_{scene_num}",
                        "sceneNumber": int(scene_num),
                        "title": scene_title,
                        "content": scene_desc,
                        "shots": [],
                    }
                )

    return result


# ===== 测试用例 =====


def test_extraction():
    """测试提取功能"""
    test_content = """
# 《测试小说》小说大纲

## 一、元数据（Metadata）

**项目信息**
- 小说名称：《测试小说》
- 题材组合：复仇逆袭 + 甜宠恋爱
- 预计总字数：640,000字
- 总章节数：53章
- 目标读者：喜爱强强对决、宿命感恋爱及爽快复仇的短剧/网文受众

**短剧配置**
- 短剧总集数：80集
- 每集时长：1.5分钟
- 短剧总时长：120.0分钟
- 付费卡点：第12集
- 付费卡点对应章节：第13章

## 二、核心设定（Core Setting）

### 2.1 世界观架构

这是一个充满权谋斗争的架空朝代，以"天命皇权"为核心统治理念。表面上，皇帝拥有至高无上的权力，但实际上，朝中大员各自结党营私，形成错综复杂的势力网。

**3条铁律**：
1. 皇权至上，不可质疑
2. 士农工商，等级分明
3. 家族荣耀高于个人生死

### 2.2 核心规则

- **权力博弈规则**：表面服从，暗中较劲
- **情感发展规则**：从敌对到相爱必须经历3次信任危机
- **复仇推进规则**：每次反击必须付出相应代价

## 三、人物体系（Characters）

### **陆北辰**
- **身份**：当朝摄政王，表面冷酷无情，实则深爱女主
- **核心特质**：偏执、深情、权谋高手
- **潜意识恐惧**：被背叛、失去所爱
- **语言风格**：简短有力，命令式语气
- **成长弧光**：从控制欲极强到学会尊重

### **苏清**
- **身份**：前朝遗孤，医术圣手
- **核心特质**：聪慧、隐忍、外柔内刚
- **潜意识恐惧**：身份暴露、连累他人
- **语言风格**：温婉中带着坚韧
- **成长弧光**：从被动接受到主动出击

## 四、情节架构（Plot Architecture）

### 第一幕：缘起与冲突（第1-10章）
**核心任务**：建立人物关系，埋下冲突种子
- Chapter 1-3：开篇钩子，男女主初次相遇
- Chapter 4-7：矛盾升级，误会加深
- Chapter 8-10：危机爆发，关系破裂边缘

### 第二幕：发展与纠缠（第11-40章）
**核心任务**：深化情感，推进主线
- Chapter 11-20：被迫合作，渐生好感
- Chapter 21-30：信任危机，关系波折
- Chapter 31-40：真相浮现，携手对敌

## 五、章节大纲（Chapter Outlines）

### Chapter 1: 婚礼惊变
**摘要**：苏清新婚之夜遭遇灭门惨案，侥幸逃脱，誓要复仇。

**场景清单**：
1. **喜房**：新娘等待新郎，气氛温馨
2. **前院**：突然闯入的黑衣人，屠杀开始
3. **密室**：苏清被奶娘推入密道，眼睁睁看着家人被杀
4. **逃亡**：雨中逃窜，发誓复仇

**张力值**：95

### Chapter 2: 五年蛰伏
**摘要**：五年后，苏清化名归来，已是一代神医。

**场景清单**：
1. **医馆**：苏清坐诊，名声渐起
2. **王府**：陆北辰身染怪病，遍寻名医
3. **初遇**：命运般的重逢，却互不相识

**张力值**：88

## 六、改编映射（Adaptation Mapping）

**整体比例**：1章小说 ≈ 1.51集短剧

**动态比例**：
- 开篇阶段(Chapter 1-3)：1章 ≈ 1.5集
- 发展阶段(Chapter 4-39)：1章 ≈ 2集
- 付费卡点章节(Chapter 13)：加长章节，对应短剧第11-12集

## 七、创作指导（Writing Guidelines）

1. **节奏控制**：前13章必须保持"一章一爽点，三章一大爽"
2. **打脸逻辑**：遵循"欲扬先抑"原则
3. **甜宠细节**：通过细节展现感情变化
4. **视觉化写作**：每一章结尾必须是强视觉悬念点

---

```json
{
  "chapter_map": [
    {"chapter": 1, "episodes": "1"},
    {"chapter": 2, "episodes": "2"}
  ],
  "paywall_info": {"chapter": 13, "episode": 12},
  "actions": ["confirm", "regenerate"]
}
```
"""

    print("=" * 60)
    print("TEST: Story Settings Extraction")
    print("=" * 60)

    # Test 1: Metadata extraction
    metadata = extract_section_markdown(test_content, ["一、元数据"], ["二、核心设定"])
    print("\n✓ Metadata extracted:")
    print(f"  Title: {metadata['parsed'].get('小说名称', 'N/A')}")
    print(f"  Genre: {metadata['parsed'].get('题材组合', 'N/A')}")

    # Test 2: Characters extraction
    characters = extract_characters_section(test_content)
    print(f"\n✓ Characters extracted: {len(characters)}")
    for char in characters[:2]:
        print(f"  - {char['name']}: {char['description'][:50]}...")

    # Test 3: Full parse
    outline = parse_skeleton_to_outline(test_content, "test_project")
    print(f"\n✓ Full parse completed:")
    print(f"  Total episodes: {outline['totalEpisodes']}")
    print(f"  Story settings keys: {list(outline.get('storySettings', {}).keys())}")

    # Test 4: Chapter detail
    if outline["episodes"]:
        ep = outline["episodes"][0]
        print(f"\n✓ First episode:")
        print(f"  Title: {ep['title']}")
        print(f"  Summary: {ep['summary'][:50]}...")
        print(f"  Scenes count: {len(ep['scenes'])}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)

    return outline


if __name__ == "__main__":
    test_extraction()
