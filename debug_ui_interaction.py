"""
调试 ui_interaction 保存问题 - 简化版
"""

import asyncio
import sys
sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.graph.checkpointer import checkpointer_manager, get_or_create_checkpointer


async def check_ui_interaction():
    """检查 checkpoint 中是否保存了 ui_interaction"""
    print("🔍 检查 checkpoint 中的 ui_interaction...\n")
    
    # 使用从截图观察到的 thread_id
    thread_id = "thread-1770374333551-e9te81fuc"
    
    await checkpointer_manager.initialize()
    checkpointer, conn = await get_or_create_checkpointer()
    
    try:
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = await checkpointer.aget_tuple(config)
        
        if not checkpoint_tuple:
            print(f"❌ 未找到 thread_id={thread_id} 的 checkpoint")
            return
        
        checkpoint = checkpoint_tuple.checkpoint
        channel_values = checkpoint.get("channel_values", {})
        
        print(f"📌 Thread ID: {thread_id}")
        print(f"   channel_values 的键: {list(channel_values.keys())}")
        
        # 检查 ui_interaction 作为独立字段
        ui_interaction = channel_values.get("ui_interaction")
        print(f"\n1️⃣ ui_interaction 字段:")
        print(f"   类型: {type(ui_interaction)}")
        print(f"   是否存在: {ui_interaction is not None}")
        
        if ui_interaction:
            if isinstance(ui_interaction, dict):
                print(f"   键: {list(ui_interaction.keys())}")
                print(f"   block_type: {ui_interaction.get('block_type')}")
        
        # 检查 messages
        messages = channel_values.get("messages", [])
        print(f"\n2️⃣ messages 数量: {len(messages)}")
        
        # 检查每条消息中是否有 ui_interaction
        for i, msg in enumerate(messages[:5]):  # 只检查前5条
            print(f"\n   消息 {i}:")
            print(f"   类型: {type(msg)}")
            
            # 检查 additional_kwargs
            additional_kwargs = None
            if hasattr(msg, 'additional_kwargs'):
                additional_kwargs = msg.additional_kwargs
            elif isinstance(msg, dict):
                if 'data' in msg:
                    additional_kwargs = msg.get('data', {}).get('additional_kwargs', {})
                elif 'additional_kwargs' in msg:
                    additional_kwargs = msg.get('additional_kwargs', {})
            
            if additional_kwargs:
                print(f"   additional_kwargs 键: {list(additional_kwargs.keys())}")
                if 'ui_interaction' in additional_kwargs:
                    ui = additional_kwargs['ui_interaction']
                    print(f"   ✅ 消息中有 ui_interaction!")
                    if isinstance(ui, dict):
                        print(f"      block_type: {ui.get('block_type')}")
                        
    finally:
        await checkpointer_manager._pool.putconn(conn)


if __name__ == "__main__":
    asyncio.run(check_ui_interaction())
