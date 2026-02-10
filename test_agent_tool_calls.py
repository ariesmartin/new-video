"""
测试脚本：验证 create_react_agent 工具调用流程

这个脚本会模拟真实的调用场景，验证：
1. 工具是否正确注册
2. ToolMessage 是否正确生成
3. 消息序列是否完整
"""

import asyncio
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.skills.theme_library import (
    load_genre_context,
    search_elements_by_effectiveness,
    get_hook_templates_by_type,
    analyze_genre_compatibility,
)


async def test_tool_calls():
    """测试工具调用流程"""

    print("=" * 80)
    print("测试 create_react_agent 工具调用流程")
    print("=" * 80)

    # 创建 Gemini 模型
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key="YOUR_API_KEY",  # 需要替换为真实的 API key
        temperature=0.7,
    )

    # 创建工具列表
    tools = [
        load_genre_context,
        search_elements_by_effectiveness,
        get_hook_templates_by_type,
        analyze_genre_compatibility,
    ]

    print(f"\n1. 工具列表:")
    for i, tool in enumerate(tools):
        print(f"   {i + 1}. {tool.name}")

    # 创建 Agent
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt="你是一个测试助手。请调用 load_genre_context 工具查询 'revenge' 题材的信息。",
    )

    print(f"\n2. Agent 创建成功")

    # 测试调用
    messages = [HumanMessage(content="请查询 revenge 题材的信息")]

    print(f"\n3. 初始消息:")
    for i, msg in enumerate(messages):
        print(f"   {i}: {type(msg).__name__} - {msg.content[:50]}...")

    print(f"\n4. 调用 Agent...")

    try:
        result = await agent.ainvoke({"messages": messages})

        print(f"\n5. Agent 返回结果:")
        output_messages = result.get("messages", [])
        print(f"   消息数量: {len(output_messages)}")

        for i, msg in enumerate(output_messages):
            msg_type = type(msg).__name__
            content_preview = (
                msg.content[:80]
                if hasattr(msg, "content") and msg.content
                else "(无内容)"
            )
            has_tool_calls = bool(getattr(msg, "tool_calls", None))

            print(f"   {i}: {msg_type}")
            print(f"      内容: {content_preview}...")
            print(f"      有 tool_calls: {has_tool_calls}")

            if has_tool_calls:
                for tc in msg.tool_calls:
                    print(f"      - Tool: {tc.get('name')}, ID: {tc.get('id')}")

        # 验证消息序列
        print(f"\n6. 消息序列验证:")
        errors = []

        for i, msg in enumerate(output_messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                # 检查下一个消息是否是 ToolMessage
                if i + 1 < len(output_messages):
                    next_msg = output_messages[i + 1]
                    if not isinstance(next_msg, ToolMessage):
                        errors.append(
                            f"消息 {i} 有 tool_calls，但消息 {i + 1} 不是 ToolMessage (是 {type(next_msg).__name__})"
                        )
                else:
                    errors.append(
                        f"消息 {i} 有 tool_calls，但没有对应的 ToolMessage (消息列表结束)"
                    )

        if errors:
            print("   ❌ 发现问题:")
            for error in errors:
                print(f"      - {error}")
        else:
            print("   ✅ 消息序列正确")

        # 检查是否有连续的 AIMessage
        consecutive_ai = []
        last_was_ai = False
        for i, msg in enumerate(output_messages):
            if isinstance(msg, AIMessage):
                if last_was_ai:
                    consecutive_ai.append(i)
                last_was_ai = True
            else:
                last_was_ai = False

        if consecutive_ai:
            print(f"\n   ⚠️  发现连续的 AIMessage 在位置: {consecutive_ai}")
        else:
            print(f"\n   ✅ 没有连续的 AIMessage")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tool_calls())
