# AI短剧生成引擎 - 正确架构设计文档 (v4.2)

**版本**: v4.2 (分批生成架构版)  
**日期**: 2026-02-10  
**状态**: ✅ 基于 LangGraph 官方文档验证 + 分批生成架构实现  
**历史文档**: 
- `Story_Planner_Architecture_Design.md` (v1.0) - 保留作为业务逻辑参考
- `ARCHITECTURE_DESIGN_v3_CORRECT.md` (v3.0) - 概念修正但未完全遵循官方模式

---

## 🎯 关键概念澄清（基于 LangGraph 官方文档验证）

根据官方文档和示例代码验证，正确的概念关系：

### 1. Node 与 Agent 的关系（已验证）

**官方定义**:
> "This graph is composed of nodes, which are the individual steps or agents in your application"

**正确理解**:
```
Node（节点）= 执行单元（最宽泛的概念）
├── Agent（智能体）= 特殊的 Node，具有自主决策和 Tool 调用能力
├── ToolNode（工具节点）= 专门执行 Tools 的 Node
└── Simple Function（普通函数）= 执行固定逻辑的 Node
```

**关键结论**:
- ✅ **Agent 是 Node 的子集**（不是所有 Node 都是 Agent）
- ✅ **Agent 必须具有 Tool 调用能力和自主决策能力**
- ✅ **create_react_agent() 返回 Compiled Graph**，既是 Agent 也是 Node

### 2. create_react_agent 返回什么（已验证）

```python
from langgraph.prebuilt import create_react_agent

# create_react_agent 返回 CompiledStateGraph
agent = create_react_agent(model, tools)  # 这是一个 CompiledStateGraph

# 可以直接 invoke
agent.invoke({"messages": [...]})

# 也可以作为 Node 添加到另一个 Graph
workflow.add_node("agent", agent)  # ✅ 可以直接使用
```

### 3. Tool/Skill 的定义与使用（已验证）

```python
from langchain_core.tools import tool

@tool
def load_theme_context(genre_id: str) -> str:
    """Skill: 加载题材上下文
    
    这是一个 Tool，也是 LangChain Multi-Agent 中的 Skill
    Prompt-driven specialization
    """
    genre = db.query("theme_genres", genre_id)
    return f"""
    ## 题材：{genre.name}
    - 核心公式：{genre.core_formula}
    - 推荐元素：{genre.tropes}
    """

# Tool 作为参数传递给 create_react_agent
agent = create_react_agent(
    model=model,
    tools=[load_theme_context, get_tropes]  # Skills 作为 Tools 被 Agent 调用
)
```

**关键结论**:
- ✅ **在 LangGraph 中，Skill 就是 Tool**
- ✅ **Tool 只能被 Agent 调用**（通过 create_react_agent 或 ToolNode）
- ✅ **普通 Node 不应该直接调用 Tool**

### 4. 正确的组件关系表

| 组件 | 官方定义 | 可以被谁调用 | 示例 |
|------|---------|-------------|------|
| **Tool** | 可执行函数，使用 `@tool` 装饰 | 被 Agent 调用 | `get_weather()` |
| **Skill** | Prompt-driven Tool（LangChain 概念） | 被 Agent 调用 | `load_theme_context()` |
| **Agent** | 具有 Tool 调用能力的 Node | 作为 Node 被 Graph 调用 | `create_react_agent()` 返回值 |
| **Node** | Graph 的执行单元 | 被 Graph 调用 | Agent / ToolNode / 普通函数 |
| **Graph** | StateGraph 编译后的工作流 | 被其他 Graph 或外部调用 | `workflow.compile()` 返回值 |

### 5. 常见误区纠正

#### ❌ 误区 1："Node = Agent"

**错误**:
```python
async def my_node(state: AgentState) -> Dict:
    """这是一个 Node，也就是一个 Agent"""  # ❌ 错误！
    theme = await load_theme_context(...)  # ❌ 普通 Node 不能直接调用 Tool
```

**正确**:
```python
# 普通 Node 只执行固定逻辑
def format_output_node(state: AgentState) -> Dict:
    """这是一个普通 Node，不是 Agent"""
    formatted = format_for_ui(state["raw_output"])
    return {"formatted_output": formatted}

# Agent 使用 create_react_agent 创建
from langgraph.prebuilt import create_react_agent

genre_strategist_agent = create_react_agent(
    model=router.get_model(task_type=TaskType.STORY_PLANNER),
    tools=[load_genre_context, get_tropes, get_market_trends],
    prompt=GENRE_STRATEGIST_SYSTEM_PROMPT
)  # ✅ 这是 Agent，具有 Tool 调用能力
```

#### ❌ 误区 2："普通函数可以调用 Skill"

**错误**:
```python
async def concept_generator_node(state):
    tropes = await get_tropes.ainvoke(...)  # ❌ 普通 Node 不应该直接调用 Tool
    return {"tropes": tropes}
```

**正确**:
```python
# Agent 自动决定何时调用 Tools
concept_generator_agent = create_react_agent(
    model=model,
    tools=[get_tropes, get_hooks, get_trending_combinations],
    prompt=CONCEPT_GENERATOR_PROMPT
)
# Agent 会根据 Prompt 和上下文自动调用 Tools
```

---

## 1. 正确目录结构

```
backend/
│
├── prompts/                         # ⭐ System Prompts (所有Agent的Prompt来源)
│   ├── 0_Master_Router.md           # 主路由
│   ├── 1_Market_Analyst.md          # 市场分析
│   ├── 2_Story_Planner.md           # 故事策划 ⭐核心
│   ├── 3_Skeleton_Builder.md        # 大纲构建
│   ├── 4_Novel_Writer.md            # 小说创作 ⭐核心
│   ├── 5_Script_Adapter.md          # 剧本改编
│   ├── 6_Storyboard_Director.md     # 分镜设计
│   ├── 7_Editor_Reviewer.md         # 编辑审阅
│   ├── 8_Refiner.md                 # 精修优化
│   ├── 9_Analysis_Lab.md            # 分析实验室
│   ├── 10_Asset_Inspector.md        # 资产探查
│   └── 11_Image_Generator.md        # 图像生成
│
├── skills/                          # ⭐ Tool/Skill 层 (Prompt-driven Tools)
│   ├── __init__.py
│   ├── theme_library.py             # 题材库查询 Skill (Tool)
│   │   ├── load_genre_context       # Tool: 加载题材上下文
│   │   ├── get_tropes               # Tool: 获取推荐元素
│   │   ├── get_hooks                # Tool: 获取钩子模板
│   │   ├── get_character_archetypes # Tool: 获取角色原型
│   │   ├── get_writing_keywords     # Tool: 获取写作关键词
│   │   └── get_visual_keywords      # Tool: 获取视觉关键词
│   │
│   ├── writing_assistant.py         # 写作辅助 Skill
│   │   ├── get_sensory_guide        # Tool: 获取五感指导
│   │   ├── get_pacing_rules         # Tool: 获取节奏规则
│   │   └── get_trending_combinations # Tool: 获取热门组合
│   │
│   └── visual_assistant.py          # 视觉辅助 Skill
│       ├── get_camera_style         # Tool: 获取镜头风格
│       └── get_visual_keywords      # Tool: 获取视觉关键词
│
├── agents/                          # ⭐ Agent 层 (create_react_agent 创建)
│   ├── __init__.py
│   ├── story_planner/               # Story Planner Agents
│   │   ├── __init__.py
│   │   ├── genre_strategist.py      # Agent: 题材策略师
│   │   ├── concept_generator.py     # Agent: 概念生成器
│   │   ├── market_assessor.py       # Agent: 市场测评员
│   │   ├── premise_engineer.py      # Agent: 梗概工程师
│   │   └── planner_core.py          # Agent: 整合核心
│   │
│   ├── skeleton_builder/            # Skeleton Builder Agents
│   │   ├── __init__.py
│   │   ├── consistency_checker.py   # Agent: 逻辑检查员
│   │   ├── character_designer.py    # Agent: 角色设计师
│   │   └── beat_sheet_planner.py    # Agent: 节拍规划师
│   │
│   ├── novel_writer/                # Novel Writer Agents
│   │   ├── __init__.py
│   │   ├── content_generator.py     # Agent: 内容生成器
│   │   ├── quality_enforcer.py      # Agent: 质量检查员
│   │   └── refiner.py               # Agent: 精修器
│   │
│   ├── script_adapter/              # Script Adapter Agents
│   │   ├── __init__.py
│   │   ├── scene_segmenter.py       # Agent: 场景分割器
│   │   └── dialog_optimizer.py      # Agent: 对话优化器
│   │
│   ├── storyboard_director/         # Storyboard Director Agents
│   │   ├── __init__.py
│   │   ├── shot_planner.py          # Agent: 镜头规划师
│   │   └── prompt_engineer.py       # Agent: Prompt 工程师
│   │
│   └── quality_control/             # Quality Control Agents
│       ├── __init__.py
│       ├── editor.py                # Agent: 编辑审阅员
│       └── refiner.py               # Agent: 质量精修器
│
├── graph/                           # ⭐ Graph 层 (工作流定义)
│   ├── __init__.py
│   ├── main_graph.py                # 主图 (Master Router)
│   │
│   └── workflows/                   # 工作流定义
│       ├── story_planner_graph.py   # Story Planner Workflow
│       ├── skeleton_builder_graph.py
│       ├── novel_writer_graph.py
│       ├── script_adapter_graph.py
│       ├── storyboard_director_graph.py
│       └── quality_control_graph.py
│
├── services/                        # 服务层
│   ├── __init__.py
│   ├── database.py                  # 数据库服务 (供 Tools 使用)
│   ├── model_router.py              # 模型路由服务
│   └── theme_library_service.py     # 题材库服务
│
└── schemas/                         # 类型定义
    ├── __init__.py
    ├── agent_state.py               # AgentState 定义
    ├── theme_models.py              # 题材库数据模型
    └── tool_schemas.py              # Tool 输入输出 Schema
```

---

## 2. Tool/Skill 层设计（详细版）

### 2.1 核心原则

- **Skill = Tool**: 使用 `@tool` 装饰器定义
- **Prompt-driven**: 返回格式化的文本内容，可直接注入 Prompt
- **可复用**: 任何 Agent 都可以通过 `tools=[skill1, skill2]` 调用
- **不调用其他 Tools**: Tool 应该是原子操作，不依赖其他 Tools

### 2.2 Theme Library Skills

#### Skill 1: load_genre_context

```python
# backend/skills/theme_library.py

from typing import Optional
from langchain_core.tools import tool
from backend.services.database import get_db_service

@tool
def load_genre_context(genre_id: str, include_tropes: bool = True, include_hooks: bool = True) -> str:
    """
    Skill: 加载指定题材的完整上下文信息。
    
    返回格式化的题材指导文本，包含核心公式、推荐元素、避雷指南等。
    可直接注入 Agent 的 System Prompt 中。
    
    Args:
        genre_id: 题材ID，可选值: revenge(复仇), sweet(甜宠), suspense(悬疑), 
                 fantasy(玄幻), urban(都市), workplace(职场) 等
        include_tropes: 是否包含推荐元素列表
        include_hooks: 是否包含钩子模板
    
    Returns:
        格式化的题材指导文本，包含以下章节:
        - 题材基本信息
        - 核心公式 (Setup → Rising → Climax → Resolution)
        - 目标受众
        - 推荐元素 (Tropes)
        - 情绪钩子 (Hooks)
        - 写作关键词
        - 视觉风格
        - 避雷清单
        - 市场趋势
    
    Example:
        >>> context = load_genre_context("revenge")
        >>> print(context)
        ## 题材指导：复仇逆袭
        
        ### 核心公式
        - Setup: 极端羞辱或背叛
        - Rising: 积累实力/隐藏身份
        - Climax: 身份揭露+打脸
        - Resolution: 正义伸张
        ...
    """
    db = get_db_service()
    
    # 查询题材基础信息
    genre = db.query(
        "themes",
        filters={"slug": genre_id, "status": "active"},
        include=["elements", "trends"]
    )
    
    if not genre:
        return f"错误：找不到题材 '{genre_id}'"
    
    # 构建返回文本
    sections = []
    
    # 章节 1: 基本信息
    sections.append(f"""
## 题材指导：{genre['name']}

{genre.get('description', '')}

**一句话总结**: {genre.get('summary', '')}
""")
    
    # 章节 2: 核心公式
    formula = genre.get('core_formula', {})
    sections.append(f"""
### 核心公式 (Core Formula)

1. **铺垫 (Setup)**: {formula.get('setup', 'N/A')}
2. **升级 (Rising)**: {formula.get('rising', 'N/A')}
3. **高潮 (Climax)**: {formula.get('climax', 'N/A')}
4. **结局 (Resolution)**: {formula.get('resolution', 'N/A')}

**情绪弧线**: {genre.get('emotional_arc', 'N/A')}
""")
    
    # 章节 3: 目标受众
    target = genre.get('target_audience', {})
    sections.append(f"""
### 目标受众

- **年龄段**: {target.get('age_range', 'N/A')}
- **性别倾向**: {target.get('gender', 'N/A')}
- **兴趣标签**: {', '.join(target.get('interests', []))}
- **观看习惯**: {target.get('viewing_habits', 'N/A')}
""")
    
    # 章节 4: 推荐元素 (Tropes)
    if include_tropes:
        tropes = db.query(
            "theme_elements",
            filters={
                "theme_id": genre['id'],
                "element_type": "trope",
                "is_active": True
            },
            order_by="weight DESC",
            limit=5
        )
        
        trope_text = "\n".join([
            f"  - **{t['name']}**: {t.get('description', '')} (权重: {t.get('weight', 1.0)})"
            for t in tropes
        ])
        
        sections.append(f"""
### 推荐元素 (Tropes)

{trope_text}

**使用建议**: 选择 2-3 个元素组合，避免堆砌。
""")
    
    # 章节 5: 钩子模板 (Hooks)
    if include_hooks:
        hooks = db.query(
            "theme_elements",
            filters={
                "theme_id": genre['id'],
                "element_type": "hook",
                "is_active": True
            },
            limit=3
        )
        
        hook_text = "\n".join([
            f"  - **{h['name']}** ({h.get('hook_type', '通用')}): {h.get('template', '')}"
            for h in hooks
        ])
        
        sections.append(f"""
### 钩子模板 (Hooks) - 用于前3秒留存

{hook_text}

**使用时机**: 前3秒必须抛出钩子，否则完播率会大幅下降。
""")
    
    # 章节 6: 写作关键词
    keywords = genre.get('keywords', {})
    writing_kw = keywords.get('writing', [])
    sections.append(f"""
### 写作关键词 (Writing Keywords)

用于指导 Novel Writer 的文风：
{', '.join(writing_kw)}

**使用方式**: 在 System Prompt 中强调这些关键词的使用。
""")
    
    # 章节 7: 视觉风格
    visual_kw = keywords.get('visual', [])
    visual_style = genre.get('visual_style', [])
    sections.append(f"""
### 视觉风格 (Visual Style)

**关键词**: {', '.join(visual_kw)}

**画面风格**: {', '.join(visual_style)}

**使用方式**: 用于指导 Storyboard Director 和 Asset Inspector。
""")
    
    # 章节 8: 避雷清单
    avoid = genre.get('avoid_patterns', [])
    sections.append(f"""
### ⚠️ 避雷清单 (Avoid Patterns)

以下套路在当前题材中已被观众厌倦，应避免使用：

{chr(10).join([f"  - ❌ {pattern}" for pattern in avoid])}

**替代方案**: 使用推荐元素中的创新组合。
""")
    
    # 章节 9: 市场趋势
    trends = genre.get('trends', {})
    sections.append(f"""
### 📊 市场趋势

- **热门度**: {genre.get('popularity_score', 0)}/100
- **成功率**: {genre.get('success_rate', 0)}%
- **趋势方向**: {trends.get('direction', 'stable')}
- **推荐度**: {'⭐⭐⭐⭐⭐' if genre.get('is_featured') else '⭐⭐⭐'}
""")
    
    return "\n---\n".join(sections)
```

#### Skill 2: get_tropes

```python
@tool
def get_tropes(genre_id: str, limit: int = 5, min_success_rate: float = 70.0) -> str:
    """
    Skill: 获取指定题材的推荐元素 (Tropes)。
    
    返回该题材下成功率最高的爆款元素列表。
    
    Args:
        genre_id: 题材ID
        limit: 返回数量 (默认5个)
        min_success_rate: 最低成功率过滤 (默认70%)
    
    Returns:
        格式化的推荐元素列表，包含名称、描述、使用场景、成功案例。
    
    Example:
        >>> tropes = get_tropes("revenge", limit=3)
        >>> print(tropes)
        ## 复仇题材推荐元素
        
        1. **身份揭露 (Identity Reveal)**
           - 描述: 主角的真实身份在关键时刻被揭露...
           - 使用场景: 第10-15集
           - 成功率: 92%
        ...
    """
    db = get_db_service()
    
    # 获取题材信息
    theme = db.query("themes", filters={"slug": genre_id})
    if not theme:
        return f"错误：找不到题材 '{genre_id}'"
    
    # 查询推荐元素
    tropes = db.query(
        "theme_elements",
        filters={
            "theme_id": theme["id"],
            "element_type": "trope",
            "is_active": True
        },
        order_by="success_rate DESC",
        limit=limit
    )
    
    # 过滤成功率
    tropes = [t for t in tropes if t.get("success_rate", 0) >= min_success_rate]
    
    if not tropes:
        return f"未找到符合条件的推荐元素 (成功率 ≥ {min_success_rate}%)"
    
    # 格式化输出
    sections = [f"## {theme['name']} 推荐元素 (Tropes)\n"]
    
    for i, trope in enumerate(tropes, 1):
        config = trope.get("config", {})
        sections.append(f"""
{i}. **{trope['name']}**
   
   {trope.get('description', '暂无描述')}
   
   - **类型**: {config.get('type', '通用')}
   - **使用时机**: {config.get('timing', '根据剧情需要')}
   - **成功率**: {trope.get('success_rate', 'N/A')}%
   - **使用次数**: {trope.get('frequency', 0)} 次
   - **是否必需**: {'✅ 是' if trope.get('is_required') else '❌ 否'}
   
   **使用示例**:
   {config.get('example', '暂无示例')}
""")
    
    sections.append(f"""
**使用建议**: 
- 从以上列表中选择 2-3 个元素组合使用
- 必需元素必须包含
- 注意元素之间的逻辑自洽
""")
    
    return "\n".join(sections)
```

#### Skill 3: get_hooks

```python
@tool
def get_hooks(genre_id: str, hook_type: Optional[str] = None, narrative_mode: str = "performance") -> str:
    """
    Skill: 获取指定题材的钩子模板 (Hooks)。
    
    钩子用于前3秒留存，是短剧完播率的关键。
    
    Args:
        genre_id: 题材ID
        hook_type: 钩子类型 (可选: question-悬念型, situation-情境型, visual-视觉型)
                  不传则返回所有类型
        narrative_mode: 剧本模式 (commentary-解说, performance-演绎, both-两者皆可)
    
    Returns:
        格式化的钩子模板列表，包含模板文本、使用效果、适用场景。
    
    Example:
        >>> hooks = get_hooks("revenge", hook_type="situation")
        >>> print(hooks)
        ## 复仇题材钩子模板 (情境型)
        
        1. **极限羞辱情境**
           模板: "主角正在遭受[极端羞辱]，倒计时[3,2,1]即将反击"
           效果: 95分
           示例: 被当众退婚、被经理泼咖啡...
        ...
    """
    db = get_db_service()
    
    # 获取题材
    theme = db.query("themes", filters={"slug": genre_id})
    if not theme:
        return f"错误：找不到题材 '{genre_id}'"
    
    # 构建查询条件
    filters = {
        "theme_id": theme["id"],
        "element_type": "hook",
        "is_active": True
    }
    
    if hook_type:
        filters["hook_type"] = hook_type
    
    # 查询钩子
    hooks = db.query(
        "theme_elements",
        filters=filters,
        order_by="effectiveness_score DESC",
        limit=5
    )
    
    # 过滤适用的 narrative_mode
    hooks = [
        h for h in hooks 
        if narrative_mode in h.get("applicable_modes", ["both"])
    ]
    
    if not hooks:
        return f"未找到符合条件的钩子模板"
    
    # 格式化输出
    type_label = f"({hook_type.upper()})" if hook_type else "(全部类型)"
    sections = [f"## {theme['name']} 钩子模板 {type_label}\n"]
    sections.append("> 💡 钩子用于前3秒，决定观众是否继续观看\n")
    
    for i, hook in enumerate(hooks, 1):
        config = hook.get("config", {})
        sections.append(f"""
{i}. **{hook['name']}**
   
   **模板**: {hook.get('template', '')}
   
   **效果评分**: {hook.get('effectiveness_score', 'N/A')}/100
   
   **适用类型**: {', '.join(hook.get('applicable_genres', []))}
   
   **使用示例**:
   {chr(10).join(['   - ' + ex for ex in config.get('examples', [])])}
   
   **使用技巧**: {config.get('tips', '根据情境灵活运用')}
""")
    
    sections.append(f"""
**使用原则**:
1. 前3秒必须抛出钩子
2. 钩子必须与后续剧情强相关（不能骗点击）
3. 钩子类型与题材匹配 (复仇→情境型, 甜宠→悬念型)
""")
    
    return "\n".join(sections)
```

#### Skill 4: get_character_archetypes

```python
@tool
def get_character_archetypes(genre_id: str, role: str = "all", limit: int = 3) -> str:
    """
    Skill: 获取指定题材推荐的角色原型。
    
    Args:
        genre_id: 题材ID
        role: 角色定位 (protagonist-主角, antagonist-反派, supporting-配角, all-全部)
        limit: 返回数量
    
    Returns:
        格式化的角色原型列表。
    """
    db = get_db_service()
    
    theme = db.query("themes", filters={"slug": genre_id})
    if not theme:
        return f"错误：找不到题材 '{genre_id}'"
    
    # 查询角色原型
    filters = {
        "theme_id": theme["id"],
        "element_type": "character",
        "is_active": True
    }
    
    if role != "all":
        filters["role"] = role
    
    archetypes = db.query(
        "theme_elements",
        filters=filters,
        order_by="weight DESC",
        limit=limit
    )
    
    if not archetypes:
        return f"未找到角色原型"
    
    sections = [f"## {theme['name']} 推荐角色原型\n"]
    
    for i, char in enumerate(archetypes, 1):
        config = char.get("config", {})
        sections.append(f"""
{i}. **{char['name']}** ({config.get('archetype', '通用')})
   
   **角色定位**: {config.get('role', 'N/A')}
   
   **性格特质**: {', '.join(config.get('traits', []))}
   
   **核心动机**: {config.get('motivation', 'N/A')}
   
   **关系动态**: {', '.join(config.get('relationship_dynamics', []))}
   
   **经典台词风格**: {config.get('dialog_style', 'N/A')}
   
   **使用建议**: {char.get('description', '')}
""")
    
    return "\n".join(sections)
```

#### Skill 5: get_writing_keywords

```python
@tool
def get_writing_keywords(genre_id: str, category: Optional[str] = None) -> str:
    """
    Skill: 获取指定题材的写作关键词。
    
    用于指导 Novel Writer 的文风。
    
    Args:
        genre_id: 题材ID
        category: 关键词类别 (emotions-情绪词, actions-动作词, descriptions-描写词)
    
    Returns:
        格式化的关键词列表。
    """
    db = get_db_service()
    
    theme = db.query("themes", filters={"slug": genre_id})
    if not theme:
        return f"错误：找不到题材 '{genre_id}'"
    
    keywords = theme.get("keywords", {})
    writing_kw = keywords.get("writing", [])
    
    # 如果有 category 过滤
    if category:
        # 这里假设 keywords 存储时带有类别标签
        writing_kw = [kw for kw in writing_kw if category in kw.get("categories", [])]
    
    sections = [f"## {theme['name']} 写作关键词\n"]
    sections.append("在小说创作中适当使用这些词汇，强化题材风格:\n")
    sections.append(", ".join(writing_kw))
    
    sections.append(f"""

**使用建议**:
- 不要过度堆砌，自然融入对话和描写
- 情绪词用于内心戏，动作词用于冲突场景
- 每章出现 2-3 个关键词即可
""")
    
    return "\n".join(sections)
```

#### Skill 6: get_market_trends

```python
from datetime import datetime, timedelta

@tool
def get_market_trends(genre_id: Optional[str] = None, days: int = 7) -> str:
    """
    Skill: 获取市场趋势数据。
    
    用于 Market Assessor Agent 进行评分。
    
    Args:
        genre_id: 题材ID (可选，不传则返回全平台趋势)
        days: 统计天数 (默认7天)
    
    Returns:
        格式化的市场趋势报告。
    """
    db = get_db_service()
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    if genre_id:
        # 查询特定题材趋势
        theme = db.query("themes", filters={"slug": genre_id})
        if not theme:
            return f"错误：找不到题材 '{genre_id}'"
        
        trends = db.query(
            "theme_trends",
            filters={
                "theme_id": theme["id"],
                "date": {"gte": start_date, "lte": end_date}
            }
        )
        
        if not trends:
            return f"{theme['name']} 暂无近期趋势数据"
        
        # 计算平均值
        avg_views = sum(t["view_count"] for t in trends) / len(trends)
        avg_completion = sum(t["completion_rate"] for t in trends) / len(trends)
        avg_engagement = sum(t["engagement_score"] for t in trends) / len(trends)
        
        return f"""
## {theme['name']} 市场趋势 (近{days}天)

**观看数据**:
- 平均日观看量: {avg_views:,.0f}
- 平均完播率: {avg_completion:.1f}%
- 平均互动分: {avg_engagement:.1f}/100

**排名变化**:
- 当前分类排名: {trends[-1].get('category_rank', 'N/A')}
- 全站排名: {trends[-1].get('daily_rank', 'N/A')}

**趋势判断**: {'🔥 上升' if trends[-1]['daily_rank'] < trends[0]['daily_rank'] else '📉 下降' if trends[-1]['daily_rank'] > trends[0]['daily_rank'] else '➡️ 平稳'}

**建议**: {'该题材正处于热度上升期，建议重点布局' if avg_completion > 75 else '该题材竞争激烈，需要有差异化创新'}
"""
    else:
        # 返回全平台热门题材
        hot_themes = db.query(
            "themes",
            filters={"status": "active", "is_featured": True},
            order_by="popularity_score DESC",
            limit=5
        )
        
        sections = ["## 🔥 全平台热门题材趋势\n"]
        
        for theme in hot_themes:
            sections.append(f"""
**{theme['name']}** (热门度: {theme['popularity_score']}/100)
- 成功率: {theme['success_rate']}%
- 使用次数: {theme['usage_count']}
- 趋势: {theme.get('trend_direction', 'stable')}
""")
        
        return "\n".join(sections)
```

### 2.3 Writing Assistant Skills

```python
# backend/skills/writing_assistant.py

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
```

### 2.4 Visual Assistant Skills

```python
# backend/skills/visual_assistant.py

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
```

---

## 3. Agent 层设计（详细版）

### 3.1 核心原则

- **使用 `create_react_agent` 创建 Agent**（不是普通函数）
- **Agent = Compiled Graph**（既是 Agent 也是 Node）
- **Agent 自动调用 Tools**（不需要手动调用）
- **通过 System Prompt 指导 Agent 行为**

### 3.1.1 Prompt加载与主题库数据注入机制

**核心流程**：
1. **从 `prompts/` 文件夹加载 Base Prompt**（唯一的Prompt来源）
2. **调用 Skills 查询主题库数据**（动态获取题材公式、元素等）
3. **动态组装完整 Prompt**（Base Prompt + 主题库数据 + 用户输入）
4. **创建 Agent**（传入组装后的完整 Prompt 和 Tools）

**代码示例**：
```python
# backend/agents/story_planner/genre_strategist.py

import os
from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes,
    get_market_trends
)

# Prompt 文件路径（唯一的Prompt来源）
PROMPT_FILE = "prompts/2_Story_Planner.md"

def create_genre_strategist_agent(user_id: str, genre_id: str):
    """
    创建 Genre Strategist Agent
    
    流程：
    1. 从 prompts/2_Story_Planner.md 加载基础Prompt
    2. 调用 Skills 查询主题库数据
    3. 组装完整Prompt
    4. 创建Agent
    """
    
    # Step 1: 从文件加载基础Prompt
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
    
    # Step 2: 查询主题库数据
    theme_data = load_genre_context(genre_id)
    tropes_data = get_tropes(genre_id, limit=5)
    market_data = get_market_trends(genre_id)
    
    # Step 3: 动态组装完整Prompt
    full_prompt = base_prompt.format(
        theme_library_data=theme_data,      # 主题库数据注入
        recommended_tropes=tropes_data,
        market_trends=market_data,
        user_config=get_user_config(user_id),
        genre=genre_id
    )
    
    # Step 4: 创建Agent（带Tools调用能力）
    agent = create_react_agent(
        model=get_model(user_id),
        tools=[load_genre_context, get_tropes, get_market_trends],
        prompt=full_prompt
    )
    
    return agent
```

**关键原则**：
- ✅ **Prompt即代码**：`prompts/` 中的文件是可版本控制的代码，不是内联字符串
- ✅ **动态注入**：主题库数据在运行时注入，不是静态Prompt
- ✅ **单一来源**：所有Prompt统一在 `prompts/` 文件夹，不再内联
- ✅ **数据驱动**：Agent行为由主题库数据驱动，不是硬编码

### 3.2 Story Planner Agents

#### Agent 1: Genre Strategist（题材策略师）

```python
# backend/agents/story_planner/genre_strategist.py

"""
Genre Strategist Agent

职责：基于用户输入和市场趋势，制定最优的题材策略。

这是一个 Agent，不是普通 Node。它使用 create_react_agent 创建，
具有 Tool 调用能力，可以自主决策调用哪些 Tools。
"""

from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes,
    get_market_trends
)
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType

# System Prompt - 定义 Agent 的角色和能力
GENRE_STRATEGIST_SYSTEM_PROMPT = """
你是资深的短剧题材策略师，专门负责基于用户输入和市场趋势制定最优的题材策略。

## 你的职责

1. **意图解析**
   - 提取用户输入中的关键词（题材、调性、元素）
   - 识别隐含需求（如"要爽的"→复仇题材）
   - 检测冲突需求（如"要虐又要甜"→需要平衡）

2. **题材策略制定**
   - 使用 Tools 查询题材库获取详细信息
   - 分析题材组合可能性
   - 制定避雷指南

3. **输出策略报告**
   - 输出结构化的 JSON 格式策略报告

## 可用的 Tools

你有以下 Tools 可供调用：

1. **load_genre_context** - 加载指定题材的完整上下文
   - 使用场景: 需要了解题材的核心公式、推荐元素、避雷清单等
   - 参数: genre_id (题材ID)

2. **get_tropes** - 获取推荐元素
   - 使用场景: 需要获取该题材的爆款元素列表
   - 参数: genre_id, limit (数量)

3. **get_market_trends** - 获取市场趋势
   - 使用场景: 需要了解当前题材的市场表现
   - 参数: genre_id, days (天数)

## 工作流程

1. **解析用户输入** → 提取题材关键词
2. **调用 load_genre_context** → 获取题材详细信息
3. **（可选）调用 get_tropes** → 获取推荐元素
4. **（可选）调用 get_market_trends** → 获取市场数据
5. **制定策略** → 综合所有信息生成策略报告
6. **输出结果** → 返回 JSON 格式的策略报告

## 输出格式

你必须输出以下 JSON 格式：

```json
{
  "strategy_report": {
    "primary_genre": "题材ID",
    "genre_name": "题材名称",
    "confidence": 0.95,
    "reasoning": "选择该题材的原因...",
    "core_formula": {
      "setup": "铺垫阶段",
      "rising": "升级阶段", 
      "climax": "高潮阶段",
      "resolution": "结局阶段"
    },
    "recommended_tropes": ["元素1", "元素2"],
    "emotional_hooks": ["钩子1", "钩子2"],
    "avoid_patterns": ["避雷1", "避雷2"],
    "target_audience": {
      "age_range": "18-35",
      "gender": "female",
      "psychographics": "追求爽感的都市女性"
    },
    "episode_structure": {
      "total": 80,
      "paywall": 12,
      "climax": 70
    },
    "market_analysis": {
      "popularity": 95,
      "trend": "rising",
      "competition": "high"
    }
  }
}
```

## 注意事项

- 总是先调用 load_genre_context 获取基础信息
- 如果用户输入模糊，选择最热门且匹配度高的题材
- 避雷清单必须完整输出
- 市场分析要客观准确
"""


def create_genre_strategist_agent(user_id: str):
    """
    创建 Genre Strategist Agent
    
    Args:
        user_id: 用户ID，用于获取用户特定的模型配置
    
    Returns:
        Compiled Agent (可以 invoke，也可以作为 Node 添加到 Graph)
    """
    # 获取模型
    router = get_model_router()
    model = router.get_model(user_id=user_id, task_type=TaskType.STORY_PLANNER)
    
    # 创建 Agent
    agent = create_react_agent(
        model=model,
        tools=[load_genre_context, get_tropes, get_market_trends],
        prompt=GENRE_STRATEGIST_SYSTEM_PROMPT,
        # 可选：配置 Agent 的行为
        max_iterations=5,  # 最大 Tool 调用次数
        handle_parsing_errors=True  # 处理解析错误
    )
    
    return agent


# 导出 Agent 创建函数
__all__ = ["create_genre_strategist_agent", "GENRE_STRATEGIST_SYSTEM_PROMPT"]
```

#### Agent 2: Concept Generator（概念生成器）

```python
# backend/agents/story_planner/concept_generator.py

"""
Concept Generator Agent

职责：基于题材策略，使用三种方法论生成 10 个粗糙但有潜力的故事概念。

使用三种生成方法论：
1. 逆向工程 (Reverse Engineering)
2. 痛点映射 (Pain Point Mapping)
3. 算法友好 (Algorithm-Friendly)
"""

from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import (
    load_genre_context,
    get_tropes,
    get_hooks
)
from backend.skills.writing_assistant import get_trending_combinations
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType

CONCEPT_GENERATOR_SYSTEM_PROMPT = """
你是创意生成专家，专门负责基于题材策略生成大量粗糙但有潜力的故事概念。

## 你的职责

1. **执行 Agentic Ideation Loop 的发散阶段**
2. **使用三种方法论各生成 3-4 个概念**（共10个）
3. **确保概念多样性**（覆盖不同角度）
4. **应用题材指导原则**

## 三种生成方法论

### 方法论 1: 逆向工程 (Reverse Engineering)

分析近期爆款短剧，提取公式，应用到新题材。

**分析维度**:
- 核心钩子: 什么吸引观众点击？
- 情绪公式: 什么情绪曲线最有效？
- 反转机制: 身份错位/误会/隐藏实力？
- 成功要素: 为什么这个爆了？

**应用到新题材**:
将爆款的核心要素移植到新题材背景中。

### 方法论 2: 痛点映射 (Pain Point Mapping)

将社会情绪转化为故事爽点。

**常见社会痛点**:
- 职场: PUA、加班、不公平待遇
- 情感: 渣男、绿茶、原生家庭
- 社会: 阶层固化、房价、内卷

**转化公式**:
痛点 × 极端情境 = 故事爽点

### 方法论 3: 算法友好 (Algorithm-Friendly)

针对前3秒完播率设计钩子。

**前3秒钩子设计**:
- 极端羞辱场景
- 生死一线情境
- 身份落差揭示
- 视觉奇观展示

**完播率优化**:
- 0-3s: 钩子抛出
- 3-10s: 悬念建立
- 10-30s: 信息释放
- 每30s: 小高潮

## 可用的 Tools

1. **load_genre_context** - 加载题材上下文
2. **get_tropes** - 获取推荐元素
3. **get_hooks** - 获取钩子模板
4. **get_trending_combinations** - 获取热门组合

## 工作流程

1. **接收题材策略** → 理解题材公式和约束
2. **调用 Tools 获取素材** → 元素、钩子、趋势
3. **应用三种方法论** → 各生成3-4个概念
4. **去重和筛选** → 确保多样性
5. **输出10个概念** → JSON格式

## 输出格式

```json
{
  "generated_concepts": [
    {
      "id": "concept_01",
      "method": "reverse_engineer",
      "title": "概念标题",
      "one_liner": "一句话梗概",
      "core_hook": "核心钩子",
      "novelty_score": 90,
      "rough_outline": "粗略大纲"
    }
  ]
}
```

## 概念质量标准

每个概念必须包含：
- ✅ 吸引人的标题
- ✅ 清晰的一句话梗概
- ✅ 明确的核心钩子
- ✅ 与题材公式匹配
- ✅ 创新度评分 (1-100)

## 注意事项

- 概念要粗糙但必须有潜力（不要过度打磨）
- 确保10个概念覆盖不同方法论
- 避免题材禁忌
- 创新度要多样化（既有稳妥的也有大胆的）
"""


def create_concept_generator_agent(user_id: str):
    """创建 Concept Generator Agent"""
    router = get_model_router()
    model = router.get_model(user_id=user_id, task_type=TaskType.STORY_PLANNER)
    
    agent = create_react_agent(
        model=model,
        tools=[
            load_genre_context,
            get_tropes,
            get_hooks,
            get_trending_combinations
        ],
        prompt=CONCEPT_GENERATOR_SYSTEM_PROMPT
    )
    
    return agent
```

#### Agent 3: Market Assessor（市场测评员）

```python
# backend/agents/story_planner/market_assessor.py

"""
Market Assessor Agent

职责：对生成的概念进行多维度市场评估，选出 Top 3 最有潜力的概念。

作为"投资人"角色，客观评估每个概念的商业价值。
"""

from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import get_market_trends
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType

MARKET_ASSESSOR_SYSTEM_PROMPT = """
你是短剧市场的资深投资人，专门负责评估故事概念的市场潜力。

## 你的角色定位

- **客观冷静**: 不被创意本身迷惑，只看数据和市场
- **经验丰富**: 看过上千个项目，知道什么能火
- **直言不讳**: 指出问题和风险，不恭维

## 评估维度

### 1. 爽点强度 (Satisfaction) - 权重 30%

评估标准：
- 10分: 极致爽感，观众看了会拍大腿
- 7-9分: 很爽，但可能缺少反转
- 4-6分: 一般爽感，套路常见
- 1-3分: 不爽，逻辑有问题

关键问题：
- 打脸是否够爽？
- 反转是否够大？
- 情绪释放是否充分？

### 2. 创新度 (Novelty) - 权重 25%

评估标准：
- 10分: 前所未见，开辟新赛道
- 7-9分: 老套路新玩法，有新鲜感
- 4-6分: 微创新，换汤不换药
- 1-3分: 纯套路，毫无新意

关键问题：
- 是否有新鲜感？
- 是否避免了老套路？
- 是否有话题性？

### 3. 执行可行性 (Feasibility) - 权重 20%

评估标准：
- 10分: 容易执行，成本低
- 7-9分: 稍微复杂，但可执行
- 4-6分: 有难度，需要资源
- 1-3分: 几乎不可能执行

评估维度：
- 成本是否可控？
- 演员是否好找？
- 场景是否复杂？
- 特效要求高吗？

### 4. 商业潜力 (Commercial) - 权重 25%

评估标准：
- 10分: 爆款预定，ROI极高
- 7-9分: 大概率赚钱
- 4-6分: 有可能赚钱
- 1-3分: 大概率亏钱

评估维度：
- 目标受众规模
- 付费卡点是否清晰
- 是否适合系列化
- 市场竞争力

## 可用的 Tools

1. **get_market_trends** - 获取市场趋势数据
   - 使用场景: 评估概念是否符合当前市场趋势
   - 参数: genre_id, days

## 工作流程

1. **接收10个概念**
2. **逐个评估** → 4维度打分
3. **计算加权总分**
4. **排序** → 选出 Top 3
5. **给出优化建议** → 针对 Top 3

## 输出格式

```json
{
  "evaluation_results": [
    {
      "concept_id": "concept_01",
      "scores": {
        "satisfaction": 9.5,
        "novelty": 9.0,
        "feasibility": 8.0,
        "commercial": 8.5
      },
      "total_score": 87.5,
      "rank": 1,
      "investment_verdict": "强烈推荐",
      "strengths": ["优势1", "优势2"],
      "weaknesses": ["风险1"],
      "optimization_suggestions": "建议增加...",
      "market_analysis": "该题材正处于..."
    }
  ],
  "top_3": ["concept_01", "concept_05", "concept_08"],
  "assessment_summary": "整体评估结论..."
}
```

## 投资人话术风格

- "这个概念有爆款潜质，但执行风险偏高..."
- "老套路了，去年已经拍烂了..."
- "钩子设计得很好，但中段可能会疲软..."
- "建议砍掉支线，专注主线打脸..."

## 注意事项

- 评分要客观，不要受个人喜好影响
- 每个维度都要有具体的评分理由
- Top 3 必须给出可执行的优化建议
- 如果有明显短板，即使总分高也要指出
"""


def create_market_assessor_agent(user_id: str):
    """创建 Market Assessor Agent"""
    router = get_model_router()
    model = router.get_model(user_id=user_id, task_type=TaskType.STORY_PLANNER)
    
    agent = create_react_agent(
        model=model,
        tools=[get_market_trends],
        prompt=MARKET_ASSESSOR_SYSTEM_PROMPT
    )
    
    return agent
```

#### Agent 4: Premise Engineer（梗概工程师）

```python
# backend/agents/story_planner/premise_engineer.py

"""
Premise Engineer Agent

职责：将粗糙的 Top 3 概念扩展为完整、可执行的故事梗概。

填充人设、冲突、钩子、卡点等细节。
"""

from langgraph.prebuilt import create_react_agent
from backend.skills.theme_library import (
    load_genre_context,
    get_hooks,
    get_character_archetypes
)
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType

PREMISE_ENGINEER_SYSTEM_PROMPT = """
你是故事梗概工程师，专门负责将粗糙的概念扩展为完整、可执行的故事梗概。

## 你的职责

1. **扩展 Top 3 概念为完整梗概**
2. **设计主角人设**（含反差设定）
3. **构建核心冲突和困境**
4. **设计开篇视觉钩子**
5. **规划付费卡点**

## 扩展内容清单

### 1. 主角人设

必须包含：
- **姓名、年龄、外表**
- **表象身份 vs 真实身份**（反差设定）
- **核心欲望**（想要什么）
- **致命弱点**（害怕什么）
- **角色弧线**（如何成长）

### 2. 核心设定

- **世界观/背景**
- **核心冲突类型**
- **驱动力**（为什么主角必须行动）

### 3. 开篇钩子（前30秒）

- **场景设计**
- **视觉冲击描述**
- **悬念建立**

### 4. 核心困境

- **两难选择设计**
- **道德困境/情感困境**
- **困境的升级路径**

### 5. 爽点设计

- **打脸时刻设计**（第几集？）
- **身份揭露时机**
- **情绪高潮点**

### 6. 付费卡点

- **卡点位置**（第X集）
- **钩子事件设计**
- **悬念留存**

## 可用的 Tools

1. **load_genre_context** - 加载题材上下文
2. **get_hooks** - 获取钩子模板
3. **get_character_archetypes** - 获取角色原型

## 工作流程

1. **接收 Top 3 概念**
2. **查询题材数据** → 确保符合题材公式
3. **设计人设** → 表象vs真实身份反差
4. **填充6项内容** → 设定、钩子、困境、爽点、卡点
5. **应用反套路雷达** → 检查常见错误
6. **输出完整梗概**

## 输出格式

```json
{
  "refined_premises": [
    {
      "concept_id": "concept_01",
      "title": "《最终标题》",
      "logline": "一句话总结",
      "protagonist": {
        "name": "主角姓名",
        "age": 25,
        "appearance": "外表描述",
        "surface_identity": "表象身份",
        "true_identity": "真实身份",
        "core_desire": "核心欲望",
        "fatal_flaw": "致命弱点",
        "character_arc": "角色成长弧线"
      },
      "core_setting": {
        "world": "世界观",
        "conflict_type": "冲突类型",
        "motivation": "驱动力"
      },
      "opening_hook": {
        "scene": "前30秒场景",
        "visual": "视觉冲击",
        "suspense": "悬念建立"
      },
      "central_dilemma": {
        "description": "两难选择",
        "escalation": "升级路径"
      },
      "satisfaction_moments": [
        {"episode": 5, "event": "首次打脸"},
        {"episode": 15, "event": "身份揭露"},
        {"episode": 70, "event": "最终反转"}
      ],
      "paywall_design": {
        "episode": 12,
        "event": "卡点事件",
        "cliffhanger": "悬念描述"
      },
      "episode_outline": [
        {"ep": 1, "title": "开篇", "key_event": "钩子抛出"},
        {"ep": 2, "title": "冲突建立", "key_event": "主角受辱"}
      ]
    }
  ]
}
```

## 梗概质量标准

- ✅ 人设必须有反差（表象vs真实）
- ✅ 开篇钩子必须吸引人
- ✅ 困境必须有张力
- ✅ 爽点必须可执行
- ✅ 卡点必须让人想付费
- ✅ 符合题材公式和避雷指南

## 注意事项

- 人设要立体，不能扁平
- 困境要真实，不能强行
- 卡点要自然，不能生硬
- 预留后续发展空间
"""


def create_premise_engineer_agent(user_id: str):
    """创建 Premise Engineer Agent"""
    router = get_model_router()
    model = router.get_model(user_id=user_id, task_type=TaskType.STORY_PLANNER)
    
    agent = create_react_agent(
        model=model,
        tools=[load_genre_context, get_hooks, get_character_archetypes],
        prompt=PREMISE_ENGINEER_SYSTEM_PROMPT
    )
    
    return agent
```

#### Agent 5: Planner Core（整合核心）

```python
# backend/agents/story_planner/planner_core.py

"""
Planner Core Agent

职责：整合所有前置输出，生成最终的三维矩阵方案。

作为 Story Planner 的最后一步，输出用户可交互的方案。
"""

from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.schemas.model_config import TaskType

PLANNER_CORE_SYSTEM_PROMPT = """
你是 Story Planner 的整合者，负责将所有前置输出整合为最终的三维矩阵方案。

## 你的职责

1. **整合策略报告、梗概、市场评估**
2. **生成三维矩阵**（爽感型/脑洞型/情感型）
3. **应用题材特定的优化**
4. **生成前端 UI 数据**
5. **输出符合前端交互格式的结果**

## 三维矩阵生成逻辑

### 方案 A: 极致爽感型

**核心逻辑**: 身份/权力落差最大化

**强制设定**:
- 双重身份（表象底层 + 底牌大佬）
- 极端权力落差（100倍以上）
- 频繁打脸（每3集一次）

**情绪价值**: 打脸、逆袭、扮猪吃虎

**适用题材**: 复仇、逆袭、战神

### 方案 B: 极致脑洞型

**核心逻辑**: 违和感与陌生化

**强制设定**:
- 极端违和元素组合（古代皇帝+现代思维）
- 身份错位（少女身太奶魂）
- 反常识设定（丧尸排队买咖啡）

**情绪价值**: 猎奇、好笑、新鲜感

**适用题材**: 穿越、奇幻、科幻

### 方案 C: 极致情感型

**核心逻辑**: 宿命与救赎

**强制设定**:
- 不可调和的对立 + 强绑定关系
- 深层次的情感困境
- 牺牲与救赎主题

**情绪价值**: 虐恋情深、极致治愈

**适用题材**: 甜宠、虐恋、家庭

## 工作流程

1. **接收所有输入**:
   - 题材策略报告
   - 10个粗糙概念
   - 市场评估报告
   - Top 3 精修梗概

2. **分析题材特征**:
   - 识别题材的核心情绪价值
   - 确定三维矩阵的侧重点

3. **生成三维方案**:
   - 为每个维度选择最适合的梗概
   - 应用该维度的强制设定
   - 生成方案对比

4. **生成 UI 数据**:
   - 卡片标题和描述
   - 标签和颜色
   - 交互按钮

5. **输出最终 JSON**

## 输出格式

```json
{
  "final_output": {
    "strategy_summary": "基于复仇题材，采用身份反转公式...",
    "schemes": {
      "A": {
        "type": "satisfaction",
        "label": "极致爽感",
        "color": "red",
        "title": "方案标题",
        "tagline": "一句话吸引语",
        "description": "方案描述...",
        "highlights": ["亮点1", "亮点2"],
        "premise": { /* 完整梗概 */ }
      },
      "B": {
        "type": "novelty", 
        "label": "极致脑洞",
        "color": "purple",
        ...
      },
      "C": {
        "type": "emotion",
        "label": "极致情感", 
        "color": "pink",
        ...
      }
    },
    "comparison": {
      "A": {
        "pros": ["优势1", "优势2"],
        "cons": ["风险1"],
        "target_audience": "适合人群",
        "market_potential": "市场潜力评估"
      },
      "B": { ... },
      "C": { ... }
    },
    "ui_data": {
      "header": "选择你的故事方向",
      "subheader": "我们为你准备了三种不同风格的方案",
      "options": [
        {
          "id": "A",
          "label": "极致爽感",
          "tagline": "打脸逆袭，痛快淋漓",
          "color": "#FF4444",
          "icon": "fire"
        },
        {
          "id": "B", 
          "label": "极致脑洞",
          "tagline": "脑洞大开，新鲜猎奇",
          "color": "#9944FF",
          "icon": "lightbulb"
        },
        {
          "id": "C",
          "label": "极致情感", 
          "tagline": "虐恋情深，极致治愈",
          "color": "#FF66AA",
          "icon": "heart"
        }
      ],
      "secondary_actions": [
        {"id": "regenerate", "label": "重新生成", "icon": "refresh"},
        {"id": "hybrid", "label": "融合方案", "icon": "combine"},
        {"id": "custom", "label": "自定义", "icon": "edit"}
      ],
      "hint": "💡 小贴士：爽感型最容易爆，脑洞型最容易出圈，情感型最容易共鸣"
    }
  }
}
```

## 注意事项

- 三个方案必须真实可选，不能敷衍
- 每个方案的差异要明显
- UI 数据要完整，前端可以直接使用
- 包含用户可能需要的二次操作（重新生成、融合等）
"""


def create_planner_core_agent(user_id: str):
    """创建 Planner Core Agent"""
    router = get_model_router()
    model = router.get_model(user_id=user_id, task_type=TaskType.STORY_PLANNER)
    
    agent = create_react_agent(
        model=model,
        tools=[],  # Core 主要是整合，不需要额外 Tools
        prompt=PLANNER_CORE_SYSTEM_PROMPT
    )
    
    return agent
```

---

## 4. Graph 工作流设计（详细版）

### 4.1 Story Planner Graph

```python
# backend/graph/workflows/story_planner_graph.py

"""
Story Planner Graph

这是一个完整的 LangGraph 工作流，串联 5 个 Story Planner Agents。

注意：Agents 是 create_react_agent 创建的 Compiled Graph，
它们既是 Agent 也是 Node，可以直接添加到工作流中。
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend.schemas.agent_state import AgentState

# 导入 Agent 创建函数
from backend.agents.story_planner.genre_strategist import create_genre_strategist_agent
from backend.agents.story_planner.concept_generator import create_concept_generator_agent
from backend.agents.story_planner.market_assessor import create_market_assessor_agent
from backend.agents.story_planner.premise_engineer import create_premise_engineer_agent
from backend.agents.story_planner.planner_core import create_planner_core_agent


def build_story_planner_graph(user_id: str, checkpointer=None):
    """
    构建 Story Planner Graph
    
    Args:
        user_id: 用户ID，用于获取用户特定的模型配置
        checkpointer: 可选的 checkpoint 用于状态持久化
    
    Returns:
        Compiled Graph
    """
    # 创建 Agents（它们既是 Agent 也是 Node）
    genre_strategist = create_genre_strategist_agent(user_id)
    concept_generator = create_concept_generator_agent(user_id)
    market_assessor = create_market_assessor_agent(user_id)
    premise_engineer = create_premise_engineer_agent(user_id)
    planner_core = create_planner_core_agent(user_id)
    
    # 创建工作流
    workflow = StateGraph(AgentState)
    
    # 添加 Nodes（Agents 作为 Nodes）
    workflow.add_node("genre_strategist", genre_strategist)
    workflow.add_node("concept_generator", concept_generator)
    workflow.add_node("market_assessor", market_assessor)
    workflow.add_node("premise_engineer", premise_engineer)
    workflow.add_node("planner_core", planner_core)
    
    # 添加辅助 Nodes（普通函数 Nodes）
    workflow.add_node("parse_input", parse_input_node)
    workflow.add_node("format_output", format_output_node)
    
    # 定义边（执行顺序）
    workflow.set_entry_point("parse_input")
    
    # parse_input -> genre_strategist
    workflow.add_edge("parse_input", "genre_strategist")
    
    # genre_strategist -> concept_generator
    workflow.add_edge("genre_strategist", "concept_generator")
    
    # concept_generator -> market_assessor
    workflow.add_edge("concept_generator", "market_assessor")
    
    # market_assessor -> premise_engineer
    workflow.add_edge("market_assessor", "premise_engineer")
    
    # premise_engineer -> planner_core
    workflow.add_edge("premise_engineer", "planner_core")
    
    # planner_core -> format_output
    workflow.add_edge("planner_core", "format_output")
    
    # format_output -> END
    workflow.add_edge("format_output", END)
    
    # 编译 Graph
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile()


def parse_input_node(state: AgentState) -> AgentState:
    """
    输入解析 Node（普通函数，不是 Agent）
    
    解析用户输入，提取关键信息。
    """
    user_input = state.get("user_input", "")
    
    # 简单的意图解析（实际可以用 LLM）
    parsed = {
        "intent": "generate_story_idea",
        "keywords": extract_keywords(user_input),
        "genre_hint": extract_genre_hint(user_input),
        "tone_hint": extract_tone_hint(user_input)
    }
    
    return {
        **state,
        "parsed_input": parsed
    }


def format_output_node(state: AgentState) -> AgentState:
    """
    输出格式化 Node（普通函数，不是 Agent）
    
    格式化最终输出，生成前端可用的数据。
    """
    final_output = state.get("final_output", {})
    
    # 确保 UI 数据完整
    if "ui_data" not in final_output:
        final_output["ui_data"] = generate_default_ui_data()
    
    return {
        **state,
        "formatted_output": final_output,
        "status": "completed"
    }


def extract_keywords(text: str) -> list:
    """提取关键词（简单实现）"""
    # 实际可以用 NLP 库或 LLM
    keywords = []
    if "复仇" in text or "爽" in text:
        keywords.append("revenge")
    if "甜" in text or "宠" in text:
        keywords.append("sweet")
    if "悬疑" in text or "推理" in text:
        keywords.append("suspense")
    return keywords


def extract_genre_hint(text: str) -> str:
    """提取题材暗示"""
    if "复仇" in text:
        return "revenge"
    elif "甜" in text:
        return "sweet"
    elif "悬疑" in text:
        return "suspense"
    return None


def extract_tone_hint(text: str) -> str:
    """提取调性暗示"""
    if "爽" in text or "痛快" in text:
        return "satisfying"
    elif "虐" in text or "哭" in text:
        return "emotional"
    elif "搞笑" in text or "轻松" in text:
        return "humorous"
    return "balanced"


def generate_default_ui_data():
    """生成默认 UI 数据"""
    return {
        "header": "故事方案已生成",
        "subheader": "请选择一个方向继续",
        "options": [],
        "secondary_actions": [
            {"id": "regenerate", "label": "重新生成", "icon": "refresh"}
        ]
    }


# 导出
__all__ = ["build_story_planner_graph"]
```

### 4.2 其他 Graphs（简要定义）

```python
# backend/graph/workflows/skeleton_builder_graph.py

from langgraph.graph import StateGraph, START, END
from backend.agents.skeleton_builder.consistency_checker import create_consistency_checker_agent
from backend.agents.skeleton_builder.character_designer import create_character_designer_agent
from backend.agents.skeleton_builder.beat_sheet_planner import create_beat_sheet_planner_agent

def build_skeleton_builder_graph(user_id: str):
    """Skeleton Builder Graph"""
    consistency_checker = create_consistency_checker_agent(user_id)
    character_designer = create_character_designer_agent(user_id)
    beat_sheet_planner = create_beat_sheet_planner_agent(user_id)
    
    workflow = StateGraph(AgentState)
    
    # Skeleton Builder 需要审阅和测评
    workflow.add_node("consistency_checker", consistency_checker)
    workflow.add_node("character_designer", character_designer)
    workflow.add_node("beat_sheet_planner", beat_sheet_planner)
    
    workflow.set_entry_point("consistency_checker")
    workflow.add_edge("consistency_checker", "character_designer")
    workflow.add_edge("character_designer", "beat_sheet_planner")
    workflow.add_edge("beat_sheet_planner", END)
    
    return workflow.compile()


# backend/graph/workflows/novel_writer_graph.py

from langgraph.graph import StateGraph, START, END
from backend.agents.novel_writer.content_generator import create_content_generator_agent
from backend.agents.novel_writer.quality_enforcer import create_quality_enforcer_agent

def build_novel_writer_graph(user_id: str):
    """Novel Writer Graph"""
    content_generator = create_content_generator_agent(user_id)
    quality_enforcer = create_quality_enforcer_agent(user_id)
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("content_generator", content_generator)
    workflow.add_node("quality_enforcer", quality_enforcer)
    
    workflow.set_entry_point("content_generator")
    workflow.add_edge("content_generator", "quality_enforcer")
    
    # 条件边：质量不达标时循环
    workflow.add_conditional_edges(
        "quality_enforcer",
        should_continue_or_refine,
        {"continue": END, "refine": "content_generator"}
    )
    
    return workflow.compile()


def should_continue_or_refine(state: AgentState) -> str:
    """决定是继续还是返工"""
    quality_score = state.get("quality_score", 0)
    retry_count = state.get("retry_count", 0)
    
    if quality_score >= 80 or retry_count >= 3:
        return "continue"
    else:
        return "refine"


# backend/graph/workflows/quality_control_graph.py

from langgraph.graph import StateGraph, START, END
from backend.agents.quality_control.editor import create_editor_agent
from backend.agents.quality_control.refiner import create_refiner_agent

def build_quality_control_graph(user_id: str):
    """Quality Control Graph"""
    editor = create_editor_agent(user_id)
    refiner = create_refiner_agent(user_id)
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("editor", editor)
    workflow.add_node("refiner", refiner)
    
    workflow.set_entry_point("editor")
    workflow.add_edge("editor", "refiner")
    
    # 精修后可以选择继续精修或结束
    workflow.add_conditional_edges(
        "refiner",
        should_continue_refinement,
        {"refine_again": "editor", "finish": END}
    )
    
    return workflow.compile()


def should_continue_refinement(state: AgentState) -> str:
    """决定是否需要继续精修"""
    refinement_round = state.get("refinement_round", 0)
    improvement_score = state.get("improvement_score", 0)
    
    if refinement_round < 3 and improvement_score > 10:
        return "refine_again"
    else:
        return "finish"
```

### 4.3 Skeleton Builder 分批生成架构（V4.2 新增）

为了解决长章节大纲生成时的 Token 限制问题（53章无法一次性生成），实现了**分批生成 + Checkpoint 暂停恢复**机制。

#### 4.3.1 核心设计原则（V4.2 实现）

```
┌─────────────────────────────────────────────────────────────────────┐
│                    分批生成核心设计（实际实现）                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 严格分层策略                                                    │
│     - 第0批: 生成完整骨架（元数据+人物+节拍+章节清单）               │
│     - 第1批: 展开 Chapter 1-13（详细内容）                          │
│     - 第2批: 展开 Chapter 14-26（详细内容）                         │
│     - 第3批: 展开 Chapter 27-39（详细内容）                         │
│     - 第4批: 展开 Chapter 40-53 + 映射表 + UI JSON                  │
│                                                                     │
│  2. 第一批自动连续机制                                              │
│     - 第0批（骨架批次）→ 不暂停，自动生成并立即进入第1批            │
│     - 第1批开始 → 暂停，显示按钮让用户选择                          │
│     - 防止用户误将骨架当作完整大纲确认                              │
│                                                                     │
│  3. Checkpoint 暂停恢复                                             │
│     - 第1批及以后每批完成后 → Graph 进入 END (暂停)                 │
│     - 状态自动保存到 Checkpoint (PostgreSQL)                        │
│     - 用户可随时点击「继续生成」恢复进度                            │
│                                                                     │
│  4. 上下文传递机制                                                  │
│     - 每批传递：完整骨架 + 前一批最后3000字                          │
│     - 确保批次间连贯性和一致性                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 AgentState 分批生成字段

```python
# backend/schemas/agent_state.py

class AgentState(TypedDict, total=False):
    # ... 原有字段 ...
    
    # ===== Level 3: Skeleton Building - Batch Generation (V4.2 新增) =====
    generation_batches: list[dict] | None  # 分批策略
    current_batch_index: int               # 当前批次索引 (0-based)
    total_batches: int                     # 总批次数
    accumulated_content: str | None        # 累积的所有批次内容
    batch_completed: bool                  # 所有批次是否已完成
    current_batch_range: str | None        # 当前批次范围 (如 "1-13")
    needs_next_batch: bool                 # 是否需要继续下一批
    auto_batch_mode: bool                  # True=自动, False=手动
```

#### 4.3.3 分批生成流程图（实际实现）

```
┌──────────────────────────────────────────────────────────────────────┐
│                     分批生成流程（V4.2 实际实现）                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  START → route_entry                                                 │
│    │                                                                  │
│    ├─ 首次生成 ──→ batch_coordinator ──→ skeleton_builder            │
│    │                                        │                        │
│    │                                        ▼                        │
│    │                              ┌──────────────────┐              │
│    │                              │ 第0批：生成骨架  │              │
│    │                              │ (元数据+人物+    │              │
│    │                              │  节拍+章节清单)  │              │
│    │                              └────────┬─────────┘              │
│    │                                        │                        │
│    │                                        ▼                        │
│    │                              ┌──────────────────┐              │
│    │                              │ validate_output  │              │
│    │                              │ auto_continue=   │              │
│    │                              │   True → 不暂停  │              │
│    │                              └────────┬─────────┘              │
│    │                                        │                        │
│    │                                        ▼                        │
│    │                              ┌──────────────────┐              │
│    │                              │ 第1批：展开      │              │
│    │                              │ Chapter 1-13     │              │
│    │                              └────────┬─────────┘              │
│    │                                        │                        │
│    │                              ┌─────────┴─────────┐              │
│    │                              ▼                   ▼              │
│    │                   batch_complete           incomplete            │
│    │                         │                      │                │
│    │                         ▼                      ▼                │
│    │                       END(暂停)          skeleton_builder       │
│    │         显示：继续/重新生成/确认            (重试)               │
│    │                         │                      │                │
│    │                         │                      │                │
│    └─────────────────────────┴──────────────────────┘                │
│                             │                                        │
│                             ▼                                        │
│                   action=continue_skeleton_generation                │
│                             │                                        │
│                             ▼                                        │
│                   第2批 → 第3批 → 第4批                              │
│                             │                                        │
│                             ▼                                        │
│                     最后一批完成后                                    │
│                             │                                        │
│                             ▼                                        │
│                    ┌──────────────────┐                             │
│                    │ quality_control  │                             │
│                    │ (完整审阅)       │                             │
│                    └────────┬─────────┘                             │
│                             │                                        │
│                             ▼                                        │
│                    ┌──────────────────┐                             │
│                    │ output_formatter │                             │
│                    │ 显示完整大纲      │                             │
│                    └────────┬─────────┘                             │
│                             │                                        │
│                             END                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### 4.3.4 关键路由逻辑（实际实现）

```python
# 1. 入口路由：处理动作请求
def route_entry(state: AgentState) -> str:
    """入口路由：检测动作请求类型"""
    routed_params = state.get("routed_parameters", {})
    action = routed_params.get("action", "")

    if action == "continue_skeleton_generation":
        # ✅ 继续下一批生成（从 Checkpoint 恢复）
        return "continue_generation"
    elif action in ["confirm_skeleton", "regenerate_skeleton"]:
        return "handle_action"
    # ... 其他路由 ...

# 2. 验证后路由：决定是否暂停（V4.2 实现）
def route_after_validate_output(state: AgentState) -> str:
    """
    输出验证后的路由决策
    
    路由逻辑：
    - batch_complete + auto_continue: 骨架批次自动继续
    - batch_complete + 还有下一批: 暂停，等待用户点击继续
    - batch_complete + 最后一批: 进入质检
    """
    validation_status = state.get("validation_status", "complete")
    retry_count = state.get("retry_count", 0)
    max_retries = 3

    if validation_status == "batch_complete":
        current_batch = state.get("current_batch_index", 0)
        total_batches = state.get("total_batches", 1)
        auto_continue = state.get("auto_continue", False)

        if current_batch < total_batches:
            # 检查是否是骨架批次且标记了自动继续
            if auto_continue and current_batch == 0:
                logger.info("Skeleton batch complete, auto-continuing")
                return "auto_continue"  # ✅ 自动继续，不暂停
            
            logger.info("Batch complete, pausing for user")
            return "pause"  # 暂停，等待用户
        else:
            return "proceed"  # 全部完成，进入质检

    if validation_status == "incomplete" and retry_count < max_retries:
        return "retry"  # 验证失败，重试

    return "proceed"

# 3. 边定义（V4.2 实现）
workflow.add_conditional_edges(
    "validate_output",
    route_after_validate_output,
    {
        "pause": END,                    # 暂停，等待用户继续
        "auto_continue": "skeleton_builder",  # ✅ 骨架批次自动继续
        "retry": "skeleton_builder",     # 重试生成
        "proceed": "quality_control",    # 全部完成
    },
)
```

#### 4.3.5 SDUI 交互设计（V4.2 实际实现）

```python
# validate_output_node 返回的 SDUI 交互块（V4.2 实现）

# 第0批（骨架批次）：不返回按钮，自动继续
if is_skeleton_batch:
    return {
        "validation_status": "batch_complete",
        "auto_continue": True,  # 标记自动继续
        # 注意：不返回 ui_interaction
    }

# 第1批及以后：显示按钮（实际代码实现）
buttons = []

# 1. 确认大纲（只在最后一批显示）
if not has_more_batches:
    buttons.append(
        ActionButton(
            label="✅ 确认大纲并开始写小说",
            action="confirm_skeleton",
            payload={"current_batch": current_batch_index, ...},
            style="primary",
            icon="FileText",
        )
    )

# 2. 编辑章节（只在最后一批显示）
if not has_more_batches:
    buttons.append(
        ActionButton(
            label="✏️ 编辑已生成章节",
            action="edit_chapter",
            payload={"available_chapters": list(range(1, batch_end + 1)), ...},
            style="ghost",
            icon="Edit",
        )
    )

# 3. 继续生成下一批（如果有下一批）
if has_more_batches:
    buttons.append(
        ActionButton(
            label=f"▶️ 继续生成 (批次 {next_batch_num}/{total_batch_num})",
            action="continue_skeleton_generation",
            payload={"current_batch": current_batch_index, ...},
            style="secondary",
            icon="Play",
        )
    )

# 4. 重新生成当前批次
buttons.append(
    ActionButton(
        label="🔄 重新生成当前批次",
        action="regenerate_skeleton",
        payload={"current_batch": current_batch_index, ...},
        style="secondary",
        icon="RefreshCw",
    )
)

# 5. 审阅完整大纲（只在最后一批显示）
if not has_more_batches:
    buttons.append(
        ActionButton(
            label="🔍 审阅完整大纲",
            action="review_skeleton",
            payload={"total_batches": total_batches, ...},
            style="secondary",
            icon="Search",
        )
    )

action_ui = UIInteractionBlock(
    block_type=UIInteractionBlockType.ACTION_GROUP,
    title=f"大纲生成进度 ({current_batch_index}/{total_batches})",
    description="已完成第 X 批章节生成...",
    buttons=buttons,
    dismissible=False,
)
```

#### 4.3.6 用户交互流程（V4.2 实际实现）

```
┌─────────────────────────────────────────────────────────────────────┐
│                      用户交互时序（实际实现）                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 用户点击「开始生成大纲」                                          │
│     └─→ API: action=start_skeleton_building                          │
│     └─→ batch_coordinator 计算分批策略 (5批: 0+4)                    │
│     └─→ skeleton_builder 生成第0批：完整骨架                         │
│         ├── 元数据、核心设定                                         │
│         ├── 人物体系（含全部成长轨迹）                               │
│         ├── 情节架构（完整节拍表 1-53）                              │
│         └── 章节清单（53章标题+摘要+钩子）                           │
│     └─→ validate_output 验证通过                                     │
│     └─→ auto_continue=True → 不暂停，自动继续                        │
│                                                                     │
│  2. 自动继续生成第1批（用户无感知）                                   │
│     └─→ skeleton_builder 生成 Chapter 1-13（详细内容）               │
│     └─→ validate_output 验证通过                                     │
│     └─→ auto_continue=False → 暂停，显示按钮                         │
│         「继续生成 (批次 2/4)」「重新生成当前批次」                   │
│                                                                     │
│  3. 用户点击「继续生成」或去做其他工作                                 │
│     └─→ Checkpoint 已保存状态                                        │
│     └─→ 可随时回到页面点击「继续生成」                                │
│                                                                     │
│  4. 用户点击「继续生成」                                             │
│     └─→ API: action=continue_skeleton_generation                     │
│     └─→ LangGraph 从 Checkpoint 恢复 State                          │
│     └─→ skeleton_builder 生成第2批 (Chapter 14-26)                  │
│     └─→ 传递上下文：骨架 + 前一批最后3000字                           │
│     └─→ ...重复直到第4批完成                                         │
│                                                                     │
│  5. 第4批完成后（最后一批）                                          │
│     └─→ 显示完整按钮：                                               │
│         ✅ 确认大纲并开始写小说                                       │
│         ✏️ 编辑已生成章节                                            │
│         🔍 审阅完整大纲                                              │
│         🔄 重新生成当前批次                                          │
│                                                                     │
│  6. 用户选择「确认大纲」                                             │
│     └─→ 进入 quality_control (质检)                                 │
│     └─→ 最终 output_formatter 显示完整大纲                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.3.7 分批 Prompt 策略（V4.2 实际实现）

```python
# 第0批：完整骨架（章节清单模式）
if is_first_batch:
    batch_instruction = """【第0批：完整骨架 - 章节清单模式】

本次生成任务：构建完整的故事大纲骨架（不包含详细章节内容）

**需要输出的完整部分**：

1. 一、元数据（Metadata）- 完整项目信息

2. 二、核心设定（Core Setting）- 完整世界观架构

3. 三、人物体系（Character System）- 完整且详细
   - 女主：完整人物小传 + 完整成长弧光（从Chapter 1到Chapter {total_chapters}）
   - 男主：完整人物小传 + 完整成长弧光（从Chapter 1到Chapter {total_chapters}）
   - 反派1号、反派2号、辅助角色：基础档案 + 人物关系
   - 人物关系图谱、人物成长对照表

4. 四、情节架构（Plot Architecture）- 完整节拍表
   - 核心梗概（超短版、短版、标准版、详细版）
   - 完整情节节拍表：列出从"开场画面"到"结局"的所有节拍
   - 张力曲线设计

5. 五、章节清单（Chapter List）- 所有{total_chapters}章的清单
   每章格式（简洁，不展开）：
   ### Chapter X: [标题]
   - **核心任务**：[本章必须完成的任务]
   - **核心冲突**：[具体冲突]
   - **一句话摘要**：[50字内概括]
   - **钩子**：[章节结尾的钩子]
   - **预计字数**：[根据阶段]
   - **对应短剧**：[第X-Y集]

**约束**：
- 人物成长弧光必须覆盖全部{total_chapters}章
- 节拍表必须列出所有节拍
- 不输出详细章节内容（留到后续批次展开）"""

# 中间批次：基于骨架展开详细章节
else:
    batch_instruction = """【第{N}批：展开 Chapter {start}-{end}】

本次生成任务：基于故事骨架，展开 Chapter {start} 到 Chapter {end} 的详细内容

**需要基于的故事骨架**（必须在所有批次中保持一致）：
- 第0批生成的完整人物设定和成长弧光
- 第0批生成的完整节拍表
- 第0批生成的章节清单（作为每章的指导）

**本次展开详细内容**：
Chapter {start} 到 Chapter {end}

每章必须包含的详细要素：
1. **元数据**：字数、对应短剧、故事阶段、是否付费卡点
2. **核心要素**：任务、冲突、抉择
3. **节奏设计**：类型、钩子位置、钩子内容
4. **情绪曲线**：起始值 → 变化 → 结束值
5. **场景清单**：3-5个场景（地点、核心事件、作用）
6. **伏笔系统**：新埋设 + 计划回收

**约束**：
- 严格遵循骨架中的人物设定
- 严格实现骨架中规划的节拍
- 保持与前面章节的连贯性
- 继续发展伏笔和角色成长"""

# 最后一批：最后N章 + 映射表 + UI JSON
if is_last_batch:
    batch_instruction += """

**额外输出**（最后一批）：
2. 六、短剧映射表（Drama Mapping）- 完整映射表
3. 七、创作指导（Writing Guidelines）- 完整
4. 八、UI交互数据 - 完整JSON
   - 包含准确的字数统计（基于所有已生成章节）
   - 包含所有章节的映射信息"""
```

### 4.4 Main Graph（Master Router）

```python
# backend/graph/main_graph.py

"""
Main Graph - Master Router

这是整个系统的入口，负责：
1. 解析用户意图
2. 条件路由到不同的工作流
3. 管理全局状态
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from backend.graph.workflows.story_planner_graph import build_story_planner_graph
from backend.graph.workflows.skeleton_builder_graph import build_skeleton_builder_graph
from backend.graph.workflows.novel_writer_graph import build_novel_writer_graph
from backend.graph.workflows.script_adapter_graph import build_script_adapter_graph
from backend.graph.workflows.storyboard_director_graph import build_storyboard_director_graph
from backend.graph.workflows.quality_control_graph import build_quality_control_graph

from backend.schemas.agent_state import AgentState


def build_main_graph(user_id: str, checkpointer=None):
    """
    构建 Main Graph
    
    这是整个系统的入口 Graph，负责路由到各个子 Graph。
    """
    # 构建子 Graphs
    story_planner = build_story_planner_graph(user_id)
    skeleton_builder = build_skeleton_builder_graph(user_id)
    novel_writer = build_novel_writer_graph(user_id)
    script_adapter = build_script_adapter_graph(user_id)
    storyboard_director = build_storyboard_director_graph(user_id)
    quality_control = build_quality_control_graph(user_id)
    
    # 创建 Main Graph
    workflow = StateGraph(AgentState)
    
    # 添加 Nodes（子 Graphs 作为 Nodes）
    workflow.add_node("story_planner", story_planner)
    workflow.add_node("skeleton_builder", skeleton_builder)
    workflow.add_node("novel_writer", novel_writer)
    workflow.add_node("script_adapter", script_adapter)
    workflow.add_node("storyboard_director", storyboard_director)
    workflow.add_node("quality_control", quality_control)
    
    # 添加辅助 Nodes
    workflow.add_node("intent_parser", intent_parser_node)
    workflow.add_node("context_loader", context_loader_node)
    
    # 设置入口点
    workflow.set_entry_point("intent_parser")
    
    # intent_parser -> context_loader
    workflow.add_edge("intent_parser", "context_loader")
    
    # context_loader -> 条件路由
    workflow.add_conditional_edges(
        "context_loader",
        route_to_workflow,
        {
            "story_planner": "story_planner",
            "skeleton_builder": "skeleton_builder",
            "novel_writer": "novel_writer",
            "script_adapter": "script_adapter",
            "storyboard_director": "storyboard_director",
            "quality_control": "quality_control"
        }
    )
    
    # 所有工作流结束后都到 END
    for node in ["story_planner", "skeleton_builder", "novel_writer", 
                 "script_adapter", "storyboard_director", "quality_control"]:
        workflow.add_edge(node, END)
    
    return workflow.compile(checkpointer=checkpointer)


def intent_parser_node(state: AgentState) -> AgentState:
    """
    意图解析 Node
    
    解析用户输入，确定用户意图。
    """
    user_input = state.get("user_input", "")
    
    # 意图识别逻辑
    intent = "story_planner"  # 默认
    
    if any(kw in user_input for kw in ["大纲", "骨架", "结构"]):
        intent = "skeleton_builder"
    elif any(kw in user_input for kw in ["小说", "写作", "正文"]):
        intent = "novel_writer"
    elif any(kw in user_input for kw in ["剧本", "脚本", "改编"]):
        intent = "script_adapter"
    elif any(kw in user_input for kw in ["分镜", "视频", "镜头"]):
        intent = "storyboard_director"
    elif any(kw in user_input for kw in ["优化", "精修", "改进"]):
        intent = "quality_control"
    
    return {
        **state,
        "user_intent": intent,
        "parsed_query": user_input
    }


def context_loader_node(state: AgentState) -> AgentState:
    """
    上下文加载 Node
    
    根据意图加载必要的上下文数据。
    """
    intent = state.get("user_intent")
    
    # 检查是否已有足够上下文
    has_outline = state.get("skeleton") is not None
    has_novel = state.get("novel_content") is not None
    has_script = state.get("script_data") is not None
    
    # 根据意图和已有数据决定下一步
    if intent == "skeleton_builder" and not has_outline:
        # 需要先生成选题
        state["reroute_to"] = "story_planner"
        state["warning"] = "需要先完成故事策划"
    elif intent == "script_adapter" and not has_novel:
        state["reroute_to"] = "novel_writer"
        state["warning"] = "需要先完成小说创作"
    elif intent == "storyboard_director" and not has_script:
        state["reroute_to"] = "script_adapter"
        state["warning"] = "需要先完成剧本改编"
    
    return state


def route_to_workflow(state: AgentState) -> str:
    """
    路由函数
    
    根据意图和状态决定路由到哪个工作流。
    """
    # 检查是否有重路由指示
    reroute = state.get("reroute_to")
    if reroute:
        return reroute
    
    # 正常路由
    return state.get("user_intent", "story_planner")


# 导出
__all__ = ["build_main_graph"]
```

---

## 5. 完整的数据流

```
用户输入
    ↓
[Main Graph - Master Router]
    ├─ intent_parser (普通 Node: 解析意图)
    ├─ context_loader (普通 Node: 加载上下文)
    └─ route_to_workflow (条件路由)
        ↓ 根据意图路由到

场景 1: 生成故事选题
    ↓
[Story Planner Graph]
    ├─ parse_input (普通 Node)
    ├─ genre_strategist (Agent: 调用 Tools)
    │   ├─ Tool: load_genre_context
    │   ├─ Tool: get_tropes
    │   └─ Tool: get_market_trends
    ├─ concept_generator (Agent: 调用 Tools)
    │   ├─ Tool: get_tropes
    │   ├─ Tool: get_hooks
    │   └─ Tool: get_trending_combinations
    ├─ market_assessor (Agent: 调用 Tools)
    │   └─ Tool: get_market_trends
    ├─ premise_engineer (Agent: 调用 Tools)
    │   ├─ Tool: get_hooks
    │   └─ Tool: get_character_archetypes
    ├─ planner_core (Agent: 整合输出)
    └─ format_output (普通 Node)
        ↓
输出: 三维矩阵方案

场景 2: 已有选题，生成大纲
    ↓
[Skeleton Builder Graph]
    ├─ consistency_checker (Agent)
    ├─ character_designer (Agent: 调用 Tool: get_character_archetypes)
    └─ beat_sheet_planner (Agent: 调用 Tool: load_genre_context)
        ↓
输出: 结构化大纲

场景 3: 已有大纲，写小说
    ↓
[Novel Writer Graph]
    ├─ content_generator (Agent: 调用 Tool: get_writing_keywords)
    ├─ quality_enforcer (Agent: 质量检查)
    └─ 条件边: 质量 < 80分? → 循环精修
        ↓ (如需精修)
        [Quality Control Graph]
            ├─ editor (Agent)
            └─ refiner (Agent)
        ↓ 循环最多3次
    ↓
输出: 小说正文

场景 4: 已有小说，改编剧本
    ↓
[Script Adapter Graph]
    ├─ scene_segmenter (Agent: 调用 Tool: get_hooks)
    └─ dialog_optimizer (Agent)
        ↓
输出: 结构化剧本

场景 5: 已有剧本，生成分镜
    ↓
[Storyboard Director Graph]
    ├─ shot_planner (Agent: 调用 Tool: get_camera_style)
    └─ prompt_engineer (Agent: 调用 Tool: get_visual_keywords)
        ↓
输出: 分镜指令集
```

---

## 6. 模块清单

### 6.1 Tool/Skill 层

| Skill 文件 | Tools | 功能 |
|------------|-------|------|
| theme_library.py | load_genre_context, get_tropes, get_hooks, get_character_archetypes, get_writing_keywords, get_visual_keywords, get_market_trends | 题材库查询 |
| writing_assistant.py | get_sensory_guide, get_pacing_rules, get_trending_combinations | 写作辅助 |
| visual_assistant.py | get_camera_style, get_visual_keywords | 视觉辅助 |

**总计**: 10 个 Tools

### 6.2 Agent 层

| 模块 | Agents | 功能 |
|------|--------|------|
| story_planner/ | genre_strategist, concept_generator, market_assessor, premise_engineer, planner_core | 故事策划 |
| skeleton_builder/ | consistency_checker, character_designer, beat_sheet_planner | 大纲构建 |
| novel_writer/ | content_generator, quality_enforcer | 小说创作 |
| script_adapter/ | scene_segmenter, dialog_optimizer | 剧本改编 |
| storyboard_director/ | shot_planner, prompt_engineer | 分镜设计 |
| quality_control/ | editor, refiner | 质量精修 |

**总计**: 14 个 Agents

### 6.3 Graph 层

| Graph 文件 | Nodes | 功能 |
|------------|-------|------|
| story_planner_graph.py | 5 Agents + 2 普通 Nodes | Story Planner 工作流 |
| skeleton_builder_graph.py | 3 Agents | Skeleton Builder 工作流 |
| novel_writer_graph.py | 2 Agents + 循环逻辑 | Novel Writer 工作流 |
| script_adapter_graph.py | 2 Agents | Script Adapter 工作流 |
| storyboard_director_graph.py | 2 Agents | Storyboard Director 工作流 |
| quality_control_graph.py | 2 Agents + 循环逻辑 | Quality Control 工作流 |
| main_graph.py | 6 子 Graphs + 2 普通 Nodes | 主路由 |

**总计**: 7 个 Graphs

---

## 7. 实施步骤

### Phase 0: 主题库数据准备（前置）

在实施系统前，必须先准备主题库数据：

**数据来源策略**：
1. **手动整理种子数据**（Week 1）
   - 分析10部爆款短剧（复仇、甜宠、悬疑等）
   - 人工提取：核心公式、爆款元素、钩子模板、避雷清单
   - 创建 `database/seed_data.json`

2. **AI辅助扩展**（Week 2）
   - 使用 Deep Research 基于种子数据生成变体
   - 每个元素生成3-5个变体
   - 自动填充到数据库

3. **持续更新**（长期）
   - 分析新爆款，自动提取模式
   - 用户反馈优化元素成功率
   - 每月更新热门组合

**实施步骤**：
- [ ] 选择10部爆款短剧进行分析
- [ ] 提取5个核心题材的种子数据
- [ ] 使用AI生成扩展数据（每个题材15-20个元素）
- [ ] 导入数据库并验证

---

### Phase 1: Tool/Skill 层（3天）

**Day 1-2: 基础设施**
- [ ] 创建 `backend/skills/__init__.py`
- [ ] 创建 `backend/services/database.py`（数据库服务）
- [ ] 创建数据库表结构（themes, theme_elements, theme_trends）
- [ ] **导入种子数据**（使用Phase 0准备的seed_data.json）

**Day 2-3: Skills 实现**
- [ ] 实现 `theme_library.py`（6 个 Tools）
- [ ] 实现 `writing_assistant.py`（3 个 Tools）
- [ ] 实现 `visual_assistant.py`（2 个 Tools）
- [ ] 编写单元测试

**交付物**:
- 10 个可工作的 Tools
- 数据库 schema 和 seed 数据
- Skills 单元测试（覆盖率 > 80%）

### Phase 2: Agent 层 - Story Planner（4天）

**Day 4-5: Agent 创建函数**
- [ ] 实现 `genre_strategist.py`（加载prompts/2_Story_Planner.md）
- [ ] 实现 `concept_generator.py`（加载prompts/2_Story_Planner.md）
- [ ] 实现 `market_assessor.py`（加载prompts/2_Story_Planner.md）
- [ ] 实现 `premise_engineer.py`（加载prompts/2_Story_Planner.md）
- [ ] 实现 `planner_core.py`（加载prompts/2_Story_Planner.md）
- [ ] 实现Prompt动态组装（Base + 主题库数据注入）

**Day 5-6: Prompts 优化**
- [ ] 更新 `prompts/2_Story_Planner.md`（添加主题库注入变量说明）
- [ ] 添加 few-shot examples
- [ ] 添加 Tools 调用说明
- [ ] 测试 Tool 调用能力

**Day 6-7: Graph 工作流**
- [ ] 实现 `story_planner_graph.py`
- [ ] 添加辅助 Nodes（parse_input, format_output）
- [ ] 集成测试（端到端）

**Day 7-8: 集成与测试**
- [ ] 集成到 Main Graph
- [ ] 完整流程测试
- [ ] 性能优化

**交付物**:
- 5 个 Story Planner Agents
- Story Planner Graph（可运行）
- 端到端测试用例

### Phase 3: 其他 Agents & Graphs（6天）

**Day 9-11: Skeleton Builder & Novel Writer**
- [ ] 实现 Skeleton Builder Agents（3 个，加载prompts/3_Skeleton_Builder.md）
- [ ] 实现 Skeleton Builder Graph
- [ ] 实现 Novel Writer Agents（2 个，加载prompts/4_Novel_Writer.md）
- [ ] 更新 `prompts/4_Novel_Writer.md`（添加写作指导注入说明）
- [ ] 实现 Novel Writer Graph（含循环逻辑）

**Day 12-13: Script Adapter & Storyboard Director**
- [ ] 实现 Script Adapter Agents（2 个，加载prompts/5_Script_Adapter.md）
- [ ] 实现 Script Adapter Graph
- [ ] 实现 Storyboard Director Agents（2 个，加载prompts/6_Storyboard_Director.md）
- [ ] 实现 Storyboard Director Graph

**Day 14-15: Quality Control & Asset Inspector**
- [ ] 实现 Quality Control Agents（2 个，加载prompts/7_Editor_Reviewer.md 和 8_Refiner.md）
- [ ] 实现 Quality Control Graph
- [ ] 实现 Asset Inspector Agent（加载prompts/10_Asset_Inspector.md）
- [ ] 更新 `prompts/10_Asset_Inspector.md`（添加视觉指导注入说明）
- [ ] 集成到 Novel Writer 循环

**交付物**:
- 9 个新 Agents
- 4 个新 Graphs
- 集成测试

### Phase 4: Main Graph & 集成测试（2天）

**Day 16-17: Main Graph**
- [ ] 完善 `main_graph.py`
- [ ] 实现条件路由逻辑
- [ ] 添加 checkpoint 持久化

**Day 17-18: 集成测试**
- [ ] 端到端测试所有场景
- [ ] 性能测试
- [ ] 修复 bug

**交付物**:
- 完整的 Main Graph
- 全链路集成测试
- 性能报告

---

## 8. 架构改进建议

### 8.1 当前代码的设计模式分析

当前代码使用了 **Node 包装 Agent** 模式：

```python
# 当前做法
async def _market_analyst_node(state: AgentState) -> Dict:
    """Node 包装 Agent"""
    user_id = state["user_id"]  # 从 state 获取
    agent = await create_market_analyst_agent(user_id)  # 运行时创建
    result = await agent.ainvoke(...)
    return result
```

**测试验证**：
- ✅ 能正确处理运行时参数（user_id）
- ❌ 但每次执行都创建 Agent（性能开销）
- ❌ 多了一层不必要的包装
- ❌ 不是最优设计

### 8.2 推荐的改进方案：Factory Pattern

**真实测试验证**：Factory Pattern 完全可行且更好

```python
# 推荐做法 - Factory Pattern
async def build_graph(user_id: str, project_id: str = None):
    """
    构建 Graph（Factory Pattern）
    
    经测试验证：
    - ✅ 能正确处理运行时参数
    - ✅ Agent 只创建一次（性能好）
    - ✅ 符合 LangGraph 官方标准
    - ✅ 不需要妥协
    """
    # 创建 Agent（传入运行时参数）
    agent = await create_market_analyst_agent(user_id, project_id)
    
    workflow = StateGraph(AgentState)
    
    # ✅ Agent 直接作为 Node（符合官方标准）
    workflow.add_node("market_analyst", agent)
    workflow.add_node("router", router_node)
    
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_decision)
    workflow.add_edge("market_analyst", "router")
    
    return workflow.compile()


# API 层使用
@app.post("/chat")
async def chat(request: ChatRequest):
    # 构建时传入运行时参数
    graph = await build_graph(
        user_id=request.user_id,
        project_id=request.project_id
    )
    
    result = await graph.ainvoke(initial_state)
    return result
```

**Factory Pattern 优势**（已验证）：

| 方面 | Node 包装（当前） | Factory Pattern（推荐） | 提升 |
|------|------------------|------------------------|------|
| 符合官方标准 | ⚠️ 妥协 | ✅ 完全符合 | 概念清晰 |
| Agent 创建次数 | ❌ 每次执行都创建 | ✅ 只创建一次 | 性能提升 1.5x |
| 代码复杂度 | ❌ 多一层包装 | ✅ 简洁直接 | 易维护 |
| 运行时参数 | ✅ 能处理 | ✅ 能处理 | 两者都能 |

### 8.3 当前架构的关键缺陷：Skills 层缺失

#### 当前问题

```python
# 当前代码（问题）
from backend.tools import query_database  # 直接导入底层 Tool

agent = create_react_agent(
    model=model,
    tools=[query_database],  # ❌ Agent 直接调用底层 Tool
    prompt="你是市场分析师..."
)
# 问题：Agent 需要自己写 SQL，这不是 Agent 应该关心的
```

**缺失的 Skills 层**：
- Tools 是底层功能（查询数据库、调用 API）
- Skills 是业务能力（分析市场趋势、生成故事大纲）
- 当前缺少 Skills，Agent 直接操作底层

#### 应该的三层架构

```
Layer 1: Tools（底层功能）
    └── query_database, call_api, search_internet

Layer 2: Skills（业务能力，Prompt-driven）⭐ 当前缺失
    └── analyze_market_trend, generate_story_outline

Layer 3: Agents（使用 Skills 的智能体）
    └── Market Analyst, Story Planner
```

#### 为什么必须引入 Skills 层

1. **分层原则**
   - Tools 只做原子操作
   - Skills 封装业务逻辑
   - Agents 只做决策和协调

2. **可维护性**
   - 业务逻辑散落在 Prompt 中 → 难以维护
   - 业务逻辑封装在 Skills → 易于复用和修改

3. **可复用性**
   - 不同 Agent 可能需要相同能力
   - Skills 可以被多个 Agent 复用

### 8.4 重构建议

#### ✅ 必须重构：引入 Skills 层（P0）

**范围**：
- 创建 `backend/skills/` 目录
- 实现 22 个 Skills
- 修改 Agents 使用 Skills

**工作量**：7-10 天

**风险**：低（新增代码，不影响现有功能）

#### ✅ 建议改进：使用 Factory Pattern（P1）

**范围**：
- 修改 Graph 构建方式
- 构建时传入 user_id/project_id
- Agent 直接作为 Node

**工作量**：3-5 天

**收益**：
- 性能提升（Agent 只创建一次）
- 代码更简洁
- 100% 符合官方标准

**示例**（当前 vs 改进）：

```python
# ❌ 当前做法
async def _market_analyst_node(state):
    user_id = state["user_id"]
    agent = await create_agent(user_id)  # 每次执行都创建
    return await agent.invoke(...)

# ✅ 改进后
async def build_graph(user_id: str):
    agent = await create_agent(user_id)  # 只创建一次
    workflow.add_node("agent", agent)     # Agent 直接作为 Node
    return workflow.compile()
```

#### ❌ 不需要重构：Multi-Agent 架构

**理由**：
- 符合官方标准（LangGraph 支持 Multi-Agent）
- 适合复杂工作流
- 当前实现正确

**建议**：保持现状

---

## 9.5 当前实现状态说明（V4.2 实际状态）

### 已实现功能

| 模块 | 文件 | 实现状态 | 说明 |
|------|------|---------|------|
| **大纲生成** | `skeleton_builder_graph.py` | ✅ 完整实现 | 支持分批生成（5批：0+4）、自动连续、一致性验证 |
| **大纲审阅** | `quality_control_graph.py` | ✅ 完整实现 | 支持全局审阅（full_cycle模式） |
| **张力曲线** | `tension_service.py` | ✅ 已实现 | 基于80集短剧生成，大纲阶段使用 |
| **故事策划** | `story_planner_graph.py` | ⚠️ 基础实现 | 有基础框架，功能待完善 |

### 未实现功能

| 模块 | 文件 | 实现状态 | 说明 |
|------|------|---------|------|
| **小说生成** | `novel_writer_graph.py` | ❌ **不存在** | 文档中描述为设计目标，后端未实现 |
| **剧本改编** | `script_adapter_graph.py` | ❌ **不存在** | 文档中描述为设计目标，后端未实现 |
| **小说审阅** | - | ❌ **不存在** | 单章审阅功能仅在前端设计中有描述 |
| **剧本审阅** | - | ❌ **不存在** | 尚未开发 |
| **分镜生成** | `storyboard_director_graph.py` | ⚠️ 部分实现 | 有Agent文件，无完整工作流 |

### 重要澄清

**关于剧本医生审阅系统**：
- ✅ **已实现**：大纲阶段的全局审阅（通过 `quality_control_graph`）
- ❌ **未实现**：小说阶段的单章审阅（文档中第14章描述的功能）
- ❌ **未实现**：剧本阶段的审阅

**关于张力曲线**：
- ✅ **已实现**：大纲阶段（基于短剧集数80集生成）
- ❌ **未实现**：小说阶段（按章节生成张力曲线）
- ❌ **未实现**：剧本阶段

**关于分批生成**：
- ✅ **已实现**：大纲阶段（Skeleton Builder V4.2）
- ❌ **未实现**：小说、剧本、分镜阶段的分批生成

### 前端与后端现状

| 前端模块 | 对应后端 | 状态 | 说明 |
|---------|---------|------|------|
| 📋 大纲 | `skeleton_builder_graph` | ✅ 可用 | 完整实现，可正常使用 |
| 📖 小说 | - | ❌ 不可用 | 前端有界面设计，后端未实现 |
| 📝 剧本 | - | ❌ 不可用 | 前端有界面设计，后端未实现 |
| 🎬 分镜 | - | ⚠️ 部分可用 | 基础功能可用，高级功能待开发 |

**结论**：当前系统**仅大纲阶段可用**，小说和剧本阶段为设计目标，尚未开发实现。

---

## 10. 与 v1.0 和 v3.0 的对比

### 10.1 概念修正对比

| 概念 | v1.0 (错误) | v3.0 (部分错误) | v4.0 (正确) |
|------|-------------|-----------------|-------------|
| **Skill** | `class Skill: def _build_graph()` | `@tool def skill()` | ✅ `@tool def skill()` |
| **Agent** | Skill 的方法 | 普通 Node 函数 | ✅ `create_react_agent()` 返回值 |
| **Node** | = Agent | = Agent | ✅ 包含 Agent/ToolNode/普通函数 |
| **Skill 调用** | 在 Graph 中 invoke | 普通 Node 直接调用 | ✅ 只有 Agent 能调用 Tools |
| **Agent 调用方式** | 编译后 invoke | 直接 await | ✅ Agent 自动调用 Tools |

### 10.2 架构对比

| 层级 | v1.0 | v4.0 |
|------|------|------|
| **Tool/Skill** | 无明确区分 | `backend/skills/` - 10 个 `@tool` |
| **Agent** | 在 Skill 中定义 | `backend/agents/` - 14 个 `create_react_agent` |
| **Node** | = Agent | 普通函数辅助 |
| **Graph** | Skill 内定义 | `backend/graph/workflows/` - 7 个 Graphs |

### 10.3 详细程度对比

| 内容 | v1.0 | v4.0 |
|------|------|------|
| Tool 详细实现 | ❌ 无 | ✅ 完整代码 |
| Agent System Prompt | ✅ 详细 | ✅ 详细 + 改进 |
| Graph 工作流 | ❌ Skill 内 | ✅ 独立文件 |
| 数据流 | ✅ 有 | ✅ 更详细 |
| 实施步骤 | ✅ 8周 | ✅ 15天 |

---

## 11. 关键要点总结

### 9.1 LangGraph 官方最佳实践

1. **Tool 定义**: 使用 `@tool` 装饰器
2. **Agent 创建**: 使用 `create_react_agent()`
3. **Node 概念**: Agent 是特殊的 Node，普通函数也是 Node
4. **Tool 调用**: 只有 Agent 能调用 Tools，普通 Node 不能
5. **Graph 构建**: 使用 `StateGraph`，Agent 作为 Node 添加

### 9.2 本架构的核心设计

1. **10 个 Tools/Skills**: 提供可复用的查询能力
2. **14 个 Agents**: 使用 `create_react_agent` 创建，具有自主决策能力
3. **7 个 Graphs**: 工作流定义，串联 Nodes
4. **层级清晰**: Tool → Agent → Node → Graph

### 9.3 与错误设计的根本区别

**❌ 错误设计**:
```python
class StoryPlannerSkill:  # Skill 是类
    def _build_graph(self):  # Skill 有 Graph
        workflow.add_node("genre_strategist", self._genre_strategist)  # Agent 是方法
    
    def _genre_strategist(self, state):  # 普通函数
        context = await load_theme_context(...)  # 直接调用 Tool
```

**✅ 正确设计**:
```python
# Tool/Skill
@tool
def load_theme_context(genre_id: str) -> str:  # Tool 是函数
    ...

# Agent
genre_strategist = create_react_agent(  # Agent 是 Compiled Graph
    model=model,
    tools=[load_theme_context],  # Agent 调用 Tools
    prompt=SYSTEM_PROMPT
)

# Graph
workflow.add_node("genre_strategist", genre_strategist)  # Agent 作为 Node
```

### 9.4 实现状态重要说明 ⚠️

**文档与实际代码的对应关系**：

| 功能模块 | 文档状态 | 实际实现 | 差异说明 |
|---------|---------|---------|---------|
| 大纲生成 | ✅ 详细描述 | ✅ 已实现 | 文档与实际一致 |
| 大纲审阅 | ✅ 详细描述 | ✅ 已实现 | 文档与实际一致 |
| 小说生成 | ✅ 详细描述 | ❌ 未实现 | 文档为设计目标，代码未开发 |
| 剧本改编 | ✅ 详细描述 | ❌ 未实现 | 文档为设计目标，代码未开发 |
| 小说审阅 | ✅ 详细描述 | ❌ 未实现 | 仅前端设计，后端未实现 |

**使用建议**：
- 当前系统**仅大纲阶段可用**（Skeleton Builder V4.2）
- 小说和剧本阶段的功能为**设计目标**，尚未开发
- 如需使用小说/剧本功能，需等待后续版本或自行开发

**详细实现状态参见**：第 9.5 章节《当前实现状态说明》

---

## 12. 文档历史

| 版本 | 日期 | 状态 | 说明 |
|------|------|------|------|
| v1.0 | 2026-02-07 | ❌ 错误 | Skill 设计为 Graph 类 |
| v2.0 | 2026-02-07 | ❌ 错误 | 延续 v1.0 错误 |
| v3.0 | 2026-02-07 | ⚠️ 部分错误 | Skill=Tool 正确，但 Agent 定义为普通函数 |
| v4.0 | 2026-02-07 | ✅ 正确 | 完全遵循 LangGraph 官方定义 |
| v4.1 | 2026-02-07 | ✅ 正确+现实 | 增加架构现实分析章节，说明为什么无法 100% 遵循官方标准 |
| v4.2 | 2026-02-10 | ✅ 新增 | **Skeleton Builder 分批生成架构**：解决长章节大纲 Token 限制问题，实现 Checkpoint 暂停恢复机制 + SDUI 交互引导 |
| v4.2.1 | 2026-02-10 | ✅ 修正 | **实现状态对齐**：添加第9.5章节说明当前实际实现状态，修正第19章工作流对应关系表，明确标注小说/剧本阶段尚未实现 |
| v4.3 | 2026-02-10 | ✅ 更新 | **前端实现对齐**：更新 OutlineEditor 为 TipTap 统一方案，添加 WorkshopStore 状态管理，完善 ChapterTree 分批生成功能 |

---

## 13. 前端架构设计（新增）

### 13.1 前端技术栈

```
new-fronted/
├── React 18 + TypeScript
├── Vite（构建工具）
├── Tailwind CSS（样式）
├── TipTap（富文本编辑器）⭐
├── Zustand（状态管理）
├── React Query / SWR（数据获取）
└── shadcn/ui（UI 组件库）
```

**技术选型说明：**
- **TipTap**: 基于 ProseMirror 的现代化富文本编辑器，支持协作、扩展性强
- **Zustand**: 轻量级状态管理，TypeScript 友好
- **React Query**: 自动缓存、重新验证、乐观更新

### 13.2 前端目录结构

```
new-fronted/src/
├── components/
│   ├── ai/                    # AI 相关组件
│   │   ├── AIAssistantPanel.tsx      # AI 助手面板
│   │   ├── AIAssistantBar.tsx        # AI 助手条（底部快捷操作）
│   │   ├── ActionBlockRenderer.tsx   # SDUI 动作块渲染
│   │   └── ScriptRenderer.tsx        # 剧本渲染（智能识别格式）
│   │
│   ├── workshop/              # 创作工坊核心组件
│   │   ├── ModuleTabs.tsx            # 标签切换（大纲/小说/剧本/分镜）
│   │   ├── OutlineEditor.tsx         # 大纲编辑器 ⭐ TipTap统一方案
│   │   ├── NovelEditor.tsx           # 小说编辑器（TipTap）
│   │   ├── ScriptEditor.tsx          # 剧本编辑器（TipTap）
│   │   ├── StoryboardEditor.tsx      # 分镜编辑器
│   │   ├── ChapterTree.tsx           # 章节树（左侧）⭐ 支持分批生成
│   │   ├── GlobalReviewPanel.tsx     # 全局审阅面板（底部）
│   │   ├── ChapterReviewPanel.tsx    # 单章审阅面板
│   │   ├── UnifiedReviewPanel.tsx    # 统一审阅面板 ⭐
│   │   └── FooterToolbar.tsx         # 底部工具栏
│   │
│   ├── ui/                    # 基础 UI 组件（shadcn/ui）
│   │   ├── button.tsx
│   │   ├── badge.tsx
│   │   ├── scroll-area.tsx
│   │   └── ...
│   │
│   └── modals/                # 模态框组件
│       └── ConfirmNovelNameDialog.tsx
│
├── api/                       # API 服务层
│   ├── client.ts              # HTTP 客户端配置（OpenAPI生成）
│   └── services/
│       ├── chat.ts            # AI 聊天 API
│       ├── outline.ts         # 大纲 API ⭐ 支持分批生成
│       ├── novel.ts           # 小说 API
│       ├── review.ts          # 审阅 API
│       ├── scenes.ts          # 场景 API
│       ├── shots.ts           # 镜头 API
│       ├── episodes.ts        # 剧集 API
│       └── projects.ts        # 项目 API
│
├── store/                     # 状态管理（Zustand）
│   ├── workshopStore.ts       # 工坊状态 ⭐ 包含大纲分批生成状态
│   └── uiStore.ts             # UI 状态
│
├── hooks/                     # 自定义 Hooks
│   ├── useStore.ts            # 状态管理 hooks
│   ├── useDebounce.ts         # 防抖 hook
│   └── useAIChat.ts           # AI 聊天 Hook
│
├── types/                     # TypeScript 类型定义
│   ├── api.ts                 # API 响应类型（OpenAPI生成）
│   ├── outline.ts             # 大纲类型 ⭐
│   ├── novel.ts               # 小说类型
│   ├── review.ts              # 审阅类型
│   └── sdui.ts                # SDUI 类型
│
├── lib/                       # 工具函数
│   ├── utils.ts               # cn 等工具
│   └── ai-chat-helper.ts      # AI 消息清理工具 ⭐
│
└── extensions/                # TipTap 自定义扩展
    ├── SceneNode.ts           # 场景节点
    ├── DialogueNode.ts        # 对话节点
    └── CharacterMark.ts       # 角色标记
```

### 13.3 页面布局设计

#### 13.3.1 剧本工坊页面（ScriptWorkshopPage）

**布局结构：**
```
┌─────────────────────────────────────────────────────────────────────────┐
│  📋 大纲   │  📖 小说   │  📝 剧本   │  🎬 分镜                    [保存] │
├──────────────┬──────────────────────────────────────┬───────────────────┤
│              │                                      │                   │
│  项目结构     │                                      │   AI 创作助手      │
│  （左侧）     │        富文本编辑器（中间）            │   （右侧面板）     │
│  ChapterTree │                                      │  AIAssistantPanel │
│              │                                      │                   │
│  ▼ 第一集    │   ┌────────────────────────────┐    │   ┌───────────┐  │
│    ├ 场景1   │   │ 第3章：初次相遇             │    │   │ 开始创作   │  │
│    ├ 场景2   │   │                            │    │   │ 剧本改编   │  │
│    └ 场景3   │   │ 这是一个**加粗**的文本...    │    │   │ ...       │  │
│  ▶ 第二集    │   │                            │    │   └───────────┘  │
│              │   │ - 要点1                     │    │                   │
│              │   │ - 要点2                     │    │   [聊天输入框]    │
│              │   │                            │    │                   │
│  [继续生成]  │   │ ## 场景描述                  │    │                   │
│              │   └────────────────────────────┘    │                   │
│              │       OutlineEditor                  │                   │
├──────────────┴──────────────────────────────────────┴───────────────────┤
│ 📊 剧本医生 88  ▶ 剧情张力曲线（当前章）   ▼ 重新诊断                     │
│         UnifiedReviewPanel                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 13.3.2 模块对应编辑器

| 模块标签 | 编辑器组件 | 说明 |
|---------|-----------|------|
| 📋 大纲 | `OutlineEditor` | TipTap富文本，编辑剧集/场景/镜头详情 |
| 📖 小说 | `NovelEditor` | TipTap富文本，支持章节标记、对话标记 |
| 📝 剧本 | `ScriptEditor` | TipTap富文本，剧本格式 |
| 🎬 分镜 | `StoryboardEditor` | 专用组件，镜头预览 |

#### 13.3.3 左侧大纲树（ChapterTree）

**数据流：**
```
backend/api/skeleton_builder.py
  ↓ (generate_outline)
parse_skeleton_to_outline() - 转换骨架内容为标准格式
  ↓
DB: save_outline()
  ↓ (ScriptWorkshopPage mount)
outlineService.get(projectId)
  ↓
workshopStore.loadOutline()
  ↓ (convertOutlineToNodes)
outlineNodes: OutlineNode[]
  ↓
ChapterTree props.nodes
```

**分批生成流程：**
```
用户点击"继续生成"
  ↓
continueOutlineGeneration(projectId)
  ↓
outlineService.continueGeneration()
  ↓ (SSE)
GET /api/graph/chat?action=continue_skeleton_generation
  ↓
backend/graph/main_graph.py
  ↓
skeleton_builder_graph 继续生成下一批
  ↓
loadOutline() 刷新大纲数据
```

### 13.4 核心组件设计

#### 13.4.1 大纲编辑器（OutlineEditor - TipTap）⭐

**实现说明：**
大纲编辑器采用与小说编辑器统一的 **TipTap** 技术方案，确保所有编辑器的用户体验一致。

```typescript
// src/components/workshop/OutlineEditor.tsx

import { useEditor, EditorContent, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Typography from '@tiptap/extension-typography';
import Highlight from '@tiptap/extension-highlight';
import { Markdown } from '@tiptap/markdown';

interface OutlineEditorProps {
  content: string;
  onChange: (content: string) => void;
  onJSONChange?: (json: any) => void;
  onMarkdownChange?: (markdown: string) => void;
  title: string;
  onTitleChange: (title: string) => void;
  nodeType: 'episode' | 'scene' | 'shot';
  nodeNumber?: number;
  readOnly?: boolean;
}

export function OutlineEditor({
  content,
  onChange,
  title,
  onTitleChange,
  nodeType,
  nodeNumber,
  readOnly = false,
}: OutlineEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3] },
        bulletList: { keepMarks: true },
        orderedList: { keepMarks: true },
      }),
      Placeholder.configure({
        placeholder: ({ node }) => {
          if (node.type.name === 'heading') return '标题...';
          return '输入内容...';
        },
      }),
      Typography.configure({
        openDoubleQuote: '「',
        closeDoubleQuote: '」',
      }),
      Highlight.configure({ multicolor: true }),
      Markdown,
    ],
    content: content,
    editable: !readOnly,
    autofocus: true,
    onUpdate: ({ editor }) => {
      const html = editor.getHTML();
      const json = editor.getJSON();
      const markdown = editor.storage.markdown?.getMarkdown?.() || '';
      onChange(html);
    },
  });

  // 类型标签配置
  const typeLabels = {
    episode: '剧集',
    scene: '场景',
    shot: '镜头',
  };

  return (
    <div className="flex flex-col h-full bg-surface">
      {/* 标题栏 */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3 mb-3">
          <span className="px-2 py-1 rounded text-xs font-medium">
            {typeLabels[nodeType]}
            {nodeNumber !== undefined && ` ${nodeNumber}`}
          </span>
        </div>
        <input
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder={`输入${typeLabels[nodeType]}标题...`}
          disabled={readOnly}
          className="w-full text-xl font-bold bg-transparent border-none outline-none"
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-sm text-text-secondary">
            字数: {editor?.getText().length || 0}
          </span>
        </div>
      </div>

      {/* 工具栏 */}
      {!readOnly && (
        <div className="px-6 py-2 border-b border-border bg-elevated/50 flex items-center gap-1">
          {/* 格式化按钮：加粗、斜体、高亮、标题、列表 */}
        </div>
      )}

      {/* 编辑器主体 */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto p-6">
          <EditorContent
            editor={editor}
            className="prose prose-sm dark:prose-invert max-w-none"
          />
        </div>
      </div>
    </div>
  );
}
```

**功能特性：**
- ✅ **富文本编辑** - 支持加粗、斜体、高亮、标题、列表
- ✅ **字数统计** - 实时显示当前编辑内容字数
- ✅ **防抖保存** - 使用 useDebounce 防抖保存，性能优化
- ✅ **类型标记** - 根据节点类型（剧集/场景/镜头）显示不同颜色标签
- ✅ **统一体验** - 与 NovelEditor、ScriptEditor 使用相同技术栈

**数据结构：**
```typescript
interface OutlineData {
  projectId: string;
  episodes: Episode[];
  totalEpisodes: number;
  metadata?: {
    chapter_map?: ChapterMapItem[];
    paywall_info?: PaywallInfo;
    source: 'skeleton_builder';
  };
}

interface Episode {
  episodeId: string;
  episodeNumber: number;
  title: string;
  summary?: string;
  scenes: Scene[];
  reviewStatus: 'pending' | 'passed' | 'warning' | 'error';
  reviewScore?: number;
  isPaidWall?: boolean;
}
```

#### 13.4.2 状态管理（WorkshopStore）⭐

**Zustand Store 设计：**

```typescript
// src/store/workshopStore.ts

interface WorkshopState {
  // 当前模块
  activeModule: 'outline' | 'novel' | 'script' | 'storyboard';
  
  // 工作流状态
  workflow: {
    stage: WorkflowStage;
    currentAgent: string | null;
    progress: number;
    message: string;
    isRunning: boolean;
  };
  
  // 大纲数据
  outline: OutlineData | null;
  outlineNodes: OutlineNode[];
  selectedNodeId: string | null;
  
  // 大纲分批生成状态 ⭐
  batchStatus: {
    currentBatch: number;
    totalBatches: number;
    needsNextBatch: boolean;
    isComplete: boolean;
  };
  
  // 全局审阅
  globalReview: GlobalReview | null;
  
  // UI 状态
  isGenerating: boolean;
  isReviewing: boolean;
  isSaving: boolean;
  
  // Actions - 大纲
  generateOutline: (projectId: string, planId: string) => Promise<void>;
  loadOutline: (projectId: string) => Promise<void>;
  updateOutlineNode: (nodeId: string, updates: Partial<OutlineNode>) => Promise<void>;
  selectNode: (nodeId: string) => void;
  
  // Actions - 大纲分批生成 ⭐
  setBatchStatus: (status: Partial<WorkshopState['batchStatus']>) => void;
  continueOutlineGeneration: (projectId: string) => Promise<void>;
  
  // Actions - 审阅
  reviewOutline: (projectId: string) => Promise<void>;
  loadGlobalReview: (projectId: string) => Promise<void>;
  
  // Actions - 模块切换
  setActiveModule: (module: WorkshopModule) => void;
  
  // Actions - 重置
  reset: () => void;
}
```

**分批生成状态流转：**

```
初始状态
  ↓
{ currentBatch: 0, totalBatches: 0, needsNextBatch: false, isComplete: false }
  ↓ (generateOutline 开始)
Skeleton Builder 分批生成中
  ↓ (第一批完成)
{ currentBatch: 1, totalBatches: 4, needsNextBatch: true, isComplete: false }
  ↓ (用户点击"继续生成")
continueOutlineGeneration()
  ↓ (SSE 流式响应)
{ currentBatch: 2, totalBatches: 4, needsNextBatch: true, isComplete: false }
  ↓ ...
{ currentBatch: 4, totalBatches: 4, needsNextBatch: false, isComplete: true }
```

**loadOutline 中的分批状态更新逻辑：**

```typescript
loadOutline: async (projectId) => {
  const outline = await outlineService.get(projectId);
  if (outline) {
    set({ outline });
    const nodes = convertOutlineToNodes(outline);
    set({ outlineNodes: nodes });
    
    // 从元数据读取分批信息
    const metadata = outline.metadata || {};
    const totalBatches = metadata.total_batches || 4;
    const currentBatch = metadata.current_batch || Math.ceil(nodes.length / 20);
    const needsNextBatch = nodes.length < (outline.totalEpisodes || 80) 
                          && currentBatch < totalBatches;
    
    set({
      batchStatus: {
        currentBatch,
        totalBatches,
        needsNextBatch,
        isComplete: !needsNextBatch,
      }
    });
  }
}
```

#### 13.4.3 小说编辑器（NovelEditor - TipTap）

```typescript
// src/components/workshop/NovelEditor.tsx

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';

interface NovelEditorProps {
  content: string;
  onChange: (content: string) => void;
  title: string;
  onTitleChange: (title: string) => void;
}

export function NovelEditor({ content, onChange, title, onTitleChange }: NovelEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: '开始创作你的小说...',
      }),
      // 自定义扩展
      CustomChapterMark,    // 章节标记
      CustomDialogueMark,   // 对话标记
      CustomSceneMark,      // 场景标记
    ],
    content: content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });
  
  return (
    <div className="novel-editor">
      <Toolbar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  );
}
```

**支持的小说格式：**
```markdown
# 第一章：初次相遇

## 场景1：咖啡馆

这是一个**重要**的场景。

小明："你好，请问这里有人吗？"（对话格式）
小红："没有，请坐。"

[场景描述]
阳光透过窗户洒进来...
```

#### 13.4.4 章节树（ChapterTree）⭐ 分批生成支持

**实现说明：**
章节树支持大纲分批生成功能，当大纲未完全生成时显示"继续生成"按钮。

```typescript
// src/components/workshop/ChapterTree.tsx

interface ChapterTreeProps {
  nodes: OutlineNode[];
  selectedId: string | null;
  onSelect: (nodeId: string, node: OutlineNode) => void;
  className?: string;
  batchStatus?: {
    currentBatch: number;
    totalBatches: number;
    needsNextBatch: boolean;
    isComplete: boolean;
  };
  onContinueGeneration?: () => void;
  isGenerating?: boolean;
}

export function ChapterTree({
  nodes,
  selectedId,
  onSelect,
  batchStatus,
  onContinueGeneration,
  isGenerating
}: ChapterTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => {
    // 默认展开所有剧集节点
    const initial = new Set<string>();
    nodes.forEach(node => {
      if (node.type === 'episode') {
        initial.add(node.id);
      }
    });
    return initial;
  });

  // 渲染逻辑...
  // - 树状结构渲染
  // - 集/场景/镜头的多级展开
  // - 审阅状态标记（✓ ⚠️ ⏳）
  // - 付费卡点标记
  // - 点击选中
  // - 分批生成按钮
}
```

**显示效果：**
```
▼ 第一集                  [88分 ✓]
  ├ 场景1：开场           [90分 ✓]
  ├ 场景2：冲突           [85分 ⚠️]
  └ 场景3：转折           [88分 ✓]
▶ 第二集                  [待审阅]
▶ 第三集                  [待审阅]

┌─────────────────────────────────────┐
│ 生成进度: 1 / 4 批次                 │
│ [▶ 继续生成下一批]                   │
└─────────────────────────────────────┘
```

**分批生成功能：**
- ✅ **进度显示** - 显示当前批次/总批次（如：1/4）
- ✅ **继续生成按钮** - 当 `needsNextBatch=true` 时显示
- ✅ **加载状态** - 生成中显示 loading 动画
- ✅ **自动加载** - 继续生成后自动刷新大纲数据

#### 13.4.5 剧本医生面板（ReviewPanel）

```typescript
// src/components/workshop/ReviewPanel.tsx

interface ReviewPanelProps {
  activeModule: 'outline' | 'novel' | 'script' | 'storyboard';
  currentChapterId?: string;
  outlineReview: GlobalReview | null;
  chapterReviews: Map<string, ChapterReview>;
  onReReview: () => void;
}

export function ReviewPanel({
  activeModule,
  currentChapterId,
  outlineReview,
  chapterReviews,
  onReReview,
}: ReviewPanelProps) {
  // 根据当前模块决定显示内容
  // - 大纲模式：显示全局报告
  // - 其他模式：显示当前章审阅详情
}
```

---

## 14. 剧本医生审阅系统设计（新增）

### 14.1 审阅触发机制

| 场景 | 触发方式 | 审阅范围 | 显示位置 |
|------|---------|---------|---------|
| 大纲首次生成 | **自动** | 全部章节 | 底部全局报告 |
| 大纲手动修改 | 保存后**自动** | 被修改章节 | 底部全局报告更新 |
| 进入小说某章 | **自动加载**预存结果 | 该章 | 底部单章审阅 |
| 小说某章修改 | 保存后**自动** | 该章 | 底部单章审阅实时更新 |
| 用户点击"重新诊断" | **手动** | 当前内容 | 底部更新结果 |

### 14.2 两种审阅模式

**不是冲突，是不同阶段：**

```
阶段1：大纲生成（自动全局审阅）
├─ 生成大纲 → 自动触发Editor审阅全部 → 显示全局报告
└─ 用户看到：整体评分 + 问题章节列表

阶段2：进入小说写作（单章审阅）
├─ 用户点击第3章 → 显示第3章预存审阅结果
├─ 用户修改第3章 → 实时重新审阅第3章
└─ 用户看到：该章具体问题 + 修改建议
```

### 14.3 审阅数据结构

```typescript
// 大纲全局审阅结果
interface GlobalReview {
  generatedAt: string;
  overallScore: number;
  categories: {
    logic: { score: number; issues: Issue[] };
    pacing: { score: number; issues: Issue[] };
    character: { score: number; issues: Issue[] };
    conflict: { score: number; issues: Issue[] };
    world: { score: number; issues: Issue[] };
    hook: { score: number; issues: Issue[] };
  };
  tensionCurve: number[];  // 80个点的张力值
  chapterReviews: {
    [chapterId: string]: {
      score: number;
      issues: Issue[];
      status: 'passed' | 'warning' | 'error';
    }
  };
}

// 单章审阅（实时）
interface ChapterReview {
  chapterId: string;
  reviewedAt: string;
  score: number;
  issues: Issue[];
  suggestions: Suggestion[];
}

interface Issue {
  id: string;
  category: 'logic' | 'pacing' | 'character' | 'conflict' | 'world' | 'hook';
  severity: 'low' | 'medium' | 'high';
  location?: {
    line: number;
    column: number;
  };
  description: string;
  suggestion: string;
}
```

### 14.4 审阅分类标准

| 分类 | 权重 | 检查要点 | 严重级别 |
|------|------|---------|---------|
| 🧠 逻辑/设定 | 动态计算 | 结构完整、世界观一致、时间线合理 | 轻微/严重 |
| 📈 节奏/张力 | 动态计算 | 曲线合理、高潮在87.5%、卡点张力≥90 | 需改进 |
| 👤 人设/角色 | 动态计算 | 小传完整、极致美丽、B-Story存在 | 轻微/严重 |
| ⚔️ 冲突/事件 | 动态计算 | 核心冲突明确、升级路径清晰 | 需改进 |
| 🌍 世界/规则 | 动态计算 | 3条铁律明确、战力平衡 | 严重 |
| 🪝 钩子/悬念 | 动态计算 | 开篇钩子≥90、每集cliffhanger | 严重 |

**权重动态计算：**
```typescript
// 根据题材组合动态计算权重
function calculateReviewWeights(genres: string[]): CategoryWeights {
  const baseWeights = {
    revenge: { logic: 0.10, pacing: 0.30, character: 0.10, conflict: 0.25, world: 0.05, hook: 0.20 },
    romance: { logic: 0.10, pacing: 0.20, character: 0.30, conflict: 0.10, world: 0.05, hook: 0.25 },
    suspense: { logic: 0.30, pacing: 0.20, character: 0.05, conflict: 0.05, world: 0.15, hook: 0.25 },
    // ... 其他题材
  };
  
  // 双题材取平均值并归一化
  // 返回最终权重
}
```

---

## 15. 前后端 API 对接设计（新增）

### 15.1 API 模块划分

```typescript
// src/api/services/index.ts

export { chatService } from './chat';           // AI 聊天 API
export { outlineService } from './outline';     // 大纲 API
export { novelService } from './novel';         // 小说 API
export { scriptService } from './script';       // 剧本 API
export { storyboardService } from './storyboard'; // 分镜 API
export { reviewService } from './review';       // 审阅 API
export { projectService } from './projects';    // 项目 API
```

### 15.2 大纲 API

```typescript
// src/api/services/outline.ts

export const outlineService = {
  // 生成大纲（触发后端 skeleton_builder_graph）
  generate: (projectId: string, planId: string) => 
    api.post('/outline/generate', { projectId, planId }),
  
  // 获取大纲（包含审阅结果）
  get: (projectId: string) => 
    api.get(`/outline/${projectId}`),
  
  // 更新大纲节点
  updateNode: (projectId: string, nodeId: string, data: any) =>
    api.patch(`/outline/${projectId}/nodes/${nodeId}`, data),
  
  // 手动触发全局审阅
  review: (projectId: string) =>
    api.post(`/outline/${projectId}/review`),
  
  // 确认大纲（进入下一步）
  confirm: (projectId: string) =>
    api.post(`/outline/${projectId}/confirm`),
};
```

### 15.3 小说 API

```typescript
// src/api/services/novel.ts

export const novelService = {
  // 获取章节列表
  listChapters: (projectId: string) =>
    api.get(`/novel/${projectId}/chapters`),
  
  // 获取单章内容
  getChapter: (projectId: string, chapterId: string) =>
    api.get(`/novel/${projectId}/chapters/${chapterId}`),
  
  // 保存章节（自动触发审阅）
  saveChapter: (projectId: string, chapterId: string, content: string) =>
    api.put(`/novel/${projectId}/chapters/${chapterId}`, { 
      content,
      autoReview: true  // 保存后自动审阅
    }),
  
  // 获取章节审阅结果
  getChapterReview: (projectId: string, chapterId: string) =>
    api.get(`/novel/${projectId}/chapters/${chapterId}/review`),
  
  // 应用修改建议
  applySuggestion: (projectId: string, chapterId: string, suggestionId: string) =>
    api.post(`/novel/${projectId}/chapters/${chapterId}/apply`, { suggestionId }),
};
```

### 15.4 审阅 API

```typescript
// src/api/services/review.ts

export const reviewService = {
  // 获取全局审阅报告（大纲用）
  getGlobalReview: (projectId: string) =>
    api.get(`/review/${projectId}/global`),
  
  // 获取单章审阅详情
  getChapterReview: (projectId: string, chapterId: string) =>
    api.get(`/review/${projectId}/chapters/${chapterId}`),
  
  // 触发重新审阅
  reReview: (projectId: string, chapterId?: string) =>
    api.post(`/review/${projectId}/re_review`, { chapterId }),
  
  // 获取张力曲线
  getTensionCurve: (projectId: string, chapterId?: string) =>
    api.get(`/review/${projectId}/tension_curve`, { params: { chapterId } }),
};
```

### 15.5 后端对应 API 端点

```python
# backend/api/routes/outline.py

@router.post("/outline/generate")
async def generate_outline(request: OutlineGenerateRequest):
    """触发大纲生成工作流"""
    # 调用 skeleton_builder_graph
    pass

@router.get("/outline/{project_id}")
async def get_outline(project_id: str):
    """获取大纲数据（包含审阅结果）"""
    pass

@router.post("/outline/{project_id}/review")
async def review_outline(project_id: str):
    """手动触发大纲全局审阅"""
    # 调用 Editor Agent 审阅全部章节
    pass

# backend/api/routes/novel.py

@router.put("/novel/{project_id}/chapters/{chapter_id}")
async def save_chapter(
    project_id: str, 
    chapter_id: str, 
    request: ChapterSaveRequest
):
    """保存章节，如 autoReview=true 则自动审阅"""
    # 保存内容
    # 如 autoReview=true，调用 Editor Agent 审阅该章
    pass

# backend/api/routes/review.py

@router.get("/review/{project_id}/global")
async def get_global_review(project_id: str):
    """获取大纲全局审阅报告"""
    pass

@router.get("/review/{project_id}/chapters/{chapter_id}")
async def get_chapter_review(project_id: str, chapter_id: str):
    """获取单章审阅详情"""
    pass

@router.post("/review/{project_id}/re_review")
async def re_review(project_id: str, chapter_id: Optional[str] = None):
    """触发重新审阅"""
    # 调用 Editor Agent
    pass
```

---

## 16. 数据流设计（新增）

```
用户操作
   ↓
触发 API 调用（生成/保存/审阅）
   ↓
后端 LangGraph 工作流执行
   ├─ skeleton_builder_graph（大纲生成）
   ├─ novel_writer_graph（小说生成）
   ├─ quality_control_graph（审阅）
   └─ ...
   ↓
返回结果 + 审阅报告
   ↓
前端更新状态
   ├─→ 左侧章节树（更新审阅状态标记 ✓ ⚠️ ⏳）
   ├─→ 中间编辑器（显示生成内容）
   ├─→ 底部面板（显示审阅结果）
   └─→ 右侧 AI 面板（显示交互选项）
```

---

## 17. 实施步骤更新（v4.1）

### Phase 1: 基础架构（1-2 周）

**Day 1-2: 前端基础**
- [ ] 集成 TipTap 富文本编辑器
- [ ] 替换现有 textarea 为 NovelEditor
- [ ] 实现基础格式工具栏（加粗、标题、列表）

**Day 3-4: 状态管理**
- [ ] 配置 Zustand 状态管理
- [ ] 定义 WorkshopState 接口
- [ ] 实现基础 actions（switchModule, selectChapter）

**Day 5-6: API 层**
- [ ] 定义所有 API 接口类型
- [ ] 创建 API 服务层（outline, novel, review）
- [ ] 配置 React Query 数据获取

**Day 7-8: 基础组件**
- [ ] 实现章节树组件（ChapterTree）
- [ ] 实现可折叠面板（ReviewPanel）
- [ ] 集成到 ScriptWorkshopPage

**交付物**:
- 基础前端架构
- 富文本编辑器可用
- API 服务层完整
- 基础组件可用

### Phase 2: 大纲模块（1 周）

**Day 9-10: 大纲编辑器**
- [ ] 实现大纲结构化编辑器
- [ ] 节点拖拽/展开/收起
- [ ] 审阅状态标记

**Day 11-12: 大纲 API 对接**
- [ ] 对接后端 skeleton_builder_graph
- [ ] 实现大纲生成流程
- [ ] 全局审阅报告展示

**Day 13-14: 大纲交互**
- [ ] 大纲确认/重新生成
- [ ] 流转到小说模块
- [ ] 状态持久化

**交付物**:
- 完整大纲模块
- 全局审阅报告
- 大纲生成工作流对接

### Phase 3: 小说模块完善（1 周）

**Day 15-16: 小说编辑器完善**
- [ ] TipTap 格式扩展（章节、对话、场景标记）
- [ ] 完整格式工具栏
- [ ] 内容导入/导出

**Day 17-18: 单章审阅**
- [ ] 对接后端 novel_writer_graph
- [ ] 保存自动触发审阅
- [ ] 底部剧本医生面板交互

**Day 19-20: 审阅交互**
- [ ] 问题列表展示
- [ ] 应用/忽略建议
- [ ] 实时更新审阅结果

**交付物**:
- 完整小说编辑器
- 单章自动审阅
- 审阅结果交互

### Phase 4: 剧本和分镜（1 周）

**Day 21-22: 剧本编辑器**
- [ ] 专业剧本格式编辑器
- [ ] 场景/对话/动作标记
- [ ] 对接 script_adapter_graph

**Day 23-24: 分镜编辑器**
- [ ] 分镜列表/预览
- [ ] 镜头编辑
- [ ] 对接 storyboard_director_graph

**Day 25: 集成测试**
- [ ] 全链路测试
- [ ] Bug 修复
- [ ] 性能优化

**交付物**:
- 完整剧本编辑器
- 分镜编辑器
- 全工作流对接

---

## 18. 关键技术决策（新增）

| 决策点 | 方案 | 理由 |
|--------|------|------|
| 富文本编辑器 | **TipTap** | 现代化、扩展性强、支持协作、TypeScript 原生 |
| 状态管理 | **Zustand** | 轻量、TypeScript 友好、无样板代码 |
| 数据同步 | **React Query** | 自动缓存、重新验证、乐观更新 |
| 树形组件 | **自研** | 需要高度定制审阅状态显示 |
| 实时协作 | **Yjs + TipTap** | 后期可扩展多人编辑 |
| 编辑器选型 | **TipTap vs 自研** | 选择 TipTap（开发周期 1-2天 vs 2-4周） |

---

## 19. 前端与后端工作流对应关系

| 前端模块 | 后端工作流 | 实现状态 | 触发时机 | 数据流向 |
|----------|-----------|---------|---------|---------|
| 故事策划 | story_planner_graph | ⚠️ 部分实现 | 用户输入需求 | 用户输入 → 三维矩阵方案 |
| 大纲 | skeleton_builder_graph | ✅ 已实现 | 选择方案后 | 方案 → 结构化大纲 + 审阅报告 |
| 小说 | novel_writer_graph | ❌ **未实现** | 大纲确认后 | 大纲 → 章节内容 + 单章审阅 |
| 剧本 | script_adapter_graph | ❌ **未实现** | 小说完成后 | 小说 → 剧本格式 |
| 分镜 | storyboard_director_graph | ⚠️ 部分实现 | 剧本完成后 | 剧本 → 分镜指令 |
| 审阅 | quality_control_graph | ✅ 已实现（仅大纲阶段） | 自动触发 | 内容 → 审阅报告 |

**重要说明**：
- ✅ **已实现**：`skeleton_builder_graph`（大纲分批生成）和 `quality_control_graph`（大纲审阅）
- ⚠️ **部分实现**：`story_planner_graph`、`storyboard_director_graph` 有基础实现但功能不完整
- ❌ **未实现**：`novel_writer_graph`（小说生成）、`script_adapter_graph`（剧本改编）**完全未实现**

### 各阶段张力曲线与审阅状态

| 阶段 | 张力曲线 | 剧本医生审阅 | 说明 |
|------|---------|-------------|------|
| **大纲 (Skeleton)** | ✅ 已实现 | ✅ 已实现 | 基于80集短剧生成张力曲线，支持全局审阅 |
| **小说 (Novel)** | ❌ 未实现 | ❌ 未实现 | 尚未开发，文档中的描述为设计目标 |
| **剧本 (Script)** | ❌ 未实现 | ❌ 未实现 | 尚未开发，文档中的描述为设计目标 |
| **分镜 (Storyboard)** | ❌ 不适用 | ❌ 未实现 | 分镜阶段通常不需要张力曲线 |

**注意**：文档中第13章（前端架构）和第14章（剧本医生审阅系统）描述的小说阶段和剧本阶段的张力曲线、审阅功能**仅为设计目标**，后端尚未实现对应的工作流。目前只有大纲阶段有完整的实现。

---

**这份设计是否正确？**

- ✅ Skill = Tool（`@tool` 装饰器）
- ✅ Agent = `create_react_agent()` 返回值（Compiled Graph）
- ✅ Node = Agent、ToolNode、或普通函数
- ✅ 只有 Agent 能调用 Tools
- ✅ 前端架构完整（TipTap + Zustand + React Query）
- ✅ 剧本医生审阅系统（全局 + 单章双模式）**【仅大纲阶段实现】**
- ✅ 前后端 API 对接完整**【仅大纲阶段实现】**
- ✅ 符合 LangGraph 官方文档定义
- ✅ 详细完整，不简化

如有任何疑问，请指出！
