"""
端到端测试：验证 Skeleton Builder 完整流程

测试步骤：
1. 创建测试项目
2. 调用大纲生成API
3. 监控执行流程
4. 验证消息序列
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


async def test_skeleton_builder_e2e():
    """端到端测试 Skeleton Builder"""

    print("=" * 80)
    print("端到端测试：Skeleton Builder")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Step 1: 健康检查
        print("\n[Step 1] 健康检查...")
        try:
            resp = await client.get(f"{BASE_URL}/api/health")
            if resp.status_code == 200:
                print("✅ 服务正常运行")
            else:
                print(f"⚠️  服务状态异常: {resp.status_code}")
        except Exception as e:
            print(f"❌ 服务未启动: {e}")
            return

        # Step 2: 创建测试项目
        print("\n[Step 2] 创建测试项目...")
        project_data = {
            "title": "测试短剧 - 复仇逆袭",
            "genre": "revenge",
            "setting": "modern",
            "total_episodes": 80,
            "episode_duration": 2,
            "ending_type": "HE",
            "description": "一个关于复仇的短剧",
        }

        try:
            resp = await client.post(f"{BASE_URL}/api/projects", json=project_data)
            if resp.status_code == 201:
                project = resp.json()
                project_id = project["data"]["id"]
                print(f"✅ 项目创建成功: {project_id}")
            else:
                print(f"⚠️  使用已有项目")
                project_id = (
                    "1b1c349b-5567-414f-8d09-53fc26a36d51"  # 使用日志中的项目ID
                )
        except Exception as e:
            print(f"⚠️  使用默认项目ID: {e}")
            project_id = "1b1c349b-5567-414f-8d09-53fc26a36d51"

        # Step 3: 调用大纲生成
        print(f"\n[Step 3] 调用大纲生成 API...")
        print(f"   项目ID: {project_id}")

        skeleton_request = {
            "projectId": project_id,
            "planId": "test-plan-001",
            "userInput": "请生成一个关于复仇逆袭的故事大纲",
        }

        print(f"\n   请求参数:")
        print(f"   - 项目ID: {skeleton_request['projectId']}")
        print(f"   - 方案ID: {skeleton_request['planId']}")
        print(f"   - 用户输入: {skeleton_request['userInput']}")

        try:
            print(f"\n   发送请求...")
            resp = await client.post(
                f"{BASE_URL}/api/skeleton/generate",
                json=skeleton_request,
                timeout=300.0,
            )

            print(f"\n   响应状态: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print(f"\n✅ API 调用成功!")
                print(f"   结果键: {list(result.keys())}")

                if "data" in result:
                    data = result["data"]
                    print(f"\n   生成结果:")
                    print(f"   - 内容长度: {len(data.get('skeleton_content', ''))}")
                    print(f"   - 最后成功节点: {data.get('last_successful_node')}")
                    print(f"   - 是否有错误: {data.get('error')}")

                    # 检查消息
                    messages = data.get("messages", [])
                    if messages:
                        print(f"\n   消息序列 ({len(messages)} 条):")
                        for i, msg in enumerate(messages[-5:]):  # 显示最后5条
                            msg_type = msg.get("type", "Unknown")
                            content_len = (
                                len(msg.get("content", "")) if msg.get("content") else 0
                            )
                            has_tool_calls = "tool_calls" in msg
                            print(
                                f"   - {i}: {msg_type} (内容{content_len}字, tool_calls={has_tool_calls})"
                            )

            else:
                print(f"\n❌ API 调用失败")
                print(f"   状态码: {resp.status_code}")
                print(f"   响应: {resp.text[:500]}")

        except asyncio.TimeoutError:
            print(f"\n⏱️  请求超时 (300秒)")
        except Exception as e:
            print(f"\n❌ 请求失败: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_skeleton_builder_e2e())
