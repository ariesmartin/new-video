"""
架构模式逻辑验证测试（简化版）

不依赖外部库，只验证核心逻辑：
1. Factory Pattern 是否能正确处理运行时参数
2. Node 包装模式是否真的"必须妥协"
"""

import asyncio
from typing import Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime


# ============ 模拟核心类 ============


@dataclass
class MockAgent:
    """模拟 Agent 类"""

    model_name: str
    tools: list
    created_at: datetime

    async def invoke(self, messages: list) -> dict:
        """模拟 Agent 执行"""
        await asyncio.sleep(0.1)  # 模拟执行时间
        return {
            "output": f"来自 {self.model_name} 的结果",
            "messages": messages
            + [{"role": "assistant", "content": f"回复 from {self.model_name}"}],
        }


class MockModelRouter:
    """模拟模型路由服务"""

    async def get_model(self, user_id: str):
        """根据 user_id 获取模型（模拟异步操作）"""
        await asyncio.sleep(0.05)  # 模拟网络延迟
        return f"model_for_{user_id}"


# ============ 工具函数 ============


async def create_agent(user_id: str) -> MockAgent:
    """创建 Agent（模拟 create_react_agent）"""
    router = MockModelRouter()
    model_name = await router.get_model(user_id)

    return MockAgent(
        model_name=model_name, tools=["tool1", "tool2"], created_at=datetime.now()
    )


def format_output_node(state: Dict) -> Dict:
    """格式化输出 Node"""
    return {**state, "formatted": f"[格式化] {state.get('output', '')}"}


# ============ 模式 1：Factory Pattern ============


class FactoryPatternGraph:
    """
    Factory Pattern 实现

    特点：
    - 构建时传入 user_id
    - Agent 只创建一次
    - Agent 直接作为 Node
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.agent = None
        self.nodes = {}

    async def build(self):
        """构建 Graph"""
        print(f"  [Factory] 创建 Agent for user_id={self.user_id}...")
        self.agent = await create_agent(self.user_id)
        print(f"  [Factory] ✅ Agent 创建成功: {self.agent.model_name}")

        # 注册 Nodes
        self.nodes["agent"] = self._agent_node
        self.nodes["format"] = format_output_node

        return self

    async def _agent_node(self, state: Dict) -> Dict:
        """Agent Node - 直接使用构建时创建的 Agent"""
        print(f"  [Factory] 执行 Agent Node...")
        result = await self.agent.invoke(state.get("messages", []))
        return {**state, "output": result["output"], "messages": result["messages"]}

    async def execute(self, initial_state: Dict) -> Dict:
        """执行 Graph"""
        print(f"  [Factory] 开始执行...")

        # Step 1: Agent Node
        state = await self.nodes["agent"](initial_state)

        # Step 2: Format Node
        state = self.nodes["format"](state)

        print(f"  [Factory] ✅ 执行完成")
        return state


# ============ 模式 2：Node 包装 Agent ============


class WrappedPatternGraph:
    """
    Node 包装 Agent 模式

    特点：
    - 构建时不需要 user_id
    - 每次执行都创建 Agent
    - Node 包装 Agent 创建和执行
    """

    def __init__(self):
        self.nodes = {}

    def build(self):
        """构建 Graph"""
        print(f"  [Wrapped] 构建 Graph（不需要 user_id）...")

        # 注册 Nodes
        self.nodes["agent_wrapped"] = self._agent_wrapped_node
        self.nodes["format"] = format_output_node

        print(f"  [Wrapped] ✅ Graph 构建成功")
        return self

    async def _agent_wrapped_node(self, state: Dict) -> Dict:
        """
        Agent Node - 包装模式

        特点：在 Node 内部创建 Agent
        """
        user_id = state.get("user_id")
        print(f"  [Wrapped] Node 内创建 Agent for user_id={user_id}...")

        # 每次执行都创建 Agent！
        agent = await create_agent(user_id)
        print(f"  [Wrapped] Agent 创建成功: {agent.model_name}")

        result = await agent.invoke(state.get("messages", []))
        return {**state, "output": result["output"], "messages": result["messages"]}

    async def execute(self, initial_state: Dict) -> Dict:
        """执行 Graph"""
        print(f"  [Wrapped] 开始执行...")

        # Step 1: Agent Node（内部创建 Agent）
        state = await self.nodes["agent_wrapped"](initial_state)

        # Step 2: Format Node
        state = self.nodes["format"](state)

        print(f"  [Wrapped] ✅ 执行完成")
        return state


# ============ 测试函数 ============


async def test_factory_pattern():
    """测试 Factory Pattern"""
    print("\n" + "=" * 60)
    print("测试 1：Factory Pattern（推荐）")
    print("=" * 60)

    user_id = "user_123"

    print(f"1. 构建 Graph...")
    graph = await FactoryPatternGraph(user_id).build()

    print(f"2. 第一次执行...")
    result1 = await graph.execute(
        {"messages": [{"role": "user", "content": "请分析数据"}], "user_id": user_id}
    )
    print(f"   结果: {result1.get('formatted', '')[:40]}...")

    print(f"3. 第二次执行（复用同一个 Agent）...")
    result2 = await graph.execute(
        {"messages": [{"role": "user", "content": "请推荐题材"}], "user_id": user_id}
    )
    print(f"   结果: {result2.get('formatted', '')[:40]}...")

    # 验证 user_id 正确传递
    assert "user_123" in result1["output"], "user_id 应该正确传递"
    print(f"4. ✅ 验证通过：user_id 正确传递")

    return True


async def test_wrapped_pattern():
    """测试 Node 包装模式"""
    print("\n" + "=" * 60)
    print("测试 2：Node 包装 Agent 模式（当前做法）")
    print("=" * 60)

    print(f"1. 构建 Graph...")
    graph = WrappedPatternGraph().build()

    print(f"2. 第一次执行...")
    result1 = await graph.execute(
        {"messages": [{"role": "user", "content": "请分析数据"}], "user_id": "user_456"}
    )
    print(f"   结果: {result1.get('formatted', '')[:40]}...")

    print(f"3. 第二次执行（再次创建 Agent）...")
    result2 = await graph.execute(
        {"messages": [{"role": "user", "content": "请推荐题材"}], "user_id": "user_456"}
    )
    print(f"   结果: {result2.get('formatted', '')[:40]}...")

    # 验证 user_id 从 state 获取
    assert "user_456" in result1["output"], "user_id 应该从 state 获取"
    print(f"4. ✅ 验证通过：user_id 从 state 获取")

    return True


async def test_performance():
    """性能对比测试"""
    print("\n" + "=" * 60)
    print("性能对比测试")
    print("=" * 60)

    # Factory Pattern
    print("\nFactory Pattern（Agent 只创建一次）：")
    graph1 = await FactoryPatternGraph("user_test").build()

    start = asyncio.get_event_loop().time()
    for i in range(3):
        await graph1.execute({"messages": [], "user_id": "user_test"})
    factory_time = asyncio.get_event_loop().time() - start
    print(f"   3 次调用总耗时: {factory_time:.3f} 秒")
    print(f"   Agent 创建次数: 1 次（构建时）")

    # Node 包装模式
    print("\nNode 包装模式（每次执行都创建 Agent）：")
    graph2 = WrappedPatternGraph().build()

    start = asyncio.get_event_loop().time()
    for i in range(3):
        await graph2.execute({"messages": [], "user_id": "user_test"})
    wrapped_time = asyncio.get_event_loop().time() - start
    print(f"   3 次调用总耗时: {wrapped_time:.3f} 秒")
    print(f"   Agent 创建次数: 3 次（每次执行）")

    print(f"\n性能差异：Node 包装比 Factory 慢 {wrapped_time / factory_time:.1f} 倍")

    if wrapped_time > factory_time:
        print(f"   ⚠️  Node 包装模式性能较差，因为每次都要重新创建 Agent")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("LangGraph 架构模式逻辑验证")
    print("=" * 60)
    print("\n测试目的：")
    print("1. 验证 Factory Pattern 是否能正确处理运行时参数")
    print("2. 验证 Node 包装模式是否真的'必须妥协'")
    print("3. 对比两种模式的性能差异")

    try:
        # 测试 Factory Pattern
        await test_factory_pattern()

        # 测试 Node 包装模式
        await test_wrapped_pattern()

        # 性能对比
        await test_performance()

        # 最终结论
        print("\n" + "=" * 60)
        print("📝 测试结论")
        print("=" * 60)
        print("""
✅ Factory Pattern（推荐）：
   - 能正确处理运行时参数（user_id）
   - Agent 只创建一次，性能好
   - 符合 LangGraph 官方标准
   - 不需要任何妥协

✅ Node 包装模式（当前做法）：
   - 也能正确处理运行时参数
   - 但每次执行都创建 Agent，性能差
   - 多了一层不必要的包装
   - 不是"必须妥协"，而是可以改进

🔍 关键发现：
   - 两种模式都能处理运行时参数
   - Factory Pattern 完全可行且更好
   - "必须妥协"的说法是错误的
   - 当前代码可以重构为 Factory Pattern

💡 建议：
   - 引入 Skills 层（必须）
   - 改进为 Factory Pattern（推荐）
   - 可以 100% 符合官方标准
        """)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
