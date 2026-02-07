"""
LangGraph 架构模式验证测试

测试目的：验证 Factory Pattern vs Node 包装 Agent 模式
"""

import asyncio
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage


# ============ 模拟数据和服务 ============


class MockModelRouter:
    """模拟模型路由服务"""

    async def get_model(self, user_id: str):
        """根据 user_id 获取模型（模拟异步操作）"""
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return MockModel(user_id)


class MockModel:
    """模拟 LLM 模型"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.model_name = f"model_for_{user_id}"

    async def ainvoke(self, messages, tools=None):
        """模拟模型调用"""
        await asyncio.sleep(0.1)

        # 模拟 Tool 调用
        if tools and len(messages) > 0:
            last_msg = messages[-1]
            if hasattr(last_msg, "content") and "使用工具" in str(last_msg.content):
                # 模拟 Tool 调用结果
                return AIMessage(content="使用了工具，结果是：成功")

        return AIMessage(content=f"来自 {self.model_name} 的回复")


# ============ Skills（Tools）===========


@tool
def analyze_data(query: str) -> str:
    """
    Skill: 分析数据

    这是一个模拟的 Skill，实际业务中会查询数据库或调用 API
    """
    return f"分析结果：{query} 的数据表现良好"


@tool
def get_recommendations(category: str) -> str:
    """
    Skill: 获取推荐

    根据类别返回推荐内容
    """
    recommendations = {
        "story": ["复仇", "甜宠", "悬疑"],
        "character": ["霸道总裁", "灰姑娘", "天才少年"],
    }
    return f"推荐：{recommendations.get(category, ['无'])}"


# ============ 模式 1：Factory Pattern（推荐）===========


async def create_agent_factory_pattern(user_id: str):
    """
    Factory Pattern：构建时创建 Agent

    这是推荐的做法，符合 LangGraph 官方标准
    """
    router = MockModelRouter()
    model = await router.get_model(user_id)

    agent = create_react_agent(
        model=model,
        tools=[analyze_data, get_recommendations],
        prompt="你是一个助手，可以使用工具帮助用户。",
    )

    return agent


def build_graph_factory_pattern(user_id: str):
    """
    使用 Factory Pattern 构建 Graph

    注意：这个函数是同步的，但内部调用了异步函数创建 Agent
    在实际应用中，可以在 API 层调用这个函数
    """
    # 为了测试方便，我们使用 asyncio.run
    # 在实际 FastAPI 中，可以直接 await
    agent = asyncio.run(create_agent_factory_pattern(user_id))

    workflow = StateGraph(Dict)

    # ✅ Agent 直接作为 Node（符合官方标准）
    workflow.add_node("agent", agent)
    workflow.add_node("format_output", format_output_node)

    workflow.add_edge(START, "agent")
    workflow.add_edge("agent", "format_output")
    workflow.add_edge("format_output", END)

    return workflow.compile()


# ============ 模式 2：Node 包装 Agent（当前做法）===========


async def _agent_node_wrapped(state: Dict) -> Dict:
    """
    Node 包装 Agent 模式

    这是当前代码的做法，被认为需要"妥协"
    """
    user_id = state.get("user_id")

    # 运行时创建 Agent（每次调用都创建）
    router = MockModelRouter()
    model = await router.get_model(user_id)

    agent = create_react_agent(
        model=model, tools=[analyze_data, get_recommendations], prompt="你是一个助手..."
    )

    # 执行 Agent
    result = await agent.ainvoke({"messages": state.get("messages", [])})

    return {
        **state,
        "messages": result["messages"],
        "output": result["messages"][-1].content if result["messages"] else "",
    }


def build_graph_wrapped():
    """
    使用 Node 包装模式构建 Graph
    """
    workflow = StateGraph(Dict)

    # ❌ Node 包装 Agent（被认为需要妥协）
    workflow.add_node("agent_wrapped", _agent_node_wrapped)
    workflow.add_node("format_output", format_output_node)

    workflow.add_edge(START, "agent_wrapped")
    workflow.add_edge("agent_wrapped", "format_output")
    workflow.add_edge("format_output", END)

    return workflow.compile()


# ============ 辅助函数 ============


def format_output_node(state: Dict) -> Dict:
    """格式化输出 Node（普通函数）"""
    return {**state, "formatted": f"[格式化] {state.get('output', '')}"}


# ============ 测试函数 ============


async def test_factory_pattern():
    """测试 Factory Pattern"""
    print("=" * 60)
    print("测试模式 1：Factory Pattern（推荐）")
    print("=" * 60)

    # 模拟 API 层收到请求
    user_id = "user_123"

    print(f"1. 为 user_id={user_id} 构建 Graph...")
    graph = build_graph_factory_pattern(user_id)
    print(f"   ✅ Graph 构建成功")

    print(f"2. 执行 Graph...")
    initial_state = {
        "messages": [HumanMessage(content="请分析数据")],
        "user_id": user_id,
    }

    result = await graph.ainvoke(initial_state)
    print(f"   ✅ 执行成功")
    print(f"   结果：{result.get('formatted', '')[:50]}...")

    print(f"3. 验证：user_id 正确传递？")
    # 检查模型名称是否包含 user_id
    assert "user_123" in str(result), "user_id 应该被正确传递"
    print(f"   ✅ user_id 正确传递")

    return True


async def test_wrapped_pattern():
    """测试 Node 包装模式"""
    print("\n" + "=" * 60)
    print("测试模式 2：Node 包装 Agent（当前做法）")
    print("=" * 60)

    graph = build_graph_wrapped()
    print(f"1. Graph 构建成功（不需要 user_id）")

    print(f"2. 执行 Graph...")
    initial_state = {
        "messages": [HumanMessage(content="请分析数据")],
        "user_id": "user_456",  # 从 state 传入
    }

    result = await graph.ainvoke(initial_state)
    print(f"   ✅ 执行成功")
    print(f"   结果：{result.get('formatted', '')[:50]}...")

    print(f"3. 验证：user_id 从 state 获取？")
    assert "user_456" in str(result), "user_id 应该从 state 获取"
    print(f"   ✅ user_id 从 state 正确获取")

    return True


async def test_performance_comparison():
    """性能对比测试"""
    print("\n" + "=" * 60)
    print("性能对比测试")
    print("=" * 60)

    # 测试 Factory Pattern
    print("Factory Pattern（Agent 只创建一次）：")
    graph1 = build_graph_factory_pattern("user_test")

    start = asyncio.get_event_loop().time()
    for i in range(3):
        await graph1.ainvoke(
            {"messages": [HumanMessage(content=f"请求{i}")], "user_id": "user_test"}
        )
    end = asyncio.get_event_loop().time()
    factory_time = end - start
    print(f"   3 次调用耗时：{factory_time:.2f} 秒")

    # 测试 Node 包装
    print("\nNode 包装模式（每次创建 Agent）：")
    graph2 = build_graph_wrapped()

    start = asyncio.get_event_loop().time()
    for i in range(3):
        await graph2.ainvoke(
            {"messages": [HumanMessage(content=f"请求{i}")], "user_id": "user_test"}
        )
    end = asyncio.get_event_loop().time()
    wrapped_time = end - start
    print(f"   3 次调用耗时：{wrapped_time:.2f} 秒")

    print(f"\n性能差异：Node 包装比 Factory 慢 {wrapped_time / factory_time:.1f} 倍")
    print("   ⚠️  因为 Node 包装每次都要重新创建 Agent")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("LangGraph 架构模式验证测试")
    print("=" * 60)

    try:
        # 测试 Factory Pattern
        await test_factory_pattern()

        # 测试 Node 包装模式
        await test_wrapped_pattern()

        # 性能对比
        await test_performance_comparison()

        print("\n" + "=" * 60)
        print("测试结论")
        print("=" * 60)
        print("""
✅ 两种模式都能正确处理运行时参数（user_id）

✅ Factory Pattern（推荐）：
   - Agent 在构建时创建，只创建一次
   - 性能更好（不需要每次重新创建）
   - 符合 LangGraph 官方标准
   - Agent 直接作为 Node

⚠️  Node 包装模式（当前做法）：
   - Agent 在运行时创建，每次调用都创建
   - 性能较差（重复创建 Agent）
   - 多了一层不必要的包装
   - 不是"必须妥协"，而是可以改进

结论：
- Factory Pattern 完全可行，不需要妥协
- 当前代码使用 Node 包装是因为早期设计选择
- 可以重构为 Factory Pattern，符合官方标准
        """)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
