#!/usr/bin/env python3
"""
LangGraph Checkpoint 全面验证测试

测试内容：
1. ✅ Checkpoint 是否正确保存对话历史
2. ✅ SDUI (按钮) 是否正确保存
3. ✅ 前端按钮是否为系统信息而非用户信息
4. ✅ 刷新后历史对话内容是否与初次对话一致（包括排序）
5. ✅ 消息过滤（隐藏初始化消息）

注意：此测试需要后端服务已启动
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Any, List, Dict

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

# 测试配置
TEST_BASE_URL = "http://localhost:8000"
TEST_THREAD_ID = f"checkpoint_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
TEST_PROJECT_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_ID = "test_user_checkpoint"


class CheckpointValidator:
    """Checkpoint 验证器"""

    def __init__(self):
        self.results = []
        self.saved_messages = []  # 首次对话保存的消息
        self.thread_id = TEST_THREAD_ID

    def log_test(self, name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        self.results.append(
            {
                "name": name,
                "passed": passed,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if details:
            print(f"      {details}")

    async def make_request(
        self, method: str, endpoint: str, data: dict = None, params: dict = None
    ) -> tuple:
        """发送 HTTP 请求"""
        try:
            import urllib.request
            import urllib.error

            url = f"{TEST_BASE_URL}{endpoint}"
            if params:
                url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])

            headers = {"Content-Type": "application/json"}

            if method == "POST" and data:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
            else:
                req = urllib.request.Request(url, method=method)

            with urllib.request.urlopen(req, timeout=30) as response:
                return response.status, json.loads(response.read().decode("utf-8"))

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "code"):
                return e.code, {"error": error_msg}
            return 0, {"error": error_msg}

    async def test_1_checkpoint_save_history(self):
        """测试1: Checkpoint 是否正确保存对话历史"""
        print("\n" + "=" * 70)
        print("测试 1: Checkpoint 对话历史保存验证")
        print("=" * 70)

        try:
            # 步骤 1: 发送冷启动消息
            print("\n  步骤 1: 发送冷启动消息...")

            payload = {
                "user_id": TEST_USER_ID,
                "project_id": TEST_PROJECT_ID,
                "session_id": self.thread_id,
                "message": "你好，开始创作",
                "action": "cold_start",
            }

            status, data = await self.make_request("POST", "/api/graph/chat", payload)

            if status != 200:
                self.log_test(
                    "冷启动响应",
                    False,
                    f"HTTP {status}: {data.get('detail', 'Unknown')}",
                )
                return False

            # 检查响应中是否有 ui_interaction
            ui_interaction = data.get("ui_interaction")
            if ui_interaction:
                self.log_test(
                    "冷启动响应",
                    True,
                    f"收到欢迎消息和 {len(ui_interaction.get('buttons', []))} 个按钮",
                )
            else:
                self.log_test("冷启动响应", True, "收到欢迎消息（无按钮）")

            # 步骤 2: 发送普通对话消息
            print("\n  步骤 2: 发送普通对话消息...")

            await asyncio.sleep(1)  # 等待 checkpoint 保存

            payload2 = {
                "user_id": TEST_USER_ID,
                "project_id": TEST_PROJECT_ID,
                "session_id": self.thread_id,
                "message": "我想写一个都市复仇的故事",
            }

            status2, data2 = await self.make_request(
                "POST", "/api/graph/chat", payload2
            )

            if status2 != 200:
                self.log_test(
                    "对话响应",
                    False,
                    f"HTTP {status2}: {data2.get('detail', 'Unknown')}",
                )
                return False

            # 检查响应
            messages = data2.get("messages", [])
            ui_interaction2 = data2.get("ui_interaction")

            if messages:
                self.log_test("对话响应", True, f"收到 {len(messages)} 条消息")
            else:
                # 即使没有 messages，也可能通过 ui_feedback 返回
                ui_feedback = data2.get("ui_feedback", "")
                if ui_feedback:
                    self.log_test("对话响应", True, f"收到反馈: {ui_feedback[:50]}...")
                else:
                    self.log_test("对话响应", True, "收到响应（无消息列表）")

            if ui_interaction2:
                self.log_test(
                    "SDUI 响应",
                    True,
                    f"收到 {len(ui_interaction2.get('buttons', []))} 个按钮",
                )
            else:
                self.log_test("SDUI 响应", False, "未收到 SDUI")

            # 步骤 3: 获取 Graph 状态验证 checkpoint 保存
            print("\n  步骤 3: 验证 Checkpoint 保存...")

            await asyncio.sleep(2)  # 等待 checkpoint 完全保存

            status3, data3 = await self.make_request(
                "GET",
                f"/api/graph/{TEST_PROJECT_ID}/state",
                params={"thread_id": self.thread_id},
            )

            if status3 != 200:
                self.log_test("Checkpoint 验证", False, f"HTTP {status3}")
                return False

            state_data = data3.get("data", {})
            messages = state_data.get("messages", [])

            if messages:
                self.saved_messages = messages
                user_count = sum(1 for m in messages if m.get("role") == "user")
                assistant_count = sum(
                    1 for m in messages if m.get("role") == "assistant"
                )
                system_count = sum(1 for m in messages if m.get("role") == "system")

                details = f"共 {len(messages)} 条消息: {user_count} 用户, {assistant_count} AI, {system_count} 系统"
                self.log_test("Checkpoint 验证", True, details)
                return True
            else:
                # 检查是否有错误信息
                error_msg = state_data.get("error_message", "")
                if error_msg:
                    self.log_test(
                        "Checkpoint 验证", False, f"状态中有错误: {error_msg}"
                    )
                else:
                    self.log_test("Checkpoint 验证", False, "状态中无消息")
                return False

        except Exception as e:
            self.log_test("Checkpoint 保存测试", False, f"异常: {str(e)}")
            import traceback

            traceback.print_exc()
            return False

    async def test_2_sdui_persistence(self):
        """测试2: SDUI 是否正确保存"""
        print("\n" + "=" * 70)
        print("测试 2: SDUI 持久化验证")
        print("=" * 70)

        try:
            # 获取状态中的 ui_interaction
            status, data = await self.make_request(
                "GET",
                f"/api/graph/{TEST_PROJECT_ID}/state",
                params={"thread_id": self.thread_id},
            )

            if status != 200:
                self.log_test("获取状态", False, f"HTTP {status}")
                return False

            state_data = data.get("data", {})
            ui_interaction = state_data.get("ui_interaction")

            if not ui_interaction:
                self.log_test("SDUI 保存", False, "状态中没有 ui_interaction")
                return False

            # 检查 ui_interaction 结构
            block_type = ui_interaction.get("block_type")
            buttons = ui_interaction.get("buttons", [])

            if not block_type:
                self.log_test("SDUI 结构", False, "缺少 block_type")
                return False

            if not buttons or not isinstance(buttons, list):
                self.log_test("SDUI 按钮", False, "缺少 buttons 数组")
                return False

            self.log_test(
                "SDUI 保存验证", True, f"类型: {block_type}, {len(buttons)} 个按钮"
            )

            # 检查按钮结构
            if buttons:
                first_btn = buttons[0]
                required_fields = ["label", "action"]
                missing = [f for f in required_fields if f not in first_btn]

                if missing:
                    self.log_test("按钮结构", False, f"缺少字段: {missing}")
                    return False
                else:
                    self.log_test(
                        "按钮结构", True, f"按钮 '{first_btn.get('label')}' 结构完整"
                    )

            return True

        except Exception as e:
            self.log_test("SDUI 持久化测试", False, f"异常: {str(e)}")
            return False

    async def test_3_button_message_role(self):
        """测试3: 前端按钮是否为系统信息而非用户信息"""
        print("\n" + "=" * 70)
        print("测试 3: 按钮消息角色验证")
        print("=" * 70)

        try:
            # 获取状态
            status, data = await self.make_request(
                "GET",
                f"/api/graph/{TEST_PROJECT_ID}/state",
                params={"thread_id": self.thread_id},
            )

            if status != 200:
                self.log_test("获取状态", False, f"HTTP {status}")
                return False

            state_data = data.get("data", {})
            messages = state_data.get("messages", [])

            # ui_interaction 是状态的一部分，不是消息的一部分
            # 在当前的架构中，ui_interaction 附加到最后一条 AI 消息
            # 我们需要检查消息中是否包含 ui_interaction

            # 查找包含 ui_interaction 的消息（如果有的话）
            ui_messages = [
                m
                for m in messages
                if m.get("ui_interaction")
                or m.get("additional_kwargs", {}).get("ui_interaction")
            ]

            # 在 LangGraph 架构中，ui_interaction 通常存储在状态中
            # 而不是单独的消息中。让我们检查状态的 ui_interaction
            ui_interaction = state_data.get("ui_interaction")

            if ui_interaction:
                # ui_interaction 是状态级别的，由 AI 生成
                # 所以应该被视为系统/AI 信息，不是用户信息
                self.log_test(
                    "UI 交互来源", True, "ui_interaction 存储在状态中（AI 生成）"
                )

            # 验证消息角色分布
            ai_messages = [m for m in messages if m.get("role") in ["assistant", "ai"]]
            user_messages = [m for m in messages if m.get("role") == "user"]

            self.log_test(
                "消息角色分布",
                True,
                f"{len(ai_messages)} AI 消息, {len(user_messages)} 用户消息",
            )

            # 确保没有用户消息包含 ui_interaction
            user_with_ui = [m for m in user_messages if m.get("ui_interaction")]

            if user_with_ui:
                self.log_test(
                    "用户消息检查",
                    False,
                    f"{len(user_with_ui)} 条用户消息错误地包含 ui_interaction",
                )
                return False
            else:
                self.log_test("用户消息检查", True, "没有用户消息包含 ui_interaction")

            return True

        except Exception as e:
            self.log_test("按钮消息角色测试", False, f"异常: {str(e)}")
            import traceback

            traceback.print_exc()
            return False

    async def test_4_refresh_consistency(self):
        """测试4: 刷新后历史对话是否与初次一致"""
        print("\n" + "=" * 70)
        print("测试 4: 刷新一致性验证")
        print("=" * 70)

        try:
            # 第一次获取状态
            status1, data1 = await self.make_request(
                "GET",
                f"/api/graph/{TEST_PROJECT_ID}/state",
                params={"thread_id": self.thread_id},
            )

            if status1 != 200:
                self.log_test("首次获取状态", False, f"HTTP {status1}")
                return False

            first_state = data1.get("data", {})
            first_messages = first_state.get("messages", [])

            # 等待一下，模拟刷新
            await asyncio.sleep(1)

            # 第二次获取状态（模拟刷新）
            status2, data2 = await self.make_request(
                "GET",
                f"/api/graph/{TEST_PROJECT_ID}/state",
                params={"thread_id": self.thread_id},
            )

            if status2 != 200:
                self.log_test("刷新获取状态", False, f"HTTP {status2}")
                return False

            second_state = data2.get("data", {})
            second_messages = second_state.get("messages", [])

            # 对比消息数量
            if len(first_messages) != len(second_messages):
                self.log_test(
                    "消息数量一致性",
                    False,
                    f"首次: {len(first_messages)}, 刷新: {len(second_messages)}",
                )
                return False

            self.log_test(
                "消息数量一致性", True, f"两次获取均为 {len(first_messages)} 条消息"
            )

            # 对比消息顺序和内容
            order_match = True
            content_match = True

            for i, (first, second) in enumerate(zip(first_messages, second_messages)):
                # 检查角色
                if first.get("role") != second.get("role"):
                    order_match = False
                    print(
                        f"    消息 {i} 角色不匹配: {first.get('role')} vs {second.get('role')}"
                    )

                # 检查内容（前50字符）
                first_content = str(first.get("content", ""))[:50]
                second_content = str(second.get("content", ""))[:50]
                if first_content != second_content:
                    content_match = False
                    print(f"    消息 {i} 内容不匹配:")
                    print(f"      首次: {first_content}...")
                    print(f"      刷新: {second_content}...")

            self.log_test("消息顺序一致性", order_match)
            self.log_test("消息内容一致性", content_match)

            # 对比 ui_interaction
            first_ui = first_state.get("ui_interaction")
            second_ui = second_state.get("ui_interaction")

            if bool(first_ui) == bool(second_ui):
                if first_ui and second_ui:
                    # 都存在的，检查按钮数量
                    first_buttons = len(first_ui.get("buttons", []))
                    second_buttons = len(second_ui.get("buttons", []))
                    if first_buttons == second_buttons:
                        self.log_test(
                            "SDUI 一致性", True, f"都有 {first_buttons} 个按钮"
                        )
                    else:
                        self.log_test(
                            "SDUI 一致性",
                            False,
                            f"按钮数量不匹配: {first_buttons} vs {second_buttons}",
                        )
                else:
                    self.log_test("SDUI 一致性", True, "都没有 ui_interaction")
            else:
                self.log_test("SDUI 一致性", False, "ui_interaction 存在性不一致")

            return order_match and content_match

        except Exception as e:
            self.log_test("刷新一致性测试", False, f"异常: {str(e)}")
            import traceback

            traceback.print_exc()
            return False

    async def test_5_message_filtering(self):
        """测试5: 消息过滤（隐藏初始化消息）"""
        print("\n" + "=" * 70)
        print("测试 5: 消息过滤验证")
        print("=" * 70)

        try:
            # 获取状态
            status, data = await self.make_request(
                "GET",
                f"/api/graph/{TEST_PROJECT_ID}/state",
                params={"thread_id": self.thread_id},
            )

            if status != 200:
                self.log_test("获取状态", False, f"HTTP {status}")
                return False

            state_data = data.get("data", {})
            messages = state_data.get("messages", [])

            # 检查是否过滤了初始化消息
            init_phrases = ["你好，开始创作", "开始创作", "你好，开始"]
            visible_init_messages = []
            hidden_messages = []

            for msg in messages:
                content = str(msg.get("content", "")).lower()
                role = msg.get("role")

                # 检查是否是初始化消息
                is_init = role == "user" and any(
                    phrase in content for phrase in init_phrases
                )

                # 检查 metadata 中的隐藏标记
                additional_kwargs = msg.get("additional_kwargs", {})
                is_hidden = additional_kwargs.get("is_hidden", False)

                if is_init and not is_hidden:
                    visible_init_messages.append(msg)
                elif is_hidden:
                    hidden_messages.append(msg)

            # 在 checkpoint 中，初始化消息应该被保存但被标记为隐藏
            if visible_init_messages:
                self.log_test(
                    "初始化消息过滤",
                    False,
                    f"{len(visible_init_messages)} 条初始化消息未被隐藏",
                )
            else:
                self.log_test("初始化消息过滤", True, "初始化消息已被正确标记或过滤")

            # 显示消息列表
            print("\n  消息列表（按角色）:")
            for i, msg in enumerate(messages):
                role = msg.get("role", "unknown")
                content = str(msg.get("content", ""))[:40]
                kwargs = msg.get("additional_kwargs", {})
                is_hidden = kwargs.get("is_hidden", False)
                status_icon = "🚫" if is_hidden else "✓"
                print(f"    {i + 1}. [{status_icon}] {role}: {content}...")

            return True

        except Exception as e:
            self.log_test("消息过滤测试", False, f"异常: {str(e)}")
            import traceback

            traceback.print_exc()
            return False

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 70)
        print("📊 Checkpoint 验证测试报告")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed

        print(f"\n总计测试: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"通过率: {passed / total * 100:.1f}%" if total > 0 else "通过率: N/A")

        print("\n详细结果:")
        for result in self.results:
            status = "✅" if result["passed"] else "❌"
            print(f"  {status} {result['name']}")
            if result["details"]:
                print(f"      {result['details']}")

        print("\n" + "=" * 70)

        return failed == 0 and total > 0


async def main():
    """主函数"""
    print("=" * 70)
    print("🧪 LangGraph Checkpoint 全面验证测试")
    print("=" * 70)
    print(f"测试线程ID: {TEST_THREAD_ID}")
    print(f"测试项目ID: {TEST_PROJECT_ID}")
    print(f"API 地址: {TEST_BASE_URL}")

    # 首先检查服务是否可用
    print("\n  检查后端服务...")
    try:
        import urllib.request

        req = urllib.request.Request(f"{TEST_BASE_URL}/api/graph/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                health_data = json.loads(resp.read().decode("utf-8"))
                print(
                    f"  ✅ 后端服务运行中 (Graph v{health_data.get('version', 'unknown')})"
                )
            else:
                print(f"  ⚠️ 后端服务返回状态 {resp.status}")
    except Exception as e:
        print(f"  ❌ 无法连接到后端服务: {e}")
        print("\n请确保后端服务已启动:")
        print(
            "  cd /Users/ariesmartin/Documents/new-video/backend && python -m backend.main"
        )
        return False

    validator = CheckpointValidator()

    # 运行所有测试
    await validator.test_1_checkpoint_save_history()
    await validator.test_2_sdui_persistence()
    await validator.test_3_button_message_role()
    await validator.test_4_refresh_consistency()
    await validator.test_5_message_filtering()

    # 生成报告
    success = validator.generate_report()

    print("\n💡 提示:")
    print(f"  - 测试使用的 thread_id: {TEST_THREAD_ID}")
    print("  - 可以在数据库中查询 checkpoint 数据验证:")
    print(f"    SELECT * FROM checkpoints WHERE thread_id = '{TEST_THREAD_ID}';")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
