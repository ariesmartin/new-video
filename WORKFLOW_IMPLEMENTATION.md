# Agent Registry & Workflow Plan 实现总结

## 实现概览

成功实现了增强版 Master Router，支持：
1. **Agent Registry** - 动态 Agent 发现和管理
2. **Workflow Plan** - 多步骤工作流规划
3. **与 Supabase 配置集成** - 自动使用数据库中的模型配置

## 核心文件

### 1. Agent Registry (`backend/graph/agents/registry.py`)

**功能**:
- 注册了 11 个 Agents（包括新增的 Image_Generator）
- 支持按能力、分类查询 Agents
- 自动生成 Prompt 描述
- 工作流验证（Agent 存在性、循环依赖检测）

**使用示例**:
```python
from backend.graph.agents.registry import AgentRegistry

# 获取所有 Agents
agents = AgentRegistry.get_all_agents()

# 根据能力查找
agents = AgentRegistry.find_by_capability("storyboard_generation")

# 生成 Prompt 描述
prompt = AgentRegistry.get_prompt_description()
```

### 2. AgentState 扩展 (`backend/schemas/agent_state.py`)

**新增字段**:
```python
workflow_plan: List[WorkflowStep]    # 工作流步骤列表
current_step_idx: int                 # 当前执行步骤
workflow_results: Dict[str, Any]      # 中间结果
intent_analysis: str                  # 意图分析
```

### 3. Master Router V4.1 (`backend/graph/agents/master_router.py`)

**增强功能**:
- 动态 Prompt 构建，自动注入 Agent Registry
- 支持单步骤和多步骤路由决策
- 工作流验证和继续执行检测
- 与 Supabase 模型配置集成（通过 `TaskType.ROUTER`）

**调用示例**:
```python
# 自动从 Supabase 获取 Router 的模型配置
model = await router.get_model(
    user_id=state["user_id"],
    task_type=TaskType.ROUTER,
    project_id=state.get("project_id")
)
```

### 4. Router 扩展 (`backend/graph/router.py`)

**新增**:
- `route_after_master` 支持 `master_router` 返回（工作流继续）
- `route_after_agent_execution` 新函数：检测工作流是否需要继续
- Image_Generator Agent 映射

### 5. Prompt 文档 (`prompts/0_Master_Router.md`)

**新增内容**:
- Multi-Step Workflow Planning 章节
- 触发词识别（"并"、"然后"、"先...再..."）
- 数据流示例
- 单步骤和多步骤输出格式
- 完整场景演练

## 与 Supabase 集成

### 模型配置

Master Router 会自动从 Supabase 读取 `ROUTER` task type 的模型配置：

```python
# 在 Supabase 中配置
TaskType: ROUTER
Model: gpt-4o / claude-3-5-sonnet / gemini-pro
Provider: OpenAI / Anthropic / Google
```

### 回退机制

如果没有专门的 ROUTER 配置，会回退到 `NOVEL_WRITER` 的配置：

```python
# 在 model_router.py 中
TASK_TYPE_TO_CATEGORY = {
    TaskType.ROUTER: TaskType.NOVEL_WRITER,  # 回退到创作模型
    # ...
}
```

### 数据库表

确保 Supabase 中有以下配置：

```sql
-- model_mappings 表
INSERT INTO model_mappings (user_id, task_type, model_name, provider_id) 
VALUES ('user_id', 'router', 'gpt-4o', 'provider_id');

-- llm_providers 表
INSERT INTO llm_providers (id, name, protocol, api_key) 
VALUES ('provider_id', 'OpenAI', 'openai', 'sk-...');
```

## 使用示例

### 单步骤任务

用户: "分析一下市场"

```json
{
  "target_agent": "Market_Analyst",
  "function_name": "analyze_market",
  "parameters": {},
  "ui_feedback": "正在分析市场趋势..."
}
```

### 多步骤任务

用户: "将第一章进行分镜并生成分镜图片"

```json
{
  "intent_analysis": "用户希望将第一章进行分镜拆分，然后为分镜生成预览图片",
  "workflow_plan": [
    {
      "step_id": "step_1",
      "agent": "Storyboard_Director",
      "task": "将第一章剧本转换为分镜描述",
      "depends_on": [],
      "input_mapping": {"script_data": "novel_content"},
      "output_mapping": "storyboard"
    },
    {
      "step_id": "step_2",
      "agent": "Image_Generator",
      "task": "为分镜生成预览图片",
      "depends_on": ["step_1"],
      "input_mapping": {"shots": "storyboard"},
      "output_mapping": "shot_images"
    }
  ],
  "ui_feedback": "我将为您：1) 分析第一章并生成分镜 2) 为每个分镜生成预览图",
  "estimated_steps": 2
}
```

## 测试覆盖

### 1. 单元测试 (`test_workflow_plan.py`)
- ✓ Agent Registry (11 Agents)
- ✓ Workflow Validation
- ✓ AgentState Fields
- ✓ Multi-Step Scenarios
- ✓ Master Router Integration

### 2. 集成测试 (`test_integration_workflow.py`)
- ✓ 单步骤工作流
- ✓ 多步骤工作流 (分镜+生图)
- ✓ 全流程工作流 (剧本→分镜→生图)
- ✓ 工作流恢复
- ✓ 错误处理
- ✓ SSE 事件流模拟

## 下一步

### 1. 真实 LLM 测试（需要 API Key）

创建 `test_real_llm.py` 测试真实 LLM 响应：

```bash
cd /Users/ariesmartin/Documents/new-video/backend
python -m backend.tests.test_real_llm
```

测试场景：
- "将第一章进行分镜并生成分镜图片" → 应该生成 2 步骤工作流
- "全文处理" → 应该生成 3 步骤工作流
- "分析一下市场" → 应该生成单步骤路由

### 2. 端到端测试

启动服务并测试完整流程：

```bash
cd /Users/ariesmartin/Documents/new-video/backend
python -m backend.main
```

然后通过 API 测试：

```bash
curl -X POST http://localhost:8000/api/graph/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "将第一章进行分镜并生成分镜图片"}'
```

### 3. 前端集成

前端需要处理的新事件类型：

```typescript
// workflow_planned 事件
{
  type: "workflow_planned",
  step_count: 2,
  current_step: 1,
  ui_feedback: "我将为您：1) 分析第一章并生成分镜..."
}

// workflow_progress 事件
{
  type: "workflow_progress",
  completed_steps: 1,
  total_steps: 2,
  current_step: "Image_Generator"
}
```

## 性能考虑

### Latency
- 工作流规划增加 1 次 LLM 调用（约 1-3 秒）
- 每个步骤仍需要单独的 LLM 调用
- 建议：前端显示 "规划工作流..." 进度条

### Token 使用
- Master Router Prompt 增加了 Agent Registry 描述（约 2K tokens）
- 多步骤模式输出更长的 JSON（约 500-1K tokens）
- 建议：监控 token 使用量

## 注意事项

1. **模型要求**: Master Router 需要较强的指令遵循能力，建议使用 GPT-4o 或 Claude 3.5 Sonnet

2. **Prompt 工程**: 如果 LLM 不能正确识别多步骤意图，可能需要：
   - 调整触发词列表
   - 增加更多示例
   - 降低 temperature

3. **错误处理**: 工作流验证失败时会优雅降级到单步骤模式

4. **并发限制**: 当前版本顺序执行，后续可扩展为并行执行（无依赖的步骤）

## 配置检查清单

- [ ] Supabase 中有 `ROUTER` task type 的模型配置
- [ ] `llm_providers` 表中有有效的 API Key
- [ ] `model_mappings` 表中有 user_id 到 provider 的映射
- [ ] Prompt 文件已更新到 V4.1
- [ ] 所有 Agents 已注册到 AgentRegistry

## 版本信息

- **Version**: 4.1.0
- **Date**: 2026-02-06
- **Changes**: 
  - 新增 Agent Registry 动态发现
  - 新增 Workflow Plan 多步骤规划
  - 与 Supabase 模型配置集成
