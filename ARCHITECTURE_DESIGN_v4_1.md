# AI短剧生成引擎 - 架构设计文档 (v4.1)

**版本**: v4.1 (Prompts整合版)  
**日期**: 2026-02-07  
**状态**: ✅ 基于 LangGraph 官方定义 + Prompts文件整合  
**变更**: 删除内联Prompt，改为从prompts/文件夹加载并动态注入主题库数据

---

## 🎯 核心架构变更（v4.0 → v4.1）

### v4.0 的问题
- ❌ System Prompts 内联在文档中（600-800行）
- ❌ 与 prompts/ 文件夹的现有Prompt重复
- ❌ 没有展示如何动态注入主题库数据

### v4.1 的解决方案
- ✅ 所有Prompt统一存放在 `prompts/` 文件夹
- ✅ v4.1 文档展示**如何加载** + **如何注入数据**
- ✅ 运行时动态组装：Base Prompt + 主题库数据 + 用户输入

---

## 📁 正确的文件组织

```
backend/
│
├── prompts/                          # ⭐ 所有System Prompts
│   ├── 0_Master_Router.md            # 主路由
│   ├── 1_Market_Analyst.md           # 市场分析
│   ├── 2_Story_Planner.md            # 故事策划 ⭐核心
│   ├── 3_Skeleton_Builder.md         # 大纲构建
│   ├── 4_Novel_Writer.md             # 小说创作 ⭐核心
│   ├── 5_Script_Adapter.md           # 剧本改编
│   ├── 6_Storyboard_Director.md      # 分镜设计
│   ├── 7_Editor_Reviewer.md          # 编辑审阅
│   ├── 8_Refiner.md                  # 精修优化
│   ├── 9_Analysis_Lab.md             # 分析实验室
│   ├── 10_Asset_Inspector.md         # 资产探查
│   └── 11_Image_Generator.md         # 图像生成
│
├── skills/                           # ⭐ Tool/Skill 层
│   ├── theme_library.py              # 主题库查询
│   ├── writing_assistant.py          # 写作辅助
│   └── visual_assistant.py           # 视觉辅助
│
├── agents/                           # ⭐ Agent 层
│   └── story_planner/
│       ├── genre_strategist.py       # 加载prompts/2_Story_Planner.md
│       ├── concept_generator.py      # 加载prompts/2_Story_Planner.md
│       └── ...
│
└── graph/                            # ⭐ Graph 层
    └── workflows/
        └── story_planner_graph.py    # 编排Agent执行
```

**关键原则**：
1. **Prompt即代码** - prompts/中的文件是可版本控制的代码
2. **动态组装** - 运行时加载 + 数据注入
3. **单一来源** - 不再内联Prompt，全部来自prompts/

---

## 1. Prompt加载与数据注入机制

### 1.1 核心流程

```
用户输入 + 题材ID
    ↓
Agent创建函数
    ├─ 1. 从 prompts/ 加载 Base Prompt
    ├─ 2. 调用 Skills 查询主题库数据
    │     ├─ load_genre_context(genre_id)
    │     ├─ get_tropes(genre_id)
    │     └─ get_market_trends(genre_id)
    ├─ 3. 动态组装完整Prompt
    │     Base Prompt + 主题库数据 + 用户输入
    └─ 4. 创建 Agent (create_react_agent)
          ├─ model
          ├─ tools (主题库Skills)
          └─ prompt (组装后的完整Prompt)
    ↓
Agent执行（可自主调用Tools）
```

### 1.2 代码实现示例

```python
# backend/agents/story_planner/genre_strategist.py

"""
Genre Strategist Agent

职责：基于用户输入和主题库数据，制定题材策略。

关键：动态加载Prompt + 注入主题库数据
"""

import os
from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes, 
    get_market_trends
)
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType

# Prompt文件路径
PROMPT_FILE = "prompts/2_Story_Planner.md"


def create_genre_strategist_agent(user_id: str, genre_id: str):
    """
    创建 Genre Strategist Agent
    
    流程：
    1. 从 prompts/2_Story_Planner.md 加载基础Prompt
    2. 调用 Skills 查询主题库（复仇/甜宠等题材数据）
    3. 组装完整Prompt（基础 + 主题库数据 + 用户配置）
    4. 创建Agent（带Tools调用能力）
    """
    
    # ===== Step 1: 加载基础Prompt =====
    if not os.path.exists(PROMPT_FILE):
        raise FileNotFoundError(f"Prompt文件不存在: {PROMPT_FILE}")
    
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
    
    # ===== Step 2: 查询主题库数据 =====
    # 这些是"预注入"的数据，Agent创建时就确定
    print(f"[GenreStrategist] 正在查询主题库: {genre_id}")
    
    theme_data = load_genre_context(genre_id)           # 完整题材指导
    tropes_data = get_tropes(genre_id, limit=5)         # 推荐元素
    market_data = get_market_trends(genre_id)           # 市场趋势
    
    # ===== Step 3: 动态组装完整Prompt =====
    # 替换 prompts/2_Story_Planner.md 中的变量占位符
    full_prompt = base_prompt.format(
        # 主题库数据注入（核心！）
        theme_library_data=theme_data,
        recommended_tropes=tropes_data,
        market_trends=market_data,
        
        # 用户配置
        user_config=get_user_config(user_id),
        genre=genre_id,
        
        # 其他上下文
        market_report="最新市场报告数据...",
        user_selection=genre_id
    )
    
    print(f"[GenreStrategist] Prompt组装完成，长度: {len(full_prompt)} 字符")
    
    # ===== Step 4: 创建Agent =====
    router = get_model_router()
    model = router.get_model(user_id=user_id, task_type=TaskType.STORY_PLANNER)
    
    agent = create_react_agent(
        model=model,
        tools=[
            load_genre_context,    # Agent可自主调用
            get_tropes,            # Agent可自主调用
            get_market_trends      # Agent可自主调用
        ],
        prompt=full_prompt,
        max_iterations=5,          # 最大Tool调用次数
        handle_parsing_errors=True
    )
    
    return agent


def get_user_config(user_id: str) -> dict:
    """获取用户配置"""
    # 从数据库或缓存获取
    return {
        "episode_count": 80,
        "episode_duration": 1.5,
        "genre": "revenge",
        "setting": "modern_urban"
    }
```

### 1.3 Prompt组装原理

**prompts/2_Story_Planner.md**（基础模板）:
```markdown
# 系统提示：AI 故事策划师（二级）

## 动态注入的主题库数据

### 题材指导（已自动注入）
{theme_library_data}

### 推荐元素（已自动注入）
{recommended_tropes}

### 市场趋势（已自动注入）
{market_trends}

### 用户配置（已自动注入）
总集数: {user_config[episode_count]}
每集时长: {user_config[episode_duration]}分钟
题材: {genre}

---

## 你的任务
基于上述已注入的数据，制定最优的题材策略...
```

**组装后**（运行时）:
```markdown
# 系统提示：AI 故事策划师（二级）

## 动态注入的主题库数据

### 题材指导（已自动注入）
## 题材指导：复仇逆袭

### 核心公式
- Setup: 极端羞辱或背叛
- Rising: 积累实力/隐藏身份
- Climax: 身份揭露+打脸
...

### 推荐元素（已自动注入）
1. **身份揭露** - 主角真实身份在关键时刻暴露...
2. **隐藏大佬** - 主角表面是底层，实则是顶层...
...

### 市场趋势（已自动注入）
- 热门度: 95/100
- 成功率: 88%
...

### 用户配置（已自动注入）
总集数: 80
每集时长: 1.5分钟
题材: revenge

---

## 你的任务
基于上述已注入的数据，制定最优的题材策略...
```

---

## 2. 所有Agents的Prompt加载模式

### 2.1 Story Planner Agents

```python
# backend/agents/story_planner/concept_generator.py

from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes,
    get_hooks,
    get_trending_combinations
)

PROMPT_FILE = "prompts/2_Story_Planner.md"  # 同一个文件，不同段落

def create_concept_generator_agent(user_id: str, genre_id: str):
    """
    Concept Generator Agent
    
    基于主题库数据，生成10个粗糙概念
    """
    
    # 加载Prompt
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
    
    # 查询主题库（Concept Generator需要的数据）
    theme_data = load_genre_context(genre_id)
    tropes = get_tropes(genre_id, limit=5)
    hooks = get_hooks(genre_id)
    trending = get_trending_combinations()
    
    # 组装Prompt
    full_prompt = base_prompt.format(
        theme_library_data=theme_data,
        recommended_tropes=tropes,
        available_hooks=hooks,
        trending_combinations=trending,
        user_config=get_user_config(user_id),
        genre=genre_id
    )
    
    # 创建Agent
    agent = create_react_agent(
        model=get_model(user_id),
        tools=[
            load_genre_context,
            get_tropes,
            get_hooks,
            get_trending_combinations
        ],
        prompt=full_prompt
    )
    
    return agent
```

### 2.2 Novel Writer Agents

```python
# backend/agents/novel_writer/content_generator.py

from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import get_writing_keywords
from backend.skills.writing_assistant import get_sensory_guide, get_pacing_rules

PROMPT_FILE = "prompts/4_Novel_Writer.md"

def create_content_generator_agent(user_id: str, genre_id: str, episode_number: int):
    """
    Content Generator Agent
    
    基于主题库写作指导，生成小说正文
    """
    
    # 加载Prompt
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
    
    # 查询写作相关的主题库数据
    writing_keywords = get_writing_keywords(genre_id)
    sensory_guide = get_sensory_guide(scene_type="conflict")
    pacing_rules = get_pacing_rules(genre_id, episode_position="middle")
    
    # 组装Prompt
    full_prompt = base_prompt.format(
        # 主题库写作指导
        writing_keywords=writing_keywords,
        sensory_vocabulary=sensory_guide,
        pacing_requirements=pacing_rules,
        
        # 上下文
        genre=genre_id,
        episode_number=episode_number,
        user_config=get_user_config(user_id)
    )
    
    # 创建Agent
    agent = create_react_agent(
        model=get_model(user_id),
        tools=[
            get_writing_keywords,
            get_sensory_guide,
            get_pacing_rules
        ],
        prompt=full_prompt
    )
    
    return agent
```

### 2.3 Asset Inspector Agent

```python
# backend/agents/asset_inspector/asset_inspector.py

from langgraph.prebuilt import create_react_agent
from backend.skills.visual_assistant import get_camera_style, get_visual_keywords

PROMPT_FILE = "prompts/10_Asset_Inspector.md"

def create_asset_inspector_agent(user_id: str, genre_id: str):
    """
    Asset Inspector Agent
    
    基于主题库视觉指导，提取和设计资产
    """
    
    # 加载Prompt
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
    
    # 查询视觉相关的主题库数据
    visual_keywords = get_visual_keywords(genre_id)
    camera_style = get_camera_style(genre_id, scene_mood="tense")
    
    # 组装Prompt
    full_prompt = base_prompt.format(
        # 主题库视觉指导
        visual_keywords=visual_keywords,
        camera_style_guide=camera_style,
        genre=genre_id
    )
    
    # 创建Agent
    agent = create_react_agent(
        model=get_model(user_id),
        tools=[
            get_visual_keywords,
            get_camera_style
        ],
        prompt=full_prompt
    )
    
    return agent
```

---

## 3. Graph工作流中的Prompt加载

### 3.1 Story Planner Graph

```python
# backend/graph/workflows/story_planner_graph.py

"""
Story Planner Graph

串联5个Agents，每个Agent都从prompts/加载Prompt
"""

from langgraph.graph import StateGraph, START, END
from backend.schemas.agent_state import AgentState

# 导入Agent创建函数
from backend.agents.story_planner.genre_strategist import create_genre_strategist_agent
from backend.agents.story_planner.concept_generator import create_concept_generator_agent
from backend.agents.story_planner.market_assessor import create_market_assessor_agent
from backend.agents.story_planner.premise_engineer import create_premise_engineer_agent
from backend.agents.story_planner.planner_core import create_planner_core_agent


def build_story_planner_graph(user_id: str, genre_id: str):
    """
    构建 Story Planner Graph
    
    每个Node都是一个Agent，都从prompts/加载自己的Prompt
    """
    
    # 创建5个Agents（每个都加载自己的Prompt）
    genre_strategist = create_genre_strategist_agent(user_id, genre_id)
    concept_generator = create_concept_generator_agent(user_id, genre_id)
    market_assessor = create_market_assessor_agent(user_id, genre_id)
    premise_engineer = create_premise_engineer_agent(user_id, genre_id)
    planner_core = create_planner_core_agent(user_id, genre_id)
    
    # 构建Graph
    workflow = StateGraph(AgentState)
    
    # 添加Nodes（每个Agent就是一个Node）
    workflow.add_node("genre_strategist", genre_strategist)
    workflow.add_node("concept_generator", concept_generator)
    workflow.add_node("market_assessor", market_assessor)
    workflow.add_node("premise_engineer", premise_engineer)
    workflow.add_node("planner_core", planner_core)
    
    # 定义边（执行顺序）
    workflow.set_entry_point("genre_strategist")
    workflow.add_edge("genre_strategist", "concept_generator")
    workflow.add_edge("concept_generator", "market_assessor")
    workflow.add_edge("market_assessor", "premise_engineer")
    workflow.add_edge("premise_engineer", "planner_core")
    workflow.add_edge("planner_core", END)
    
    return workflow.compile()
```

---

## 4. 主题库数据获取策略

### 4.1 数据来源（补充章节）

**Phase 1: 手动整理种子数据（Week 1）**

```python
# scripts/create_seed_data.py

def create_minimal_seed_data():
    """
    创建最小可运行的种子数据
    基于10部爆款短剧人工提取
    """
    
    seed_data = {
        "themes": [
            {
                "id": "theme_revenge",
                "name": "复仇逆袭",
                "slug": "revenge",
                "core_formula": {
                    "setup": {
                        "description": "极端羞辱或背叛",
                        "duration_episodes": "1-2集",
                        "key_elements": ["羞辱场景", "围观反应", "隐忍表现"],
                        "emotional_goal": "让观众产生同情和愤怒",
                        "avoid": "不要过度虐待（不超过3集无反击）"
                    },
                    "rising": {
                        "description": "积累实力/隐藏身份",
                        "duration_episodes": "3-15集",
                        "pacing": "每3集一个小打脸",
                        "key_elements": ["实力积累", "小反击", "身份暗示"]
                    },
                    "climax": {
                        "description": "身份揭露+连续打脸",
                        "duration_episodes": "第15-20集",
                        "execution": "身份揭露→打脸1→打脸2→打脸3",
                        "visual_requirements": "特写、慢动作、强烈对比"
                    },
                    "resolution": {
                        "description": "正义伸张，反派悔过",
                        "duration_episodes": "最后5集",
                        "avoid": "圣母原谅（必须彻底胜利）"
                    }
                },
                "keywords": {
                    "writing": ["红眼", "掐腰", "居高临下", "冷笑", "颤抖"],
                    "visual": ["破碎感", "逆光", "高对比", "权力象征"]
                },
                "tropes": [
                    {
                        "name": "身份揭露",
                        "description": "主角真实身份在关键时刻暴露",
                        "effectiveness_score": 95,
                        "usage_timing": "第10-15集"
                    },
                    {
                        "name": "隐藏大佬",
                        "description": "主角表面是底层，实则是顶层",
                        "effectiveness_score": 92,
                        "usage_timing": "贯穿全剧"
                    }
                ],
                "hooks": [
                    {
                        "type": "situation",
                        "name": "极限羞辱",
                        "template": "主角正在遭受[羞辱]，倒计时[3,2,1]即将反击",
                        "effectiveness_score": 95
                    }
                ]
            }
        ]
    }
    
    return seed_data
```

**Phase 2: AI扩展（Week 2）**

```python
# scripts/ai_generate_variations.py

from backend.services.model_router import get_model_router

def generate_trope_variations(base_trope: dict, count: int = 5):
    """
    基于基础元素，AI生成变体
    """
    
    prompt = f"""
    基于以下爆款元素，生成{count}个创新变体：
    
    基础元素: {base_trope['name']}
    描述: {base_trope['description']}
    
    要求：
    1. 保持核心情绪价值
    2. 添加创新twist
    3. 适合不同子题材
    
    输出JSON数组格式。
    """
    
    model = get_model_router().get_model(task_type="data_generation")
    response = model.invoke(prompt)
    
    return parse_json(response.content)
```

**Phase 3: 持续更新（长期）**

```python
# backend/services/theme_updater.py

class ThemeLibraryUpdater:
    """主题库自动更新服务"""
    
    async def daily_update(self):
        """每日更新"""
        # 1. 抓取最新爆款
        viral_dramas = await scrape_viral_dramas()
        
        # 2. 分析新趋势
        new_trends = await analyze_trends(viral_dramas)
        
        # 3. 更新热门组合
        await update_trending_combinations(new_trends)
        
        # 4. 调整元素权重
        await adjust_element_weights(new_trends)
```

---

## 5. Prompt更新检查清单

### 所有Prompts需要添加的内容：

#### ✅ 2_Story_Planner.md（已完成，详见下方）
- [x] 主题库注入变量说明
- [x] 可用的Tools说明
- [x] 工作流程指导

#### ⏳ 其他Prompts待更新
- [ ] 1_Market_Analyst.md - 添加市场数据来源说明
- [ ] 3_Skeleton_Builder.md - 添加主题库节奏模板
- [ ] 4_Novel_Writer.md - 添加写作关键词注入
- [ ] 5_Script_Adapter.md - 添加转场风格指导
- [ ] 6_Storyboard_Director.md - 添加视觉风格注入
- [ ] 10_Asset_Inspector.md - 添加视觉关键词注入

---

## 6. 文档历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2026-02-07 | 完整架构设计，但内联Prompts |
| v4.1 | 2026-02-07 | **改为从prompts/加载，动态注入主题库数据** |

---

**关键改进**：
1. ✅ Prompt统一存放在prompts/文件夹
2. ✅ 运行时动态加载 + 主题库数据注入
3. ✅ 展示了完整的Agent创建代码
4. ✅ 补充了主题库数据获取策略

**下一步**：更新所有prompts/文件，添加主题库注入说明
