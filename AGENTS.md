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