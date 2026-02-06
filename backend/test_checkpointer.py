"""
Test Checkpointer

验证 AsyncPostgresSaver 的初始化和基本功能。
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone

# 添加项目根目录到路径
sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

import structlog
from langchain_core.messages import HumanMessage, AIMessage

from backend.config import settings
from backend.graph.checkpointer import (
    checkpointer_manager,
    init_checkpointer,
    close_checkpointer,
    get_checkpointer,
)
from backend.schemas.agent_state import AgentState, create_initial_state

logger = structlog.get_logger(__name__)


async def test_checkpointer_initialization():
    """测试 Checkpointer 初始化"""
    print("\n" + "=" * 60)
    print("测试 1: Checkpointer 初始化")
    print("=" * 60)

    try:
        await init_checkpointer()
        health = await checkpointer_manager.health_check()
        print(f"✅ Checkpointer 初始化成功")
        print(f"   状态: {health['status']}")
        print(f"   连接池大小: {health['pool_size']}")
        print(f"   可用连接: {health['available']}")
        return True
    except Exception as e:
        print(f"❌ Checkpointer 初始化失败: {e}")
        return False


async def test_checkpoint_save_and_load():
    """测试保存和加载检查点"""
    print("\n" + "=" * 60)
    print("测试 2: 检查点保存和加载")
    print("=" * 60)

    try:
        # 创建测试配置
        thread_id = f"test_{uuid.uuid4().hex[:8]}"
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": "",
            }
        }

        # 创建测试状态
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        project_id = f"project_{uuid.uuid4().hex[:8]}"
        state = create_initial_state(user_id, project_id, thread_id)

        # 添加测试消息
        state["messages"] = [
            HumanMessage(content="Hello, this is a test message"),
            AIMessage(content="This is a test response from AI"),
        ]
        state["current_stage"] = "L1"

        async with get_checkpointer() as saver:
            # 保存检查点
            checkpoint = {
                "v": 4,
                "ts": datetime.utcnow().isoformat() + "+00:00",
                "id": str(uuid.uuid4()),
                "channel_values": state,
                "channel_versions": {"__start__": 1, "messages": 2},
                "versions_seen": {"__input__": {}, "__start__": {"__start__": 1}},
            }

            await saver.aput(config, checkpoint, {}, {})
            print(f"✅ 检查点保存成功 (thread_id: {thread_id})")

            # 加载检查点
            loaded = await saver.aget(config)
            if loaded:
                print(f"✅ 检查点加载成功")
                print(f"   版本: {loaded.get('v')}")
                print(f"   时间戳: {loaded.get('ts')}")
                return True
            else:
                print(f"❌ 检查点加载失败: 返回 None")
                return False

    except Exception as e:
        print(f"❌ 检查点操作失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_checkpoint_list():
    """测试列出检查点"""
    print("\n" + "=" * 60)
    print("测试 3: 列出检查点")
    print("=" * 60)

    try:
        thread_id = f"test_{uuid.uuid4().hex[:8]}"
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": "",
            }
        }

        # 创建多个检查点
        async with get_checkpointer() as saver:
            for i in range(3):
                checkpoint = {
                    "v": 4,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "id": str(uuid.uuid4()),
                    "channel_values": {"test": f"value_{i}"},
                    "channel_versions": {"__start__": i + 1},
                    "versions_seen": {},
                }
                await saver.aput(config, checkpoint, {}, {})

            # 列出检查点
            checkpoints = []
            async for cp in saver.alist(config):
                checkpoints.append(cp)

            print(f"✅ 成功列出 {len(checkpoints)} 个检查点")
            return True

    except Exception as e:
        print(f"❌ 列出检查点失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_cleanup():
    """测试清理资源"""
    print("\n" + "=" * 60)
    print("测试 4: 资源清理")
    print("=" * 60)

    try:
        await close_checkpointer()
        health = await checkpointer_manager.health_check()

        if health["status"] == "not_initialized":
            print(f"✅ 资源清理成功")
            return True
        else:
            print(f"❌ 资源清理不完全")
            return False

    except Exception as e:
        print(f"❌ 资源清理失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 LangGraph Checkpointer 测试套件")
    print("=" * 70)
    print(f"数据库 URL: {settings.database_url}")

    results = []

    # 测试1: 初始化
    results.append(("初始化", await test_checkpointer_initialization()))

    # 测试2: 保存和加载
    results.append(("保存/加载", await test_checkpoint_save_and_load()))

    # 测试3: 列出检查点
    results.append(("列出检查点", await test_checkpoint_list()))

    # 测试4: 清理
    results.append(("资源清理", await test_cleanup()))

    # 打印总结
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status}: {name}")

    print("\n" + "-" * 70)
    print(f"总计: {passed}/{total} 测试通过 ({passed / total * 100:.1f}%)")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
