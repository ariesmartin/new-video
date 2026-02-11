# 方案到大纲数据流失问题 - 修复验证报告

**验证时间**: 2026-02-11  
**验证方式**: 代码审查 + 单元测试  
**验证结果**: 9/9 修复已验证，1 个 bug 已修复

---

## 📊 验证摘要

| GAP | 问题 | 修复状态 | 验证状态 | 备注 |
|-----|------|---------|---------|------|
| GAP-1 | DB INSERT 缺少 plan_id | ✅ 已修复 | ✅ 已验证 | 代码中已添加 plan_id 字段 |
| GAP-2 | API 格式不匹配 | ✅ 已修复 | ✅ 已验证 | DB 行 → 标准格式转换正确 |
| GAP-3 | 路由函数状态突变 | ✅ 已修复 | ✅ 已验证 | 已拆分到独立 Node |
| GAP-4 | 自动跳转问题 | ✅ 已修复 | ✅ 已验证 | 检查 action 后才跳转 |
| GAP-5 | paywall 提取失败 | ✅ 已修复 | ✅ 已验证 | 从 plan_content 提取 |
| GAP-6 | 类型注解不匹配 | ✅ 已修复 | ✅ 已验证 | str \| list[StoryPlan] |
| GAP-7 | DB save 错误静默 | ✅ 已修复 | ✅ 已验证 | logger.error + 详细日志 |
| GAP-8 | 查询无排序 | ✅ 已修复 | ✅ 已验证 | order: updated_at.desc |
| GAP-9 | regex 脆弱 | ✅ 已修复 | ✅ 已验证 | 支持 ##/###/Fusion，修复了 f-string bug |

---

## 🔍 详细验证结果

### GAP-1: DB INSERT 添加 plan_id ✅

**文件**: `backend/graph/main_graph.py:470`

```python
"plan_id": plan_id,  # ✅ GAP-1 修复：添加 plan_id，使 get_plan() 可检索
```

**验证**: 代码审查确认 INSERT 语句包含 plan_id 字段。

---

### GAP-2: API 端点格式转换 ✅

**文件**: `backend/api/skeleton_builder.py:302-319`

```python
# ✅ GAP-2 修复：将 DB 行格式转换为 skeleton_builder 期望的标准格式
raw_plan_data = db_plan.get("plan_data") or {}
# ... 解析 plan_data ...
selected_plan = {
    "id": db_plan.get("plan_id") or raw_plan_data.get("plan_id", ""),
    "title": db_plan.get("title") or raw_plan_data.get("title", ""),
    "label": raw_plan_data.get("label", ""),
    "content": raw_plan_data.get("content", ""),
}
```

**验证**: 代码审查确认转换逻辑正确，包含所有必需字段。

---

### GAP-3: 状态突变拆分到 Node ✅

**文件**: `backend/graph/main_graph.py:1252-1351`

**关键修改**:
- 新增 `_sdui_action_router_node` 函数
- `route_from_start` 不再直接修改 state
- 状态变更通过 Node 返回值完成

```python
async def _sdui_action_router_node(state: AgentState) -> dict:
    # 状态变更在 Node 中完成
    return {
        "routed_agent": target_agent,
        "routed_parameters": action_data,
        ...
    }
```

**验证**: 代码审查确认符合 LangGraph 规范。

---

### GAP-4: 路由检查 action ✅

**文件**: `backend/graph/router.py:202-211`

```python
# ✅ GAP-4 修复：只有当 action 明确是 start_skeleton_building 时才自动跳转
if action == "start_skeleton_building" and selected_plan:
    return "skeleton_builder"

# select_plan 完成后，等待用户确认（不自动跳转）
if last_successful_node == "story_planner_plan_selected":
    return "wait_for_input"
```

**验证**: 代码审查确认逻辑正确，用户需要点击按钮才会跳转。

---

### GAP-5: paywall 从 content 提取 ✅

**文件**: `backend/graph/workflows/skeleton_builder_graph.py:583-606`

```python
# ✅ GAP-5 修复：selected_plan 标准格式没有 paywall_design 字段
# 需要从 plan content markdown 中提取
plan_content = selected_plan.get("content", "")
if plan_content:
    paywall_match = _re.search(
        r"付费卡点.*?第?\s*(\d+)\s*[-~到至]\s*(\d+)\s*集",
        plan_content,
        _re.DOTALL,
    )
```

**验证**: 代码审查确认与 validate_input_node 逻辑一致。

---

### GAP-6: 类型注解修复 ✅

**文件**: `backend/schemas/agent_state.py:243`

```python
# ✅ GAP-6 修复：story_plans 实际存储的是 AI 输出的 markdown 字符串
story_plans: str | list[StoryPlan]  # markdown 文本或结构化方案列表
```

**验证**: 代码审查确认类型注解匹配实际使用。

---

### GAP-7: DB save 错误升级 ✅

**文件**: `backend/graph/main_graph.py:485-495`

```python
# ✅ GAP-7 修复：DB 保存失败时升级为 error 级别并记录到 state
logger.error(
    "❌ Failed to save selected_plan to database - plan may not persist",
    error=str(e),
    plan_id=plan_id,
    project_id=project_id,
)
# 记录错误到 state 供前端显示
return {
    **state,
    "error": f"Failed to save plan to database: {str(e)}",
    "last_successful_node": "story_planner_save_failed",
}
```

**验证**: 代码审查确认使用 logger.error 并返回错误状态。

---

### GAP-8: ORDER BY 添加 ✅

**文件**: `backend/services/database.py:2049`

```python
"order": "updated_at.desc",  # ✅ GAP-8 修复：确定性排序，取最新选中的
```

**验证**: 代码审查确认已添加排序参数。

---

### GAP-9: regex 加固 ✅

**文件**: `backend/graph/main_graph.py:104-159`

**修复内容**:
1. 支持 `##` 和 `###` 标题
2. 支持 Fusion 特殊 ID
3. **关键 bug 修复**: `#{2,3}` → `#{{2,3}}`（f-string 双大括号转义）

**单元测试**:
```python
# 测试用例全部通过 ✅
("### 方案 A: 《测试》", "A", True)
("## 方案 B：内容", "B", True)
("### 方案C: 内容", "C", True)
("### 融合方案: 融合内容", "Fusion", True)
```

**重要发现**: 原始代码中 `#{2, 3}`（带空格）在 Python f-string 中被解释为匹配 `#` 后跟字面值 `(2, 3)`，而不是 2-3 个 `#`。已修复为 `#{{2,3}}`。

---

## 🐛 验证过程中发现的 Bug

### Bug: GAP-9 regex f-string 格式错误

**问题**: `rf"#{2, 3}\s*方案"` 中的 `{2, 3}` 被 Python 解释为表达式，结果为 `'#(2, 3)\s*方案'`（匹配 `#` 后跟字面值 `(2, 3)`）。

**修复**: 改为 `rf"#{{2,3}}\s*方案"`，使用双大括号转义。

**状态**: ✅ 已修复并验证

---

## 📋 建议后续行动

1. **部署前测试**: 在实际环境中测试完整流程（选择方案 → 生成大纲）
2. **监控日志**: 部署后观察 `Failed to save selected_plan` 错误是否消失
3. **数据库验证**: 确认 story_plans 表中开始有数据写入
4. **回归测试**: 测试各种边界情况（Fusion 方案、特殊字符等）

---

## ✅ 最终结论

所有 9 个 GAP 修复已验证完毕，代码审查 + 单元测试通过。GAP-9 在验证过程中发现 f-string bug 并已修复。建议进行部署前测试。

**验证完成时间**: 2026-02-11  
**验证人**: AI Assistant  
**状态**: ✅ 全部通过
