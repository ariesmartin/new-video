"""
End-to-End API Test: Full workflow including AI Random Plan fix verification

Tests the complete flow through the /api/graph/chat endpoint
"""

import asyncio
import aiohttp
import json
import sys

# API Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


async def test_api_endpoint(session: aiohttp.ClientSession, test_name: str, payload: dict) -> dict:
    """Test a single API endpoint"""
    print(f"\n{'=' * 60}")
    print(f"Test: {test_name}")
    print(f"{'=' * 60}")

    try:
        async with session.post(
            f"{BASE_URL}/api/graph/chat", json=payload, headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ API Response (Status: {response.status})")
                print(f"   routed_agent: {result.get('routed_agent', 'N/A')}")

                # Check for workflow plan
                workflow_plan = result.get("workflow_plan", [])
                if workflow_plan:
                    print(f"   workflow_plan: {len(workflow_plan)} steps")
                    for i, step in enumerate(workflow_plan, 1):
                        print(f"      Step {i}: {step.get('agent', 'N/A')}")
                else:
                    print(f"   workflow_plan: None (single-step)")

                print(f"   ui_feedback: {result.get('ui_feedback', 'N/A')[:60]}...")
                return {"success": True, "result": result}
            else:
                error_text = await response.text()
                print(f"❌ API Error (Status: {response.status})")
                print(f"   {error_text[:200]}")
                return {"success": False, "error": error_text}

    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return {"success": False, "error": str(e)}


async def test_single_step_market_analysis():
    """Test single-step market analysis"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "user_id": TEST_USER_ID,
            "project_id": str(__import__("uuid").uuid4()),
            "session_id": str(__import__("uuid").uuid4()),
            "message": "分析一下当前短剧市场趋势",
            "context": {"current_stage": "L1"},
        }

        result = await test_api_endpoint(session, "单步骤-市场分析", payload)

        # Verify
        success = result["success"]
        if success:
            api_result = result["result"]
            workflow_plan = api_result.get("workflow_plan", [])
            routed_agent = api_result.get("routed_agent", "")

            if len(workflow_plan) > 0:
                print("❌ Expected single-step, got multi-step")
                success = False
            elif routed_agent != "Market_Analyst":
                print(f"❌ Expected Market_Analyst, got {routed_agent}")
                success = False
            else:
                print("✅ Verification passed")

        return success


async def test_multi_step_storyboard():
    """Test multi-step storyboard + image generation"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "user_id": TEST_USER_ID,
            "project_id": str(__import__("uuid").uuid4()),
            "session_id": str(__import__("uuid").uuid4()),
            "message": "将第一章进行分镜并生成分镜图片",
            "context": {
                "current_stage": "ModA",
                "novel_content": "第一章：夜幕降临，主角走出房门...",
            },
        }

        result = await test_api_endpoint(session, "多步骤-分镜并生图", payload)

        # Verify
        success = result["success"]
        if success:
            api_result = result["result"]
            workflow_plan = api_result.get("workflow_plan", [])

            if len(workflow_plan) != 2:
                print(f"❌ Expected 2 steps, got {len(workflow_plan)}")
                success = False
            else:
                expected_agents = ["Storyboard_Director", "Image_Generator"]
                actual_agents = [step.get("agent") for step in workflow_plan]
                if actual_agents != expected_agents:
                    print(f"❌ Expected {expected_agents}, got {actual_agents}")
                    success = False
                else:
                    print("✅ Verification passed")

        return success


async def test_random_plan_no_loop():
    """Test AI Random Plan - CRITICAL: Must not cause infinite loop"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "user_id": TEST_USER_ID,
            "project_id": str(__import__("uuid").uuid4()),
            "session_id": str(__import__("uuid").uuid4()),
            "action": "random_plan",  # This previously caused infinite loop
            "context": {"current_stage": "ModA", "novel_content": "第一章测试内容..."},
        }

        print("\n" + "=" * 60)
        print("Test: AI随机方案 (random_plan)")
        print("⚠️  CRITICAL: Verifying no infinite loop")
        print("=" * 60)

        start_time = asyncio.get_event_loop().time()

        try:
            async with session.post(
                f"{BASE_URL}/api/graph/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),  # 30 second timeout
            ) as response:
                elapsed = asyncio.get_event_loop().time() - start_time

                if response.status == 200:
                    result = await response.json()
                    print(f"✅ API Response in {elapsed:.2f}s (Status: {response.status})")
                    print(f"   routed_agent: {result.get('routed_agent', 'N/A')}")

                    # Verify no loop
                    if elapsed > 25:
                        print(f"⚠️  Warning: Response took {elapsed:.2f}s - possible slowdown")
                    else:
                        print(f"✅ Response time normal ({elapsed:.2f}s)")

                    # Check result is meaningful
                    routed_agent = result.get("routed_agent", "")
                    if not routed_agent or routed_agent == "":
                        print("❌ No agent routed")
                        return False

                    print("✅ Verification passed - No infinite loop!")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ API Error (Status: {response.status})")
                    print(f"   {error_text[:200]}")
                    return False

        except asyncio.TimeoutError:
            print(f"❌ TIMEOUT: Request took longer than 30s - possible infinite loop!")
            return False
        except Exception as e:
            print(f"❌ Request Failed: {e}")
            return False


async def main():
    """Run all E2E tests"""
    print("\n" + "=" * 60)
    print("End-to-End API Tests")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")
    print()

    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/health", timeout=5) as resp:
                if resp.status == 200:
                    print("✅ Backend server is running\n")
                else:
                    print(f"⚠️  Server returned status {resp.status}\n")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure the server is running on port 8000")
        return False

    # Run tests
    results = []

    # Test 1: Single-step
    results.append(("单步骤-市场分析", await test_single_step_market_analysis()))

    # Test 2: Multi-step
    results.append(("多步骤-分镜并生图", await test_multi_step_storyboard()))

    # Test 3: AI Random Plan (Critical - must not loop)
    results.append(("AI随机方案(防循环)", await test_random_plan_no_loop()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\n总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"成功率: {(passed / len(results) * 100):.1f}%")

    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
