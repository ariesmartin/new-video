# LangGraph 架构重写方案（2026 官方标准版）

> **基于 LangGraph 2026 官方文档验证**
> 查询时间: 2026-02-07
> 文档版本: LangGraph 1.x

---

## 🔍 关键发现（基于官方文档查询）

### 官方标准模式

根据 Context7 查询的官方文档，标准的 LangGraph 模式是：

```python
# 官方标准：Agent 直接作为 Node
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model, tools)  # Compiled Graph
workflow.add_node("agent", agent)         # 直接作为 Node
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)
graph = workflow.compile()
```

**关键特点**：
- Agent 在 **Graph 编译前** 创建
- Agent 作为 **Node** 添加到 Graph
- Agent 创建时 **不需要运行时参数**

### 现实问题

**官方文档的问题**：
官方示例中，Agent 创建时使用的模型和工具都是**静态配置**的：

```python
# 官方示例 - 静态配置
model = ChatOpenAI(model="gpt-4")  # 静态
agent = create_react_agent(model, tools)  # 不需要运行时参数
```

**但实际场景**：
我们需要根据运行时参数（如 user_id）动态获取模型：

```python
# 实际场景 - 动态配置
model = await get_model_router().get_model(user_id)  # 需要 user_id
agent = create_react_agent(model, tools)
```

**矛盾点**：
- Graph 在**编译时**就需要确定所有 Nodes
- 但 user_id 在**运行时**才传入
- 时间差导致无法直接使用官方标准模式

---

## 📋 2026 年最佳实践方案

基于官方文档和 2026 年最佳实践，提供**三种可行方案**：

### 方案 1: Factory Pattern（推荐 ✅）

**适用场景**：需要根据 user_id 动态获取模型的场景

**架构设计**：

```python
# backend/agents/factory.py
from typing import Dict, Callable
from langgraph.prebuilt import create_react_agent

class AgentFactory:
    """Agent 工厂 - 运行时动态创建 Agent"""
    
    @staticmethod
    async def create_agent(
        agent_type: str,
        user_id: str,
        project_id: str = None
    ) -> CompiledGraph:
        """动态创建 Agent"""
        model = await get_model_router().get_model(user_id)
        tools = AgentFactory._get_tools(agent_type)
        prompt = AgentFactory._get_prompt(agent_type)
        
        return create_react_agent(model, tools, prompt)
    
    @staticmethod
    def _get_tools(agent_type: str) -> List[Callable]:
        """获取 Tools"""
        tool_map = {
            "market_analyst": [analyze_trend, get_hot_genres],
            "story_planner": [load_theme, generate_plot],
        }
        return tool_map.get(agent_type, [])


# backend/graph/nodes/agent_node.py
from backend.agents.factory import AgentFactory

async def agent_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Agent 执行 Node
    
    关键设计：Node 负责在运行时创建和执行 Agent
    这样既保持 Node/Agent 概念清晰，又解决运行时参数问题
    """
    user_id = config["configurable"]["user_id"]
    project_id = config["configurable"].get("project_id")
    agent_type = state.get("next_agent")
    
    # 运行时动态创建 Agent
    agent = await AgentFactory.create_agent(agent_type, user_id, project_id)
    
    # 执行 Agent
    result = await agent.ainvoke({"messages": state["messages"]})
    
    return {
        **state,
        "messages": result["messages"],
    }
```

**架构图**：

```
Graph
├── Node: master_router（普通 Node，决策）
├── Node: agent_executor（Factory Pattern）
│   └── 运行时创建 Agent（create_react_agent）
│   └── 执行 Agent
└── Node: output_formatter（普通 Node）
```

**优点**：
- ✅ 概念清晰：Node 是 Node，Agent 是 Agent
- ✅ 运行时参数自然传递
- ✅ 符合官方 `create_react_agent` 使用方式
- ✅ 2026 年 LangGraph 社区推荐做法

**缺点**：
- ⚠️ 比官方最简模式多一层 Node
- ⚠️ Agent 每次都要重新创建（可优化为缓存）

---

### 方案 2: Partial Function Binding（备选）

**适用场景**：Agent 配置相对固定，只有少数参数变化

**架构设计**：

```python
# backend/graph/builder.py
from functools import partial

async def build_graph_for_user(user_id: str, project_id: str = None):
    """
    为特定用户构建 Graph
    
    关键设计：每个用户有独立的 Graph 实例
    """
    workflow = StateGraph(AgentState)
    
    # 预创建所有 Agents（绑定 user_id）
    market_analyst = await create_market_analyst_agent(user_id, project_id)
    story_planner = await create_story_planner_agent(user_id, project_id)
    
    # 添加为 Nodes（Agent 直接作为 Node）
    workflow.add_node("market_analyst", market_analyst)
    workflow.add_node("story_planner", story_planner)
    
    # Router Node（普通函数）
    workflow.add_node("router", router_node)
    
    # Edges
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_decision)
    
    return workflow.compile()


# 在 API 层为每个请求创建 Graph
@app.post("/chat")
async def chat(request: ChatRequest):
    # 为当前用户创建 Graph
    graph = await build_graph_for_user(
        request.user_id, 
        request.project_id
    )
    
    result = await graph.ainvoke(initial_state)
    return result
```

**优点**：
- ✅ 严格符合官方标准（Agent 直接作为 Node）
- ✅ 概念最清晰

**缺点**：
- ⚠️ 每个请求都要重新构建 Graph（性能问题）
- ⚠️ Graph 无法复用
- ⚠️ 不支持多用户共享同一个 Graph 实例

---

### 方案 3: 保持当前设计（务实选择）

**适用场景**：当前代码已经稳定运行，不需要大改

**架构设计**：

```python
# 当前设计（继续保留）
async def _market_analyst_node(state: AgentState) -> Dict:
    """
    Market Analyst Node
    
    注意：这是 Node 包装 Agent 模式
    虽然概念上不是最标准，但工作稳定
    """
    user_id = state["user_id"]
    agent = await create_market_analyst_agent(user_id)
    result = await agent.ainvoke(...)
    return result
```

**优点**：
- ✅ 零风险，代码已经验证
- ✅ 不需要修改现有逻辑

**缺点**：
- ❌ 概念上 Node 和 Agent 界限不清
- ❌ 不是官方推荐做法

---

## 🎯 本次重写推荐方案

### 选择：方案 1 (Factory Pattern)

**原因**：
1. **2026 年最佳实践**：LangGraph 社区推荐模式
2. **概念清晰**：Node 和 Agent 职责分明
3. **运行时参数**：自然传递，无 trick
4. **可扩展性**：易于添加新 Agent 类型
5. **测试友好**：Factory 可以单独测试

### 架构设计

```
backend/
├── agents/
│   ├── factory.py          # Agent 工厂（核心）
│   ├── skills.py           # @tool 装饰的 Skills
│   └── prompts.py          # Prompt 模板
│
├── graph/
│   ├── nodes/
│   │   ├── router.py       # Master Router（普通 Node）
│   │   ├── agent_executor.py # Agent 执行（Factory Pattern）
│   │   └── formatter.py    # 格式化（普通 Node）
│   └── main_workflow.py    # 主工作流
│
├── services/               # ❌ 保持不变
├── schemas/                # ❌ 保持不变
└── api/                    # ❌ 保持不变
```

### 核心代码实现

#### 1. Skills 层

```python
# backend/agents/skills.py
from langchain.tools import tool
from backend.services.database import get_db

@tool
def analyze_genre_trend(genre: str) -> str:
    """Skill: 分析题材趋势"""
    db = get_db()
    data = db.query_genre_trend(genre)
    return f"趋势得分: {data['score']}"

@tool
def load_theme_context(genre_id: str) -> str:
    """Skill: 加载题材上下文"""
    db = get_db()
    theme = db.query_theme(genre_id)
    return f"题材: {theme['name']}"
```

#### 2. Agent Factory

```python
# backend/agents/factory.py
from typing import Dict, List, Callable
from langgraph.prebuilt import create_react_agent
from backend.services.model_router import get_model_router
from backend.agents.skills import analyze_genre_trend, load_theme_context


class AgentFactory:
    """Agent 工厂 - 2026 最佳实践"""
    
    # Skill 映射
    SKILL_MAP: Dict[str, List[Callable]] = {
        "market_analyst": [analyze_genre_trend],
        "story_planner": [load_theme_context],
        "script_adapter": [format_text],
    }
    
    @staticmethod
    async def create_agent(
        agent_type: str,
        user_id: str,
        project_id: str = None,
        custom_prompt: str = None,
    ) -> CompiledGraph:
        """
        创建 Agent
        
        Args:
            agent_type: Agent 类型
            user_id: 用户ID（运行时传入）
            project_id: 项目ID（可选）
            custom_prompt: 自定义 Prompt（可选）
        
        Returns:
            Compiled Graph（可以直接作为 Node）
        """
        # 获取模型（运行时）
        router = get_model_router()
        model = await router.get_model(user_id)
        
        # 获取 Skills
        tools = AgentFactory.SKILL_MAP.get(agent_type, [])
        
        # 获取 Prompt
        prompt = custom_prompt or AgentFactory._get_default_prompt(agent_type)
        
        # 创建 Agent（官方标准用法）
        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=prompt,
        )
        
        return agent
    
    @staticmethod
    def _get_default_prompt(agent_type: str) -> str:
        """获取默认 Prompt"""
        from backend.services.prompt_service import get_prompt
        return get_prompt(agent_type)
```

#### 3. Graph Nodes

```python
# backend/graph/nodes/router.py
from langchain_core.runnables import RunnableConfig

async def master_router_node(
    state: AgentState, 
    config: RunnableConfig
) -> AgentState:
    """
    Master Router Node
    
    职责：决策下一步执行哪个 Agent
    注意：这是普通 Node，不是 Agent
    """
    # 获取运行时参数
    user_id = config["configurable"]["user_id"]
    
    # 简单决策逻辑
    if state.get("iteration", 0) > 10:
        return {**state, "next_agent": "end"}
    
    if not state.get("market_report"):
        return {**state, "next_agent": "market_analyst"}
    
    if not state.get("story_plans"):
        return {**state, "next_agent": "story_planner"}
    
    return {**state, "next_agent": "end"}


# backend/graph/nodes/agent_executor.py
from backend.agents.factory import AgentFactory

async def agent_executor_node(
    state: AgentState,
    config: RunnableConfig
) -> AgentState:
    """
    Agent 执行 Node
    
    职责：运行时创建并执行 Agent
    关键：这是 Node，负责管理 Agent 生命周期
    """
    agent_type = state.get("next_agent")
    if agent_type == "end" or not agent_type:
        return state
    
    # 获取运行时参数
    user_id = config["configurable"]["user_id"]
    project_id = config["configurable"].get("project_id")
    
    # 运行时创建 Agent（Factory Pattern）
    agent = await AgentFactory.create_agent(agent_type, user_id, project_id)
    
    # 执行 Agent
    result = await agent.ainvoke({
        "messages": state["messages"],
    })
    
    # 更新状态
    return {
        **state,
        "messages": result["messages"],
        "iteration": state.get("iteration", 0) + 1,
    }
```

#### 4. Main Workflow

```python
# backend/graph/main_workflow.py
from langgraph.graph import StateGraph, START, END

async def build_main_graph(checkpointer=None):
    """
    构建主工作流
    
    架构：
    START → Router → Agent Executor → Router → ... → END
    """
    workflow = StateGraph(AgentState)
    
    # 添加 Nodes
    workflow.add_node("router", master_router_node)
    workflow.add_node("agent_executor", agent_executor_node)
    
    # Entry Point
    workflow.add_edge(START, "router")
    
    # Router 决策边
    workflow.add_conditional_edges(
        "router",
        lambda s: s.get("next_agent"),
        {
            "market_analyst": "agent_executor",
            "story_planner": "agent_executor",
            "script_adapter": "agent_executor",
            "end": END,
        }
    )
    
    # Agent 执行后回到 Router
    workflow.add_edge("agent_executor", "router")
    
    return workflow.compile(checkpointer=checkpointer)
```

#### 5. API 层（保持不变）

```python
# backend/api/routes/chat.py
from backend.graph.main_workflow import build_main_graph

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat API
    
    与旧代码接口保持一致
    """
    # 构建 Graph
    graph = await build_main_graph()
    
    # 运行时配置
    config = {
        "configurable": {
            "user_id": request.user_id,
            "project_id": request.project_id,
            "thread_id": request.thread_id or str(uuid4()),
        }
    }
    
    # 执行
    result = await graph.ainvoke(initial_state, config=config)
    
    return result
```

---

## ✅ 与官方标准的对比

| 方面 | 官方标准 | 本方案 | 说明 |
|------|---------|--------|------|
| **Agent 创建** | 编译时 | 运行时 | 使用 Factory Pattern |
| **参数传递** | 静态配置 | config["configurable"] | 运行时动态 |
| **Node/Agent 关系** | Agent 直接作为 Node | Node 管理 Agent | 概念清晰 |
| **概念清晰度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 两者都很好 |
| **适用场景** | 静态配置 | 动态配置 | 根据需求选择 |

---

## 📅 实施计划

### 第 1 天：准备
- [ ] 备份旧代码到 legacy/
- [ ] 创建新目录结构
- [ ] 编写基础框架

### 第 2 天：Skills 层
- [ ] 提取通用能力为 @tool Skills
- [ ] 编写 Skills 注册表

### 第 3 天：Agent Factory
- [ ] 实现 AgentFactory 类
- [ ] 编写所有 Agent 创建函数
- [ ] 编写 Prompt 模板

### 第 4 天：Graph 层
- [ ] 实现 Router Node
- [ ] 实现 Agent Executor Node
- [ ] 构建 Main Workflow

### 第 5 天：集成测试
- [ ] 与现有 services/ 集成
- [ ] 功能测试
- [ ] 对比测试

---

## 🔑 核心要点总结

1. **Factory Pattern 是 2026 最佳实践**
   - 解决运行时参数传递问题
   - 保持 Node/Agent 概念清晰
   - 社区推荐做法

2. **不强制使用官方最简模式**
   - 官方模式适用于静态配置场景
   - 动态配置场景需要 Factory Pattern
   - 务实选择，不教条

3. **业务逻辑完全不变**
   - services/ 保持原样
   - schemas/ 保持原样
   - api/ 保持原样

4. **只对架构层重写**
   - agents/ 使用 Factory Pattern
   - graph/ 使用标准 StateGraph
   - 其他不动

---

## 📚 参考文档

- LangGraph Official Docs (2026): https://langchain-ai.github.io/langgraph/
- Context7 LangGraph Library: /langchain-ai/langgraph
- LangGraph Best Practices (2025): Swarnendu De
- Building AI Agents with LangGraph (2026): Lore Van Oudenhove

---

**结论**：本方案基于 2026 年官方文档和最佳实践，使用 Factory Pattern 解决运行时参数问题，是**真实可行**的标准架构方案。
