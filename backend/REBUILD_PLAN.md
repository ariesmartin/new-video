# 后端重构计划 (v4.0.0 Agent 架构)

## 架构说明

本文档基于 **LangChain Agent Skill** 架构设计。每个业务节点是一个完整的 **LangChain Agent**（具备自主决策、工具调用、多轮推理能力）。

**核心架构**:
- ✅ 使用 `create_react_agent` / `create_tool_calling_agent` 创建 Agents
- ✅ 目录: `backend/graph/agents/`
- ✅ 每个 Agent 有明确的 System Prompt + Tools + 推理循环
- ✅ Agent 自主决定何时以及如何使用 Tools

---

## 第一步：数据骨架基础 (Step 1: Data Schema) ✅ COMPLETE

**目标**: 定义系统间通信和状态管理的"宪法"级数据结构。

- [x] 创建 `backend/schemas/common.py`: 定义 `UIInteractionBlock`, `ActionButton` (SDUI 协议)。
- [x] 创建 `backend/schemas/agent_state.py`: 定义 `AgentState` (LangGraph 内存), `UserConfig`, `StoryPlan`, `StageType`。

**状态**: ✅ 已完成，无需修改。

---

## 第二步：基础设施层 (Step 2: Infrastructure) ✅ COMPLETE

**目标**: 建立可靠的存储、大模型推理和配置服务。

- [x] 创建 `backend/services/model_router.py`: 统一的大模型调用接口 (OpenAI, Gemini)。
- [x] 创建 `backend/services/prompt_service.py`: 系统 Prompt 模板管理器。
- [x] 创建 `backend/graph/checkpointer.py`: **关键** - 带有全局连接池的健壮 AsyncPostgresSaver。

**状态**: ✅ 已完成，测试通过 (4/4)。

---

## 第三步：Agent 定义层 (Step 3: Agent Definitions) 🔄 IN PROGRESS

**目标**: 使用 LangChain Agent 架构实现各阶段业务逻辑。

**架构原则**:
1. **每个 Agent 使用 `create_react_agent`** - 具备自主决策和 Tool 调用能力
2. **System Prompt 定义职责** - 清晰的 Agent 角色和能力边界
3. **Tools 提供能力** - Agent 通过 Tools 与外部世界交互
4. **自主决策** - Agent 自主决定何时调用 Tool、如何处理结果
5. **返回结构化输出** - 包含 `messages`, `ui_interaction`, 状态更新

**文件清单**:
```
backend/graph/agents/
├── __init__.py                    # Agent 导出
├── master_router.py               # Level 0 - AI 意图识别 Agent
├── market_analyst.py              # Level 1 - 市场分析 Agent
├── story_planner.py               # Level 2 - 故事规划 Agent
├── skeleton_builder.py            # Level 3 - 骨架构建 Agent
├── novel_writer.py                # Module A - 小说创作 Agent
├── content_editor.py              # Module A - 内容审阅 Agent
├── content_refiner.py             # Module A - 内容精修 Agent
├── script_adapter.py              # Module B - 剧本提取 Agent
├── storyboard_director.py         # Module C - 分镜导演 Agent
├── analysis_lab.py                # Module A+ - 分析实验室 Agent
└── asset_inspector.py             # Module X - 资产探查 Agent
```

**Agent 定义示例**:
```python
# backend/graph/agents/market_analyst.py
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from backend.tools import metaso_search, trend_analyzer

MARKET_ANALYST_PROMPT = """你是短剧市场分析专家。

职责：
1. 分析当前短剧市场趋势
2. 识别热门题材和赛道
3. 提供数据驱动的推荐

可用工具：
- metaso_search: 实时搜索市场信息
- trend_analyzer: 分析历史趋势数据

输出要求：
1. 返回市场分析报告 (JSON 格式)
2. 生成 SDUI 交互块 (赛道选择按钮)
"""

# 创建 Agent
market_analyst_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=[metaso_search, trend_analyzer],
    state_modifier=MARKET_ANALYST_PROMPT,
)

__all__ = ["market_analyst_agent"]
```

**任务列表**:
- [ ] 创建 `backend/graph/agents/__init__.py` - Agent 导出
- [ ] 创建 `backend/graph/agents/master_router.py` - Level 0 Agent
- [ ] 创建 `backend/graph/agents/market_analyst.py` - Level 1 Agent
- [ ] 创建 `backend/graph/agents/story_planner.py` - Level 2 Agent
- [ ] 创建 `backend/graph/agents/skeleton_builder.py` - Level 3 Agent
- [ ] 编写 Agent 测试用例

---

## 第四步：全局路由架构 (Step 4: Global Routing)

**目标**: 组装"大脑"。实现 Master Router 作为单一入口。

**关于 router.py 的处理**:

现有 `backend/graph/router.py` 包含纯函数路由逻辑：
- `route_from_start()` - 入口路由
- `route_after_master()` - Master Router 后路由
- `route_after_market_analyst()` - Market Analyst 后路由

**决策**: ✅ **保留 router.py，但简化逻辑**

理由：
1. 路由函数是纯函数，与 Agent 架构不冲突
2. LangGraph 需要路由函数决定条件边
3. 可以复用现有逻辑，只需调整以适应 Agent 架构

**需要修改的内容**:
1. 删除 `use_master_router` 相关逻辑（不再需要双路由）
2. 简化 `route_from_start()` - 所有请求都经过 Master Router
3. 保留 `route_after_*` 函数用于子图内部路由

**文件清单**:
```
backend/graph/
├── router.py                      # 路由决策函数（保留并简化）
├── main_graph.py                  # 主 StateGraph 定义
└── subgraphs/                     # 子图定义
    ├── __init__.py
    ├── module_a.py               # 小说生成子图 (Writer-Editor-Refiner 闭环)
    ├── module_b.py               # 剧本提取子图
    └── module_c.py               # 分镜拆分子图
```

**简化后的 router.py**:
```python
# backend/graph/router.py (简化版)

from typing import Literal
from backend.schemas.agent_state import AgentState

def route_from_start(state: AgentState) -> Literal["master_router"]:
    """
    入口路由 - 所有请求都经过 Master Router
    """
    return "master_router"

def route_after_master(state: AgentState) -> Literal[
    "market_analyst", "story_planner", "skeleton_builder", 
    "module_a", "module_b", "module_c", "end"
]:
    """
    Master Router 后的路由决策
    根据 routed_agent 字段决定
    """
    routed_agent = state.get("routed_agent")
    
    agent_map = {
        "market_analyst": "market_analyst",
        "story_planner": "story_planner",
        "skeleton_builder": "skeleton_builder",
        "novel_writer": "module_a",
        "script_adapter": "module_b",
        "storyboard_director": "module_c",
    }
    
    return agent_map.get(routed_agent, "end")

def route_after_editor(state: AgentState) -> Literal["approve", "refine"]:
    """
    Editor Agent 后的路由决策（用于 Module A 子图）
    """
    quality_score = state.get("quality_score", 0)
    revision_count = state.get("revision_count", 0)
    max_retries = 3
    
    if quality_score >= 80 or revision_count >= max_retries:
        return "approve"
    return "refine"
```

**主图定义** (`main_graph.py`):
```python
# backend/graph/main_graph.py

from langgraph.graph import StateGraph, START, END
from backend.graph.agents import (
    master_router_agent,
    market_analyst_agent,
    story_planner_agent,
    skeleton_builder_agent,
)
from backend.graph.subgraphs import create_module_a_subgraph
from backend.graph.router import route_from_start, route_after_master

def create_main_graph(checkpointer=None):
    """创建主图 - Master Router 作为单一入口"""
    graph = StateGraph(AgentState)
    
    # 编译子图
    module_a_subgraph = create_module_a_subgraph().compile()
    
    # 添加 Agent 节点
    graph.add_node("master_router", master_router_agent)
    graph.add_node("market_analyst", market_analyst_agent)
    graph.add_node("story_planner", story_planner_agent)
    graph.add_node("skeleton_builder", skeleton_builder_agent)
    graph.add_node("module_a", module_a_subgraph)
    # ... 其他 Agents
    
    # 入口：所有请求都经过 Master Router
    graph.add_edge(START, "master_router")
    
    # Master Router -> 各 Agent
    graph.add_conditional_edges(
        "master_router",
        route_after_master,
        {
            "market_analyst": "market_analyst",
            "story_planner": "story_planner",
            "skeleton_builder": "skeleton_builder",
            "module_a": "module_a",
            # ...
            "end": END,
        }
    )
    
    # 各 Agent 完成后回到 Master Router（等待下一条消息）
    for node in ["market_analyst", "story_planner", "skeleton_builder", "module_a"]:
        graph.add_edge(node, "master_router")
    
    return graph.compile(checkpointer=checkpointer)
```

**子图示例** (Module A):
```python
# backend/graph/subgraphs/module_a.py
from langgraph.graph import StateGraph, END
from backend.graph.agents import (
    novel_writer_agent,
    content_editor_agent,
    content_refiner_agent,
)
from backend.graph.router import route_after_editor

def create_module_a_subgraph():
    """Module A: 小说生成子图"""
    subgraph = StateGraph(AgentState)
    
    # 添加 Agent 节点
    subgraph.add_node("writer", novel_writer_agent)
    subgraph.add_node("editor", content_editor_agent)
    subgraph.add_node("refiner", content_refiner_agent)
    
    # 设置入口
    subgraph.set_entry_point("writer")
    
    # Writer -> Editor
    subgraph.add_edge("writer", "editor")
    
    # Editor 决策
    subgraph.add_conditional_edges(
        "editor",
        route_after_editor,
        {"approve": END, "refine": "refiner"}
    )
    
    # Refiner -> Writer (循环)
    subgraph.add_edge("refiner", "writer")
    
    return subgraph
```

**任务列表**:
- [ ] 简化 `backend/graph/router.py` - 删除双路由逻辑
- [ ] 创建 `backend/graph/main_graph.py` - 主图定义
- [ ] 创建 `backend/graph/subgraphs/__init__.py`
- [ ] 创建 `backend/graph/subgraphs/module_a.py` - 小说生成子图
- [ ] 编写 Graph 集成测试

---

## 第五步：API 接口层 (Step 5: API Layer)

**目标**: 通过 SSE 暴露接口供前端使用。

**文件清单**:
```
backend/api/
├── __init__.py
├── deps.py                        # 依赖注入
└── routers/
    ├── __init__.py
    ├── graph.py                   # /chat (SSE), /messages/{thread_id}
    ├── action.py                  # SDUI Action 处理
    ├── projects.py
    └── jobs.py
```

**关键端点**:
- `POST /api/graph/chat` - SSE 流式输出
- `GET /api/graph/messages/{thread_id}` - 历史记录恢复
- `POST /api/graph/action` - SDUI Action 处理
- `POST /api/graph/approve` - 用户确认 (Human-in-the-Loop)

**SSE 事件类型**:
```python
{
    "type": "node_start",          # Agent 开始执行
    "node": "market_analyst",
    "desc": "🔍 正在分析市场趋势..."
}
{
    "type": "tool_call",           # Agent 调用 Tool
    "tool": "metaso_search",
    "input": "2026年短剧市场趋势"
}
{
    "type": "token",               # LLM 流式输出
    "content": "根据最新数据..."
}
{
    "type": "ui_interaction",      # SDUI 交互块
    "data": {...}
}
{
    "type": "done",                # 执行完成
    "state": {...}
}
```

**任务列表**:
- [ ] 创建 `backend/api/routers/graph.py` - Graph API
- [ ] 创建 `backend/api/routers/action.py` - Action API
- [ ] 实现 SSE 流式输出
- [ ] 实现历史记录恢复
- [ ] 编写 API 测试

---

## 第六步：联调与验证 (Step 6: Integration)

**目标**: 启动并测试基本流程。

**验证路径**:
```
前端发送 CMD:start
    ↓
Master Router Agent → 意图识别
    ↓
Market Analyst Agent → 分析市场
    ↓
返回 SDUI (赛道选择按钮)
    ↓
用户点击按钮
    ↓
Story Planner Agent → 生成故事方案
    ↓
...
```

**测试清单**:
- [ ] Agent 能够自主调用 Tools
- [ ] Agent 返回正确的 SDUI 格式
- [ ] 状态在节点间正确传递
- [ ] Human-in-the-Loop 正常工作
- [ ] SSE 流式输出正常

---

## 第七步：模块化扩展 (Step 7: Modular Expansion)

**目标**: 核心稳定后，添加高级功能模块。

**扩展 Agent**:
- [ ] `Analysis Lab` - 情绪分析与定向修文
- [ ] `Asset Inspector` - 资产探查与设定图生成
- [ ] `Style Transfer` - 文风克隆与迁移
- [ ] `Parallel Generation` - Map-Reduce 并行分镜生成

---

## 构建顺序建议

### Phase 1: 核心 Agents (Week 1)
1. ✅ 保持 `router.py`（简化逻辑）
2. 创建 `agents/__init__.py`
3. 创建 `agents/master_router.py`
4. 创建 `agents/market_analyst.py`
5. 创建 `agents/story_planner.py`
6. 创建 `main_graph.py`（基础版本）

### Phase 2: 子图实现 (Week 2)
7. 创建 `subgraphs/module_a.py`
8. 创建 `agents/novel_writer.py`
9. 创建 `agents/content_editor.py`
10. 创建 `agents/content_refiner.py`
11. 更新 `main_graph.py`（集成子图）

### Phase 3: API 层 (Week 3)
12. 创建 `api/routers/graph.py`
13. 创建 `api/routers/action.py`
14. 实现 SSE 流式输出
15. 联调测试

---

## 附录 A: 目录结构 (v4.0.0 Agent 架构)

```
backend/
├── api/                           # API 路由层
│   ├── __init__.py
│   └── routers/
│       ├── graph.py              # Graph 流式 API
│       ├── action.py             # SDUI Action 处理
│       └── ...
├── graph/                         # LangGraph 核心
│   ├── __init__.py
│   ├── main_graph.py             # 主 StateGraph
│   ├── router.py                 # 路由决策函数（保留并简化）
│   ├── checkpointer.py           # PostgreSQL 检查点
│   ├── agents/                   # Agent 定义 (核心)
│   │   ├── __init__.py           # Agent 导出
│   │   ├── master_router.py      # L0 Agent
│   │   ├── market_analyst.py     # L1 Agent
│   │   ├── story_planner.py      # L2 Agent
│   │   ├── skeleton_builder.py   # L3 Agent
│   │   ├── novel_writer.py       # Mod A Agent
│   │   ├── content_editor.py     # Mod A Agent
│   │   ├── content_refiner.py    # Mod A Agent
│   │   ├── script_adapter.py     # Mod B Agent
│   │   ├── storyboard_director.py # Mod C Agent
│   │   ├── analysis_lab.py       # Mod A+ Agent
│   │   └── asset_inspector.py    # Mod X Agent
│   └── subgraphs/                # 子图定义
│       ├── __init__.py
│       ├── module_a.py           # 小说生成闭环
│       ├── module_b.py           # 剧本提取
│       └── module_c.py           # 分镜拆分
├── schemas/                       # 数据模型
├── services/                      # 服务层
├── tools/                         # Tool 定义
└── ...
```

---

## 附录 B: 关于 router.py 的说明

**Q: 是否需要删除 router.py？**

**A: 不需要删除，但需要简化。**

理由：
1. LangGraph 的条件边需要路由函数（纯函数）
2. 现有逻辑大部分可以复用
3. 只需删除 `use_master_router` 双路由逻辑

**需要删除的内容**:
- `use_master_router` 标志检查
- 双路由模式的条件分支
- 复杂的默认路由逻辑

**需要保留的内容**:
- `route_from_start()` - 简化为直接返回 "master_router"
- `route_after_master()` - 根据 `routed_agent` 路由
- `route_after_editor()` - 子图内部路由
- Agent 名称映射函数

---

## 附录 C: 变更记录

### v4.0.0 (2026-02-06)
- ✅ **采用 Agent 架构** - 使用 `create_react_agent` 替代传统节点函数
- ✅ **目录重构** - `nodes/` → `agents/`
- ✅ **架构升级** - 每个节点成为具备自主决策能力的 Agent
- ✅ **简化路由** - Master Router 作为单一入口，删除双路由模式
- 🎯 **下一步** - 创建 `agents/` 目录和所有 Agent 定义

---

**最后更新**: 2026-02-06  
**版本**: v4.0.0 Agent 架构  
**状态**: Step 2 完成，Step 3 进行中
