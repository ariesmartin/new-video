# 故事策划到大纲生成全流程梳理

## 流程概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        故事策划 → 大纲生成 → 审阅修改                          │
└─────────────────────────────────────────────────────────────────────────────┘

【故事策划阶段】
用户选择方案 → story_planner 输出确认消息 → 显示"开始大纲拆解"按钮

【大纲生成阶段】
点击"开始大纲拆解" → 路由到 skeleton_builder → 验证输入 → 生成大纲 → 质量控制审阅 → 输出结果

【审阅修改阶段】
自动触发全局审阅 → Editor 审阅整体 → 逐章审阅每个 episode → 保存审阅报告 → 前端展示
```

## 详细流程

### 1. 故事策划阶段 (Story Planner)

**文件**: `backend/graph/main_graph.py`

**触发**: 用户点击"选择方案"按钮
- Action: `select_plan`
- Payload: `{ plan_id, label }`

**处理逻辑**:
```python
# 从 plan_label 提取剧名
selected_plan = {
    "id": plan_id,
    "title": plan_title,  # 提取的剧名
    "label": plan_label,
}
```

**输出**:
- 返回确认消息（AIMessage）
- 包含 UI 交互块（ActionButton）
  - `action: "start_skeleton_building"`
  - `payload: { plan_id, plan_title }`
- State 更新: `selected_plan`, `user_config`
- 路由决策: 设置 `routed_agent: "skeleton_builder"`

### 2. 路由到 Skeleton Builder

**文件**: `backend/graph/main_graph.py`

**入口路由** (`route_from_start`):
```python
# 检测到 SDUI action: start_skeleton_building
state["routed_agent"] = "skeleton_builder"
return "master_router"
```

**Master Router 后路由** (`route_after_master`):
```python
# 从 state 读取 routed_agent
routed_agent = state.get("routed_agent")  # "skeleton_builder"
# 映射到节点
return "skeleton_builder"
```

### 3. Skeleton Builder Graph 执行

**文件**: `backend/graph/workflows/skeleton_builder_graph.py`

**入口函数**: `run_skeleton_builder()`

**输入参数**:
```python
{
    user_id: str,
    project_id: str,
    selected_plan: Dict,  # { id, title, label }
    user_config: Dict,     # { genre, setting, ending, total_episodes, ... }
    market_report: Optional[Dict]
}
```

**初始状态**:
```python
state = create_initial_state(user_id, project_id)
state["selected_plan"] = selected_plan
state["user_config"] = user_config
state["market_report"] = market_report
state["messages"] = [HumanMessage(content="请根据选中的方案生成故事大纲。")]
```

**Graph 结构**:
```
START → handle_action → validate_input → [conditional]
  ├─ [complete] → skeleton_builder → quality_control → [conditional]
  │                                              ├─ [format] → output_formatter → END
  │                                              ├─ [refine] → refiner → editor (loop)
  └─ [incomplete] → request_ending → END
```

**Node 说明**:

1. **handle_action_node**: 处理 `confirm_skeleton` 和 `regenerate_skeleton` action
2. **validate_input_node**: 检查 `selected_plan` 和 `ending_type`
   - 缺少字段则标记 `validation_status: "incomplete"`
3. **skeleton_builder_node**: 调用 Agent 生成大纲内容
4. **quality_control_node**: 调用 quality_control_graph 子图进行审阅
5. **output_formatter_node**: 格式化输出，添加 SDUI 按钮

### 4. Quality Control Graph（子图）

**文件**: `backend/graph/workflows/quality_control_graph.py`

**调用方式**: `quality_control_node` 中作为子图调用

**输入**: `skeleton_content`（从 state 获取）

**Graph 结构**:
```
START → prepare_input → [conditional]
  ├─ [review] → editor → [conditional]
  │              ├─ [end] → finalize_output → END
  │              └─ [refine] → refiner → [conditional]
  │                                  ├─ [end] → finalize_output → END
  │                                  └─ [review] → editor (full_cycle loop)
  └─ [refine] → refiner → finalize_output → END
```

**模式说明**:
- `global_review`: 全局审阅（单次审阅）
- `chapter_review`: 单章审阅
- `full_cycle`: 审阅 → 修复 → 审阅循环
- `refine_only`: 单次修复

**输出**: `{ review_report, quality_score }`

### 5. API 层保存和审阅

**文件**: `backend/api/skeleton_builder.py`

**生成流程** (`POST /api/skeleton/generate`):
```python
1. 获取用户配置: db.get_user_config(projectId)
2. 获取选中方案: db.get_plan(planId)
3. 运行 skeleton_builder_graph: run_skeleton_builder(...)
4. 解析生成的内容: json.loads(skeleton_content)
5. 保存大纲: db.save_outline(projectId, outline_data)
6. 自动触发审阅: trigger_global_review(projectId, outline_data)
```

**审阅流程** (`trigger_global_review`):
```python
1. 格式化大纲为文本: format_outline_for_review(outline_data)
2. 全局审阅: run_quality_review(outline_text, mode="global_review")
3. 逐章审阅: 
   for each episode:
       run_chapter_review(chapter_text, mode="chapter_review")
4. 构建完整报告: { overallScore, categories, tensionCurve, chapterReviews }
5. 保存审阅结果: db.save_outline_review(projectId, global_review)
```

### 6. 数据流向

**故事策划 → 大纲生成**:
```
story_planner (select_plan action)
    ↓
设置 state.selected_plan = { id, title, label }
    ↓
返回确认消息 + "开始大纲拆解" 按钮
    ↓
用户点击按钮 (action: start_skeleton_building)
    ↓
路由到 skeleton_builder
    ↓
run_skeleton_builder(selected_plan, user_config)
    ↓
Agent 生成大纲 → quality_control 审阅
    ↓
output_formatter 格式化输出
```

**大纲生成 → 审阅保存**:
```
API: POST /api/skeleton/generate
    ↓
run_skeleton_builder(...)
    ↓
生成 skeleton_content
    ↓
API 层: trigger_global_review(projectId, outline_data)
    ↓
    ├─ run_quality_review(outline_text) → 全局审阅报告
    ├─ run_chapter_review(episode_text) → 每章审阅报告
    └─ 组装全局报告 + chapterReviews 映射
    ↓
db.save_outline_review(projectId, global_review)
    ↓
前端通过 GET /api/review/{projectId}/global 获取审阅结果
```

## 关键问题修复

### 问题 1: Skeleton Builder Node 未输出 skeleton_content

**位置**: `backend/agents/skeleton_builder.py:174-193`

**修复**:
```python
# 从 Agent 输出中提取内容
output_messages = result.get("messages", [])
skeleton_content = ""
if output_messages:
    last_message = output_messages[-1]
    skeleton_content = last_message.content if hasattr(last_message, "content") else str(last_message)

return {
    "messages": output_messages,
    "skeleton_content": skeleton_content,  # 新增
    "tension_curve": tension_curve,
    "last_successful_node": "skeleton_builder",
}
```

### 问题 2: 前端 Action 标签缺失

**位置**: `new-fronted/src/components/ai/AIAssistantPanel.tsx:177-199`

**修复**: 添加 action 标签映射
```typescript
'start_skeleton_building': '📋 开始大纲拆解',
'confirm_skeleton': '✅ 确认大纲',
'regenerate_skeleton': '🔄 重新生成大纲',
```

### 问题 3: 前端 outlineService 是模拟实现

**位置**: `new-fronted/src/api/services/outline.ts`

**修复**: 实现真实 API 调用
- `generate()` → `POST /api/skeleton/generate`
- `get()` → `GET /api/skeleton/{project_id}`
- `updateNode()` → `PATCH /api/skeleton/{project_id}/nodes/{node_id}`
- `review()` → `POST /api/skeleton/{project_id}/review`
- `confirm()` → `POST /api/skeleton/{project_id}/confirm`

## 数据模型

### selected_plan (故事方案)
```typescript
{
  id: string;           // 方案 ID
  title: string;        // 剧名
  label: string;        // 显示标签
}
```

### outline_data (大纲数据)
```typescript
{
  projectId: string;
  episodes: Episode[];
  totalEpisodes: number;
  // ...
}
```

### global_review (全局审阅报告)
```typescript
{
  generatedAt: string;
  overallScore: number;
  categories: {
    logic: { score, weight, issues },
    pacing: { score, weight, issues },
    character: { score, weight, issues },
    conflict: { score, weight, issues },
    world: { score, weight, issues },
    hook: { score, weight, issues }
  };
  tensionCurve: number[];
  chapterReviews: {
    [chapterId]: {
      score: number;
      status: "passed" | "warning" | "error";
      issues: Issue[];
      comment: string;
      episodeNumber: number;
    }
  };
  summary: string;
  recommendations: string[];
}
```

## API 端点

### Skeleton Builder API

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/skeleton/generate` | 生成大纲 |
| GET | `/api/skeleton/{project_id}` | 获取大纲 |
| PATCH | `/api/skeleton/{project_id}/nodes/{node_id}` | 更新节点 |
| POST | `/api/skeleton/{project_id}/review` | 触发审阅 |
| POST | `/api/skeleton/{project_id}/confirm` | 确认大纲 |

### Review API

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/review/{project_id}/global` | 获取全局审阅 |
| GET | `/api/review/{project_id}/chapters/{chapter_id}` | 获取章节审阅 |
| POST | `/api/review/{project_id}/re_review` | 重新审阅 |
| GET | `/api/review/{project_id}/tension_curve` | 获取张力曲线 |
| GET | `/api/review/{project_id}/status` | 获取审阅状态 |

## 状态流转

```
Story Planning (L2) → Skeleton Building (L3) → Novel Writing (ModA)
      ↓                        ↓
selected_plan           skeleton_content
                        quality_score
                        review_report
```

## 下一步建议

1. ✅ 已修复 skeleton_builder_node 输出 skeleton_content
2. ✅ 已修复前端 action 标签映射
3. ✅ 已修复前端 outlineService API 调用
4. 需要测试完整流程：
   - 选择一个方案
   - 点击"开始大纲拆解"
   - 验证大纲是否正确生成
   - 验证审阅报告是否正确保存
5. 考虑添加错误处理和重试机制
6. 优化前端加载大纲的 UI 反馈
