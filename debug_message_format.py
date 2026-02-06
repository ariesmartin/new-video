"""
调试消息格式问题 - 找出消息在哪个环节变成字典格式
"""

import asyncio
import sys
sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.graph.checkpointer import checkpointer_manager, get_or_create_checkpointer
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langchain_core.messages import AIMessage, HumanMessage
import json


async def test_serialization():
    """测试 JsonPlusSerializer 的序列化和反序列化"""
    print("=" * 60)
    print("测试 1: JsonPlusSerializer 序列化/反序列化")
    print("=" * 60)
    
    serde = JsonPlusSerializer(pickle_fallback=True)
    
    # 创建测试消息
    ai_msg = AIMessage(
        content="你好！我是你的 AI 创作助手。",
        additional_kwargs={"is_welcome": True}
    )
    
    print(f"\n原始消息类型: {type(ai_msg)}")
    print(f"原始消息内容: {ai_msg.content[:50]}...")
    
    # 使用正确的 API: dumps_typed / loads_typed
    try:
        serialized = serde.dumps_typed(ai_msg)
        print(f"\n序列化后类型: {type(serialized)}")
        print(f"序列化后内容 (tuple): {serialized[0]}, {str(serialized[1])[:100]}...")
        
        # 反序列化
        deserialized = serde.loads_typed(serialized)
        print(f"\n反序列化后类型: {type(deserialized)}")
        print(f"反序列化后是 AIMessage: {isinstance(deserialized, AIMessage)}")
        
        if isinstance(deserialized, dict):
            print(f"反序列化后是字典，键: {list(deserialized.keys())}")
        
        return isinstance(deserialized, AIMessage)
    except Exception as e:
        print(f"\n序列化/反序列化失败: {e}")
        return False


async def test_checkpoint_read():
    """测试从 checkpoint 读取消息的格式"""
    print("\n" + "=" * 60)
    print("测试 2: 从 Checkpoint 读取消息格式")
    print("=" * 60)
    
    # 使用一个已知的 thread_id
    thread_id = "thread-1770374333551-e9te81fuc"  # 从错误日志获取
    
    await checkpointer_manager.initialize()
    checkpointer, conn = await get_or_create_checkpointer()
    
    try:
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": "",
            }
        }
        
        # 获取最新的 checkpoint
        checkpoint_tuple = await checkpointer.aget_tuple(config)
        
        if checkpoint_tuple:
            print(f"\n找到 checkpoint!")
            checkpoint = checkpoint_tuple.checkpoint
            channel_values = checkpoint.get("channel_values", {})
            
            messages = channel_values.get("messages", [])
            print(f"消息数量: {len(messages)}")
            
            for i, msg in enumerate(messages):
                print(f"\n消息 {i}:")
                print(f"  类型: {type(msg)}")
                print(f"  是 AIMessage: {isinstance(msg, AIMessage)}")
                print(f"  是 dict: {isinstance(msg, dict)}")
                
                if isinstance(msg, dict):
                    print(f"  字典键: {list(msg.keys())}")
                    if "type" in msg:
                        print(f"  type 字段: {msg.get('type')}")
                elif hasattr(msg, 'content'):
                    print(f"  content: {msg.content[:50]}...")
        else:
            print(f"\n未找到 thread_id={thread_id} 的 checkpoint")
            print("尝试列出所有可用的 checkpoints...")
            
            # 列出所有 checkpoints
            count = 0
            async for cp in checkpointer.alist(None):
                print(f"  - thread_id: {cp.config.get('configurable', {}).get('thread_id', 'N/A')}")
                count += 1
                if count >= 3:
                    break
                
    finally:
        await checkpointer_manager._pool.putconn(conn)


async def test_add_messages_behavior():
    """测试 add_messages reducer 的行为"""
    print("\n" + "=" * 60)
    print("测试 3: add_messages reducer 行为")
    print("=" * 60)
    
    from langgraph.graph.message import add_messages
    
    # 模拟从 checkpoint 恢复的字典格式消息 (LangChain 序列化格式)
    dict_message = {
        'type': 'ai', 
        'data': {
            'content': '你好！我是你的 AI 创作助手。',
            'additional_kwargs': {'is_welcome': True}
        }
    }
    
    # 测试 add_messages 是否能处理这种格式
    print(f"\n测试消息格式: {{'type': 'ai', 'data': ...}}")
    try:
        result = add_messages([], [dict_message])
        print(f"  ✅ 成功! 结果类型: {type(result[0]) if result else 'N/A'}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
    
    # 测试 OpenAI 风格的消息
    openai_message = {
        'role': 'assistant',
        'content': '你好！我是你的 AI 创作助手。'
    }
    
    print(f"\n测试消息格式: {{'role': 'assistant', 'content': ...}}")
    try:
        result = add_messages([], [openai_message])
        print(f"  ✅ 成功! 结果类型: {type(result[0]) if result else 'N/A'}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 测试 AIMessage 对象
    ai_msg = AIMessage(content="测试")
    print(f"\n测试消息格式: AIMessage 对象")
    try:
        result = add_messages([], [ai_msg])
        print(f"  ✅ 成功! 结果类型: {type(result[0]) if result else 'N/A'}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")


async def main():
    print("\n🔍 开始调试消息格式问题\n")
    
    # 测试 1: 序列化器
    serde_ok = await test_serialization()
    
    # 测试 2: Checkpoint 读取
    await test_checkpoint_read()
    
    # 测试 3: add_messages 行为
    await test_add_messages_behavior()
    
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    if not serde_ok:
        print("❌ JsonPlusSerializer 反序列化未返回 AIMessage 对象")
        print("   这可能是问题根源！")
    else:
        print("✅ JsonPlusSerializer 正确还原 AIMessage 对象")
        print("\n问题可能出在:")
        print("   1. checkpoint 存储时格式不对")
        print("   2. add_messages reducer 未被正确调用")
        print("   3. 消息在其他环节被转换为字典")


if __name__ == "__main__":
    asyncio.run(main())
