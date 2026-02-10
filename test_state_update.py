#!/usr/bin/env python3
"""
验证 State 更新流程

测试 validate_output_node 返回的 retry_count 是否正确传递到 skeleton_builder_node
"""

import asyncio
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.graph.workflows.skeleton_builder_graph import validate_output_node


async def test_validate_output_node_state_update():
    """测试 validate_output_node 返回中是否正确包含 retry_count"""
    print("=" * 60)
    print("Test 1: validate_output_node 返回 retry_count")
    print("=" * 60)

    # 模拟验证失败的情况
    mock_state = {
        "skeleton_content": "不完整的大纲",  # 故意不完整
        "chapter_mapping": {"total_chapters": 60},
        "retry_count": 0,  # 初始为 0
    }

    result = await validate_output_node(mock_state)

    print(f"\n输入 state['retry_count']: {mock_state['retry_count']}")
    print(f"返回 result['validation_status']: {result.get('validation_status')}")
    print(f"返回 result['retry_count']: {result.get('retry_count')}")

    # 验证 1: validation_status 应该是 incomplete
    if result.get("validation_status") == "incomplete":
        print("✅ validation_status 正确标记为 incomplete")
    else:
        print("❌ validation_status 不正确")
        return False

    # 验证 2: retry_count 应该从 0 增加到 1
    if result.get("retry_count") == 1:
        print("✅ retry_count 正确更新为 1")
    else:
        print(f"❌ retry_count 未正确更新，期望 1，实际 {result.get('retry_count')}")
        return False

    return True


async def test_validate_output_node_increments():
    """测试多次验证失败时 retry_count 是否正确递增"""
    print("\n" + "=" * 60)
    print("Test 2: retry_count 递增测试")
    print("=" * 60)

    current_retry = 0
    for i in range(3):
        mock_state = {
            "skeleton_content": "不完整的大纲",
            "chapter_mapping": {"total_chapters": 60},
            "retry_count": current_retry,
        }

        result = await validate_output_node(mock_state)
        new_retry = result.get("retry_count")

        print(
            f"\n迭代 {i + 1}: 输入 retry_count={current_retry}, 输出 retry_count={new_retry}"
        )

        if new_retry == current_retry + 1:
            print(f"  ✅ 正确递增")
        else:
            print(f"  ❌ 递增错误，期望 {current_retry + 1}，实际 {new_retry}")
            return False

        current_retry = new_retry

    print(f"\n最终 retry_count: {current_retry}")
    if current_retry == 3:
        print("✅ 3 次递增后 retry_count 正确为 3")
        return True
    else:
        print(f"❌ 最终 retry_count 错误，期望 3，实际 {current_retry}")
        return False


async def test_skeleton_builder_uses_retry_count():
    """测试 skeleton_builder_node 是否正确使用 retry_count"""
    print("\n" + "=" * 60)
    print("Test 3: skeleton_builder_node 重试逻辑检查")
    print("=" * 60)

    from backend.agents.skeleton_builder import skeleton_builder_node
    import inspect

    source = inspect.getsource(skeleton_builder_node)

    # 检查关键代码
    checks = [
        ('retry_count = state.get("retry_count", 0)', "读取 retry_count"),
        ("if retry_count > 0 and messages:", "条件检查"),
        ("Retry detected, simplifying messages", "日志输出"),
    ]

    all_passed = True
    for code_snippet, description in checks:
        if code_snippet in source:
            print(f"✅ {description}: 代码存在")
        else:
            print(f"❌ {description}: 代码缺失")
            all_passed = False

    return all_passed


async def main():
    print("🚀 State 更新流程验证测试")
    print("=" * 60)

    results = []

    # Test 1
    results.append(
        (
            "validate_output_node 返回 retry_count",
            await test_validate_output_node_state_update(),
        )
    )

    # Test 2
    results.append(("retry_count 递增", await test_validate_output_node_increments()))

    # Test 3
    results.append(
        (
            "skeleton_builder_node 重试逻辑",
            await test_skeleton_builder_uses_retry_count(),
        )
    )

    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！State 更新流程已修复。")
    else:
        print("⚠️ 部分测试失败，需要进一步检查。")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
