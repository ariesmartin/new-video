# AI 短剧台 - 系统架构文档 V3.0 (融合版)

## 文档信息

| 项目 | 内容 |
|------|------|
| 产品名称 | AI 短剧台 (AI Drama Studio) |
| 版本号 | V3.0 |
| 文档类型 | 系统架构设计 (融合版) |
| 创建日期 | 2026-02-02 |
| 融合来源 | V1 (系统架构文档.md) + V2 (System-Architecture-V2.md) |
| 实现状态 | 约 85% 已代码实现 |

## 版本说明

本文档是 V1 和 V2 架构文档的融合版本，采用以下融合策略：
- **数据模型**：保留 V1 的 `story_nodes` 通用节点系统（已代码实现）
- **部署模式**：保留 V1 的 ComfyUI 模式（FastAPI 托管前端）
- **技术栈**：采用 V2 的明确技术选型描述
- **交互协议**：统一使用 V2 的 SDUI 术语，但保留 V1 的 Action Block 结构
- **模型管理**：融合 V2 的 4-Role 分类，保持 V1 的 TaskType 细粒度映射

---

## 1. 系统总览

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │  React 19 SPA  │  │  Zustand Store │  │  SDUI Renderer │                 │
│  │  (Vite Build)  │  │  (State Mgmt)  │  │  (Action Block)│                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                              API Gateway (FastAPI)                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │  REST API      │  │  SSE Stream    │  │  Action API    │                 │
│  │  /api/*        │  │  /api/stream   │  │  /api/action   │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                              Agent Orchestration (LangGraph)                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Master Router Agent                             │ │
│  │  (意图识别 → 上下文构建 → Agent 路由 → SDUI 生成)                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │  Market    │ │  Story     │ │  Module A  │ │  Module B  │               │
│  │  Analyst   │ │  Planner   │ │  (Novel)   │ │  (Script)  │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │  Module C  │ │  Asset     │ │  Editor    │ │  Refiner   │               │
│  │(Storyboard)│ │  Inspector │ │  Agent     │ │  Agent     │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
├─────────────────────────────────────────────────────────────────────────────┤
│                              Data Layer                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │  PostgreSQL    │  │  Redis         │  │  Supabase      │                 │
│  │  (Supabase)    │  │  (Cache/Queue) │  │  Storage       │                 │
│  │  - story_nodes │  │  - Sessions    │  │  - Assets      │                 │
│  │  - projects    │  │  - Jobs        │  │  - Checkpoints │                 │
│  │  - llm_provide │  │  - Pub/Sub     │  │                │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                              External Services                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │  LLM APIs  │ │  Image Gen │ │  Video Gen │ │  TTS APIs  │               │
│  │  (多模型)  │ │  (多模型)  │ │  (多模型)  │ │  (多模型)  │               │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 层级 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **Frontend** | Vite + React 19 | React 19.0.0 | SPA 架构，ComfyUI 模式托管 |
| **UI Framework** | Shadcn/UI + TailwindCSS | Tailwind 3.4 | 暗色优先设计系统 |
| **State Management** | Zustand | 4.5.x | 多 Store 架构 (App/Canvas/Chat) |
| **Backend** | Python FastAPI | 0.115.x | 高性能异步框架 |
| **Agent Framework** | LangGraph | 0.2.x | 有状态多 Agent 编排 |
| **LLM Integration** | LangChain | 0.3.x | 多模型统一接口 |
| **Database** | PostgreSQL (Supabase) | 15.x | 主数据存储 + pgvector |
| **Cache** | Redis | 7.x | 会话缓存、任务队列、PubSub |
| **Storage** | Supabase Storage | - | 对象存储 (图片/视频/音频) |
| **Auth** | Supabase Auth | - | JWT + RBAC |
| **Queue** | Celery + Redis | 5.3.x | 异步任务处理 |
| **Logging** | Structlog | 24.x | 结构化日志 |

---

## 2. Agent 系统设计

### 2.1 Agent 架构图

```
                                    ┌─────────────────────┐
                                    │    User Input       │
                                    │  (自然语言/按钮)    │
                                    └──────────┬──────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Master Router Agent                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  1. 上下文构建 (Context Building)                                       │ │
│  │     - 当前模块 (current_module): L1/L2/L3/ModA/ModB/ModC                │ │
│  │     - 当前项目 (project_id)                                             │ │
│  │     - 选中内容 (selected_content)                                       │ │
│  │     - 用户配置 (user_config: genre, tone, etc.)                         │ │
│  ├─────────────────────────────────────────────────────────────────────────┤ │
│  │  2. 意图识别 (Intent Classification)                                    │ │
│  │     - 创作意图 (Creation) → Novel Writer / Story Planner                │ │
│  │     - 编辑意图 (Editing) → Editor / Refiner                             │ │
│  │     - 分析意图 (Analysis) → Market Analyst / Analysis Lab               │ │
│  │     - 生成意图 (Generation) → Storyboard Director / Asset Inspector     │ │
│  │     - 系统意图 (System) → 内部路由处理                                  │ │
│  ├─────────────────────────────────────────────────────────────────────────┤ │
│  │  3. 参数提取 (Parameter Extraction)                                     │ │
│  │     - 目标 (target): episode_id, scene_id, shot_id                      │ │
│  │     - 操作 (operation): create, update, delete, generate                │ │
│  │     - 约束 (constraints): word_count, style, format                     │ │
│  ├─────────────────────────────────────────────────────────────────────────┤ │
│  │  4. SDUI 生成 (UI Feedback Generation)                                  │ │
│  │     - ui_feedback: 用户可读的反馈文本 (Markdown)                        │ │
│  │     - ui_interaction: Action Block (按钮组/选择器/确认框)               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                                               │
                     ┌──────────────────────────┼──────────────────────────┐
                     │                          │                          │
                     ▼                          ▼                          ▼
         ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
         │   Level 1: Market │      │   Level 2: Story  │      │   Level 3: Skeleton│
         │   Analyst         │      │   Planner         │      │   Builder          │
         │   (市场分析师)    │      │   (故事规划师)    │      │   (骨架构建师)     │
         └─────────┬─────────┘      └─────────┬─────────┘      └─────────┬─────────┘
                   │                          │                          │
                   ▼                          ▼                          ▼
         ┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
         │   Module A: Novel │      │   Module B: Script│      │   Module C: Story │
         │   Writer Loop     │      │   Adapter         │      │   board Director  │
         │   (Writer-Editor- │      │   (剧本解析师)    │      │   (分镜导演)      │
         │    Refiner闭环)   │      │                   │      │                   │
         └───────────────────┘      └───────────────────┘      └───────────────────┘
```

### 2.2 Agent 职责定义

| Agent | 职责 | 输入 | 输出 | 触发条件 |
|-------|------|------|------|----------|
| **Master Router** | 意图识别、上下文构建、Agent 路由 | 用户输入 + 当前状态 | target_agent + parameters + SDUI | 所有用户输入 |
| **Market Analyst** | 市场分析、题材推荐、SWOT 分析 | user_config (genre, tone) | 市场报告 + 参数验证 | Level 1 |
| **Story Planner** | 故事方案生成、人设构建 | market_report + user_config | 3-5 个 story_plans | Level 2 |
| **Skeleton Builder** | 分集大纲、详细人设 | selected_plan | character_bible + beat_sheet | Level 3 |
| **Novel Writer** | 小说正文撰写 | beat_sheet + style_dna | novel_content (per episode) | Module A |
| **Script Adapter** | 小说转剧本、场景切分 | novel_content + narrative_mode | script_data (list[Scene]) | Module B |
| **Storyboard Director** | 剧本转分镜、镜头设计 | script_data + visual_config | storyboard (list[Shot]) | Module C |
| **Asset Inspector** | 资产提取、设计补全 | any_text_content | asset_manifest + prompts | Module X |
| **Editor Agent** | 质量审阅、评分 | generated_content | quality_score + feedback | 每个生成节点后 |
| **Refiner Agent** | 内容精修、问题修复 | content + editor_feedback | refined_content | Editor 评分 < 80 |
| **Analysis Lab** | 情绪分析、定向修文 | novel_content | emotion_curve + surgery_result | Module A+ |

### 2.3 Agent 实现示例

**核心原则**: 使用 `create_react_agent` 创建真正的 LangChain Agent，而非普通函数。

```python
# backend/graph/agents/market_analyst.py

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from backend.tools import metaso_search, trend_analyzer

# Agent System Prompt - 明确定义职责、工具和输出格式
MARKET_ANALYST_PROMPT = """你是短剧市场分析专家。

## 职责
1. 分析当前短剧市场趋势和热门题材
2. 基于用户输入推荐合适的赛道
3. 提供数据驱动的洞察

## 可用工具
- `metaso_search`: 实时搜索市场信息
- `trend_analyzer`: 分析历史趋势数据

## 工作流
1. 首先分析用户需求，判断是否明确
2. 如需要，调用 metaso_search 获取最新市场数据
3. 生成市场分析报告 (JSON 格式)
4. 生成 SDUI 交互块，提供赛道选择按钮

## 输出要求
必须返回有效的 JSON 格式：
```json
{
  "genres": [
    {"id": "revenge", "name": "逆袭复仇", "description": "...", "trend": "hot"}
  ],
  "tones": ["爽感", "暗黑"],
  "insights": "市场洞察文本",
  "audience": "目标受众描述"
}
```
"""

# 创建 Agent - 使用 create_react_agent
market_analyst_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=[metaso_search, trend_analyzer],
    state_modifier=MARKET_ANALYST_PROMPT,
)

# 导出供 Graph 使用
__all__ = ["market_analyst_agent"]
```

**Agent 目录结构**:
```
backend/graph/agents/
├── __init__.py              # Agent 导出
├── master_router.py         # Level 0 - 意图识别 Agent
├── market_analyst.py        # Level 1 - 市场分析 Agent
├── story_planner.py         # Level 2 - 故事规划 Agent
├── skeleton_builder.py      # Level 3 - 骨架构建 Agent
├── novel_writer.py          # Module A - 小说创作 Agent
├── content_editor.py        # Module A - 内容审阅 Agent
├── content_refiner.py       # Module A - 内容精修 Agent
├── script_adapter.py        # Module B - 剧本提取 Agent
├── storyboard_director.py   # Module C - 分镜导演 Agent
├── analysis_lab.py          # Module A+ - 分析实验室 Agent
└── asset_inspector.py       # Module X - 资产探查 Agent
```

### 2.4 Agent State 定义

```python
# backend/schemas/agent_state.py
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    """LangGraph Agent 全局状态 - 融合 V1 + V2 定义"""
    
    # ===== Core Identifiers =====
    thread_id: str                          # 会话 ID (LangGraph checkpoint)
    project_id: Optional[str]               # 项目 ID
    user_id: str                            # 用户 ID
    
    # ===== Level 1: User Configuration =====
    user_config: Dict[str, Any]             # 用户配置
    # {
    #   "genre": "逆袭复仇",           # 题材赛道
    #   "sub_tags": ["重生", "打脸"],  # 细分标签
    #   "tone": ["爽感", "暗黑"],      # 内容调性
    #   "target_word_count": 500,       # 单集字数
    #   "total_episodes": 10,           # 目标集数
    #   "ending_type": "HE",            # HE/BE/OE
    #   "aspect_ratio": "9:16",         # 画面比例
    #   "drawing_type": "电影写实",     # 绘图类型
    #   "visual_style": "现代都市",     # 画面风格
    #   "style_dna": "短句为主，冷峻",  # 文风 DNA
    #   "avoid_tags": ["狗血", "圣母"]  # 排除标签
    # }
    market_report: Optional[Dict]           # 市场分析报告
    
    # ===== Level 2: Story Planning =====
    story_plans: List[Dict]                 # 3-5 个候选方案
    selected_plan: Optional[Dict]           # 用户选中的方案
    fusion_request: Optional[Dict]          # 方案融合请求
    
    # ===== Level 3: Skeleton Building =====
    character_bible: List[Dict]             # 角色圣经 (详细人设)
    beat_sheet: List[Dict]                  # 分集大纲 (Beat Sheet)
    
    # ===== Module A: Novel Generation =====
    current_episode: int                    # 当前生成的集数
    novel_content: str                      # 当前集小说内容
    novel_archive: Dict[int, str]           # 归档: {episode_num: content}
    
    # ===== Module B: Script Extraction =====
    script_data: List[Dict]                 # 结构化剧本 (Scenes)
    narrative_mode: str                     # 叙事模式: dialog/voiceover/hybrid
    
    # ===== Module C: Storyboard =====
    storyboard: List[Dict]                  # 分镜列表 (Shots)
    generation_model: str                   # 图片/视频生成模型
    
    # ===== Module X: Asset Inspector =====
    asset_manifest: Dict                    # 资产清单 (角色/场景/道具)
    asset_prompts: List[Dict]               # 设定图提示词列表
    
    # ===== Module A+: Analysis Lab =====
    emotion_curve: List[Dict]               # 情绪曲线数据
    surgery_result: str                     # 定向修文结果
    
    # ===== Long-Term Memory (Logic Guardian) =====
    hero_state: Dict                        # 主角弧光追踪
    unresolved_mysteries: List[str]         # 未填坑的伏笔列表
    history_summary: str                    # 滚动剧情摘要
    
    # ===== Control Flags =====
    current_stage: str                      # L1/L2/L3/ModA/ModB/ModC
    approval_status: str                    # PENDING/APPROVED/REJECTED
    human_feedback: str                     # 用户修改意见
    revision_count: int                     # 修改次数 (max=3)
    quality_score: float                    # Editor Agent 评分
    skill_scores: Dict[str, float]          # 详细评分矩阵
    
    # ===== Routing Control =====
    use_master_router: bool                 # 是否使用智能路由
    routed_agent: Optional[str]             # AI 解析出的目标 Agent
    routed_function: Optional[str]          # AI 解析出的函数
    routed_parameters: Optional[Dict]       # AI 解析出的参数
    
    # ===== SDUI Protocol =====
    ui_interaction: Optional[Dict]          # UI 交互块 (Action Block)
    
    # ===== Error Handling =====
    error_message: Optional[str]            # 错误信息
    last_successful_node: Optional[str]     # 最后成功节点
```

---

## 3. LangGraph 流程设计

### 3.1 主流程图

```
                              ┌─────────────┐
                              │   START     │
                              └──────┬──────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │     master_router      │
                        │  (意图识别 + 路由决策) │
                        └────────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
        ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
        │market_analyst │  │ story_planner │  │ 直接跳转      │
        └───────┬───────┘  └───────┬───────┘  │ (ModA/B/C)    │
                │                  │          └───────────────┘
                ▼                  ▼
        ┌───────────────┐  ┌───────────────┐
        │ skeleton_     │  │               │
        │ builder       │  │               │
        └───────┬───────┘  │               │
                │          └───────────────┘
                ▼
        ┌───────────────────────────────┐
        │       Module A Subgraph       │
        │  ┌─────────┐    ┌─────────┐   │
        │  │ Writer  │───→│ Editor  │   │
        │  └─────────┘    └────┬────┘   │
        │                      │         │
        │              ┌───────┴───────┐ │
        │         <80? │               │ │
        │         ┌───→│   Refiner    │ │
        │         │    │   (循环)     │ │
        │         │    └──────┬──────┘ │
        │         │           └────────→│ (回到 Writer)
        │         │                     │
        │         └──→ END (>=80)       │
        └───────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │       Module B Subgraph       │
        │    (Script Adapter Loop)      │
        └───────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │       Module C Subgraph       │
        │  (Storyboard Director Loop)   │
        └───────────────────────────────┘
                    │
                    ▼
            ┌─────────────┐
            │  save_and_  │
            │    exit     │
            └──────┬──────┘
                   │
                   ▼
              ┌─────────┐
              │   END   │
              └─────────┘
```

### 3.2 条件路由逻辑

```python
# backend/graph/main_graph.py

def route_after_master_router(state: AgentState) -> str:
    """Master Router 后的路由决策"""
    
    target = state.get("routed_agent")
    current_stage = state.get("current_stage", "L1")
    
    # Agent 名称到节点名称的映射
    agent_node_map = {
        # Level 1-3
        "Market_Analyst": "market_analyst",
        "Story_Planner": "story_planner",
        "Skeleton_Builder": "skeleton_builder",
        # Module Agents (映射到子图)
        "Novel_Writer": "module_a",
        "Module_A": "module_a",
        "Script_Adapter": "module_b",
        "Module_B": "module_b",
        "Storyboard_Director": "module_c",
        "Module_C": "module_c",
        # Special Agents
        "Analysis_Lab": "analysis_lab",
        "Asset_Inspector": "asset_inspector",
        "Editor": "editor_agent",
        "Refiner": "refiner_agent",
    }
    
    if target in agent_node_map:
        return agent_node_map[target]
    
    # 基于阶段的默认路由
    stage_map = {
        "L1": "market_analyst",
        "L2": "story_planner",
        "L3": "skeleton_builder",
        "ModA": "module_a",
        "ModB": "module_b",
        "ModC": "module_c",
    }
    
    return stage_map.get(current_stage, "error_handler")


def route_after_editor(state: AgentState) -> str:
    """Editor Agent 后的路由决策"""
    
    skill_scores = state.get("skill_scores", {})
    overall_score = state.get("quality_score", 100)
    revision_count = state.get("revision_count", 0)
    max_retries = 3
    
    # 评分阈值
    if overall_score >= 80:
        return "end"  # 通过，进入下一节点
    elif revision_count < max_retries:
        return "refiner_agent"  # 需要修改，进入精修
    else:
        # 达到最大重试次数，标记警告但继续
        return "end_with_warning"


def route_after_module_a(state: AgentState) -> str:
    """Module A 完成后的路由"""
    
    current_episode = state.get("current_episode", 1)
    total_episodes = state.get("user_config", {}).get("total_episodes", 10)
    
    # 检查用户是否选择进入下一阶段
    if state.get("routed_agent") == "module_b":
        return "module_b"
    
    # 如果还有剩余集数，继续生成
    if current_episode < total_episodes:
        return "continue"  # 回到 Module A 生成下一集
    
    # 所有集数完成，进入 Module B
    return "module_b"
```

### 3.3 Graph 构建代码

```python
# backend/graph/main_graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from backend.schemas.agent_state import AgentState
from backend.graph.agents import (
    master_router_agent,
    market_analyst_agent,
    story_planner_agent,
    skeleton_builder_agent,
    analysis_lab_agent,
    asset_inspector_agent,
)
from backend.graph.subgraphs import (
    create_module_a_subgraph,  # Writer-Editor-Refiner
    create_module_b_subgraph,  # Script Adapter
    create_module_c_subgraph,  # Storyboard Director
)


def create_main_graph(checkpointer: BaseCheckpointSaver | None = None):
    """创建主图 - 支持双路由模式 (Agent 架构)"""
    
    graph = StateGraph(AgentState)
    
    # ===== 编译子图 =====
    module_a_subgraph = create_module_a_subgraph().compile()
    module_b_subgraph = create_module_b_subgraph().compile()
    module_c_subgraph = create_module_c_subgraph().compile()
    
    # ===== 添加 Agent 节点 =====
    # 使用 create_react_agent 创建的 Agents
    graph.add_node("master_router", master_router_agent)
    graph.add_node("market_analyst", market_analyst_agent)
    graph.add_node("story_planner", story_planner_agent)
    graph.add_node("skeleton_builder", skeleton_builder_agent)
    graph.add_node("module_a", module_a_subgraph)  # 子图封装
    graph.add_node("module_b", module_b_subgraph)  # 子图封装
    graph.add_node("module_c", module_c_subgraph)  # 子图封装
    graph.add_node("analysis_lab", analysis_lab_agent)
    graph.add_node("asset_inspector", asset_inspector_agent)
    graph.add_node("save_and_exit", _save_and_exit_node)
    
    # ===== 添加边 =====
    
    # 入口: 双路由模式
    graph.add_conditional_edges(
        START,
        _route_from_start,
        {
            "master_router": "master_router",  # 智能路由
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            "skeleton_builder": "skeleton_builder",
            "module_a": "module_a",
            "module_b": "module_b",
            "module_c": "module_c",
        },
    )
    
    # Master Router -> 各 Agent
    graph.add_conditional_edges(
        "master_router",
        route_after_master_router,
        {
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            "skeleton_builder": "skeleton_builder",
            "module_a": "module_a",
            "module_b": "module_b",
            "module_c": "module_c",
            "analysis_lab": "analysis_lab",
            "asset_inspector": "asset_inspector",
            "end": END,
        }
    )
    
    # Level 1 -> Level 2 -> Level 3
    graph.add_conditional_edges(
        "market_analyst",
        _route_after_market_analyst,
        {"wait": END, "next": "story_planner"}
    )
    graph.add_conditional_edges(
        "story_planner",
        _route_after_planner,
        {"wait": END, "next": "skeleton_builder"}
    )
    graph.add_conditional_edges(
        "skeleton_builder",
        _route_after_skeleton,
        {"wait": END, "next": "module_a"}
    )
    
    # Module A -> Module B
    graph.add_conditional_edges(
        "module_a",
        route_after_module_a,
        {"continue": "module_a", "next": "module_b"}
    )
    
    # Module B -> Module C -> Save
    graph.add_edge("module_b", "module_c")
    graph.add_edge("module_c", "save_and_exit")
    graph.add_edge("save_and_exit", END)
    
    # Special modules -> END
    graph.add_edge("analysis_lab", END)
    graph.add_edge("asset_inspector", END)
    
    # ===== 编译图 =====
    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            "story_planner",      # 等待用户选择方案
            "skeleton_builder",   # 等待用户确认大纲
            "module_a",           # 等待用户确认进入小说生成
            "module_b",           # 等待用户确认进入剧本提取
            "module_c",           # 等待用户确认进入分镜拆分
        ],
    )
    
    return compiled
```

### 3.4 高级 LangGraph 特性

本节详细描述系统使用的高级 LangGraph 特性，这些特性是实现专业级 AI 编排的关键。

#### 3.4.1 Map-Reduce (并发分镜生成)

**问题场景**：当 Script Adapter 生成包含 20 个场景的剧本后，需要为每个场景生成分镜。串行执行耗时过长。

**解决方案**：使用 LangGraph `Send` API 实现 Map-Reduce 并行处理。

```python
# backend/graph/nodes/storyboard_director.py
from langgraph.constants import Send

async def storyboard_router_node(state: AgentState):
    """分镜路由节点 - 分发并行任务"""
    scenes = state.get("script_data", [])
    
    # Map: 为每个场景创建一个 Send 任务
    return [
        Send("shot_generator", {
            "scene": scene,
            "scene_index": idx,
            "total_scenes": len(scenes),
        })
        for idx, scene in enumerate(scenes)
    ]

async def shot_generator_node(state: AgentState):
    """单个场景的分镜生成节点"""
    scene = state["scene"]
    scene_idx = state["scene_index"]
    
    # 生成该场景的所有分镜
    shots = await generate_shots_for_scene(scene)
    
    return {
        "storyboard": shots,  # 会被 reducer 合并
        "progress": f"已生成场景 {scene_idx + 1}/{state['total_scenes']}"
    }

# 在子图中使用
def create_module_c_subgraph():
    graph = StateGraph(AgentState)
    
    # 添加节点
    graph.add_node("shot_router", storyboard_router_node)
    graph.add_node("shot_generator", shot_generator_node)
    graph.add_node("shot_assembler", shot_assembler_node)  # Reduce
    
    # 路由到并行生成
    graph.add_conditional_edges(
        "shot_router",
        lambda state: state,  # 返回 Send 列表
        ["shot_generator"]
    )
    
    # 所有并行任务完成后，汇聚到 assembler
    graph.add_edge("shot_generator", "shot_assembler")
    
    return graph
```

**配置参数**：
```python
# 前端配置面板暴露的选项
MAX_CONCURRENCY = 5  # 最大并发数，防止 API 限流
```

**Reduce 策略**：
```python
def merge_storyboard(existing: list, new: list) -> list:
    """合并分镜列表 - 保持场景顺序"""
    result = existing.copy() if existing else []
    result.extend(new)
    # 按场景索引排序
    return sorted(result, key=lambda x: x.get("scene_index", 0))

# 在 State 定义中使用
class AgentState(TypedDict):
    storyboard: Annotated[list[ShotData], merge_storyboard]
```

#### 3.4.3 Live Directing (实时导戏 / 热修补)
[...内容保持不变...]

### 3.5 Server-Driven UI Text (SDUI-Text)

**问题场景**：由前端硬编码 AI 节点的中文状态描述（如 "Market Analyst" -> "正在分析..."）导致扩展性差，每增加一个 Agent 都需要修改前端映射。

**解决方案**：将 UI 文案的定义权收归后端，通过 SSE 协议动态下发。

**架构设计**：
1. **Backend Definition**:
   在 `backend/api/graph.py` 中定义 `NODE_DISPLAY_NAMES` 常量：
   ```python
   NODE_DISPLAY_NAMES = {
       "market_analyst": "🔍 正在分析市场趋势...",
       "story_planner": "✍️ 正在构思故事方案...",
       "skeleton_builder": "🏗️ 正在搭建故事骨架..."
   }
   ```

2. **Protocol Extension**:
   SSE `node_start` 和 `on_tool_start` 事件增加 `desc` 和 `status` 字段：
   ```json
   {
     "type": "node_start",
     "node": "market_analyst",
     "desc": "🔍 正在分析市场趋势..."  // 前端直接显示此文本
   }
   ```
   ```json
   {
     "type": "status",
     "message": "🌐 正在搜索最新市场数据...", // 工具调用状态
     "tool": "metaso_search"
   }
   ```

3. **Frontend Rendering**:
   前端 `AIAssistantBar` 移除所有硬编码映射，直接渲染后端下发的 `desc` 或 `message`。

**优势**：
- **Zero Frontend Change**: 增加新 Agent 节点只需修改后端 Python 代码。
- **Dynamic Context**: 后端可以根据上下文（如 Genre）动态调整提示文本。
- **Consistency**: 保证了日志、UI 提示和业务逻辑的一致性。

**问题场景**：用户想基于第 3 章创建"复仇版"剧情分支，同时保留原"虐恋版"。

**解决方案**：利用 Checkpoint 机制创建分支。

**状态分叉机制**：
```python
# backend/api/graph.py

@router.post("/branch")
async def create_branch(
    request: BranchRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    创建新的剧情分支 (平行宇宙)
    
    Request:
    {
        "source_thread_id": "thread_001",
        "branch_point": "chapter_3",  # 从哪个节点分叉
        "branch_name": "复仇版",
        "modifications": {
            "hero_personality": "冷酷果断",
            "plot_direction": "复仇"
        }
    }
    """
    graph = get_compiled_graph()
    
    # 生成新的 thread_id
    new_thread_id = f"{request.source_thread_id}_branch_{uuid.uuid4().hex[:8]}"
    
    source_config = {"configurable": {"thread_id": request.source_thread_id}}
    target_config = {"configurable": {"thread_id": new_thread_id}}
    
    # 1. 获取源线程在分叉点的状态
    source_state = await graph.aget_state(source_config)
    
    # 2. 创建新线程，从分叉点开始
    await graph.aupdate_state(
        target_config,
        values={
            **source_state.values,
            **request.modifications,  # 应用修改
            "thread_id": new_thread_id,
            "parent_thread_id": request.source_thread_id,
            "branch_point": request.branch_point,
            "branch_name": request.branch_name,
        },
        as_node=request.branch_point,  # 从指定节点继续
    )
    
    # 3. 可选：立即执行一步
    async for event in graph.astream(None, target_config):
        pass
    
    return {"new_thread_id": new_thread_id, "status": "created"}
```

**前端界面 - 分支管理**：
```
┌─────────────────────────────────────────┐
│ 分支管理 - 《野犬加冕》                  │
├─────────────────────────────────────────┤
│                                         │
│ 主线 (当前)                             │
│ ●────────●────────●────────●───────►   │
│ L1      L2      L3    Chapter 3       │
│                                         │
│ 分支 (2)                                │
│ ●────────●────────●────────┬───────►   │
│                           │            │
│                    ┌──────┴──────┐    │
│                    ▼              ▼    │
│               [复仇版]        [甜宠版]  │
│               (运行中)        (暂停)   │
│                                         │
│ [+ 从当前节点创建分支]                   │
│                                         │
└─────────────────────────────────────────┘
```

**Time Travel (时间旅行)**：
```python
@router.post("/rollback")
async def rollback(
    request: RollbackRequest,
):
    """
    回滚到指定检查点
    """
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # 获取历史检查点列表
    history = await graph.aget_state_history(config)
    
    # 找到目标检查点
    target_checkpoint = None
    for state in history:
        if state.checkpoint_id == request.checkpoint_id:
            target_checkpoint = state
            break
    
    if not target_checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    
    # 创建回滚记录
    await db.execute("""
        INSERT INTO branch_history 
        (thread_id, action, from_checkpoint, to_checkpoint, reason)
        VALUES (%s, 'ROLLBACK', %s, %s, %s)
    """, (request.thread_id, 
          (await graph.aget_state(config)).checkpoint_id,
          request.checkpoint_id,
          request.reason))
    
    # 实际回滚：更新状态到目标检查点
    await graph.aupdate_state(
        config,
        values=target_checkpoint.values,
        as_node=target_checkpoint.next_node,  # 从下一个节点继续
    )
    
    return {"status": "rolled_back", "to_checkpoint": request.checkpoint_id}
```

#### 3.4.3 Live Directing (实时导戏 / 热修补)

**问题场景**：Agent 正在写第 5 章，用户突然想修改背景设定或人物性格。

**解决方案**：State Patching - 运行时状态修补。

```python
# backend/api/graph.py

@router.patch("/state")
async def patch_state(
    request: StatePatchRequest,
):
    """
    实时修补 Graph 状态 (Live Directing)
    
    就像导演在片场喊"卡！"，然后调整演员表演
    """
    graph = get_compiled_graph()
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # 1. 获取当前执行状态
    current_state = await graph.aget_state(config)
    
    # 2. 验证当前是否正在运行
    if current_state.next_node is None:
        raise HTTPException(
            status_code=400, 
            detail="Graph 不在运行中，无法热修补"
        )
    
    # 3. 应用修补
    allowed_patches = {
        "user_config",      # 修改配置
        "character_bible",  # 修改人设
        "human_feedback",   # 添加反馈
        "hero_state",       # 修改主角状态
    }
    
    patches = {k: v for k, v in request.patches.items() if k in allowed_patches}
    
    # 4. 更新状态
    await graph.aupdate_state(config, patches)
    
    # 5. 记录导演指令
    logger.info(
        "Live directing applied",
        thread_id=request.thread_id,
        patches=list(patches.keys()),
        current_node=current_state.next_node,
    )
    
    return {
        "status": "patched",
        "applied_patches": patches,
        "current_node": current_state.next_node,
        "message": f"修补已应用，Agent 将在下一节点读取新状态"
    }
```

**前端 UX - 实时控制面板**：
```
┌─────────────────────────────────────────┐
│ 🎬 实时导演控制台                       │
│                                         │
│ 当前状态: 正在生成 Chapter 5...         │
│ 进度: ████████████░░░░ 65%              │
│                                         │
│ 快速调整:                               │
│ ┌─────────────────────────────────────┐ │
│ │ 背景设定                              │ │
│ │ [现代都市 ▼] → [赛博朋克 ▼]          │ │
│ │                                      │ │
│ │ 主角性格                              │ │
│ ● 温和善良 ○ 冷酷果断 ○ 腹黑深沉       │ │
│ │                                      │ │
│ │ [紧急修改] [软重启] [强制停止]       │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 最近指令:                               │
│ • 14:32 - 背景改为"雨夜" (已生效)       │
│ • 14:28 - 男主增加"傲娇"属性 (下一章生效)│
│                                         │
└─────────────────────────────────────────┘
```

**软重启 vs 硬重启**：
```python
# 软重启：保留已生成内容，从下一节点应用修改
async def soft_restart(thread_id: str, patches: dict):
    config = {"configurable": {"thread_id": thread_id}}
    
    # 只更新状态，不中断当前执行
    await graph.aupdate_state(config, patches)
    
    return {"message": "修改将在下一节点生效"}

# 硬重启：中断当前生成，重新从指定节点开始
async def hard_restart(thread_id: str, from_node: str, patches: dict):
    config = {"configurable": {"thread_id": thread_id}}
    
    # 中止当前执行
    await cancel_running_tasks(thread_id)
    
    # 更新状态
    await graph.aupdate_state(config, patches)
    
    # 从指定节点重新开始
    await graph.aupdate_state(config, as_node=from_node)
    
    # 恢复执行
    async for event in graph.astream(None, config):
        pass
    
    return {"message": f"已从 {from_node} 节点重新开始"}
```

#### 3.4.4 Advanced Memory & Caching (记忆增强)

**A. Time-Weighted Memory (记忆衰减)**

**问题**：随着剧情推进，Agent 不应频繁引用 100 章前的无关细节。

**解决方案**：基于时间的向量检索权重衰减。

```python
# backend/services/memory_service.py
from langchain_community.retrievers import TimeWeightedVectorStoreRetriever

class TimeWeightedMemory:
    """时间加权记忆服务"""
    
    def __init__(self, decay_rate: float = 0.01):
        self.decay_rate = decay_rate
        self.retriever = TimeWeightedVectorStoreRetriever(
            vectorstore=SupabaseVectorStore(),
            decay_rate=decay_rate,
            k=5,  # 返回 top 5
        )
    
    async def recall(
        self, 
        query: str, 
        project_id: str,
        current_timestamp: float,
    ) -> list[Document]:
        """
        检索记忆，时间越久权重越低
        
        Score = Semantic_Similarity * exp(-decay_rate * time_delta)
        """
        # 添加项目过滤
        filters = {"project_id": project_id}
        
        docs = await self.retriever.aretrieve(
            query,
            filters=filters,
            current_time=current_timestamp,
        )
        
        return docs
```

**配置参数**：
```python
# decay_rate 配置
DECAY_RATES = {
    "fast": 0.05,    # 快速遗忘，适合短篇
    "normal": 0.01,  # 正常遗忘，适合中篇
    "slow": 0.005,   # 慢速遗忘，适合长篇
}
```

**B. Semantic Caching (语义缓存)**

**问题**：用户重复点击生成，或相似 Prompt 重复提交，浪费 API 费用。

**解决方案**：基于 Embedding 相似度的缓存。

```python
# backend/services/semantic_cache.py
import hashlib
from typing import Optional

class SemanticCache:
    """语义缓存服务"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.threshold = similarity_threshold
        self.embedding_model = OpenAIEmbeddings()
    
    async def get(
        self, 
        prompt: str, 
        model_name: str,
    ) -> Optional[str]:
        """获取缓存响应"""
        
        # 计算当前 prompt 的 embedding
        prompt_embedding = await self.embedding_model.aembed_query(prompt)
        
        # 在数据库中查找相似 prompt
        similar = await db.fetch_one("""
            SELECT response, prompt_embedding <=> %s as distance
            FROM semantic_cache
            WHERE model_name = %s
              AND prompt_embedding <=> %s < %s
            ORDER BY distance
            LIMIT 1
        """, (prompt_embedding, model_name, 1 - self.threshold))
        
        if similar:
            # 更新命中次数
            await db.execute("""
                UPDATE semantic_cache 
                SET hit_count = hit_count + 1,
                    last_hit_at = NOW()
                WHERE prompt_hash = %s
            """, (hashlib.sha256(prompt.encode()).hexdigest(),))
            
            return similar["response"]
        
        return None
    
    async def set(
        self, 
        prompt: str, 
        response: str,
        model_name: str,
    ):
        """设置缓存"""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        prompt_embedding = await self.embedding_model.aembed_query(prompt)
        
        await db.execute("""
            INSERT INTO semantic_cache 
            (prompt_hash, prompt_embedding, response, model_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (prompt_hash) DO NOTHING
        """, (prompt_hash, prompt_embedding, response, model_name))
```

**缓存策略**：
```python
# 在 ModelRouter 中使用
class ModelRouter:
    async def get_model_response(self, task_type: str, prompt: str):
        # 1. 检查语义缓存
        cached = await self.semantic_cache.get(prompt, task_type)
        if cached:
            logger.info("Semantic cache hit", similarity=0.97)
            return cached
        
        # 2. 调用模型
        model = await self.get_model(task_type)
        response = await model.ainvoke(prompt)
        
        # 3. 存入缓存
        await self.semantic_cache.set(prompt, response.content, task_type)
        
        return response.content
```

**效果**：
- **Zero Latency**: 缓存命中时秒回
- **Zero Cost**: 不扣 API 费用
- **命中率**: 重复操作时可达 60-80%

---

## 4. API 设计

### 4.1 API 端点总览

| 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/health` | GET | 健康检查 | 🟢 已实现 |
| `/api/projects` | GET/POST | 项目列表/创建 | 🟢 已实现 |
| `/api/projects/{id}` | GET/PUT/DELETE | 项目详情/更新/删除 | 🟢 已实现 |
| `/api/projects/{id}/nodes` | GET/POST | 节点列表/创建 | 🟢 已实现 |
| `/api/nodes/{id}` | GET/PUT/DELETE | 节点详情/更新/删除 | 🟢 已实现 |
| `/api/graph/chat` | POST | 聊天消息 (SSE) | 🟢 已实现 |
| `/api/graph/approve` | POST | 用户确认 (Human-in-the-Loop) | 🟢 已实现 |
| `/api/graph/state` | GET | 获取 Graph 状态 | 🟢 已实现 |
| `/api/graph/topology` | GET | 获取图拓扑 (Mermaid) | 🟢 已实现 |
| `/api/action` | POST | SDUI Action 处理 | 🟡 需确认 |
| `/api/jobs` | GET/POST | 任务列表/创建 | 🟢 已实现 |
| `/api/jobs/{id}/cancel` | POST | 取消任务 | 🟢 已实现 |
| `/api/models/providers` | GET/POST | 模型服务商管理 | 🟢 已实现 |
| `/api/models/mappings` | GET/POST | 任务模型映射 | 🟢 已实现 |
| `/api/tools/*` | POST | 工具箱 API | 🟢 已实现 |

### 4.2 核心 API 详解

#### 4.2.1 聊天 API (SSE 流式)

```python
# backend/api/graph.py

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    发送消息并获取流式响应
    
    使用 Server-Sent Events (SSE) 返回 Agent 的思考过程。
    """
    graph = get_compiled_graph()
    
    config = {
        "configurable": {
            "thread_id": request.thread_id or str(request.project_id),
        }
    }
    
    # 获取或创建状态
    state = await graph.aget_state(config)
    if state.values:
        current_state = state.values
    else:
        current_state = create_initial_state(
            user_id=user_id,
            project_id=str(request.project_id),
            thread_id=request.thread_id,
        )
    
    # 添加用户消息并启用智能路由
    current_state["messages"] = current_state.get("messages", []) + [
        HumanMessage(content=request.message)
    ]
    current_state["use_master_router"] = True
    current_state["routed_agent"] = None
    
    async def generate() -> AsyncGenerator[str, None]:
        async for event in graph.astream_events(current_state, config, version="v2"):
            event_type = event.get("event")
            
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content"):
                    content = chunk.content
                    if content:
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            
            elif event_type == "on_chain_start":
                node = event.get("metadata", {}).get("langgraph_node", "")
                if node and node not in INTERNAL_NODES:
                    yield f"data: {json.dumps({'type': 'node_start', 'node': node})}\n\n"
        
        # 发送最终状态
        final_state = await graph.aget_state(config)
        yield f"data: {json.dumps({'type': 'done', 'state': _serialize_state(final_state.values)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

**SSE 事件类型**:

| 事件类型 | 说明 | 数据格式 |
|----------|------|----------|
| `token` | 流式 token | `{"type": "token", "content": "text"}` |
| `node_start` | 节点开始执行 | `{"type": "node_start", "node": "writer"}` |
| `node_end` | 节点执行完成 | `{"type": "node_end", "node": "writer"}` |
| `ui_update` | UI 交互块更新 | `{"type": "ui_update", "ui_interaction": {...}}` |
| `state_update` | 状态变更 | `{"type": "state_update", "key": "value"}` |
| `error` | 错误信息 | `{"type": "error", "message": "..."}` |
| `done` | 完成 | `{"type": "done", "state": {...}}` |

#### 4.2.2 Action API (SDUI)

```python
# 需要确认是否已实现 /api/action

@router.post("/action")
async def handle_action(request: ActionRequest):
    """
    处理 SDUI 按钮 Action
    
    核心原则：不将按钮点击转换为聊天消息，直接处理 Action
    """
    graph = get_compiled_graph()
    
    config = {
        "configurable": {
            "thread_id": request.thread_id,
        }
    }
    
    # 根据 action 类型构建状态更新
    updates = _build_state_updates(request.action, request.payload)
    
    # 更新状态
    await graph.aupdate_state(config, updates)
    
    # 恢复 Graph 执行
    async for event in graph.astream(None, config):
        pass
    
    # 获取新状态
    new_state = await graph.aget_state(config)
    
    return ActionResponse(
        success=True,
        message=updates.get("ui_feedback", "操作已执行"),
        ui_interaction=new_state.values.get("ui_interaction"),
        state_updates=updates,
    )
```

---

## 5. 数据模型

### 5.1 核心实体 (V1 通用节点系统)

```sql
-- =====================================================
-- AI Video Engine - Database Schema V3 (融合版)
-- =====================================================
-- 设计原则: 保留 V1 的通用节点系统，支持无限画布

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ===== 项目与资产 (Project & Assets) =====
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    cover_image TEXT,
    meta JSONB DEFAULT '{}'::jsonb,  -- { genre, tone, target_word_count, ... }
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 资产表 (角色/场景/道具)
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('character', 'location', 'prop')),
    visual_tokens JSONB DEFAULT '{}'::jsonb,
    avatar_url TEXT,
    reference_urls TEXT[] DEFAULT '{}',
    prompts JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== 通用内容节点 (Generic Node System) =====
-- 这是 V1 的核心设计，用于支持无限画布
CREATE TABLE IF NOT EXISTS story_nodes (
    node_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES story_nodes(node_id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,  -- episode, scene, shot, outline, etc.
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 节点布局 (支持多画布 Tab)
CREATE TABLE IF NOT EXISTS node_layouts (
    node_id UUID NOT NULL REFERENCES story_nodes(node_id) ON DELETE CASCADE,
    canvas_tab VARCHAR(50) NOT NULL,  -- 'novel', 'script', 'storyboard'
    position_x FLOAT NOT NULL DEFAULT 0,
    position_y FLOAT NOT NULL DEFAULT 0,
    PRIMARY KEY (node_id, canvas_tab)
);

-- ===== 全局模型配置 (Model Governance) =====
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(50) NOT NULL,
    protocol VARCHAR(20) DEFAULT 'openai' CHECK (protocol IN ('openai', 'anthropic', 'gemini', 'azure')),
    base_url VARCHAR(255),
    api_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    available_models JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 任务模型映射表
CREATE TABLE IF NOT EXISTS model_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    provider_id UUID NOT NULL REFERENCES llm_providers(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    parameters JSONB DEFAULT '{"temperature": 0.7, "max_tokens": 4096}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== 数据增强层 (Data Enhancement) =====
-- 节点历史版本 (Time Travel)
CREATE TABLE IF NOT EXISTS node_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID NOT NULL REFERENCES story_nodes(node_id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    user_id UUID,
    reason VARCHAR(50),  -- 'AI_Regenerate', 'User_Edit', 'Rollback'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 语义记忆向量 (RAG)
CREATE TABLE IF NOT EXISTS project_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    node_id UUID REFERENCES story_nodes(node_id) ON DELETE SET NULL,
    embedding VECTOR(1536),
    text_chunk TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== 异步任务队列 (Job Queue) =====
CREATE TABLE IF NOT EXISTS job_queue (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- 'video_generation', 'novel_writing', etc.
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'DEAD_LETTER')),
    priority INT DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
    progress_percent INT DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    current_step VARCHAR(255),
    input_payload JSONB DEFAULT '{}'::jsonb,
    output_result JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    last_heartbeat TIMESTAMPTZ
);

-- ===== 熔断器状态 (Circuit Breaker) =====
CREATE TABLE IF NOT EXISTS circuit_breaker_states (
    provider_id UUID PRIMARY KEY REFERENCES llm_providers(id) ON DELETE CASCADE,
    state VARCHAR(20) NOT NULL DEFAULT 'CLOSED' CHECK (state IN ('CLOSED', 'OPEN', 'HALF_OPEN')),
    failure_count INT DEFAULT 0,
    last_failure_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== 语义缓存 (Semantic Cache) =====
CREATE TABLE IF NOT EXISTS semantic_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_hash VARCHAR(64) NOT NULL,
    prompt_embedding VECTOR(1536),
    response TEXT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    hit_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_hit_at TIMESTAMPTZ
);
```

### 5.2 JSONB 内容结构

#### story_nodes.content 字段结构

```typescript
// Episode 节点
{
  "type": "episode",
  "content": {
    "episode_number": 1,
    "title": "第一集标题",
    "summary": "剧情摘要",
    "word_count": 500,
    "novel_text": "小说正文...",
    "status": "draft" | "completed"
  }
}

// Scene 节点 (剧本场景)
{
  "type": "scene",
  "content": {
    "scene_number": "S01",
    "location": "[室内] 客厅 - 夜晚",
    "visual_description": "环境氛围描述",
    "elements": [
      {"type": "D", "character": "林恩", "text": "对白内容"},
      {"type": "A", "text": "动作描述"},
      {"type": "V", "text": "旁白内容"},
      {"type": "S", "text": "音效描述"}
    ]
  }
}

// Shot 节点 (分镜) - v6.0 节点形式
{
  "type": "shot",
  "content": {
    "shot_number": "S01-01",
    "shot_type": "特写",
    "shot_type_en": "Close-up",
    "camera_movement": "推",
    "camera_movement_en": "Push In",
    "subject": "林恩的脸",
    "action": "表情从平静转为愤怒",
    "visual_description": "光影、色彩、构图描述",
    "dialogue": "林恩: 来...",
    "sound": "风啸声",
    "nano_banana_prompt": "English prompt for image generation",
    "image_url": "生成的图片 URL",
    "thumbnail_url": "缩略图 URL (80x45)",
    "video_url": "生成的视频 URL",
    "status": "completed",
    "position": {"x": 100, "y": 200},
    "generation_params": {
      "resolution": "2K",
      "aspect_ratio": "16:9",
      "style": "cinematic_realistic"
    }
  }
}

// Canvas 节点 (画布状态 - v6.0 新增)
{
  "type": "canvas",
  "content": {
    "episode_id": "episode_uuid",
    "canvas_version": "v6.0",
    "viewport": {
      "x": 0,
      "y": 0,
      "zoom": 1.0
    },
    "nodes": [
      {
        "id": "node_001",
        "type": "scene_master",
        "scene_id": "scene_001",
        "position": {"x": 100, "y": 100},
        "grid_data": ["thumb_1", "thumb_2", ...]  // 25格缩略图
      },
      {
        "id": "node_002",
        "type": "shot",
        "shot_id": "shot_001",
        "position": {"x": 400, "y": 100}
      }
    ],
    "connections": [
      {
        "id": "conn_001",
        "source": "node_001",
        "target": "node_002",
        "type": "sequence"
      }
    ]
  }
}

// Character 节点 (角色)
{
  "type": "character",
  "content": {
    "name": "林恩",
    "appearance": "外貌描述",
    "personality_flaw": "性格缺陷",
    "core_desire": "核心欲望",
    "speech_pattern": "说话方式",
    "b_story": "B故事暗线 (配角)"
  }
}

// Outline 节点 (大纲)
{
  "type": "outline",
  "content": {
    "title": "剧名",
    "logline": "一句话梗概",
    "protagonist": {...},
    "deuteragonist": {...},
    "core_appeal": ["爽点1", "爽点2"]
  }
}
```

---

## 6. 模型路由层

### 6.1 4-Role 分类策略 (融合 V2 简化)

```python
# backend/schemas/model_config.py

from enum import Enum

class TaskCategory(str, Enum):
    """任务分类 - 融合 V2 的 4-Role 设计"""
    CREATIVE = "creative"      # 🧠 创意规划
    CONTENT = "content"        # ✍️ 内容生成
    QUALITY = "quality"        # 🔍 质检优化
    VIDEO = "video"            # 🎬 视频制作

class TaskType(str, Enum):
    """任务类型 - 保留 V1 的细粒度 (用于内部路由)"""
    # 创意规划
    MARKET_ANALYST = "market_analyst"
    STORY_PLANNER = "story_planner"
    SKELETON_BUILDER = "skeleton_builder"
    
    # 内容生成
    NOVEL_WRITER = "novel_writer"
    SCRIPT_ADAPTER = "script_adapter"
    STORYBOARD_DIRECTOR = "storyboard_director"
    
    # 质检优化
    EDITOR = "editor"
    REFINER = "refiner"
    ANALYSIS_LAB = "analysis_lab"
    
    # 视频制作
    ASSET_INSPECTOR = "asset_inspector"
    VIDEO_GENERATION = "video_generation"
    
    # 路由
    ROUTER = "router"


# 任务类别到 TaskType 的映射
TaskCategoryMapping = {
    TaskCategory.CREATIVE: [
        TaskType.MARKET_ANALYST,
        TaskType.STORY_PLANNER,
        TaskType.SKELETON_BUILDER,
    ],
    TaskCategory.CONTENT: [
        TaskType.NOVEL_WRITER,
        TaskType.SCRIPT_ADAPTER,
        TaskType.STORYBOARD_DIRECTOR,
    ],
    TaskCategory.QUALITY: [
        TaskType.EDITOR,
        TaskType.REFINER,
        TaskType.ANALYSIS_LAB,
    ],
    TaskCategory.VIDEO: [
        TaskType.ASSET_INSPECTOR,
        TaskType.VIDEO_GENERATION,
    ],
}
```

### 6.2 ModelRouter 实现

```python
# backend/services/model_router.py

class ModelRouter:
    """模型路由器 - 支持 TaskCategory 和 TaskType 双模式"""
    
    def __init__(self, db_service):
        self._db = db_service
        self._cache: dict[str, BaseChatModel] = {}
    
    async def get_model(
        self, 
        user_id: str, 
        task_type: TaskType, 
        project_id: str | None = None
    ) -> BaseChatModel:
        """获取任务对应的 LLM 实例"""
        
        # 1. 尝试查找 TaskType 级别的映射
        mapping = await self._db.get_model_mapping(
            user_id, task_type.value, project_id
        )
        
        # 2. 如果没有，回退到 TaskCategory 级别的映射
        if not mapping:
            category = self._get_category_for_task(task_type)
            category_task = self._get_representative_task(category)
            mapping = await self._db.get_model_mapping(
                user_id, category_task.value, project_id
            )
        
        # 3. 如果还没有，使用默认模型
        if not mapping:
            return self._get_default_model(task_type)
        
        # 创建模型实例
        return self._create_model_from_mapping(mapping)
    
    def _get_category_for_task(self, task_type: TaskType) -> TaskCategory:
        """获取 TaskType 所属的分类"""
        for category, tasks in TaskCategoryMapping.items():
            if task_type in tasks:
                return category
        return TaskCategory.CONTENT  # 默认
    
    def _get_representative_task(self, category: TaskCategory) -> TaskType:
        """获取分类的代表性 TaskType"""
        representatives = {
            TaskCategory.CREATIVE: TaskType.MARKET_ANALYST,
            TaskCategory.CONTENT: TaskType.NOVEL_WRITER,
            TaskCategory.QUALITY: TaskType.EDITOR,
            TaskCategory.VIDEO: TaskType.ASSET_INSPECTOR,
        }
        return representatives.get(category, TaskType.NOVEL_WRITER)
```

---

## 7. SDUI 协议 (Server-Driven UI)

### 7.1 交互块类型定义

```python
# backend/schemas/common.py

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class UIInteractionBlockType(str, Enum):
    """UI 交互块类型 - 融合 V1 + V2 定义"""
    ACTION_GROUP = "action_group"       # 操作按钮组
    SELECTOR = "selector"               # 选择器
    CONFIRMATION = "confirmation"       # 确认框
    FORM = "form"                       # 表单
    CARD_GRID = "card_grid"            # 卡片网格
    PROGRESS = "progress"               # 进度指示
    TEXT_DISPLAY = "text_display"       # 文本展示


class ActionButton(BaseModel):
    """操作按钮 - V1 Action Block 结构"""
    label: str                          # 按钮文字
    action: str                         # Action 类型标识
    payload: Dict[str, Any] = {}        # Action 参数
    style: str = "primary"              # primary/secondary/danger/ghost
    icon: Optional[str] = None          # 图标名称 (Lucide icon)
    disabled: bool = False              # 是否禁用
    tooltip: Optional[str] = None       # 提示文字
    shortcut: Optional[str] = None      # 快捷键 (如 "Ctrl+Enter")


class UIInteractionBlock(BaseModel):
    """UI 交互块 - Agent 返回的 UI 指令"""
    block_type: UIInteractionBlockType
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Action Group
    buttons: List[ActionButton] = []
    
    # Selector
    options: List[Dict[str, Any]] = []  # [{"label": "...", "value": "..."}]
    multi_select: bool = False
    default_value: Any = None
    
    # Form
    fields: List[Dict[str, Any]] = []   # [{"name": "...", "type": "...", "required": true}]
    
    # Card Grid
    cards: List[Dict[str, Any]] = []    # [{"id": "...", "title": "...", "content": "..."}]
    
    # Progress
    percent: int = 0
    status: str = "active"              # active/success/error
    steps: List[str] = []               # ["步骤1", "步骤2", ...]
    current_step: int = 0
    
    # Display
    content: Optional[str] = None       # Markdown 内容
    
    # 通用属性
    dismissible: bool = True            # 是否可关闭
    timeout_seconds: Optional[int] = None  # 自动关闭时间
    priority: str = "normal"            # high/normal/low
```

### 7.2 SDUI 使用示例

```python
# 题材选择 (Level 1)
ui_interaction = UIInteractionBlock(
    block_type=UIInteractionBlockType.ACTION_GROUP,
    title="选择创作题材",
    description="选择一个热门题材，或者直接描述你的想法",
    buttons=[
        ActionButton(
            label="🔥 逆袭复仇",
            action="select_genre",
            payload={"genre": "逆袭复仇", "tone": ["爽感", "暗黑"]},
            style="primary"
        ),
        ActionButton(
            label="💕 霸总甜宠",
            action="select_genre",
            payload={"genre": "霸总甜宠", "tone": ["甜蜜", "虐恋"]},
            style="secondary"
        ),
        ActionButton(
            label="✍️ 自由创作",
            action="start_custom",
            payload={},
            style="ghost"
        ),
    ],
    dismissible=False  # 必须选择，不能关闭
)

# 方案确认 (Level 2)
ui_interaction = UIInteractionBlock(
    block_type=UIInteractionBlockType.CARD_GRID,
    title="选择故事方案",
    description="AI 为您生成了 3 个方案，请选择最满意的一个",
    cards=[
        {
            "id": "plan_001",
            "title": "《野犬加冕》",
            "content": "Logline: ...",
            "tags": ["复仇", "逆袭"],
            "highlight": "黄金前三集"
        },
        # ... 更多方案
    ],
    buttons=[
        ActionButton(label="选择方案 1", action="select_plan", payload={"plan_id": "plan_001"}),
        ActionButton(label="融合方案", action="fuse_plans", payload={}, style="secondary"),
    ]
)

# 进度指示 (Module A 生成中)
ui_interaction = UIInteractionBlock(
    block_type=UIInteractionBlockType.PROGRESS,
    title="正在生成第 3 集",
    percent=45,
    status="active",
    steps=["构思情节", "撰写正文", "质量审阅", "内容精修"],
    current_step=1,
    buttons=[
        ActionButton(label="取消生成", action="cancel_generation", style="danger"),
    ]
)
```

---

## 8. 部署架构

### 8.1 ComfyUI 模式 (保留 V1 实现)

```
┌─────────────────────────────────────────────────────────┐
│                    Deployment View                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Browser]                                              │
│      │                                                  │
│      │ (HTTPS)                                          │
│      ▼                                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │           Cloudflare (CDN + WAF)                │   │
│  └─────────────────────────────────────────────────┘   │
│      │                                                  │
│      ▼                                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Railway / Render                   │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │           FastAPI Server                  │  │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌───────────┐  │  │   │
│  │  │  │ REST API│  │Graph SSE│  │Static Files│  │  │   │
│  │  │  └─────────┘  └─────────┘  └───────────┘  │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
│      │                                                  │
│      │                                                  │
│      ▼                                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │   │
│  │  │ Supabase │  │ Upstash  │  │   Supabase   │   │   │
│  │  │PostgreSQL│  │  Redis   │  │   Storage    │   │   │
│  │  └──────────┘  └──────────┘  └──────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 8.2 为什么保留 ComfyUI 模式

| 优势 | 说明 |
|------|------|
| **零 CORS** | 浏览器视作同源，无需跨域配置 |
| **单进程** | 部署只需启动一个 Python 进程 |
| **易打包** | 可直接打包为 .exe 或 Docker Image |
| **简化运维** | 前端构建后由 FastAPI 统一伺服 |

### 8.3 本地开发 vs 生产部署

```python
# Development
# Terminal A: npm run dev (Port 5173)
# Terminal B: uvicorn main:app --reload (Port 8000)
# Frontend proxy /api to 8000

# Production
# 1. cd frontend && npm run build -> generates ./dist
# 2. FastAPI serves ./dist at /
# 3. SPA fallback: all non-API routes return index.html

# backend/main.py
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")))
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
```

---

## 9. 运行时治理

### 9.1 熔断器 (Circuit Breaker)

#### 9.1.1 设计原理

熔断器模式防止级联故障，当某个 LLM Provider 持续失败时，自动切断请求，避免拖垮整个系统。

**状态流转图**：

```
                    ┌─────────────┐
         失败 < 阈值 │             │ 失败 >= 阈值
         ┌──────────│   CLOSED    │──────────┐
         │          │   (关闭)    │          │
         │          └─────────────┘          │
         │                                   ▼
         │                          ┌─────────────┐
         │                          │             │
         │                          │    OPEN     │
         │                          │   (打开)    │
         │                          └──────┬──────┘
         │                                 │
         │                          超时时间到
         │                                 ▼
         │                          ┌─────────────┐
         │          成功 │           │             │ 失败
         └──────────────│  HALF_OPEN  │──────────►
                        │  (半开)     │
                        └─────────────┘
```

#### 9.1.2 完整实现

```python
# backend/services/circuit_breaker.py

import time
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

class CircuitState(str, Enum):
    CLOSED = "CLOSED"       # 正常状态
    OPEN = "OPEN"          # 熔断状态
    HALF_OPEN = "HALF_OPEN"  # 半开状态(试探)

class CircuitBreaker:
    """
    熔断器 - 防止 LLM API 崩坏
    
    配置参数:
    - failure_threshold: 触发熔断的失败次数阈值
    - recovery_timeout: 熔断后等待恢复的时间(秒)
    - half_open_max_calls: 半开状态允许的最大试探请求数
    - success_threshold: 半开状态恢复所需的连续成功次数
    """
    
    def __init__(
        self, 
        provider_id: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 300,  # 5分钟
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
    ):
        self.provider_id = provider_id
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        
        # 状态
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        
        # 时间戳
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
    
    async def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # 检查是否到达恢复时间
            if self._should_attempt_reset():
                logger.info(
                    "Circuit breaker entering HALF_OPEN state",
                    provider_id=self.provider_id
                )
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                self.success_count = 0
                return True
            
            logger.warning(
                "Circuit breaker is OPEN, request rejected",
                provider_id=self.provider_id,
                opened_at=self.opened_at
            )
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # 限制半开状态的请求数量
            if self.half_open_calls >= self.half_open_max_calls:
                logger.warning(
                    "Circuit breaker HALF_OPEN limit reached",
                    provider_id=self.provider_id
                )
                return False
            
            self.half_open_calls += 1
            return True
        
        return True
    
    async def record_success(self):
        """记录成功请求"""
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # 连续成功达到阈值，关闭熔断器
            if self.success_count >= self.success_threshold:
                logger.info(
                    "Circuit breaker closing after successful recovery",
                    provider_id=self.provider_id
                )
                await self._close_circuit()
        
        elif self.state == CircuitState.CLOSED:
            # 重置失败计数
            self.failure_count = 0
    
    async def record_failure(self, error: Exception):
        """记录失败请求"""
        
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.CLOSED:
            # 检查是否达到熔断阈值
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    "Circuit breaker opening due to failures",
                    provider_id=self.provider_id,
                    failure_count=self.failure_count,
                    error=str(error)
                )
                await self._open_circuit()
        
        elif self.state == CircuitState.HALF_OPEN:
            # 半开状态失败，立即重新熔断
            logger.error(
                "Circuit breaker re-opening after half-open failure",
                provider_id=self.provider_id
            )
            await self._open_circuit()
    
    async def _open_circuit(self):
        """打开熔断器"""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        
        # 持久化到数据库
        await db.execute("""
            INSERT INTO circuit_breaker_states 
            (provider_id, state, failure_count, opened_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (provider_id) 
            DO UPDATE SET 
                state = EXCLUDED.state,
                failure_count = EXCLUDED.failure_count,
                opened_at = EXCLUDED.opened_at,
                updated_at = NOW()
        """, (self.provider_id, self.state.value, self.failure_count, self.opened_at))
    
    async def _close_circuit(self):
        """关闭熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.opened_at = None
        
        await db.execute("""
            UPDATE circuit_breaker_states 
            SET state = %s, 
                failure_count = 0,
                updated_at = NOW()
            WHERE provider_id = %s
        """, (self.state.value, self.provider_id))
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试恢复"""
        if not self.opened_at:
            return True
        
        elapsed = (datetime.now() - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout


# 在 ModelRouter 中使用
class ModelRouter:
    def __init__(self, db_service):
        self._db = db_service
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
    
    async def get_model(self, user_id: str, task_type: TaskType):
        mapping = await self._db.get_model_mapping(user_id, task_type.value)
        provider_id = mapping["provider_id"]
        
        # 获取或创建熔断器
        if provider_id not in self._circuit_breakers:
            self._circuit_breakers[provider_id] = CircuitBreaker(provider_id)
        
        cb = self._circuit_breakers[provider_id]
        
        # 检查熔断器状态
        if not await cb.can_execute():
            raise CircuitBreakerOpenError(
                f"Provider {provider_id} is currently unavailable (circuit open)"
            )
        
        try:
            # 调用模型
            model = self._create_model(mapping)
            response = await model.ainvoke(...)
            
            # 记录成功
            await cb.record_success()
            
            return response
            
        except Exception as e:
            # 记录失败
            await cb.record_failure(e)
            raise
```

#### 9.1.3 配置建议

```python
# 不同 Provider 的熔断器配置
CIRCUIT_BREAKER_CONFIGS = {
    "openai": {
        "failure_threshold": 5,
        "recovery_timeout": 60,  # OpenAI 恢复快
    },
    "anthropic": {
        "failure_threshold": 3,
        "recovery_timeout": 120,
    },
    "gemini": {
        "failure_threshold": 5,
        "recovery_timeout": 300,
    },
    # 自建/不稳定的服务商配置更严格
    "self_hosted": {
        "failure_threshold": 3,
        "recovery_timeout": 600,
    },
}
```

#### 9.1.4 监控指标

```python
# 熔断器状态监控
async def get_circuit_breaker_metrics():
    """获取熔断器监控指标"""
    
    metrics = await db.fetch_all("""
        SELECT 
            provider_id,
            state,
            failure_count,
            opened_at,
            updated_at
        FROM circuit_breaker_states
        WHERE state != 'CLOSED'
    """)
    
    return {
        "open_circuits": len([m for m in metrics if m["state"] == "OPEN"]),
        "half_open_circuits": len([m for m in metrics if m["state"] == "HALF_OPEN"]),
        "details": metrics
    }
```

### 9.2 看门狗 (Watchdog)

#### 9.2.1 设计原理

看门狗机制用于检测和处理异常状态的任务，防止"僵尸任务"占用资源 indefinitely。

**检测策略**：
- **超时检测**: 运行时间超过阈值的任务
- **心跳检测**: 长时间未上报心跳的任务
- **资源检测**: CPU/内存异常的任务 (可选)

#### 9.2.2 完整实现

```python
# backend/tasks/watchdog.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import structlog

logger = structlog.get_logger(__name__)

class WatchdogConfig:
    """看门狗配置"""
    # 任务类型 -> 超时时间 (分钟)
    TIMEOUT_CONFIGS = {
        "novel_writing": 30,        # 写小说最长30分钟
        "script_parsing": 10,       # 剧本解析10分钟
        "storyboard_generation": 60, # 分镜生成60分钟
        "video_generation": 300,    # 视频生成5小时
        "image_generation": 15,     # 图片生成15分钟
        "default": 30,              # 默认30分钟
    }
    
    # 心跳超时时间 (分钟)
    HEARTBEAT_TIMEOUT = 5
    
    # 看门狗扫描间隔 (秒)
    SCAN_INTERVAL = 60


class Watchdog:
    """看门狗服务"""
    
    def __init__(self):
        self.config = WatchdogConfig()
        self.running = False
    
    async def start(self):
        """启动看门狗"""
        self.running = True
        logger.info("Watchdog started")
        
        while self.running:
            try:
                await self._scan_jobs()
                await asyncio.sleep(self.config.SCAN_INTERVAL)
            except Exception as e:
                logger.error("Watchdog scan failed", error=str(e))
                await asyncio.sleep(5)  # 出错后快速重试
    
    async def stop(self):
        """停止看门狗"""
        self.running = False
        logger.info("Watchdog stopped")
    
    async def _scan_jobs(self):
        """扫描任务队列"""
        
        # 1. 检测超时任务
        timeout_jobs = await self._detect_timeout_jobs()
        
        # 2. 检测心跳超时任务
        heartbeat_jobs = await self._detect_heartbeat_timeout_jobs()
        
        # 3. 处理异常任务
        for job in timeout_jobs + heartbeat_jobs:
            await self._handle_zombie_job(job)
        
        # 4. 记录统计
        if timeout_jobs or heartbeat_jobs:
            logger.warning(
                "Watchdog scan completed",
                timeout_count=len(timeout_jobs),
                heartbeat_timeout_count=len(heartbeat_jobs)
            )
    
    async def _detect_timeout_jobs(self) -> List[Dict]:
        """检测运行时间超长的任务"""
        
        jobs = await db.fetch_all("""
            SELECT 
                job_id,
                type,
                started_at,
                current_step,
                EXTRACT(EPOCH FROM (NOW() - started_at)) / 60 as runtime_minutes
            FROM job_queue
            WHERE status = 'RUNNING'
              AND started_at IS NOT NULL
        """)
        
        zombie_jobs = []
        for job in jobs:
            timeout_threshold = self.config.TIMEOUT_CONFIGS.get(
                job["type"], 
                self.config.TIMEOUT_CONFIGS["default"]
            )
            
            if job["runtime_minutes"] > timeout_threshold:
                zombie_jobs.append(job)
        
        return zombie_jobs
    
    async def _detect_heartbeat_timeout_jobs(self) -> List[Dict]:
        """检测心跳超时的任务"""
        
        jobs = await db.fetch_all("""
            SELECT 
                job_id,
                type,
                started_at,
                last_heartbeat,
                current_step
            FROM job_queue
            WHERE status = 'RUNNING'
              AND last_heartbeat IS NOT NULL
              AND last_heartbeat < NOW() - INTERVAL '%s minutes'
        """ % (self.config.HEARTBEAT_TIMEOUT,))
        
        return jobs
    
    async def _handle_zombie_job(self, job: Dict):
        """处理僵尸任务"""
        
        job_id = job["job_id"]
        job_type = job["type"]
        
        logger.error(
            "Zombie job detected",
            job_id=job_id,
            job_type=job_type,
            runtime=job.get("runtime_minutes"),
            current_step=job.get("current_step")
        )
        
        # 1. 尝试保存 Checkpoint (如果可能)
        try:
            await self._save_emergency_checkpoint(job_id)
        except Exception as e:
            logger.error("Failed to save emergency checkpoint", error=str(e))
        
        # 2. 强制终止任务进程/线程
        await self._kill_job_process(job_id)
        
        # 3. 更新数据库状态
        await db.execute("""
            UPDATE job_queue
            SET 
                status = 'DEAD_LETTER',
                error_message = 'Killed by watchdog: timeout or heartbeat lost',
                ended_at = NOW()
            WHERE job_id = %s
        """, (job_id,))
        
        # 4. 发送通知
        await self._notify_job_failure(job)
    
    async def _save_emergency_checkpoint(self, job_id: str):
        """紧急保存 Checkpoint"""
        # 通过 Job 关联的 thread_id 找到对应的状态
        job = await db.fetch_one("""
            SELECT thread_id FROM job_queue WHERE job_id = %s
        """, (job_id,))
        
        if job and job["thread_id"]:
            # 触发状态保存
            graph = get_compiled_graph()
            config = {"configurable": {"thread_id": job["thread_id"]}}
            
            # 获取当前状态并保存
            state = await graph.aget_state(config)
            if state.values:
                await db.execute("""
                    INSERT INTO emergency_checkpoints 
                    (job_id, thread_id, state, saved_at)
                    VALUES (%s, %s, %s, NOW())
                """, (job_id, job["thread_id"], json.dumps(state.values)))
    
    async def _kill_job_process(self, job_id: str):
        """终止任务进程"""
        # 如果是 Celery 任务，发送撤销信号
        from celery.task.control import revoke
        revoke(job_id, terminate=True, signal='SIGTERM')
    
    async def _notify_job_failure(self, job: Dict):
        """通知用户任务失败"""
        # 通过 WebSocket 推送通知
        await websocket_manager.broadcast(
            channel=f"user:{job['user_id']}",
            message={
                "type": "job.failed",
                "job_id": job["job_id"],
                "reason": "watchdog_timeout",
                "recoverable": True,  # 可以重试
            }
        )


# Celery 定时任务配置
@celery.on_after_configure.connect
def setup_watchdog_tasks(sender, **kwargs):
    """配置看门狗定时任务"""
    
    # 每分钟执行一次看门狗扫描
    sender.add_periodic_task(
        60.0,  # 每60秒
        watchdog_scan.s(),
        name='watchdog-scan',
    )

@celery.task
def watchdog_scan():
    """看门狗扫描任务入口"""
    watchdog = Watchdog()
    asyncio.run(watchdog._scan_jobs())
```

#### 9.2.3 任务心跳机制

```python
# 在长时间运行的任务中上报心跳

@celery.task(bind=True)
def long_running_task(self, project_id: str, ...):
    """示例长时间任务"""
    
    async def update_heartbeat():
        """定期更新心跳"""
        while True:
            await db.execute("""
                UPDATE job_queue
                SET last_heartbeat = NOW(),
                    current_step = %s,
                    progress_percent = %s
                WHERE job_id = %s
            """, (current_step, progress, self.request.id))
            
            await asyncio.sleep(30)  # 每30秒上报一次
    
    # 启动心跳任务
    heartbeat_task = asyncio.create_task(update_heartbeat())
    
    try:
        # 执行实际工作
        await do_work()
        
    finally:
        # 确保心跳任务停止
        heartbeat_task.cancel()
```

#### 9.2.4 紧急 Checkpoint 表

```sql
-- 紧急 Checkpoint 表 (用于僵尸任务恢复)
CREATE TABLE IF NOT EXISTS emergency_checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES job_queue(job_id),
    thread_id VARCHAR(255),
    state JSONB NOT NULL,  -- 保存的 AgentState
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    recovered BOOLEAN DEFAULT FALSE,
    recovered_at TIMESTAMPTZ
);

CREATE INDEX idx_emergency_checkpoints_job_id ON emergency_checkpoints(job_id);
```

### 9.3 优雅停机 (Graceful Shutdown)

#### 9.3.1 设计原理

优雅停机确保在部署更新或服务器重启时，正在运行的任务不会丢失数据或状态。

**信号处理**：
- **SIGTERM**: 温和终止信号 (Docker/K8s 默认)
- **SIGINT**: 中断信号 (Ctrl+C)
- **超时**: 如果在超时时间内无法完成，强制退出

#### 9.3.2 完整实现

```python
# backend/lifespan.py

import signal
import asyncio
from contextlib import asynccontextmanager
from typing import Set
import structlog

logger = structlog.get_logger(__name__)

# 全局状态
running_jobs: Set[str] = set()
shutdown_event = asyncio.Event()

class GracefulShutdown:
    """优雅停机管理器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.shutdown_in_progress = False
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        # Docker/K8s 发送 SIGTERM
        signal.signal(signal.SIGTERM, self._handle_signal)
        # Ctrl+C 发送 SIGINT
        signal.signal(signal.SIGINT, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """处理终止信号"""
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        
        logger.info(
            f"Received {signal_name}, initiating graceful shutdown...",
            signal=signal_name
        )
        
        if not self.shutdown_in_progress:
            self.shutdown_in_progress = True
            # 触发异步关闭流程
            asyncio.create_task(self._shutdown())
    
    async def _shutdown(self):
        """执行关闭流程"""
        
        # 1. 停止接受新请求
        logger.info("Stopping request acceptance...")
        shutdown_event.set()
        
        # 2. 通知所有运行中的任务准备关闭
        logger.info(f"Notifying {len(running_jobs)} running jobs...")
        await self._notify_jobs_shutdown()
        
        # 3. 等待任务完成或超时
        logger.info(f"Waiting up to {self.timeout}s for jobs to complete...")
        await self._wait_for_jobs()
        
        # 4. 保存所有未完成的 Checkpoint
        logger.info("Saving pending checkpoints...")
        await self._save_all_checkpoints()
        
        # 5. 关闭资源连接
        logger.info("Closing connections...")
        await self._close_connections()
        
        # 6. 强制退出 (如果还有任务没完成)
        remaining = len(running_jobs)
        if remaining > 0:
            logger.warning(
                f"Force exiting with {remaining} jobs still running",
                jobs=list(running_jobs)
            )
        
        logger.info("Graceful shutdown completed")
    
    async def _notify_jobs_shutdown(self):
        """通知所有任务准备关闭"""
        # 通过消息队列或共享状态通知
        for job_id in running_jobs:
            await db.execute("""
                UPDATE job_queue
                SET status = 'CANCELLING',
                    cancellation_requested_at = NOW()
                WHERE job_id = %s
            """, (job_id,))
    
    async def _wait_for_jobs(self):
        """等待任务完成"""
        start_time = asyncio.get_event_loop().time()
        
        while running_jobs:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if elapsed > self.timeout:
                logger.warning(f"Shutdown timeout reached, {len(running_jobs)} jobs incomplete")
                break
            
            # 每秒检查一次
            await asyncio.sleep(1)
            
            # 记录剩余任务
            if len(running_jobs) > 0 and int(elapsed) % 5 == 0:
                logger.info(f"Waiting for {len(running_jobs)} jobs...", 
                          jobs=list(running_jobs))
    
    async def _save_all_checkpoints(self):
        """保存所有未完成的 Checkpoint"""
        
        for job_id in list(running_jobs):
            try:
                # 获取 job 对应的 thread_id
                job = await db.fetch_one("""
                    SELECT thread_id FROM job_queue WHERE job_id = %s
                """, (job_id,))
                
                if job and job["thread_id"]:
                    # 获取并保存当前状态
                    graph = get_compiled_graph()
                    config = {"configurable": {"thread_id": job["thread_id"]}}
                    state = await graph.aget_state(config)
                    
                    if state.values:
                        await db.execute("""
                            INSERT INTO emergency_checkpoints 
                            (job_id, thread_id, state, saved_at)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (job_id) DO UPDATE SET
                                state = EXCLUDED.state,
                                saved_at = NOW()
                        """, (job_id, job["thread_id"], json.dumps(state.values)))
                        
                        logger.info(f"Emergency checkpoint saved for job {job_id}")
                        
            except Exception as e:
                logger.error(f"Failed to save checkpoint for job {job_id}", error=str(e))
    
    async def _close_connections(self):
        """关闭所有连接"""
        # 关闭数据库连接池
        await db.close()
        
        # 关闭 Redis 连接
        await redis.close()
        
        # 关闭 WebSocket 连接
        await websocket_manager.close_all()


# 在 FastAPI lifespan 中使用
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    
    # ===== 启动阶段 =====
    logger.info("Starting up...")
    
    # 初始化连接
    await db.connect()
    await redis.connect()
    
    # 加载模型
    await load_model_router()
    
    # 编译 LangGraph
    await compile_graph()
    
    # 设置优雅停机
    shutdown_manager = GracefulShutdown(timeout=30)
    shutdown_manager.setup_signal_handlers()
    
    # 启动看门狗
    watchdog = Watchdog()
    watchdog_task = asyncio.create_task(watchdog.start())
    
    logger.info("Application startup completed")
    
    yield
    
    # ===== 关闭阶段 =====
    # 如果还没有触发优雅停机，在这里触发
    if not shutdown_manager.shutdown_in_progress:
        await shutdown_manager._shutdown()
    
    # 停止看门狗
    await watchdog.stop()
    watchdog_task.cancel()
    
    logger.info("Application shutdown completed")


# 在任务中注册/注销
@celery.task(bind=True)
def tracked_task(self, ...):
    """被跟踪的任务"""
    job_id = self.request.id
    
    # 注册到运行中任务集合
    running_jobs.add(job_id)
    
    try:
        # 检查是否收到关闭信号
        if shutdown_event.is_set():
            raise ShutdownException("Shutdown in progress, task cancelled")
        
        # 执行实际工作
        result = do_work()
        
        return result
        
    finally:
        # 从运行中任务集合移除
        running_jobs.discard(job_id)
```

#### 9.3.3 部署配置

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    stop_signal: SIGTERM      # 发送 SIGTERM 信号
    stop_grace_period: 35s    # 35秒优雅停机时间 (30s timeout + 5s buffer)
    
  # Kubernetes 配置
  # deployment.yaml
  spec:
    template:
      spec:
        terminationGracePeriodSeconds: 35
        containers:
        - name: backend
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]  # 等待负载均衡器移除流量
```

#### 9.3.4 停机检查清单

```python
# 停机状态检查
async def get_shutdown_status():
    """获取停机状态 (用于监控)"""
    return {
        "shutdown_in_progress": shutdown_event.is_set(),
        "running_jobs_count": len(running_jobs),
        "running_jobs": list(running_jobs),
        "emergency_checkpoints_count": await db.fetchval("""
            SELECT COUNT(*) FROM emergency_checkpoints WHERE recovered = FALSE
        """),
    }
```

### 9.3 结构化日志

```python
# backend/config.py

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()  # JSON 格式
        if settings.app_env == "production"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# 使用示例
logger.info(
    "Model routing",
    user_id=user_id,
    task_type=task_type,
    provider=provider_name,
    model=model_name,
    latency_ms=latency,
)
```

---

## 10. 路线图与待实现功能

### 10.1 当前实现状态 (约 85%)

| 模块 | 实现度 | 状态 |
|------|--------|------|
| 数据库 Schema | 100% | 🟢 已完成 |
| LangGraph 主图 | 95% | 🟢 已实现 |
| Module A/B/C 子图 | 90% | 🟢 已编译 |
| 模型路由 | 90% | 🟢 已实现 |
| REST API | 85% | 🟢 已实现 |
| SSE 流式 | 95% | 🟢 已实现 |
| Prompt as Code | 100% | 🟢 已完成 |
| SDUI 协议 | 70% | 🟡 后端模型完成，前端需完善 |
| Action API | 50% | 🟡 需确认是否完整实现 |
| 前端基础组件 | 60% | 🟡 存在，需按 V2 设计重构 |
| 全局 AI 助手 | 50% | 🟡 需完善 UI 和交互流程 |
| 视频生成引擎 | 10% | 🔴 仅预留接口 |
| Analysis Lab 可视化 | 20% | 🔴 后端返回数据，前端缺图表 |
| TTS/BGM/字幕 | 0% | 🔴 未开始 |

### 10.2 优先级路线图

**P0 - 核心功能完善 (1-2 周)**
- [ ] 完善 SDUI 前端渲染器 (ActionBlockRenderer.tsx)
- [ ] 实现 /api/action 端点 (如果未完整实现)
- [ ] 重构全局 AI 助手面板 (320px 可折叠)
- [ ] 按 V2 设计重构工作台 Dashboard

**P1 - 功能扩展 (2-4 周)**
- [ ] 分镜生图模块集成
- [ ] 视频生成引擎 (Sora/Runway API)
- [ ] Analysis Lab 情绪曲线可视化

**P2 - 生产模块 (4-6 周)**
- [ ] TTS 配音集成
- [ ] BGM 生成 (Suno API)
- [ ] 字幕自动生成
- [ ] 视频合成导出

**P3 - 优化与扩展 (6-8 周)**
- [ ] 剪映工程导出
- [ ] 移动端适配
- [ ] 团队协作功能
- [ ] 性能优化

---

## 11. 文档归档

### 11.1 历史版本文档

| 文档 | 版本 | 状态 | 说明 |
|------|------|------|------|
| `系统架构文档.md` | V1 | 📁 已归档 | 原始架构文档 |
| `System-Architecture-V2.md` | V2 | 📁 已归档 | V2 架构设计 (草稿) |
| `System-Architecture-V3.md` | V3 | 📝 当前 | 本文档 (融合版) |

### 11.2 相关文档

| 文档 | 说明 |
|------|------|
| `Product-Spec-V3.md` | 融合产品需求文档 |
| `Frontend-Design-V3.md` | 前端设计规范 (V2 重构版) |
| `Implementation-Roadmap.md` | 实现路线图 |
| `Product-Spec-CHANGELOG.md` | 变更日志 |

---

## 附录 A：环境变量配置

```bash
# Database
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIzaSy...

# Application
APP_ENV=development  # development/production
LOG_LEVEL=info
CORS_ORIGINS=["http://localhost:5173"]

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## 附录 B：目录结构

```
.
├── backend/                      # FastAPI 后端
│   ├── api/                      # API 路由
│   │   ├── graph.py             # Graph API (SSE)
│   │   ├── projects.py          # 项目管理
│   │   ├── nodes.py             # 节点管理
│   │   ├── jobs.py              # 异步任务
│   │   ├── models.py            # 模型配置
│   │   ├── tools.py             # 工具箱
│   │   └── health.py            # 健康检查
│   ├── graph/                    # LangGraph 定义
│   │   ├── main_graph.py        # 主图
│   │   ├── nodes/               # 节点实现
│   │   │   ├── master_router.py
│   │   │   ├── market_analyst.py
│   │   │   ├── story_planner.py
│   │   │   └── ...
│   │   └── subgraphs/           # 子图定义
│   │       ├── module_a.py      # Writer-Editor-Refiner
│   │       ├── module_b.py      # Script Adapter
│   │       └── module_c.py      # Storyboard Director
│   ├── schemas/                  # Pydantic 模型
│   │   ├── agent_state.py       # AgentState 定义
│   │   ├── node.py              # Node 模型
│   │   ├── project.py           # Project 模型
│   │   └── common.py            # 通用模型 (SDUI)
│   ├── services/                 # 业务服务
│   │   ├── model_router.py      # 模型路由
│   │   ├── prompt_service.py    # Prompt 管理
│   │   ├── database.py          # 数据库操作
│   │   └── circuit_breaker.py   # 熔断器
│   ├── tasks/                    # Celery 任务
│   │   ├── celery_app.py        # Celery 配置
│   │   └── job_processor.py     # 任务处理器
│   ├── tools/                    # LangChain Tools
│   ├── supabase/                 # 数据库迁移
│   │   └── migrations/
│   │       ├── 001_initial_schema.sql
│   │       └── 002_vector_functions.sql
│   ├── config.py                 # 配置管理
│   ├── main.py                   # 应用入口
│   └── lifespan.py               # 生命周期管理
│
├── frontend/                     # React 前端
│   ├── components/               # 组件
│   │   ├── ui/                  # UI 组件 (Shadcn)
│   │   ├── nodes/               # 节点组件
│   │   ├── canvas/              # 画布组件
│   │   ├── ActionBlockRenderer.tsx  # SDUI 渲染器
│   │   ├── ChatConsole.tsx      # AI 助手面板
│   │   ├── Dashboard.tsx        # 工作台
│   │   └── ...
│   ├── services/                 # API 服务
│   │   └── generated/           # 自动生成的客户端
│   ├── store/                    # Zustand Store
│   │   ├── useAppStore.ts
│   │   ├── useCanvasStore.ts
│   │   └── useChatStore.ts
│   ├── hooks/                    # 自定义 Hooks
│   ├── utils/                    # 工具函数
│   ├── types/                    # TypeScript 类型
│   ├── App.tsx                   # 根组件
│   ├── main.tsx                  # 入口
│   └── vite.config.ts            # Vite 配置
│
├── prompts/                      # Prompt as Code
│   ├── 0_Master_Router.md
│   ├── 1_Market_Analyst.md
│   ├── 2_Story_Planner.md
│   ├── 3_Skeleton_Builder.md
│   ├── 4_Novel_Writer.md
│   ├── 5_Script_Adapter.md
│   ├── 6_Storyboard_Director.md
│   ├── 7_Editor_Reviewer.md
│   ├── 8_Refiner.md
│   ├── 9_Analysis_Lab.md
│   └── 10_Asset_Inspector.md
│
├── servers/                      # MCP Servers (Optional)
│   ├── browser-automation/
│   └── douyin-specialist/
│
├── docs/                         # 文档
│   ├── System-Architecture-V3.md      # 本文档
│   ├── Product-Spec-V3.md             # 产品需求
│   ├── Frontend-Design-V3.md          # 前端设计
│   └── Implementation-Roadmap.md      # 路线图
│
└── docker-compose.yml            # 开发环境配置
```

---

**文档结束**

*本文档是 V1 和 V2 的融合版本，保留了 V1 已实现的优秀架构设计，同时吸收了 V2 的现代交互概念。当前代码实现度约 85%，核心架构已稳定运行。*
