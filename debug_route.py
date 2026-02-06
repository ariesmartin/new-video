#!/usr/bin/env python3
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

import asyncio
import json
from uuid import uuid4


async def debug():
    from backend.schemas.agent_state import create_initial_state, StageType
    from backend.graph.main_graph import create_main_graph, _route_from_start
    from backend.graph.checkpointer import get_checkpointer
    from backend.services.chat_init_service import prepare_initial_state

    checkpointer = await get_checkpointer()
    graph = create_main_graph(checkpointer)

    project_id = str(uuid4())
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # 冷启动
    state = create_initial_state("test-user", project_id, thread_id)
    state = prepare_initial_state(state, "你好，开始创作", is_cold_start=True)

    async for _ in graph.astream_events(state, config, version="v2"):
        pass

    # 选择赛道
    state2 = await graph.aget_state(config)
    select_msg = json.dumps(
        {
            "action": "select_genre",
            "payload": {"genre": "银发觉醒", "setting": "modern"},
        }
    )
    state2_prepared = prepare_initial_state(
        state2.values, select_msg, is_cold_start=False
    )
    await graph.aupdate_state(config, {"routed_agent": None})

    async for _ in graph.astream_events(state2_prepared, config, version="v2"):
        pass

    # 现在测试 random_plan
    state3 = await graph.aget_state(config)
    print("选择赛道后状态:")
    print(f"  current_stage: {state3.values.get('current_stage')}")
    print(f"  routed_agent: {state3.values.get('routed_agent')}")
    print(f"  approval_status: {state3.values.get('approval_status')}")
    print(f"  messages数量: {len(state3.values.get('messages', []))}")

    # 准备 random_plan
    random_msg = json.dumps({"action": "random_plan", "payload": {"genre": "银发觉醒"}})
    state3_prepared = prepare_initial_state(
        state3.values, random_msg, is_cold_start=False
    )

    print("\n准备 random_plan:")
    print(f"  messages数量: {len(state3_prepared.get('messages', []))}")

    # 检查最后一条消息
    last_msg = (
        state3_prepared.get("messages", [])[-1]
        if state3_prepared.get("messages")
        else None
    )
    if last_msg:
        print(f"  最后一条消息类型: {type(last_msg).__name__}")
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        print(f"  最后一条消息内容: {content[:100]}")

    # 测试路由
    route_result = _route_from_start(state3_prepared)
    print(f"\n路由结果: {route_result}")


asyncio.run(debug())
