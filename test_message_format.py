#!/usr/bin/env python3
"""
测试 chat_init_endpoint 的消息格式化逻辑
"""

import json


def format_message_content(content) -> str:
    """将消息内容转换为友好格式，处理 action JSON 和 Master Router JSON"""
    if not content:
        return ""

    content_str = str(content).strip()

    # Action 到友好标签的映射（用于用户消息）
    action_labels = {
        "start_creation": "🎬 开始创作",
        "adapt_script": "📜 剧本改编",
        "create_storyboard": "🎨 分镜制作",
        "inspect_assets": "👤 资产探查",
        "random_plan": "🎲 随机方案",
        "select_genre": "🎯 选择赛道",
        "start_custom": "✨ 自由创作",
        "reset_genre": "🔙 重选背景",
        "select_plan": "📋 选择方案",
        "proceed_to_planning": "🤖 AI 自动选题",
        "cold_start": "🚀 启动助手",
    }

    # 1. 尝试解析 action JSON（用户消息）
    if content_str.startswith("{") and '"action"' in content_str:
        try:
            parsed = json.loads(content_str)
            action = parsed.get("action") if parsed else None
            if action and isinstance(action, str):
                label = action_labels.get(action) or action
                # 如果有 genre，添加到标签
                if parsed.get("payload", {}).get("genre"):
                    genre = parsed["payload"]["genre"]
                    if genre:
                        label = f"{label} ({genre})"
                return label
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # 2. 尝试解析 Master Router JSON（AI 消息）
    # 格式: {"thought_process": "...", "target_agent": "...", "ui_feedback": "..."}
    if content_str.startswith("{") and (
        '"ui_feedback"' in content_str or '"thought_process"' in content_str
    ):
        try:
            parsed = json.loads(content_str)
            if parsed and isinstance(parsed, dict):
                # 优先提取 ui_feedback
                ui_feedback = parsed.get("ui_feedback")
                if ui_feedback and isinstance(ui_feedback, str) and ui_feedback.strip():
                    return ui_feedback.strip()

                # 如果没有 ui_feedback，尝试提取 thought_process
                thought_process = parsed.get("thought_process")
                if (
                    thought_process
                    and isinstance(thought_process, str)
                    and thought_process.strip()
                ):
                    return thought_process.strip()
        except (json.JSONDecodeError, TypeError):
            pass

    return content_str


def test_format_message_content():
    """测试消息格式化函数"""

    print("=" * 80)
    print("测试消息格式化逻辑")
    print("=" * 80)

    # 测试1: Master Router JSON（AI 响应）
    print("\n测试1: Master Router JSON（AI 响应）")
    ai_response = """{
  "thought_process": "用户通过结构化指令明确要求启动'故事规划'（Story Planning）阶段。虽然当前处于 LEVEL_1（市场分析阶段），但用户跳过了市场分析，直接指定目标为 story_planner。这是一个明确的单步骤跳转指令。",
  "target_agent": "Story_Planner",
  "function_name": "plan_story_cold_start",
  "parameters": {},
  "ui_feedback": "没问题，正在为您启动故事规划器。让我们开始构思一个精彩的故事，您可以先告诉我您感兴趣的题材或关键词。"
}"""

    result = format_message_content(ai_response)
    print(f"输入长度: {len(ai_response)} 字符")
    print(f"输出: {result}")
    print(
        f"✅ 测试通过"
        if result
        == "没问题，正在为您启动故事规划器。让我们开始构思一个精彩的故事，您可以先告诉我您感兴趣的题材或关键词。"
        else "❌ 测试失败"
    )

    # 测试2: Action JSON（用户消息）
    print("\n测试2: Action JSON（用户消息）")
    user_action = '{"action": "start_creation", "payload": {"target": "story_planner"}}'
    result = format_message_content(user_action)
    print(f"输入: {user_action}")
    print(f"输出: {result}")
    print(f"✅ 测试通过" if result == "🎬 开始创作" else "❌ 测试失败")

    # 测试3: 普通文本
    print("\n测试3: 普通文本")
    plain_text = "你好，这是一个普通的消息"
    result = format_message_content(plain_text)
    print(f"输入: {plain_text}")
    print(f"输出: {result}")
    print(f"✅ 测试通过" if result == plain_text else "❌ 测试失败")

    # 测试4: 带 genre 的 action
    print("\n测试4: 带 genre 的 action")
    action_with_genre = '{"action": "select_genre", "payload": {"genre": "悬疑"}}'
    result = format_message_content(action_with_genre)
    print(f"输入: {action_with_genre}")
    print(f"输出: {result}")
    print(f"✅ 测试通过" if result == "🎯 选择赛道 (悬疑)" else "❌ 测试失败")

    # 测试5: 只有 thought_process 没有 ui_feedback
    print("\n测试5: 只有 thought_process 没有 ui_feedback")
    only_thought = '{"thought_process": "这是思考过程", "target_agent": "Test"}'
    result = format_message_content(only_thought)
    print(f"输入: {only_thought}")
    print(f"输出: {result}")
    print(f"✅ 测试通过" if result == "这是思考过程" else "❌ 测试失败")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


def test_api_endpoints():
    """提供 API 测试命令"""
    print("\n\n")
    print("=" * 80)
    print("API 测试命令（请在后端服务运行时执行）")
    print("=" * 80)

    print("""
1. 测试冷启动（新项目）:
curl -X POST http://localhost:8000/api/graph/chat/init \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test-user-001",
    "project_id": "test-project-001",
    "session_id": "test-thread-001"
  }'

2. 测试发送消息（SSE 流式）:
curl -N "http://localhost:8000/api/graph/chat?message=开始创作短剧&project_id=test-project-001&thread_id=test-thread-001&user_id=test-user-001"

3. 测试刷新后获取历史:
curl -X POST http://localhost:8000/api/graph/chat/init \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test-user-001",
    "project_id": "test-project-001",
    "session_id": "test-thread-001"
  }'

4. 直接查询 checkpointer:
curl http://localhost:8000/api/graph/messages/test-thread-001?user_id=test-user-001
""")


if __name__ == "__main__":
    test_format_message_content()
    test_api_endpoints()
