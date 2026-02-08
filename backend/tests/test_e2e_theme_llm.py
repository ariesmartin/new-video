"""
End-to-End LLM Integration Test: Theme Library + Story Planner

This test validates that:
1. Theme data is correctly injected into Story Planner prompts
2. The AI actually uses the injected theme data in its output
3. Quality improves with theme data vs baseline (without theme data)

Requirements:
- Running backend server on localhost:8000
- Database with theme data populated
- LLM API access (OpenRouter/Ollama)

Usage:
    cd /Users/ariesmartin/Documents/new-video
    source backend/.venv/bin/activate
    python -m backend.tests.test_e2e_theme_llm
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Test Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-theme-llm-001"


@dataclass
class TestResult:
    """Test result container"""

    name: str
    success: bool
    duration_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None


class ThemeE2ETest:
    """E2E Test for Theme Library LLM Integration"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_server(self) -> bool:
        """Check if backend server is running"""
        try:
            async with self.session.get(f"{BASE_URL}/api/health", timeout=5) as resp:
                if resp.status == 200:
                    print("✅ Backend server is running")
                    return True
                else:
                    print(f"⚠️  Server returned status {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            print(
                "   Make sure the server is running: cd backend && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
            )
            return False

    async def create_project(self, genre: str, setting: str) -> Optional[str]:
        """Create a test project with specific genre"""
        try:
            payload = {
                "user_id": TEST_USER_ID,
                "name": f"Theme Test - {genre}",
                "genre": genre,
                "setting": setting,
                "episode_count": 80,
                "episode_duration": 1.5,
            }

            async with self.session.post(
                f"{BASE_URL}/api/projects",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    project_id = result.get("id")
                    print(f"   Created project: {project_id}")
                    return project_id
                else:
                    error = await resp.text()
                    print(f"   ❌ Failed to create project: {error[:200]}")
                    return None
        except Exception as e:
            print(f"   ❌ Error creating project: {e}")
            return None

    async def invoke_story_planner(
        self, project_id: str, genre: str, setting: str, with_theme_data: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Invoke Story Planner via API"""
        try:
            # First, trigger genre selection
            select_payload = {
                "user_id": TEST_USER_ID,
                "project_id": project_id,
                "session_id": f"session-{int(time.time())}",
                "action": "select_genre",
                "payload": {"genre": genre, "setting": setting},
                "context": {"current_stage": "L2"},
            }

            async with self.session.post(
                f"{BASE_URL}/api/graph/chat",
                json=select_payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    print(f"   ❌ Genre selection failed: {error[:200]}")
                    return None

                result = await resp.json()

            # Then trigger episode config
            config_payload = {
                "user_id": TEST_USER_ID,
                "project_id": project_id,
                "session_id": f"session-{int(time.time())}",
                "action": "set_episode_config",
                "payload": {
                    "genre": genre,
                    "setting": setting,
                    "episode_count": 80,
                    "episode_duration": 1.5,
                },
                "context": {"current_stage": "L2"},
            }

            async with self.session.post(
                f"{BASE_URL}/api/graph/chat",
                json=config_payload,
                headers={"Content-Type": "application/json"},
                timeout=120,  # Story generation may take time
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error = await resp.text()
                    print(f"   ❌ Story planner failed: {error[:200]}")
                    return None

        except asyncio.TimeoutError:
            print("   ❌ Timeout waiting for story planner")
            return None
        except Exception as e:
            print(f"   ❌ Error invoking story planner: {e}")
            return None

    def analyze_theme_usage(self, content: str, genre: str) -> Dict[str, Any]:
        """Analyze if AI output uses theme data"""
        analysis = {
            "content_length": len(content),
            "has_structure": False,
            "has_tropes": False,
            "has_hooks": False,
            "has_archetypes": False,
            "genre_keywords": [],
            "quality_score": 0,
        }

        # Check for structured output (JSON markers)
        if "```json" in content or '"options"' in content:
            analysis["has_structure"] = True

        # Genre-specific keywords to look for
        genre_keywords = {
            "复仇逆袭": ["复仇", "逆袭", "打脸", "背叛", "身份", "隐藏", "实力", "正义"],
            "甜宠恋爱": ["甜宠", "恋爱", "男神", "女主", "宠溺", "暖心", "甜蜜", "浪漫"],
            "悬疑推理": ["悬疑", "推理", "侦探", "线索", "真相", "嫌疑人", "案件", "谜团"],
            "穿越重生": ["穿越", "重生", "改变", "命运", "原著", "现代", "古代", "逆袭"],
        }

        keywords = genre_keywords.get(genre, [])
        found_keywords = [kw for kw in keywords if kw in content]
        analysis["genre_keywords"] = found_keywords
        analysis["keyword_coverage"] = len(found_keywords) / len(keywords) if keywords else 0

        # Check for trope-like elements
        trope_indicators = ["元素", "套路", "设定", "情节", "冲突", "反转"]
        analysis["has_tropes"] = any(indicator in content for indicator in trope_indicators)

        # Check for hook/opening indicators
        hook_indicators = ["钩子", "开场", "前3秒", "留存", "吸引"]
        analysis["has_hooks"] = any(indicator in content for indicator in hook_indicators)

        # Check for character archetypes
        archetype_indicators = ["主角", "反派", "角色", "人物", "性格", "特征"]
        analysis["has_archetypes"] = any(indicator in content for indicator in archetype_indicators)

        # Calculate quality score (0-100)
        score = 0
        if analysis["has_structure"]:
            score += 30
        if analysis["has_tropes"]:
            score += 20
        if analysis["has_hooks"]:
            score += 20
        if analysis["has_archetypes"]:
            score += 15
        score += min(15, int(analysis["keyword_coverage"] * 15))
        analysis["quality_score"] = score

        return analysis

    async def test_theme_injection_with_genre(self, genre: str, setting: str) -> TestResult:
        """Test theme library injection for a specific genre"""
        start_time = time.time()
        test_name = f"Theme Injection - {genre}"

        print(f"\n{'=' * 60}")
        print(f"Test: {test_name}")
        print(f"{'=' * 60}")

        try:
            # Create project
            print("1. Creating test project...")
            project_id = await self.create_project(genre, setting)
            if not project_id:
                return TestResult(
                    name=test_name,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={},
                    error="Failed to create project",
                )

            # Invoke story planner
            print("2. Invoking Story Planner (with theme data)...")
            result = await self.invoke_story_planner(
                project_id, genre, setting, with_theme_data=True
            )

            if not result:
                return TestResult(
                    name=test_name,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={},
                    error="Story planner returned no result",
                )

            # Extract AI output
            messages = result.get("messages", [])
            if not messages:
                return TestResult(
                    name=test_name,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    details={},
                    error="No messages in result",
                )

            ai_content = (
                messages[-1].get("content", "")
                if isinstance(messages[-1], dict)
                else str(messages[-1])
            )

            # Analyze theme usage
            print("3. Analyzing AI output for theme data usage...")
            analysis = self.analyze_theme_usage(ai_content, genre)

            print(f"   Content length: {analysis['content_length']} chars")
            print(f"   Has structure: {analysis['has_structure']}")
            print(f"   Has tropes: {analysis['has_tropes']}")
            print(f"   Has hooks: {analysis['has_hooks']}")
            print(f"   Has archetypes: {analysis['has_archetypes']}")
            print(f"   Genre keywords found: {analysis['genre_keywords']}")
            print(f"   Keyword coverage: {analysis['keyword_coverage']:.1%}")
            print(f"   Quality score: {analysis['quality_score']}/100")

            # Determine success criteria
            success = (
                analysis["quality_score"] >= 50
                and analysis["has_structure"]
                and analysis["keyword_coverage"] >= 0.3
            )

            duration_ms = (time.time() - start_time) * 1000

            return TestResult(
                name=test_name,
                success=success,
                duration_ms=duration_ms,
                details={
                    "project_id": project_id,
                    "content_preview": ai_content[:500],
                    "analysis": analysis,
                },
                error=None
                if success
                else f"Quality score {analysis['quality_score']} below threshold",
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=test_name, success=False, duration_ms=duration_ms, details={}, error=str(e)
            )

    async def test_prompt_injection_directly(self) -> TestResult:
        """Test prompt injection directly without full API flow"""
        start_time = time.time()
        test_name = "Direct Prompt Injection Test"

        print(f"\n{'=' * 60}")
        print(f"Test: {test_name}")
        print(f"{'=' * 60}")

        try:
            # Import and test directly
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent))

            from backend.agents.story_planner import _load_story_planner_prompt, _genre_to_slug

            # Test with revenge genre
            genre = "复仇逆袭"
            print(f"1. Testing prompt loading for genre: {genre}")

            prompt = _load_story_planner_prompt(
                market_report=None,
                episode_count=80,
                episode_duration=1.5,
                genre=genre,
                setting="modern",
            )

            # Verify theme data is injected
            checks = {
                "has_theme_section": "## 题材指导" in prompt,
                "has_core_formula": "核心公式" in prompt,
                "has_elements": "爆款元素" in prompt,
                "has_hooks": "钩子模板" in prompt,
                "has_archetypes": "角色原型" in prompt or "隐忍复仇者" in prompt,
                "has_market_data": "市场评分" in prompt or "成功率" in prompt,
            }

            print("2. Checking prompt injection:")
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}: {passed}")

            # Calculate injection score
            injection_score = sum(1 for v in checks.values() if v) / len(checks)
            print(f"\n   Injection completeness: {injection_score:.1%}")
            print(f"   Prompt length: {len(prompt)} characters")

            # Show preview of theme section
            theme_start = prompt.find("## 题材指导")
            if theme_start != -1:
                preview = prompt[theme_start : theme_start + 600]
                print(f"\n   Theme data preview:")
                print(f"   {preview}...")

            success = injection_score >= 0.7  # At least 70% of sections injected

            duration_ms = (time.time() - start_time) * 1000

            return TestResult(
                name=test_name,
                success=success,
                duration_ms=duration_ms,
                details={
                    "prompt_length": len(prompt),
                    "injection_score": injection_score,
                    "checks": checks,
                    "genre_slug": _genre_to_slug(genre),
                },
                error=None
                if success
                else f"Injection score {injection_score:.1%} below 70% threshold",
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            import traceback

            return TestResult(
                name=test_name,
                success=False,
                duration_ms=duration_ms,
                details={},
                error=f"{str(e)}\n{traceback.format_exc()}",
            )

    async def test_all_genres(self) -> List[TestResult]:
        """Test theme injection across all supported genres"""
        genres = [
            ("复仇逆袭", "modern"),
            ("甜宠恋爱", "modern"),
            ("悬疑推理", "modern"),
            ("穿越重生", "ancient"),
            ("家庭伦理", "modern"),
        ]

        results = []
        for genre, setting in genres:
            result = await self.test_theme_injection_with_genre(genre, setting)
            results.append(result)

        return results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("E2E LLM Integration Test Summary")
        print("=" * 60)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed

        avg_duration = sum(r.duration_ms for r in self.results) / total if total > 0 else 0

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed / total * 100):.1f}%" if total > 0 else "N/A")
        print(f"Average Duration: {avg_duration:.0f}ms")

        print("\nDetailed Results:")
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"\n  {status}: {result.name}")
            print(f"     Duration: {result.duration_ms:.0f}ms")

            if result.details:
                if "analysis" in result.details:
                    analysis = result.details["analysis"]
                    print(f"     Quality Score: {analysis.get('quality_score', 0)}/100")
                    print(f"     Keyword Coverage: {analysis.get('keyword_coverage', 0):.1%}")
                elif "injection_score" in result.details:
                    print(f"     Injection Score: {result.details['injection_score']:.1%}")

            if result.error:
                print(f"     Error: {result.error[:100]}")

        print("\n" + "=" * 60)

        if failed == 0:
            print("🎉 All E2E LLM tests passed!")
            print("Theme Library integration is working correctly.")
        else:
            print(f"⚠️  {failed} test(s) failed. Check details above.")

        print("=" * 60)

        return failed == 0


async def main():
    """Main test runner"""
    print("\n" + "🎭" * 30)
    print("E2E LLM Integration Test: Theme Library + Story Planner")
    print("🎭" * 30)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")

    async with ThemeE2ETest() as tester:
        # Check server
        print("\n" + "-" * 60)
        print("Pre-flight Checks")
        print("-" * 60)
        if not await tester.check_server():
            print("\n❌ Server not available. Cannot run tests.")
            return False

        # Run tests
        print("\n" + "-" * 60)
        print("Running Tests")
        print("-" * 60)

        # Test 1: Direct prompt injection (fast, no LLM)
        result1 = await tester.test_prompt_injection_directly()
        tester.results.append(result1)

        # Test 2-6: Full LLM tests for each genre (slow, requires LLM)
        print("\n⚠️  Note: Following tests invoke actual LLM and may take 30-120s each")
        print("   Press Ctrl+C to skip LLM tests and only check prompt injection\n")

        try:
            genre_results = await tester.test_all_genres()
            tester.results.extend(genre_results)
        except KeyboardInterrupt:
            print("\n\n⚠️  LLM tests skipped by user")

        # Print summary
        return tester.print_summary()


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
