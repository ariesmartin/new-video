#!/usr/bin/env python3
"""
End-to-End Skeleton Builder System Test

This script tests the complete workflow:
1. Skeleton Builder Agent - Generate outline
2. Editor Agent - Review outline with 6-category framework
3. Refiner Agent - Fix issues while maintaining style
4. Quality Loop - Iterate until score >= 80 or max iterations

Run with: python test_skeleton_e2e.py
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

# Setup paths
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.graph.workflows.skeleton_builder_graph import build_skeleton_builder_graph
from backend.services.review_service import calculate_weights_unified, get_checkpoints
from backend.services.tension_service import generate_tension_curve
from backend.schemas.agent_state import AgentState, UserConfig
from langchain_core.messages import HumanMessage, AIMessage


class TestReport:
    """Collect and format test results"""

    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add_result(self, phase: str, success: bool, details: Dict[str, Any]):
        self.results.append(
            {
                "phase": phase,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "details": details,
            }
        )

    def print_summary(self):
        print("\n" + "=" * 80)
        print("📊 END-TO-END TEST SUMMARY")
        print("=" * 80)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])

        for r in self.results:
            status = "✅ PASS" if r["success"] else "❌ FAIL"
            print(f"\n{status} | {r['phase']}")
            if "error" in r["details"]:
                print(f"   Error: {r['details']['error']}")
            if "score" in r["details"]:
                print(f"   Score: {r['details']['score']}")
            if "iteration" in r["details"]:
                print(f"   Iteration: {r['details']['iteration']}")

        print(f"\n{'=' * 80}")
        print(f"Total: {passed}/{total} tests passed")
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"Duration: {duration:.2f} seconds")
        print("=" * 80)


async def test_services():
    """Test ReviewService and TensionService"""
    print("\n🧪 Testing Services...")

    # Test ReviewService
    weights = calculate_weights_unified(
        genre_combination=["revenge", "romance"], content_type="outline"
    )
    assert "logic" in weights, "Missing logic weight"
    assert "pacing" in weights, "Missing pacing weight"
    assert sum(weights.values()) > 0, "Weights sum to 0"

    checkpoints = get_checkpoints("outline")
    assert "logic" in checkpoints, "Missing logic checkpoints"

    print("  ✅ ReviewService working correctly")

    # Test TensionService
    curve = generate_tension_curve(80, "standard")
    assert len(curve["values"]) == 80, f"Expected 80 episodes, got {len(curve['values'])}"
    assert "key_points" in curve, "Missing key_points"

    print("  ✅ TensionService working correctly")

    return {"weights": weights, "curve_episodes": len(curve["values"])}


async def test_graph_construction():
    """Test graph can be built and has correct nodes"""
    print("\n🧪 Testing Graph Construction...")

    graph = build_skeleton_builder_graph()
    nodes = list(graph.nodes.keys())

    expected_nodes = [
        "__start__",
        "validate_input",
        "request_ending",
        "skeleton_builder",
        "editor",
        "refiner",
    ]

    for node in expected_nodes:
        assert node in nodes, f"Missing node: {node}"

    print(f"  ✅ Graph has {len(nodes)} nodes: {nodes}")

    return {"nodes": nodes}


async def test_validate_input():
    """Test validate_input node with incomplete requirements"""
    print("\n🧪 Testing Validate Input Node...")

    graph = build_skeleton_builder_graph()

    # Create incomplete state (missing ending)
    state = AgentState(
        messages=[HumanMessage(content="Generate a 40-episode revenge drama outline")],
        user_id="test_user_001",
        project_id="test_project_001",
        user_config=UserConfig(
            total_episodes=40,
            genre="revenge",
            sub_tags=[],
            tone=[],
            ending_type="",  # Missing - should trigger request_ending
        ),
    )

    # Execute just the validate_input node
    result = await graph.ainvoke(state, config={"configurable": {"thread_id": "test_validate_001"}})

    # Should have requested ending (check for ui_interaction or next routing)
    assert "user_config" in result, "Missing user_config in result"

    print(f"  ✅ Validate input completed")

    return {"validation_result": "complete"}


async def test_skeleton_generation():
    """Test full skeleton generation flow"""
    print("\n🧪 Testing Skeleton Generation (with real LLM)...")

    graph = build_skeleton_builder_graph()

    # Create complete requirements with ALL required fields
    state = AgentState(
        messages=[HumanMessage(content="Generate a 10-episode revenge romance outline")],
        user_id="test_user_001",
        project_id="test_project_001",
        user_config=UserConfig(
            total_episodes=10,
            genre="revenge",
            sub_tags=["romance"],
            tone=["dramatic"],
            ending_type="HEA",
        ),
        selected_plan={
            "plan_id": "plan_001",
            "title": "标准复仇甜宠方案",
            "genre": "revenge",
            "sub_tags": ["romance"],
            "tone": ["dramatic"],
            "logline": "女主遭背叛后华丽回归，在复仇中与冷酷男主相爱",
            "selling_points": ["强女主", "甜虐交织", "快节奏"],
        },
        # Pre-populate some context
        style_dna={
            "narrative_rhythm": "moderate",
            "dialogue_density": 0.4,
            "emotional_intensity": 0.7,
        },
        character_voices={
            "protagonist": "坚韧、聪明、外冷内热",
            "love_interest": "表面冷漠，内心深情",
            "antagonist": "阴险狡诈，权谋高手",
        },
    )

    print("  ⏳ Executing skeleton_builder (this may take 30-60 seconds)...")

    try:
        # Execute graph with timeout
        result = await asyncio.wait_for(
            graph.ainvoke(
                state,
                config={
                    "configurable": {
                        "thread_id": "test_skeleton_001",
                        "max_iterations": 1,  # Limit for testing
                    }
                },
            ),
            timeout=120,  # 2 minute timeout
        )

        # Check results
        has_outline = bool(result.get("generated_outline"))
        has_messages = len(result.get("messages", [])) > 0

        print(f"  ✅ Skeleton generation completed")
        print(f"     - Has outline: {has_outline}")
        print(f"     - Message count: {len(result.get('messages', []))}")

        # Show outline preview if available
        if has_outline:
            outline = result["generated_outline"]
            if isinstance(outline, dict) and "episodes" in outline:
                print(f"     - Episodes generated: {len(outline['episodes'])}")

        return {
            "has_outline": has_outline,
            "has_messages": has_messages,
            "message_count": len(result.get("messages", [])),
            "final_state_keys": list(result.keys()),
        }

    except asyncio.TimeoutError:
        return {"error": "Timeout - skeleton generation took too long"}
    except Exception as e:
        return {"error": str(e)}


async def test_editor_review():
    """Test editor agent with sample content"""
    print("\n🧪 Testing Editor Agent (with real LLM)...")

    from backend.agents.quality_control.editor import create_editor_agent

    # Create test content
    test_outline = {
        "title": "Test Revenge Drama",
        "total_episodes": 10,
        "episodes": [
            {
                "episode": 1,
                "title": "The Betrayal",
                "plot": "Protagonist discovers their partner's betrayal. They decide to seek revenge.",
                "key_scenes": ["Discovery scene", "Confrontation"],
                "tension_level": 0.7,
            },
            {
                "episode": 2,
                "title": "Planning",
                "plot": "Protagonist starts planning their revenge strategy.",
                "key_scenes": ["Strategy meeting", "Resource gathering"],
                "tension_level": 0.5,
            },
        ],
    }

    # Calculate weights
    weights = calculate_weights_unified(
        genre_combination=["revenge", "romance"], content_type="outline"
    )

    checkpoints = get_checkpoints("outline")

    # Create editor agent
    editor = await create_editor_agent(
        user_id="test_user_001",
        project_id="test_project_001",
        content_type="outline",
        genre_combination=["revenge", "romance"],
        ending="HEA",
        total_episodes=10,
    )

    print("  ⏳ Executing editor review (this may take 20-30 seconds)...")

    try:
        result = await asyncio.wait_for(
            editor.ainvoke(
                {
                    "messages": [
                        HumanMessage(
                            content=f"""
Review this outline and provide scores for each category:

Content Type: outline
Genre: revenge + romance
Ending: HEA
Total Episodes: 10

Weights:
{json.dumps(weights, indent=2, ensure_ascii=False)}

Checkpoints:
{json.dumps(checkpoints, indent=2, ensure_ascii=False)}

Content to Review:
{json.dumps(test_outline, indent=2, ensure_ascii=False)}

Provide scores (0-100) for each category and detailed feedback.
"""
                        )
                    ]
                }
            ),
            timeout=60,
        )

        print(f"  ✅ Editor review completed")
        print(f"     - Response length: {len(str(result))} chars")

        # Try to extract scores
        content = str(result)
        has_scores = any(
            f'"{cat}"' in content or f"{cat}:" in content.lower()
            for cat in ["logic", "pacing", "character", "conflict", "world", "hook"]
        )

        return {
            "has_scores": has_scores,
            "response_length": len(str(result)),
            "response_preview": str(result)[:500],
        }

    except asyncio.TimeoutError:
        return {"error": "Timeout - editor review took too long"}
    except Exception as e:
        return {"error": str(e)}


async def test_refiner_fix():
    """Test refiner agent with sample issues"""
    print("\n🧪 Testing Refiner Agent (with real LLM)...")

    from backend.agents.quality_control.refiner import create_refiner_agent

    # Create test content with issues
    original_content = {
        "episode": 1,
        "title": "The Betrayal",
        "plot": "Protagonist discovers betrayal. They get angry.",
        "issues": "Plot is too simple, lacks emotional depth",
    }

    review_report = {
        "overall_score": 65,
        "categories": {
            "logic": {"score": 70, "issues": ["Plot progression too fast"]},
            "pacing": {"score": 60, "issues": ["Lacks tension buildup"]},
            "character": {"score": 65, "issues": ["Protagonist motivation unclear"]},
        },
        "fix_suggestions": [
            "Add more scenes showing protagonist's emotional journey",
            "Include secondary characters to create complexity",
            "Slow down the discovery scene for more impact",
        ],
    }

    style_dna = {
        "narrative_rhythm": "moderate",
        "dialogue_density": 0.4,
        "emotional_intensity": 0.7,
    }

    # Create refiner agent
    refiner = await create_refiner_agent(user_id="test_user_001", project_id="test_project_001")

    print("  ⏳ Executing refiner (this may take 20-30 seconds)...")

    try:
        result = await asyncio.wait_for(
            refiner.ainvoke(
                {
                    "messages": [
                        HumanMessage(
                            content=f"""
Fix this content based on the review report while maintaining style consistency.

Content Type: outline
Style DNA: {json.dumps(style_dna, indent=2, ensure_ascii=False)}

Original Content:
{json.dumps(original_content, indent=2, ensure_ascii=False)}

Review Report:
{json.dumps(review_report, indent=2, ensure_ascii=False)}

Provide the fixed content and a change log.
"""
                        )
                    ]
                }
            ),
            timeout=60,
        )

        print(f"  ✅ Refiner completed")
        print(f"     - Response length: {len(str(result))} chars")

        return {
            "response_length": len(str(result)),
            "response_preview": str(result)[:500],
        }

    except asyncio.TimeoutError:
        return {"error": "Timeout - refiner took too long"}
    except Exception as e:
        return {"error": str(e)}


async def main():
    """Run all tests"""
    print("🚀 SKELETON BUILDER E2E TEST")
    print("=" * 80)
    print("This test will:")
    print("  1. Test services (ReviewService, TensionService)")
    print("  2. Test graph construction")
    print("  3. Test validate_input node")
    print("  4. Test skeleton generation (with real LLM)")
    print("  5. Test editor review (with real LLM)")
    print("  6. Test refiner fix (with real LLM)")
    print("=" * 80)

    # Initialize services
    print("\n🔧 Initializing services...")
    services_initialized = False
    try:
        from backend.services.database import DatabaseService
        from backend.services.model_router import init_model_router

        # Create mock DB service for testing
        db_service = DatabaseService(base_url="http://localhost:54321", service_key="test-key")

        # Initialize model router
        init_model_router(db_service)
        services_initialized = True
        print("  ✅ Services initialized")
    except Exception as e:
        print(f"  ⚠️ Service initialization skipped: {e}")
        print("  (Tests requiring LLM will be skipped)")

    report = TestReport()

    # Test 1: Services
    try:
        details = await test_services()
        report.add_result("Services (Review & Tension)", True, details)
    except Exception as e:
        report.add_result("Services (Review & Tension)", False, {"error": str(e)})

    # Test 2: Graph Construction
    try:
        details = await test_graph_construction()
        report.add_result("Graph Construction", True, details)
    except Exception as e:
        report.add_result("Graph Construction", False, {"error": str(e)})

    # Test 3: Validate Input
    try:
        details = await test_validate_input()
        report.add_result("Validate Input Node", True, details)
    except Exception as e:
        report.add_result("Validate Input Node", False, {"error": str(e)})

    # Test 4: Skeleton Generation (with real LLM)
    try:
        details = await test_skeleton_generation()
        success = "error" not in details
        report.add_result("Skeleton Generation (LLM)", success, details)
    except Exception as e:
        report.add_result("Skeleton Generation (LLM)", False, {"error": str(e)})

    # Test 5: Editor Review (with real LLM) - only if services initialized
    if services_initialized:
        try:
            details = await test_editor_review()
            success = "error" not in details
            report.add_result("Editor Review (LLM)", success, details)
        except Exception as e:
            report.add_result("Editor Review (LLM)", False, {"error": str(e)})
    else:
        report.add_result("Editor Review (LLM)", False, {"error": "Services not initialized"})

    # Test 6: Refiner Fix (with real LLM) - only if services initialized
    if services_initialized:
        try:
            details = await test_refiner_fix()
            success = "error" not in details
            report.add_result("Refiner Fix (LLM)", success, details)
        except Exception as e:
            report.add_result("Refiner Fix (LLM)", False, {"error": str(e)})
    else:
        report.add_result("Refiner Fix (LLM)", False, {"error": "Services not initialized"})

    # Print summary
    report.print_summary()

    # Save detailed results (convert to serializable format)
    output_file = f"/Users/ariesmartin/Documents/new-video/backend/test_e2e_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        serializable_results = []
        for r in report.results:
            serializable_results.append(
                {
                    "phase": r["phase"],
                    "success": r["success"],
                    "timestamp": r["timestamp"],
                    "details": {
                        k: str(v) if not isinstance(v, (str, int, float, bool, list, dict)) else v
                        for k, v in r["details"].items()
                    },
                }
            )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "results": serializable_results,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\n📄 Detailed results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️ Could not save results: {e}")


if __name__ == "__main__":
    asyncio.run(main())
