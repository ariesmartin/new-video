#!/usr/bin/env python3
"""
集成测试脚本 - 测试后端 API
需要后端服务运行在 localhost:8000
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


async def test_chat_init_cold_start():
    """测试冷启动 - 新项目"""
    print("\n" + "=" * 80)
    print("测试1: 冷启动（新项目）")
    print("=" * 80)

    async with aiohttp.ClientSession() as session:
        payload = {
            "user_id": f"test-user-{datetime.now().timestamp()}",
            "project_id": f"test-project-{datetime.now().timestamp()}",
            "session_id": f"test-thread-{datetime.now().timestamp()}",
        }

        print(f"请求: POST /api/graph/chat/init")
        print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        try:
            async with session.post(
                f"{BASE_URL}/api/graph/chat/init", json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"\n✅ 成功 (状态码: {resp.status})")
                    print(f"is_cold_start: {data.get('is_cold_start')}")
                    print(f"messages 数量: {len(data.get('messages', []))}")

                    if data.get("messages"):
                        first_msg = data["messages"][0]
                        print(f"\n第一条消息:")
                        print(f"  - role: {first_msg.get('role')}")
                        print(f"  - content: {first_msg.get('content', '')[:100]}...")
                        print(
                            f"  - has ui_interaction: {first_msg.get('ui_interaction') is not None}"
                        )

                        # 检查 content 是否包含 JSON
                        content = first_msg.get("content", "")
                        if content.startswith("{") and "thought_process" in content:
                            print(
                                f"\n❌ 错误: 消息内容仍然包含原始 JSON，未提取 ui_feedback!"
                            )
                        else:
                            print(f"\n✅ 消息内容已正确格式化")

                    return data
                else:
                    print(f"\n❌ 失败 (状态码: {resp.status})")
                    text = await resp.text()
                    print(f"响应: {text}")
                    return None
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return None


async def test_chat_init_with_history(thread_id: str, user_id: str, project_id: str):
    """测试带历史记录的初始化"""
    print("\n" + "=" * 80)
    print("测试2: 带历史记录的初始化（模拟刷新页面）")
    print("=" * 80)

    async with aiohttp.ClientSession() as session:
        payload = {
            "user_id": user_id,
            "project_id": project_id,
            "session_id": thread_id,
        }

        print(f"请求: POST /api/graph/chat/init")
        print(f"使用相同的 thread_id: {thread_id}")

        try:
            async with session.post(
                f"{BASE_URL}/api/graph/chat/init", json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"\n✅ 成功 (状态码: {resp.status})")
                    print(f"is_cold_start: {data.get('is_cold_start')}")
                    print(f"messages 数量: {len(data.get('messages', []))}")

                    if not data.get("is_cold_start"):
                        print(f"✅ 正确识别为有历史记录")

                        # 检查每条消息的格式
                        for idx, msg in enumerate(data.get("messages", [])):
                            content = msg.get("content", "")
                            if content.startswith("{") and "thought_process" in content:
                                print(f"\n❌ 消息 {idx} 仍包含原始 JSON:")
                                print(f"   {content[:200]}...")
                            else:
                                print(
                                    f"\n✅ 消息 {idx} 已正确格式化: {content[:80]}..."
                                )
                    else:
                        print(f"⚠️  仍然返回冷启动（历史记录可能未保存）")

                    return data
                else:
                    print(f"\n❌ 失败 (状态码: {resp.status})")
                    return None
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return None


async def test_send_message_sse(
    thread_id: str, user_id: str, project_id: str, message: str
):
    """测试发送消息（SSE 流式）"""
    print("\n" + "=" * 80)
    print(f"测试3: 发送消息 (SSE 流式)")
    print("=" * 80)

    params = {
        "message": message,
        "project_id": project_id,
        "thread_id": thread_id,
        "user_id": user_id,
    }

    print(f"请求: GET /api/graph/chat")
    print(f"Params: {params}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/graph/chat", params=params) as resp:
                if resp.status == 200:
                    print(f"\n✅ 连接成功 (状态码: {resp.status})")
                    print("\n接收到的流式数据:")
                    print("-" * 80)

                    content_buffer = ""
                    async for line in resp.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data_str = line[6:]  # 去掉 'data: ' 前缀
                            try:
                                data = json.loads(data_str)
                                event_type = data.get("type")

                                if event_type == "token":
                                    content = data.get("content", "")
                                    content_buffer += content
                                    print(content, end="", flush=True)
                                elif event_type == "done":
                                    print(f"\n\n✅ 流式输出完成")
                                    print(f"总内容长度: {len(content_buffer)} 字符")

                                    # 检查内容是否包含 JSON
                                    if (
                                        content_buffer.startswith("{")
                                        and "thought_process" in content_buffer
                                    ):
                                        print(f"\n❌ 错误: 流式内容包含原始 JSON!")
                                        print(f"内容: {content_buffer[:200]}...")
                                    else:
                                        print(f"✅ 流式内容已正确格式化")

                                    return True
                                elif event_type == "error":
                                    print(f"\n❌ 错误: {data.get('message')}")
                                    return False
                            except json.JSONDecodeError:
                                continue
                else:
                    print(f"\n❌ 失败 (状态码: {resp.status})")
                    text = await resp.text()
                    print(f"响应: {text}")
                    return False
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("开始集成测试")
    print(f"目标: {BASE_URL}")
    print("=" * 80)

    # 生成测试 ID
    timestamp = int(datetime.now().timestamp())
    user_id = f"test-user-{timestamp}"
    project_id = f"test-project-{timestamp}"
    thread_id = f"test-thread-{timestamp}"

    print(f"\n测试参数:")
    print(f"  user_id: {user_id}")
    print(f"  project_id: {project_id}")
    print(f"  thread_id: {thread_id}")

    # 测试1: 冷启动
    init_data = await test_chat_init_cold_start()
    if not init_data:
        print("\n❌ 冷启动测试失败，停止后续测试")
        return

    # 测试2: 发送消息
    success = await test_send_message_sse(
        thread_id, user_id, project_id, "开始创作短剧"
    )

    if not success:
        print("\n⚠️  发送消息测试失败，继续测试历史记录...")

    # 等待一小段时间确保数据保存
    print("\n⏳ 等待 2 秒确保数据保存到 checkpointer...")
    await asyncio.sleep(2)

    # 测试3: 刷新后获取历史
    await test_chat_init_with_history(thread_id, user_id, project_id)

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    # 检查依赖
    try:
        import aiohttp
    except ImportError:
        print("请先安装 aiohttp: pip install aiohttp")
        exit(1)

    print("\n确保后端服务已启动: python -m uvicorn main:app --reload")
    print("按 Enter 开始测试...")
    input()

    asyncio.run(run_all_tests())
