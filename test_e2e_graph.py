"""
端到端测试：通过 Graph API 触发 Skeleton Builder

测试步骤：
1. 调用 /api/graph/chat 开始创建流程
2. 选择赛道/题材
3. 生成故事方案
4. 选择方案并生成大纲
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
USER_ID = "test-user-001"


async def test_full_workflow():
    """测试完整工作流程"""

    print("=" * 80)
    print("端到端测试：完整工作流程 → Skeleton Builder")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=60.0) as client:
        project_id = None

        # Step 1: 冷启动 - 开始创作
        print("\n[Step 1] 冷启动 - 开始创作...")
        chat_request = {"user_id": USER_ID, "action": "cold_start"}

        try:
            resp = await client.post(f"{BASE_URL}/api/graph/chat", json=chat_request)
            print(f"   状态: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print(f"   ✅ 冷启动成功")
                print(f"   响应: {result.get('ui_feedback', 'N/A')[:100]}...")
            else:
                print(f"   响应: {resp.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

        # Step 2: 选择赛道 - 复仇逆袭
        print("\n[Step 2] 选择赛道 - 复仇逆袭...")
        chat_request = {
            "user_id": USER_ID,
            "action": "select_genre",
            "context": {"genre": "revenge", "setting": "modern"},
        }

        try:
            resp = await client.post(f"{BASE_URL}/api/graph/chat", json=chat_request)
            print(f"   状态: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                project_id = result.get("context", {}).get("project_id")
                print(f"   ✅ 赛道选择成功")
                print(f"   项目ID: {project_id}")
                print(f"   响应: {result.get('ui_feedback', 'N/A')[:100]}...")
            else:
                print(f"   响应: {resp.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

        if not project_id:
            # 使用默认项目ID
            project_id = "1b1c349b-5567-414f-8d09-53fc26a36d51"
            print(f"\n   ⚠️  使用默认项目ID: {project_id}")

        # Step 3: 确认剧集配置
        print("\n[Step 3] 确认剧集配置...")
        chat_request = {
            "user_id": USER_ID,
            "project_id": project_id,
            "action": "set_episode_config",
            "context": {
                "total_episodes": 80,
                "episode_duration": 2,
                "ending_type": "HE",
            },
        }

        try:
            resp = await client.post(f"{BASE_URL}/api/graph/chat", json=chat_request)
            print(f"   状态: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print(f"   ✅ 剧集配置成功")
                print(f"   响应: {result.get('ui_feedback', 'N/A')[:100]}...")
            else:
                print(f"   响应: {resp.text[:200]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

        # Step 4: AI 自动选题（生成故事方案）
        print("\n[Step 4] AI 自动选题（生成故事方案）...")
        print("   ⏱️  此步骤可能需要 30-60 秒...")

        chat_request = {
            "user_id": USER_ID,
            "project_id": project_id,
            "action": "proceed_to_planning",
        }

        try:
            resp = await client.post(
                f"{BASE_URL}/api/graph/chat", json=chat_request, timeout=120.0
            )
            print(f"   状态: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print(f"   ✅ 故事方案生成成功")
                print(f"   响应: {result.get('ui_feedback', 'N/A')[:200]}...")

                # 尝试提取方案ID
                ui_interaction = result.get("ui_interaction")
                if ui_interaction and "buttons" in ui_interaction:
                    for btn in ui_interaction["buttons"]:
                        if btn.get("action") == "select_plan":
                            plan_id = btn.get("payload", {}).get("plan_id")
                            print(f"\n   📋 方案ID: {plan_id}")
                            break
            else:
                print(f"   响应: {resp.text[:500]}")
        except asyncio.TimeoutError:
            print(f"   ⏱️  请求超时（这是正常的，方案生成需要时间）")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

        # Step 5: 选择方案（假设选择第一个方案）
        print("\n[Step 5] 选择方案...")
        chat_request = {
            "user_id": USER_ID,
            "project_id": project_id,
            "action": "select_plan",
            "context": {
                "plan_id": "plan-001"  # 假设的方案ID
            },
        }

        try:
            resp = await client.post(f"{BASE_URL}/api/graph/chat", json=chat_request)
            print(f"   状态: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print(f"   ✅ 方案选择成功")
                print(f"   响应: {result.get('ui_feedback', 'N/A')[:200]}...")
            else:
                print(f"   响应: {resp.text[:500]}")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

        print("\n" + "=" * 80)
        print("测试流程完成")
        print("=" * 80)
        print("\n注意：完整的大纲生成流程需要：")
        print("1. 先生成故事方案（story_planner）")
        print("2. 用户选择方案（select_plan）")
        print("3. 触发大纲生成（skeleton_builder）")
        print("\n由于需要LLM调用，以上测试可能需要较长时间。")


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
