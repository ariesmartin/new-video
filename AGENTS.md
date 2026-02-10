📚 LangGraph 官方文档验证版
1. Node 与 Agent 的关系（已验证）
官方定义：
> "This graph is composed of nodes, which are the individual steps or agents in your application"
正确理解：
Node（节点）= 执行单元（最宽泛的概念）
├── Agent（智能体）= 特殊的 Node，具有自主决策能力
├── ToolNode（工具节点）= 专门执行 Tools 的 Node
└── Simple Function（普通函数）= 执行固定逻辑的 Node
关键结论：
- ✅ Agent 是 Node 的子集
- ✅ 所有 Agent 都是 Node，但不是所有 Node 都是 Agent
- ✅ Agent 必须具有 Tool 调用能力和自主决策能力
---
2. create_react_agent 返回什么（已验证）
官方示例：
from langgraph.prebuilt import create_react_agent
# create_react_agent 返回一个 Compiled Graph
app = create_react_agent(model, tools)  # 这是一个 CompiledStateGraph
# 可以直接 invoke
app.invoke({"messages": [...]})
# 也可以作为 Node 添加到另一个 Graph
workflow.add_node("agent", app)  # ✅ 可以直接使用
正确理解：
- create_react_agent() 返回的是 CompiledStateGraph
- 它既是 Graph，也是 Agent，也是 Node
- 可以被直接调用，也可以被添加到其他 Graph 中作为 Node
---
3. Tool 的定义与使用（已验证）
官方定义：
from langchain_core.tools import tool
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return weather_data.get(location.lower(), "Not available")
# Tool 作为参数传递给 create_react_agent
agent = create_react_agent(model=model, tools=[get_weather])
两种使用方式：
方式 1：作为 Agent 的 Tools（推荐）
agent = create_react_agent(model, tools=[get_weather, calculate])
方式 2：使用 ToolNode
from langgraph.prebuilt import ToolNode
tool_node = ToolNode([get_weather, calculate])
workflow.add_node("tools", tool_node)
---
4. 关于 Skill 的官方说明
重要发现：在 LangGraph 官方文档中，没有明确区分 Skill 和 Tool。
根据 LangChain Multi-Agent 文档：
> "Skills are primarily prompt-driven specializations that an agent can invoke on-demand."
正确理解：
- 在 LangGraph 层面，只有 Tool 概念
- Skill 是 LangChain Multi-Agent 系统的概念
- 在 LangGraph 中，Skill 就是 Prompt-driven 的 Tool
正确的 Skill 实现：
from langchain_core.tools import tool
@tool
def load_theme_context(genre_id: str) -> str:
    """
    Skill: 加载题材上下文
    - 这是一个 Tool
    - 也是 LangChain Multi-Agent 中的 Skill
    - Prompt-driven specialization
    """
    genre = db.query("theme_genres", genre_id)
    return f"""
    ## 题材：{genre.name}
    - 核心公式：{genre.core_formula}
    - 推荐元素：{genre.tropes}
    """
---
✅ 正确的组件关系表
| 组件 | 官方定义 | 可以被谁调用 | 示例 |
|------|---------|-------------|------|
| Tool | 可执行函数，使用 @tool 装饰 | 被 Agent 调用 | get_weather() |
| Skill | Prompt-driven Tool（LangChain 概念） | 被 Agent 调用 | load_theme_context() |
| Agent | 具有 Tool 调用能力的 Node | 作为 Node 被 Graph 调用 | create_react_agent() 返回值 |
| Node | Graph 的执行单元（包含 Agent、ToolNode、函数） | 被 Graph 调用 | workflow.add_node() 的参数 |
| Graph | StateGraph 编译后的工作流 | 被其他 Graph 或外部调用 | workflow.compile() 返回值 |
---
🎯 正确的代码架构
层级 1：Tool / Skill
from langchain_core.tools import tool
@tool
def search_database(query: str) -> str:
    """Tool/Skill: 数据库搜索"""
    return db.search(query)
层级 2：Agent
from langgraph.prebuilt import create_react_agent
# Agent = create_react_agent 返回的 Compiled Graph
agent = create_react_agent(
    model=model,
    tools=[search_database],  # Tools/Skills
    prompt="你是助手..."
)
层级 3：Node
# Agent 本身就是 Node，可以直接添加
workflow.add_node("my_agent", agent)  # ✅ agent 是 Node
# 或者使用 ToolNode
tool_node = ToolNode([search_database])
workflow.add_node("tools", tool_node)  # ✅ tool_node 也是 Node
# 或者使用普通函数
def process_data(state):
    return {"result": "processed"}
workflow.add_node("process", process_data)  # ✅ 普通函数也是 Node
层级 4：Graph
from langgraph.graph import StateGraph, START, END
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)
graph = workflow.compile()  # Compiled Graph
---
❌ 常见误区纠正
误区 1："Node = Agent"
错误：
async def my_node(state: AgentState) -> Dict:
    """这是一个 Node，也就是一个 Agent"""  # ❌ 错误！
正确：
async def my_node(state: AgentState) -> Dict:
    """这是一个普通的 Node，不是 Agent
    Agent 必须具有 Tool 调用能力
    """
    return {"result": "fixed_logic"}
# Agent 应该使用 create_react_agent
agent = create_react_agent(model, tools)  # ✅ 这是 Agent
误区 2："Skill 与 Tool 是不同的"
错误：认为 Skill 和 Tool 是两个不同的层。
正确：
# 在 LangGraph 中，Skill 就是 Tool
@tool
def my_skill():
    """这既是 Tool，也是 Skill"""
    pass
# 作为 Tool 使用
agent = create_react_agent(model, tools=[my_skill])
误区 3："普通函数可以调用 Skill"
错误：
async def my_node(state):
    result = await my_skill()  # ❌ 普通 Node 不应该直接调用 Skill
    prompt = f"结果：{result}"
    return model.invoke(prompt)
正确：
# Skill 应该作为 Tool 被 Agent 调用
agent = create_react_agent(model, tools=[my_skill])
# Agent 会自动决定何时调用 my_skill
---
📋 官方最佳实践总结
1. 什么时候使用普通 Node？
- 执行固定逻辑（不需要 LLM 决策）
- 数据转换、格式化
- 简单的状态更新
def format_messages(state):
    """普通 Node：格式化消息"""
    messages = state["messages"]
    formatted = "\n".join([m.content for m in messages])
    return {"formatted_text": formatted}
2. 什么时候使用 Agent？
- 需要 LLM 推理
- 需要 Tool 调用能力
- 需要自主决策
agent = create_react_agent(model, tools)
3. 什么时候使用 ToolNode？
- 需要精细控制 Tool 执行
- 需要自定义错误处理
- 需要与 Agent 分离 Tool 执行
tool_node = ToolNode(
    tools=[search_database],
    handle_tool_errors=custom_handler
)
---
🔑 核心要点
1. Node 是最宽泛的概念，包含 Agent、ToolNode、普通函数
2. Agent 是特殊的 Node，具有 Tool 调用和自主决策能力
3. create_react_agent 返回 Compiled Graph，既是 Agent 也是 Node
4. 在 LangGraph 中，Skill 就是 Tool，使用 @tool 装饰器
5. Tool 只能被 Agent 调用（通过 create_react_agent 或 ToolNode）
---
🆕 5. 模块构建规范（新增模块时必须遵守）
### 5.1 模块架构原则
```
┌─────────────────────────────────────────────────────────────────────┐
│                    标准模块架构（3层结构）                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 1: API Gateway 层（数据网关）                                │
│  ├─ 读取输入：从 DB/Request 获取                                     │
│  ├─ 调用 Graph：Stateless，纯内存传递                               │
│  ├─ 写入输出：保存到 DB                                              │
│  └─ Checkpoint：长流程（>2分钟）必须启用                             │
│                                                                     │
│  Layer 2: Graph 执行层（无状态）                                     │
│  ├─ 纯内存传递（State/Messages）                                    │
│  ├─ 不访问数据库                                                     │
│  ├─ 可测试、可重试                                                   │
│  └─ 可独立使用（通过参数传入所有数据）                               │
│                                                                     │
│  Layer 3: Agent 执行层                                              │
│  ├─ create_react_agent 创建                                         │
│  ├─ 通过 Tools 访问外部服务                                          │
│  └─ 自主决策 + Tool 调用                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
### 5.2 Checkpoint 策略（强制）
| 模块类型 | 执行时间 | Checkpoint | 原因 |
|---------|---------|------------|------|
| 市场分析 | <30s | 可选 | 短流程，可重现 |
| 故事策划 | <60s | 推荐 | 中等流程，有LLM调用 |
| **大纲构建** | **2-8分钟** | **必须** | **长流程，多LLM调用，有循环** |
| 剧本创作 | 5-15分钟 | 必须 | 超长流程，必须恢复能力 |
| 分镜生成 | 3-10分钟 | 必须 | 长流程，图片生成成本高 |
**Checkpoint 启用代码模板**：
```python
# api/{module_name}.py
from backend.graph.checkpointer import get_checkpointer

@router.post("/generate")
async def generate_something(request: Request):
    # 1. 读取输入（Gateway职责）
    db = get_db_service()
    input_data = await db.get_input_data(request.projectId)
    
    # 2. 长流程必须启用 checkpoint
    async with get_checkpointer() as checkpointer:
        result = await run_module_graph(
            user_id=input_data.user_id,
            project_id=request.projectId,
            input_data=input_data,
            checkpointer=checkpointer,  # ✅ 必须传入
        )
    
    # 3. 写入输出（Gateway职责）
    await db.save_result(request.projectId, result)
    return result
```
### 5.3 数据流规范（强制）
**✅ 正确做法**（Gateway模式）：
```python
# api/skeleton_builder.py - 正确示例
async def generate_outline(request):
    # Gateway职责：读取输入
    db = get_db_service()
    selected_plan = await db.get_plan(request.planId)
    user_config = await db.get_user_config(request.projectId)
    
    # 调用Graph：纯内存传递
    result = await run_skeleton_builder(
        selected_plan=selected_plan,  # 显式传参
        user_config=user_config,       # 显式传参
        checkpointer=checkpointer,     # 启用持久化
    )
    
    # Gateway职责：写入输出
    await db.save_outline(request.projectId, result)
```
**❌ 错误做法**（Graph内部访问DB）：
```python
# 不要在Graph内部访问数据库！
async def skeleton_builder_node(state):
    # ❌ 错误：Node内部访问DB
    db = get_db_service()
    user_config = await db.get_user_config(state["project_id"])
    
    # 正确：从state获取
    user_config = state.get("user_config")
```
### 5.4 模块独立使用规范
**所有模块必须支持两种调用方式**：
```python
# backend/graph/workflows/{module}_graph.py

# 方式1：独立使用（API/脚本调用）
async def run_module(
    user_id: str,
    project_id: str,
    input_data: Dict[str, Any],
    checkpointer: Optional[BaseCheckpointSaver] = None,
) -> Dict[str, Any]:
    """
    独立运行模块
    
    所有输入通过参数传入，函数内部不访问DB
    """
    graph = build_module_graph(checkpointer=checkpointer)
    state = create_initial_state(user_id, project_id)
    state["input_data"] = input_data
    
    if checkpointer:
        config = {"configurable": {"thread_id": f"{module_name}_{project_id}"}}
        return await graph.ainvoke(state, config=config)
    else:
        return await graph.ainvoke(state)

# 方式2：集成使用（作为main_graph的节点）
async def module_node(state: AgentState) -> Dict[str, Any]:
    """
    作为main_graph的节点使用
    
    从state提取数据，调用独立函数
    """
    # 从state提取（main_graph已传递）
    input_data = state.get("input_data")
    
    # 调用独立函数（复用逻辑）
    result = await run_module(
        user_id=state["user_id"],
        project_id=state["project_id"],
        input_data=input_data,
        # checkpointer由main_graph管理
    )
    
    # 合并结果到state
    return {
        **state,
        "module_output": result["output"],
        "last_successful_node": "module_name",
    }
```
### 5.5 Node返回规范（强制）
**所有Node必须返回完整的state更新**：
```python
# ✅ 正确：返回完整更新
async def my_node(state: AgentState) -> Dict[str, Any]:
    output = process(state["input"])
    return {
        "output": output,                           # 新数据
        "last_successful_node": "my_node",          # 节点标记
        # 可选：其他状态更新
    }

# ❌ 错误：只返回部分数据
async def my_node(state: AgentState) -> Dict[str, Any]:
    output = process(state["input"])
    return {"output": output}  # ❌ 缺少last_successful_node
```
### 5.6 新增模块检查清单
添加新模块时，必须验证：
- [ ] 模块是否定义了`run_{module}`独立函数
- [ ] 长流程（>2分钟）是否启用了checkpoint
- [ ] Graph内部是否不访问数据库
- [ ] API层是否正确作为Gateway（读写DB）
- [ ] Node是否返回`last_successful_node`
- [ ] 是否支持从main_graph调用（提供{module}_node函数）
- [ ] 是否通过测试（包含checkpoint恢复测试）
---
❌ 常见误区纠正
误区 1："Node = Agent"
错误：
async def my_node(state: AgentState) -> Dict:
    """这是一个 Node，也就是一个 Agent"""  # ❌ 错误！
正确：
async def my_node(state: AgentState) -> Dict:
    """这是一个普通的 Node，不是 Agent
    Agent 必须具有 Tool 调用能力
    """
    return {"result": "fixed_logic"}
# Agent 应该使用 create_react_agent
agent = create_react_agent(model, tools)  # ✅ 这是 Agent
误区 2："Skill 与 Tool 是不同的"
错误：认为 Skill 和 Tool 是两个不同的层。
正确：
# 在 LangGraph 中，Skill 就是 Tool
@tool
def my_skill():
    """这既是 Tool，也是 Skill"""
    pass
# 作为 Tool 使用
agent = create_react_agent(model, tools=[my_skill])
误区 3："普通函数可以调用 Skill"
错误：
async def my_node(state):
    result = await my_skill()  # ❌ 普通 Node 不应该直接调用 Skill
    prompt = f"结果：{result}"
    return model.invoke(prompt)
正确：
# Skill 应该作为 Tool 被 Agent 调用
agent = create_react_agent(model, tools=[my_skill])
# Agent 会自动决定何时调用 my_skill
误区 4："Graph内部可以访问数据库"
错误：
async def my_node(state):
    db = get_db_service()  # ❌ Node内部不应直接访问DB
    data = await db.get_data(state["project_id"])
正确：
# API层（Gateway）访问DB，传入Graph
async def api_endpoint(request):
    db = get_db_service()
    data = await db.get_data(request.project_id)  # ✅ Gateway职责
    result = await run_graph(data=data)  # 传入Graph
误区 5："长流程不需要checkpoint"
错误：
# 大纲生成2-8分钟，不启用checkpoint
result = await run_skeleton_builder(...)  # ❌ 崩溃后全部丢失
正确：
async with get_checkpointer() as checkpointer:
    result = await run_skeleton_builder(..., checkpointer=checkpointer)  # ✅
---
📋 官方最佳实践总结
1. 什么时候使用普通 Node？
- 执行固定逻辑（不需要 LLM 决策）
- 数据转换、格式化
- 简单的状态更新
def format_messages(state):
    """普通 Node：格式化消息"""
    messages = state["messages"]
    formatted = "\n".join([m.content for m in messages])
    return {"formatted_text": formatted}
2. 什么时候使用 Agent？
- 需要 LLM 推理
- 需要 Tool 调用能力
- 需要自主决策
agent = create_react_agent(model, tools)
3. 什么时候使用 ToolNode？
- 需要精细控制 Tool 执行
- 需要自定义错误处理
- 需要与 Agent 分离 Tool 执行
tool_node = ToolNode(
    tools=[search_database],
    handle_tool_errors=custom_handler
)
4. 什么时候启用 Checkpoint？
- 执行时间 > 2 分钟
- 有多个 LLM 调用
- 需要故障恢复能力
- 有循环迭代（如审阅-修复循环）
async with get_checkpointer() as checkpointer:
    result = await run_graph(checkpointer=checkpointer)