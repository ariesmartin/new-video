#!/usr/bin/env python3
"""
独立测试 - 验证 LangGraph checkpointer 的正确用法
按照官方文档和搜索结果创建
"""

import asyncio
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")


async def test_with_json_plus_serde():
    """使用 JsonPlusSerializer 测试"""
    print("=" * 80)
    print("测试1: 使用 JsonPlusSerializer")
    print("=" * 80)

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    # 数据库连接字符串
    DB_URI = "postgresql://postgres:postgres@192.168.2.70:9000/postgres"

    # 使用 JsonPlusSerializer 初始化
    checkpointer = AsyncPostgresSaver.from_conn_string(
        DB_URI, serde=JsonPlusSerializer(pickle_fallback=True)
    )

    thread_id = "test-json-plus-001"
    write_config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    read_config = {"configurable": {"thread_id": thread_id}}

    # 准备数据 - 包含 list 和 dict
    checkpoint = {
        "v": 1,
        "ts": "2024-01-01T00:00:00",
        "id": "test-id-001",
        "channel_values": {
            "messages": [{"role": "ai", "content": "Hello"}],  # list
            "ui_interaction": {"buttons": []},  # dict
            "text": "simple string",
            "number": 42,
        },
        "channel_versions": {},
        "versions_seen": {},
    }

    try:
        # 正确使用 async context manager
        async with checkpointer as saver:
            await saver.setup()
            await saver.aput(write_config, checkpoint, {}, {})
            print("✅ Saved successfully")

            # 读取
            result = await saver.aget(read_config)
            if result:
                cv = result.get("channel_values", {})
                print(f"Keys: {list(cv.keys())}")
                print(f"messages exists: {'messages' in cv}")
                print(f"messages: {cv.get('messages')}")
                print(f"ui_interaction exists: {'ui_interaction' in cv}")
            else:
                print("❌ No checkpoint found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


async def test_standard_serde():
    """使用标准 serde 测试（不指定 serde）"""
    print("\n" + "=" * 80)
    print("测试2: 使用标准 serde（当前代码使用的方式）")
    print("=" * 80)

    from backend.graph.checkpointer import get_or_create_checkpointer

    checkpointer = await get_or_create_checkpointer()
    thread_id = "test-standard-001"
    write_config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    read_config = {"configurable": {"thread_id": thread_id}}

    checkpoint = {
        "v": 1,
        "ts": "2024-01-01T00:00:00",
        "id": "test-id-002",
        "channel_values": {
            "messages": [{"role": "ai", "content": "Hello"}],
            "ui_interaction": {"buttons": []},
            "text": "simple string",
        },
        "channel_versions": {},
        "versions_seen": {},
    }

    try:
        await checkpointer.aput(write_config, checkpoint, {}, {})
        print("✅ Saved successfully")

        result = await checkpointer.aget(read_config)
        if result:
            cv = result.get("channel_values", {})
            print(f"Keys: {list(cv.keys())}")
            print(f"messages exists: {'messages' in cv}")
            print(f"messages: {cv.get('messages')}")
        else:
            print("❌ No checkpoint found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


async def test_with_new_versions():
    """测试 new_versions 参数"""
    print("\n" + "=" * 80)
    print("测试3: 使用 new_versions 参数")
    print("=" * 80)

    from backend.graph.checkpointer import get_or_create_checkpointer

    checkpointer = await get_or_create_checkpointer()
    thread_id = "test-versions-001"
    write_config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    read_config = {"configurable": {"thread_id": thread_id}}

    checkpoint = {
        "v": 1,
        "ts": "2024-01-01T00:00:00",
        "id": "test-id-003",
        "channel_values": {
            "messages": [{"role": "ai", "content": "Hello"}],
            "ui_interaction": {"buttons": []},
        },
        "channel_versions": {},
        "versions_seen": {},
    }

    # 设置 new_versions
    metadata = {"source": "test", "step": 0, "writes": {}}
    new_versions = {
        "messages": 1,
        "ui_interaction": 1,
    }

    try:
        await checkpointer.aput(write_config, checkpoint, metadata, new_versions)
        print("✅ Saved with new_versions")

        result = await checkpointer.aget(read_config)
        if result:
            cv = result.get("channel_values", {})
            print(f"Keys: {list(cv.keys())}")
            print(f"messages exists: {'messages' in cv}")
            print(f"messages: {cv.get('messages')}")
        else:
            print("❌ No checkpoint found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


async def main():
    print("LangGraph Checkpointer 独立测试")
    print("=" * 80)

    await test_with_json_plus_serde()
    await test_standard_serde()
    await test_with_new_versions()

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
