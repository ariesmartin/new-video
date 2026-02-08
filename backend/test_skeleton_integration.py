"""
Skeleton Builder Integration Test

测试完整的骨架构建流程，包含：
1. 输入验证
2. Skeleton Builder Agent（mocked）
3. Editor Agent（mocked）
4. Refiner Agent（mocked）
5. 输出格式化
6. Action 处理

使用 unittest.mock 来 mock LLM 响应，无需真实 API 调用。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# 设置测试环境
import sys

sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.schemas.agent_state import AgentState, StageType
from backend.graph.workflows.skeleton_builder_graph import (
    build_skeleton_builder_graph,
    validate_input_node,
    request_ending_node,
    output_formatter_node,
    handle_action_node,
    route_after_validation,
    route_after_editor,
    route_after_refiner,
)


class MockLLMResponse:
    """Mock LLM 响应生成器"""

    @staticmethod
    def skeleton_builder_response() -> str:
        """模拟 Skeleton Builder 返回的大纲"""
        return """# 《极致美丽》故事大纲

## 核心设定
- **女主**: 林美丽，28岁，从丑小鸭逆袭的职场精英
- **男主**: 顾景深，30岁，冷酷总裁，内心孤独
- **核心冲突**: 女主因外貌被歧视，通过努力和蜕变赢得尊重与爱情

## 分集大纲

**第1集 丑小鸭的觉醒**
开场：林美丽因外貌被同事嘲笑，决定改变。

**第2-5集 蜕变之路**
女主开始健身、学习穿搭、提升能力。

**第6-10集 初次相遇**
女主以新形象出现在公司年会，引起男主注意。

[... 中间省略 ...]

**第80集 圆满结局**
女主成为公司VP，与男主有情人终成眷属。

## 付费卡点设计
- **第10集**: 女主蜕变后惊艳亮相
- **第25集**: 男主发现女主真实身份
- **第50集**: 重大误会与决裂
- **第75集**: 最终考验与救赎
"""

    @staticmethod
    def editor_response_high_quality() -> str:
        """模拟 Editor 返回的高质量评价"""
        return """## 审阅报告

### 总分: 85/100 ✅

**逻辑 (18/20)**: 故事线完整，因果关系清晰
**节奏 (17/20)**: 前20集hook密集，付费卡点位置合理
**人设 (17/20)**: 女主成长弧线完整，男主有层次感
**冲突 (17/20)**: 内外冲突交织，张力足够
**世界 (16/20)**: 职场设定真实可信

### 通过标准
- ✅ 所有质量指标 >= 16分
- ✅ 总分 >= 80分

**结论**: 质量达标，无需修改。"""

    @staticmethod
    def editor_response_low_quality() -> str:
        """模拟 Editor 返回的低质量评价（需要修改）"""
        return """## 审阅报告

### 总分: 65/100 ⚠️

**逻辑 (12/20)**: 第30-40集逻辑跳跃严重
**节奏 (18/20)**: 整体节奏良好
**人设 (15/20)**: 男主动机不足，缺乏说服力
**冲突 (10/20)**: 中后期冲突重复，缺乏新意
**世界 (10/20)**: 职场细节不真实

### 问题列表
1. **CRITICAL**: 第35集转折过于突兀，需要铺垫
2. **MAJOR**: 男主在第40集的行为与前设矛盾
3. **MAJOR**: 付费卡点第50集张力不足

### 改进建议
- 在第30集增加男主童年回忆，解释其行为动机
- 重写第35集，增加3个铺垫场景
- 强化第50集的冲突，增加时间限制

**结论**: 需要修改后重新提交。"""

    @staticmethod
    def refiner_response() -> str:
        """模拟 Refiner 返回的修改后大纲"""
        return """# 《极致美丽》故事大纲（修订版）

## 核心设定
- **女主**: 林美丽，28岁，从丑小鸭逆袭的职场精英
- **男主**: 顾景深，30岁，冷酷总裁，内心孤独（新增：童年被遗弃创伤）
- **核心冲突**: 女主因外貌被歧视，通过努力和蜕变赢得尊重与爱情

## 分集大纲

**第1集 丑小鸭的觉醒**
开场：林美丽因外貌被同事嘲笑，决定改变。

**第2-5集 蜕变之路**
女主开始健身、学习穿搭、提升能力。

**第6-10集 初次相遇**
女主以新形象出现在公司年会，引起男主注意。

**[修订] 第30集 童年的阴影（新增）**
插入男主回忆：童年被母亲遗弃在孤儿院，解释他对"真诚"的渴望。

**[修订] 第35集 真相大白（重写）**
增加铺垫：
1. 第33集：女主发现男主秘密调查她
2. 第34集：男主收到匿名威胁信
3. 第35集：对峙场景增加情感爆发

**[修订] 第50集 绝境（强化）**
新增时间限制：女主必须在24小时内筹集500万，否则公司破产。

[... 中间省略 ...]

**第80集 圆满结局**
女主成为公司VP，与男主有情人终成眷属。

## 付费卡点设计
- **第10集**: 女主蜕变后惊艳亮相
- **第25集**: 男主发现女主真实身份
- **第50集**: 绝境与救赎（强化冲突）
- **第75集**: 最终考验与救赎

## 修改日志
- 新增第30集男主背景故事
- 重写第35集，增加3个铺垫场景
- 强化第50集冲突，增加时间压力
"""


@pytest.fixture
def mock_agent_state() -> AgentState:
    """创建测试用的 AgentState"""
    return {
        "messages": [],
        "user_id": "test_user",
        "project_id": "test_project",
        "user_config": {
            "genre": "现代都市",
            "setting": "modern",
            "episode_count": 80,
            "episode_duration": 1.5,
            "ending_type": "HE",
            "total_episodes": 80,
        },
        "selected_plan": {
            "id": "plan_001",
            "title": "极致美丽",
            "label": "锁定《极致美丽》进行细化",
        },
        "current_stage": StageType.LEVEL_3,
        "validation_status": "complete",
        "quality_score": 0,
        "revision_count": 0,
        "routed_parameters": {},
    }


class TestValidateInputNode:
    """测试输入验证节点"""

    @pytest.mark.asyncio
    async def test_validation_complete(self, mock_agent_state):
        """测试完整输入通过验证"""
        result = await validate_input_node(mock_agent_state)

        assert result["validation_status"] == "complete"
        assert result["last_successful_node"] == "validate_input"
        assert result["current_stage"] == StageType.LEVEL_3

    @pytest.mark.asyncio
    async def test_validation_missing_plan(self, mock_agent_state):
        """测试缺少方案时验证失败"""
        mock_agent_state["selected_plan"] = {}

        result = await validate_input_node(mock_agent_state)

        assert result["validation_status"] == "incomplete"
        assert "selected_plan" in result["missing_fields"]

    @pytest.mark.asyncio
    async def test_validation_missing_ending(self, mock_agent_state):
        """测试缺少结局时验证失败"""
        mock_agent_state["user_config"]["ending_type"] = None

        result = await validate_input_node(mock_agent_state)

        assert result["validation_status"] == "incomplete"
        assert "ending_type" in result["missing_fields"]

    @pytest.mark.asyncio
    async def test_validation_auto_infer_episodes(self, mock_agent_state):
        """测试自动推断集数配置"""
        del mock_agent_state["user_config"]["total_episodes"]

        result = await validate_input_node(mock_agent_state)

        assert result["validation_status"] == "complete"
        assert result["inferred_config"]["total_episodes"] == 80


class TestRequestEndingNode:
    """测试请求结局节点"""

    @pytest.mark.asyncio
    async def test_ending_ui_created(self, mock_agent_state):
        """测试结局选择UI正确创建"""
        result = await request_ending_node(mock_agent_state)

        assert "messages" in result
        assert result["last_successful_node"] == "request_ending"
        assert "ui_interaction" in result

        ui = result["ui_interaction"]
        assert ui.block_type.value == "action_group"
        assert ui.title == "选择结局类型"
        assert len(ui.buttons) == 3  # HE, BE, OE


class TestOutputFormatterNode:
    """测试输出格式化节点"""

    @pytest.mark.asyncio
    async def test_format_high_quality(self, mock_agent_state):
        """测试高质量大纲格式化"""
        mock_agent_state["skeleton_content"] = "测试大纲内容"
        mock_agent_state["quality_score"] = 85
        mock_agent_state["revision_count"] = 1

        result = await output_formatter_node(mock_agent_state)

        assert "messages" in result
        assert result["last_successful_node"] == "output_formatter"

        message = result["messages"][0]
        assert "✅" in message.content
        assert "85/100" in message.content
        assert "《极致美丽》" in message.content

    @pytest.mark.asyncio
    async def test_format_low_quality(self, mock_agent_state):
        """测试低质量大纲格式化（显示警告）"""
        mock_agent_state["skeleton_content"] = "测试大纲内容"
        mock_agent_state["quality_score"] = 65
        mock_agent_state["revision_count"] = 3

        result = await output_formatter_node(mock_agent_state)

        message = result["messages"][0]
        assert "⚠️" in message.content
        assert "65/100" in message.content

    @pytest.mark.asyncio
    async def test_sdui_buttons_present(self, mock_agent_state):
        """测试 SDUI 按钮存在"""
        mock_agent_state["skeleton_content"] = "测试大纲"
        mock_agent_state["quality_score"] = 85

        result = await output_formatter_node(mock_agent_state)

        ui = result["ui_interaction"]
        assert len(ui.buttons) == 2
        assert ui.buttons[0].action == "confirm_skeleton"
        assert ui.buttons[1].action == "regenerate_skeleton"


class TestHandleActionNode:
    """测试动作处理节点"""

    @pytest.mark.asyncio
    async def test_confirm_skeleton(self, mock_agent_state):
        """测试确认大纲动作"""
        mock_agent_state["routed_parameters"] = {"action": "confirm_skeleton"}

        result = await handle_action_node(mock_agent_state)

        assert result["skeleton_approved"] == True
        assert result["current_stage"] == StageType.LEVEL_4
        assert "已确认" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_regenerate_skeleton(self, mock_agent_state):
        """测试重新生成动作"""
        mock_agent_state["routed_parameters"] = {
            "action": "regenerate_skeleton",
            "variation_seed": 12345,
        }
        mock_agent_state["skeleton_content"] = "旧大纲"
        mock_agent_state["quality_score"] = 75

        result = await handle_action_node(mock_agent_state)

        assert result["skeleton_content"] is None
        assert result["quality_score"] == 0
        assert result["revision_count"] == 0
        assert result["regeneration_seed"] == 12345
        assert "重新生成" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_unknown_action(self, mock_agent_state):
        """测试未知动作"""
        mock_agent_state["routed_parameters"] = {"action": "unknown_action"}

        result = await handle_action_node(mock_agent_state)

        assert "未知操作" in result["messages"][0].content
        assert result["last_successful_node"] == "handle_action_unknown"


class TestRoutingFunctions:
    """测试路由函数"""

    def test_route_after_validation_complete(self, mock_agent_state):
        """测试验证通过路由"""
        mock_agent_state["validation_status"] = "complete"

        result = route_after_validation(mock_agent_state)
        assert result == "complete"

    def test_route_after_validation_incomplete(self, mock_agent_state):
        """测试验证失败路由"""
        mock_agent_state["validation_status"] = "incomplete"

        result = route_after_validation(mock_agent_state)
        assert result == "incomplete"

    def test_route_after_editor_high_quality(self, mock_agent_state):
        """测试高质量评分路由到格式化"""
        mock_agent_state["quality_score"] = 85

        result = route_after_editor(mock_agent_state)
        assert result == "format"

    def test_route_after_editor_low_quality(self, mock_agent_state):
        """测试低质量评分路由到修复"""
        mock_agent_state["quality_score"] = 65
        mock_agent_state["review_report"] = "有问题需要修复"

        result = route_after_editor(mock_agent_state)
        assert result == "refine"

    def test_route_after_editor_max_revisions(self, mock_agent_state):
        """测试达到最大修改次数强制结束"""
        mock_agent_state["quality_score"] = 70
        mock_agent_state["revision_count"] = 3

        result = route_after_editor(mock_agent_state)
        assert result == "format"  # 强制格式化输出

    def test_route_after_editor_zero_score(self, mock_agent_state):
        """测试评分为0（系统错误）"""
        mock_agent_state["quality_score"] = 0

        result = route_after_editor(mock_agent_state)
        assert result == "format"  # 仍然格式化，但会显示错误

    def test_route_after_editor_no_report(self, mock_agent_state):
        """测试缺少审阅报告"""
        mock_agent_state["quality_score"] = 65
        mock_agent_state["review_report"] = None

        result = route_after_editor(mock_agent_state)
        assert result == "format"  # 无法修复，直接结束

    def test_route_after_refiner(self, mock_agent_state):
        """测试修复后路由"""
        mock_agent_state["revision_count"] = 1

        result = route_after_refiner(mock_agent_state)
        assert result == "review"


class TestFullWorkflow:
    """测试完整工作流"""

    @pytest.mark.asyncio
    async def test_graph_builds_successfully(self):
        """测试 Graph 能成功构建"""
        graph = build_skeleton_builder_graph()

        assert graph is not None
        nodes = list(graph.nodes.keys())

        # 验证所有节点存在
        assert "handle_action" in nodes
        assert "validate_input" in nodes
        assert "request_ending" in nodes
        assert "skeleton_builder" in nodes
        assert "editor" in nodes
        assert "refiner" in nodes
        assert "output_formatter" in nodes

    @pytest.mark.asyncio
    async def test_mocked_full_workflow_high_quality(self, mock_agent_state):
        """测试完整工作流（高质量路径）"""
        # Mock 所有 Agent
        with (
            patch("backend.agents.skeleton_builder.create_skeleton_builder_agent") as mock_skeleton,
            patch("backend.agents.quality_control.editor.create_editor_agent") as mock_editor,
            patch("backend.agents.quality_control.refiner.create_refiner_agent") as mock_refiner,
        ):
            # 设置 Mock 返回值
            mock_skeleton_agent = AsyncMock()
            mock_skeleton_agent.ainvoke.return_value = {
                "messages": [MagicMock(content=MockLLMResponse.skeleton_builder_response())],
                "skeleton_content": MockLLMResponse.skeleton_builder_response(),
            }
            mock_skeleton.return_value = mock_skeleton_agent

            mock_editor_agent = AsyncMock()
            mock_editor_agent.ainvoke.return_value = {
                "messages": [MagicMock(content=MockLLMResponse.editor_response_high_quality())],
                "review_report": MockLLMResponse.editor_response_high_quality(),
                "quality_score": 85,
            }
            mock_editor.return_value = mock_editor_agent

            mock_refiner_agent = AsyncMock()
            mock_refiner.return_value = mock_refiner_agent

            # 构建并执行 Graph
            graph = build_skeleton_builder_graph()
            result = await graph.ainvoke(mock_agent_state)

            # 验证结果
            assert result is not None
            assert result.get("quality_score") == 85
            assert result.get("skeleton_content") is not None

    @pytest.mark.asyncio
    async def test_mocked_full_workflow_with_refinement(self, mock_agent_state):
        """测试完整工作流（需要修改路径）"""
        with (
            patch("backend.agents.skeleton_builder.create_skeleton_builder_agent") as mock_skeleton,
            patch("backend.agents.quality_control.editor.create_editor_agent") as mock_editor,
            patch("backend.agents.quality_control.refiner.create_refiner_agent") as mock_refiner,
        ):
            # 第一轮：低质量，需要修改
            mock_skeleton_agent = AsyncMock()
            mock_skeleton_agent.ainvoke.return_value = {
                "messages": [MagicMock(content=MockLLMResponse.skeleton_builder_response())],
                "skeleton_content": MockLLMResponse.skeleton_builder_response(),
            }
            mock_skeleton.return_value = mock_skeleton_agent

            # Editor 第一次返回低质量
            mock_editor_agent = AsyncMock()
            editor_calls = [
                {  # 第一次调用
                    "messages": [MagicMock(content=MockLLMResponse.editor_response_low_quality())],
                    "review_report": MockLLMResponse.editor_response_low_quality(),
                    "quality_score": 65,
                },
                {  # 第二次调用（修改后）
                    "messages": [MagicMock(content=MockLLMResponse.editor_response_high_quality())],
                    "review_report": MockLLMResponse.editor_response_high_quality(),
                    "quality_score": 85,
                },
            ]
            mock_editor_agent.ainvoke.side_effect = editor_calls
            mock_editor.return_value = mock_editor_agent

            # Refiner 返回修改后的大纲
            mock_refiner_agent = AsyncMock()
            mock_refiner_agent.ainvoke.return_value = {
                "messages": [MagicMock(content=MockLLMResponse.refiner_response())],
                "refiner_output": MockLLMResponse.refiner_response(),
                "skeleton_content": MockLLMResponse.refiner_response(),
            }
            mock_refiner.return_value = mock_refiner_agent

            # 执行 Graph
            graph = build_skeleton_builder_graph()
            result = await graph.ainvoke(mock_agent_state)

            # 验证经过了一次修改
            assert result.get("quality_score") == 85
            assert result.get("revision_count", 0) >= 1

    @pytest.mark.asyncio
    async def test_mocked_action_handling(self, mock_agent_state):
        """测试动作处理流程"""
        # 先完成大纲生成
        mock_agent_state["skeleton_content"] = MockLLMResponse.skeleton_builder_response()
        mock_agent_state["quality_score"] = 85

        # 测试确认动作
        mock_agent_state["routed_parameters"] = {"action": "confirm_skeleton"}

        graph = build_skeleton_builder_graph()
        result = await graph.ainvoke(mock_agent_state)

        assert result.get("skeleton_approved") == True


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_max_revisions_enforced(self, mock_agent_state):
        """测试最大修改次数限制"""
        # 设置已经达到最大修改次数
        mock_agent_state["revision_count"] = 3
        mock_agent_state["quality_score"] = 70  # 低于阈值
        mock_agent_state["review_report"] = "仍需改进"

        # 应该强制结束，不再进入 refiner
        result = route_after_editor(mock_agent_state)
        assert result == "format"

    @pytest.mark.asyncio
    async def test_empty_skeleton_handling(self, mock_agent_state):
        """测试空大纲处理"""
        mock_agent_state["skeleton_content"] = ""
        mock_agent_state["quality_score"] = 0

        result = route_after_editor(mock_agent_state)
        assert result == "format"  # 应该进入格式化，显示错误状态

    @pytest.mark.asyncio
    async def test_regenerate_resets_state(self, mock_agent_state):
        """测试重新生成重置状态"""
        mock_agent_state["routed_parameters"] = {
            "action": "regenerate_skeleton",
            "variation_seed": 999,
        }
        mock_agent_state["skeleton_content"] = "旧内容"
        mock_agent_state["quality_score"] = 75
        mock_agent_state["revision_count"] = 2
        mock_agent_state["review_report"] = "旧报告"

        result = await handle_action_node(mock_agent_state)

        # 验证所有相关状态被重置
        assert result["skeleton_content"] is None
        assert result["quality_score"] == 0
        assert result["revision_count"] == 0
        assert result["review_report"] is None
        assert result["regeneration_seed"] == 999


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
