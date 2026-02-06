# AI 短剧台 - API 端点文档 (更新版)

## 新增 API 端点

本次更新完善了后端功能，新增以下 API 模块：

### 1. 资产管理 (Assets)

路径前缀: `/api/projects`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/{project_id}/assets` | 获取项目资产列表 |
| POST | `/{project_id}/assets` | 创建资产 |
| GET | `/assets/{asset_id}` | 获取资产详情 |
| PATCH | `/assets/{asset_id}` | 更新资产 |
| DELETE | `/assets/{asset_id}` | 删除资产 |
| POST | `/assets/extract` | 从内容中提取资产 |

**资产类型**: character(角色), location(场景), prop(道具)

**示例请求**:
```json
POST /api/projects/{project_id}/assets
{
  "name": "主角陈默",
  "asset_type": "character",
  "visual_tokens": {
    "age": "25",
    "gender": "male",
    "appearance": "冷酷眼神，黑色西装"
  },
  "reference_urls": ["https://example.com/ref1.jpg"],
  "prompts": {
    "sd": "a handsome man, black suit, cold eyes",
    "mj": "handsome male protagonist, cinematic lighting"
  }
}
```

### 2. 节点布局管理 (Nodes Layout)

新增批量更新布局端点：

| 方法 | 端点 | 说明 |
|------|------|------|
| PATCH | `/api/projects/nodes/{node_id}/layout` | 更新单个节点布局 |
| POST | `/api/projects/nodes/batch/layout` | 批量更新节点布局 |

**示例请求**:
```json
POST /api/projects/nodes/batch/layout
[
  {
    "node_id": "550e8400-e29b-41d4-a716-446655440001",
    "canvas_tab": "novel",
    "position_x": 100.0,
    "position_y": 200.0
  },
  {
    "node_id": "550e8400-e29b-41d4-a716-446655440002",
    "canvas_tab": "novel",
    "position_x": 100.0,
    "position_y": 400.0
  }
]
```

### 3. Graph 分支管理 (Graph Branch)

路径前缀: `/api/graph`

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/branch` | 创建分支（平行宇宙） |
| GET | `/branches/{thread_id}` | 获取分支列表 |
| POST | `/rollback` | 回滚到检查点 |
| PATCH | `/state` | 实时修补状态 |
| GET | `/history/{thread_id}` | 获取执行历史 |

**创建分支**:
```json
POST /api/graph/branch
{
  "source_thread_id": "thread_001",
  "branch_point": "chapter_3",
  "branch_name": "复仇版",
  "description": "黑化复仇走向",
  "modifications": {
    "hero_personality": "冷酷果断",
    "plot_direction": "复仇"
  }
}
```

**回滚**:
```json
POST /api/graph/rollback
{
  "thread_id": "thread_001",
  "steps_back": 2,
  "reason": "想回到之前的状态"
}
```

**实时导演**:
```json
PATCH /api/graph/state
{
  "thread_id": "thread_001",
  "patches": {
    "character_bible": {
      "hero_personality": "冷酷果断"
    }
  },
  "mode": "soft"
}
```

### 4. SDUI Action 处理 (Action)

路径前缀: `/api/action`

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/` | 处理按钮 Action |

**支持的动作类型**:

| Action | 说明 |
|--------|------|
| `select_plan` | 选择故事方案 |
| `approve_skeleton` | 确认大纲 |
| `reject_skeleton` | 拒绝大纲 |
| `next_episode` | 切换到下一集 |
| `regenerate` | 重新生成 |
| `approve_novel` | 确认小说 |
| `confirm_script` | 确认剧本 |
| `change_narrative_mode` | 切换叙事模式 |
| `generate_shots` | 生成分镜 |
| `approve_shots` | 确认分镜 |
| `create_asset` | 创建资产 |
| `update_asset` | 更新资产 |
| `delete_asset` | 删除资产 |
| `analyze_emotion` | 分析情绪曲线 |
| `apply_surgery` | 应用定向修文 |
| `update_layout` | 更新布局 |
| `batch_update_nodes` | 批量更新节点 |
| `pause_workflow` | 暂停工作流 |
| `resume_workflow` | 恢复工作流 |
| `cancel_workflow` | 取消工作流 |
| `create_branch` | 创建分支 |
| `switch_branch` | 切换分支 |
| `set_config` | 设置配置 |
| `switch_stage` | 切换阶段 |

**示例**:
```json
POST /api/action
{
  "thread_id": "thread_001",
  "action": "select_plan",
  "payload": {
    "plan": {
      "plan_id": "plan_a",
      "title": "方案A"
    }
  },
  "project_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5. WebSocket 实时通信

路径: `/api/ws/project/{project_id}`

**事件类型**:

| 事件 | 说明 |
|------|------|
| `connected` | 连接成功 |
| `node.created` | 节点创建 |
| `node.updated` | 节点更新 |
| `node.deleted` | 节点删除 |
| `job.started` | 任务开始 |
| `job.progress` | 进度更新 |
| `job.completed` | 任务完成 |
| `job.failed` | 任务失败 |

**消息格式**:
```json
{
  "type": "node.created",
  "data": {
    "node_id": "xxx",
    "type": "novel_chapter",
    "content_preview": "..."
  }
}
```

## 完整 API 列表

### 项目与节点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects` | GET/POST | 项目列表/创建 |
| `/api/projects/{id}` | GET/PATCH/DELETE | 项目详情/更新/删除 |
| `/api/projects/{id}/nodes` | GET/POST | 节点列表/创建 |
| `/api/projects/{id}/nodes/tree` | GET | 节点树结构 |
| `/api/nodes/{id}` | GET/PATCH/DELETE | 节点详情/更新/删除 |
| `/api/nodes/{id}/layout` | PATCH | 更新布局 |
| `/api/nodes/batch/layout` | POST | 批量更新布局 |

### 资产管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/projects/{id}/assets` | GET/POST | 资产列表/创建 |
| `/api/assets/{id}` | GET/PATCH/DELETE | 资产详情/更新/删除 |
| `/api/assets/extract` | POST | 提取资产 |

### LangGraph

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/graph/chat` | POST | 聊天（SSE 流式） |
| `/api/graph/approve` | POST | 确认步骤 |
| `/api/graph/{id}/state` | GET | 获取状态 |
| `/api/graph/topology` | GET | 图拓扑 |
| `/api/graph/branch` | POST | 创建分支 |
| `/api/graph/branches/{id}` | GET | 分支列表 |
| `/api/graph/rollback` | POST | 回滚 |
| `/api/graph/state` | PATCH | 修补状态 |
| `/api/graph/history/{id}` | GET | 执行历史 |

### SDUI

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/action` | POST | 处理按钮 Action |

### 任务队列

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/jobs` | GET/POST | 任务列表/创建 |
| `/api/jobs/{id}` | GET | 任务详情 |
| `/api/jobs/{id}/cancel` | POST | 取消任务 |

### 模型配置

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/models/providers` | GET/POST | 服务商列表/创建 |
| `/api/models/providers/{id}` | PATCH/DELETE | 更新/删除 |
| `/api/models/providers/test` | POST | 测试连接 |
| `/api/models/providers/{id}/refresh` | POST | 刷新模型列表 |
| `/api/models/mappings` | GET/POST | 映射列表/创建 |
| `/api/models/mappings/{id}` | PATCH/DELETE | 更新/删除 |
| `/api/models/task-types` | GET | 任务类型列表 |

### 工具箱

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tools/extract-assets` | POST | 提取资产 |
| `/api/tools/generate-prompts` | POST | 生成提示词 |
| `/api/tools/analyze-content` | POST | 分析内容 |

### WebSocket

| 端点 | 说明 |
|------|------|
| `/api/ws/project/{id}` | 项目实时同步 |

### 健康检查

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |

## 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容） |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 504 | 超时 |

## 响应格式

标准响应格式：

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

错误响应格式：

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Project not found"
  }
}
```

## 认证

所有 API（除 `/api/health` 外）都需要认证。

**Header**: `Authorization: Bearer <token>`

**获取 Token**: 通过 Supabase Auth 获取 JWT Token。
