"""
Quick Routing Validation Test

Validates the routing logic matches the implementation.
"""

import sys
sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.schemas.agent_state import AgentState
from backend.graph.workflows.skeleton_builder_graph import (
    route_after_validation,
    route_after_editor,
    route_after_refiner,
)


def test_routing():
    """Test all routing functions"""
    print("\n🚦 路由逻辑验证测试")
    print("=" * 60)
    
    # Test route_after_validation
    print("\n1. route_after_validation")
    for status, expected in [
        ("complete", "complete"),
        ("incomplete", "incomplete"),
        ("awaiting_action", "awaiting_action"),
    ]:
        state = AgentState()
        state["validation_status"] = status
        result = route_after_validation(state)
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"   ✅ {status} → {result}")
    
    # Test route_after_editor
    print("\n2. route_after_editor")
    test_cases = [
        # (quality_score, revision_count, has_report, expected)
        (85, 0, True, "end"),       # High quality
        (70, 1, True, "refine"),    # Low quality, refine
        (0, 0, True, "end"),        # System error
        (70, 3, True, "end"),       # Max revisions
        (75, 2, True, "refine"),    # Medium quality
    ]
    
    for score, count, has_report, expected in test_cases:
        state = AgentState()
        state["quality_score"] = score
        state["revision_count"] = count
        if has_report:
            state["review_report"] = {"passed": score >= 80}
        result = route_after_editor(state)
        assert result == expected, f"Score={score}, Count={count}: Expected {expected}, got {result}"
        print(f"   ✅ score={score:2d}, count={count} → {result}")
    
    # Test route_after_refiner
    print("\n3. route_after_refiner")
    state = AgentState()
    state["revision_count"] = 1
    state["skeleton_output"] = {"episodes": []}
    result = route_after_refiner(state)
    assert result == "review", f"Expected 'review', got {result}"
    print(f"   ✅ has_output → {result}")
    
    print("\n✅ 所有路由测试通过!")


if __name__ == "__main__":
    test_routing()
