#!/usr/bin/env python3
"""
测试新的 save_state 和 load_state 辅助函数
"""

import asyncio
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")


async def test_save_load():
    from backend.graph.checkpointer import (
        save_state,
        load_state,
        init_checkpointer,
        close_checkpointer,
    )

    print("初始化 checkpointer...")
    await init_checkpointer()

    thread_id = "test-save-load-001"
    config = {"configurable": {"thread_id": thread_id}}

    # 测试保存
    print(f"\n测试保存状态到 thread: {thread_id}")
    test_state = {
        "messages": [{"role": "assistant", "content": "Test welcome message"}],
        "ui_interaction": {
            "block_type": "action_group",
            "title": "Test",
            "buttons": [{"label": "Test", "action": "test"}],
        },
    }

    success = await save_state(config, test_state)
    if success:
        print("✅ 保存成功")
    else:
        print("❌ 保存失败")
        return

    # 测试读取
    print(f"\n测试读取状态从 thread: {thread_id}")
    loaded = await load_state(config)
    if loaded:
        print(f"✅ 读取成功")
        print(f"   messages: {loaded.get('messages')}")
        print(f"   has ui_interaction: {loaded.get('ui_interaction') is not None}")
    else:
        print("⚠️  读取成功但数据为空")

    await close_checkpointer()
    print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_save_load())
