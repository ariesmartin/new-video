#!/usr/bin/env python3
"""
测试 checkpointer 是否能正确保存和读取
"""

import asyncio
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")


async def test_checkpointer():
    from backend.graph.checkpointer import get_or_create_checkpointer

    print("初始化 checkpointer...")
    checkpointer = await get_or_create_checkpointer()

    if not checkpointer:
        print("❌ checkpointer 初始化失败")
        return

    print(f"✅ checkpointer 初始化成功: {type(checkpointer)}")

    thread_id = "test-checkpointer-001"
    config = {"configurable": {"thread_id": thread_id}}

    # 测试保存
    print(f"\n测试保存状态到 thread: {thread_id}")
    test_state = {
        "messages": [{"role": "assistant", "content": "Test message"}],
        "ui_interaction": {
            "block_type": "action_group",
            "title": "Test",
            "buttons": [],
        },
    }

    try:
        await checkpointer.aput(config, test_state)
        print("✅ 保存成功")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        import traceback

        traceback.print_exc()
        return

    # 测试读取
    print(f"\n测试读取状态从 thread: {thread_id}")
    try:
        checkpoint = await checkpointer.aget(config)
        if checkpoint:
            print(f"✅ 读取成功")
            print(f"   数据: {checkpoint}")
        else:
            print("⚠️  读取成功但数据为空")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_checkpointer())
