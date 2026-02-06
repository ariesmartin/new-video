## [v6.2.0] - 2026-02-04
 
### 🚀 UX Enhancement - AI 智能感知与交互体验升级

**核心目标**: 提升 AI 助手的透明度和易用性，消除用户的等待焦虑，实现"所想即所得"的无缝创作流。

#### 1. Server-Driven Thinking UI (服务端驱动的思考可视化)
- **机制**: 后端通过 SSE 流式下发 `node_start` (节点执行)、`on_tool_start` (工具调用) 事件。
- **协议**: 新增 `status`, `desc` 字段，直接由后端定义前端显示的中文状态文本。
- **效果**:
  - 节点级: "🔍 正在分析市场趋势...", "✍️ 正在构思故事方案..."
  - 工具级: "🌐 正在搜索最新市场数据...", "📊 正在分析搜索结果..."
- **架构**: 前端 `AIAssistantBar` 仅负责渲染，状态文案完全解耦并由后端 `NODE_DISPLAY_NAMES` 配置控制。

#### 2. Seamless Prompt Carrying (无缝创作流)
- **流程**: 首页输入创意 -> `sessionStorage` 缓存 -> 自动跳转工作台 -> AI 自动读取并执行。
- **优化**: 消除"首页输入一次，进工作台还要输一次"的割裂感，实现真正的"一键开始"。
- **状态管理**: 引入 `chatService.clearSession()`，确保每次从首页进入都是干净的全新会话。

#### 3. AI Assistant Visibility & Control
- **智能显隐**: 首页隐藏 AI 助手（避免干扰），进入项目/工作台自动显示。
- **Reset Session**: 新增"重置会话"按钮（RotateCcw图标），一键清空上下文和临时状态，方便反复测试。

#### 4. Market Analyst 混合推荐逻辑 (Hybrid SDUI)
- **重构**: Phase 1 推荐逻辑改为"AI 动态推荐 + 静态全量补充"。
- **UI**: AI 推荐的题材带有 🔥 图标并高亮显示，静态分类作为补充选项折叠展示。
- **Prompt**: 修正 Prompt 注入 `GENRE_DEFINITIONS` Keys，确保 AI 输出的推荐能正确映射到前端组件。

#### 5. HomePage Experience Optimization
- **Layout Tweaks**: 调整首页构图比例，采用顶部权重布局 (Top-Weighted) 代替垂直居中，优化视觉平衡。
- **Simplification**: 移除右下角 "幕境 Studio" 水印 Logo，保持界面纯净。
- **Focus**: 强化 "创意输入区" 的视觉核心地位。

---

## [v6.1.6] - 2026-02-04

### 📝 Content Update - Market Analyst Prompt 修正

**问题**: 市场分析师 (Market Analyst) 提示词存在年份漂移 (2024/2025) 及中英混杂问题。
**修改内容**:
1. **prompts/1_Market_Analyst.md**:
   - 全面中文化提示词内容 (保留 JSON Key 为英文以兼容代码)。
   - 强制指定 **2026年** 为当前系统时间，严禁生成过时数据的年份。
   - 优化逻辑规则 (Logic Rules)，增加对 "逆袭"、"复仇" 等中文关键词的直接支持。

---

## [v6.1.5] - 2026-02-04

### ✨ Feature - 添加图像服务商设置

**问题**: 页面设置中缺少图像服务商的配置选项
**背景**: 根据 Product-Spec.md 第 3.6.1 节，项目需要分镜生图功能，应支持图像服务商配置

#### 修改文件

1. **new-fronted/src/types/index.ts**
   - `ProviderType`: 添加 `'image'` 类型

2. **new-fronted/src/components/modals/BackstageModal.tsx**
   - `SettingsTabType`: 添加 `'image'` 选项
   - 添加 `imageProviders` provider 筛选逻辑（基于 `provider_type` 字段）
   - 在设置选项卡列表中添加"图像服务商"选项卡
   - 图像服务商使用 LLM 协议列表（openai/anthropic/gemini/azure）
   - 更新路由配置支持 `image_process` 任务类型使用图像服务商
   - 添加图像服务商配置界面渲染逻辑

#### 设计说明
- **所有服务商复用 LLM 协议**：LLM/视频/图像 三类服务商都使用相同的 API 协议（openai、anthropic、gemini、azure）
- **通过 provider_type 区分类型**：使用 `provider_type` 字段（'llm' | 'video' | 'image'）区分服务商用途，而非 protocol
- **视频服务商识别方式**：通过服务商名称识别（如包含 "sora"/"runway"/"pika"），而非 protocol
- **灵活性**：例如 DALL-E 使用 OpenAI 协议，只需 provider_type='image' 即可标记为图像服务商

#### 后端修改

3. **backend/schemas/model_config.py**
   - `ProtocolType`: 移除视频专用协议（sora/runway/pika），只保留通用协议（openai/anthropic/gemini/azure）
   - `ProviderType`: 添加 `IMAGE = "image"` 类型

4. **backend/services/video_generator.py**
   - 修改视频服务商加载逻辑：通过 `name` 字段识别具体服务（sora/runway/pika），而非 `protocol`

---

## [v6.1.4] - 2026-02-03

### 🐛 Bug Fix - 修复 HTTPS 混合内容错误 (ALPN_NEGOTIATION_FAILED)

**问题**: 前端在 HTTPS 环境下无法连接到本地 HTTP 后端 (`ERR_ALPN_NEGOTIATION_FAILED`)
**根因**: `client.ts` 和 `chat.ts` 中存在硬编码的 `http://localhost:8000` URL

#### 修改文件

1. **new-fronted/src/api/client.ts** (第 5 行)
   - 修改前: `baseUrl: 'http://localhost:8000'`
   - 修改后: `baseUrl: import.meta.env.VITE_API_URL || ''`

2. **new-fronted/src/api/services/chat.ts** (第 54-56 行)
   - 修改前: 硬编码 `http://localhost:8000/api/graph/chat`
   - 修改后: 使用 `import.meta.env.VITE_API_URL` 动态构建 URL

3. **new-fronted/vite.config.ts** (新增 server.proxy 配置)
   - 添加 `/api` 代理到 `http://localhost:8000`

4. **new-fronted/.env.example** (新增)
   - 添加环境变量配置示例

#### 部署说明
- **开发环境**: 使用 Vite 代理，无需配置环境变量
- **生产环境**: 设置 `VITE_API_URL=https://api.yourdomain.com` 指向实际后端地址

---

## [v6.1.3] - 2026-02-03

### Backend - Database Service Layer 完整实现

**目标**: 实现所有 v6.0 API 所需的数据库服务方法，支持 Episodes、Shot Nodes、Canvas、Scenes、Connections 的完整 CRUD 操作。

#### 实现内容

**backend/services/database.py** 新增 30+ 个数据库方法：

##### Episodes 管理 (6 个方法)
- `list_episodes(project_id)` - 获取剧集列表
- `get_next_episode_number(project_id)` - 获取下一个剧集编号
- `create_episode(...)` - 创建剧集
- `get_episode(episode_id)` - 获取剧集详情
- `update_episode(...)` - 更新剧集信息
- `delete_episode(episode_id)` - 删除剧集（级联删除关联数据）

##### Canvas 管理 (4 个方法)
- `get_episode_canvas(episode_id)` - 获取画布数据
- `save_episode_canvas(...)` - 保存画布数据
- `update_episode_viewport(...)` - 更新视口状态
- `sync_shot_nodes_from_canvas(...)` - 同步画布节点

##### Shot Nodes 管理 (9 个方法)
- `list_shot_nodes(...)` - 获取分镜列表（支持筛选）
- `get_next_shot_number(episode_id)` - 获取下一个分镜编号
- `create_shot_node(...)` - 创建分镜
- `batch_create_shot_nodes(...)` - 批量创建分镜
- `get_shot_node(shot_id)` - 获取分镜详情
- `update_shot_node(...)` - 更新分镜
- `batch_update_shot_positions(...)` - 批量更新位置
- `delete_shot_node(shot_id)` - 删除分镜
- `_update_episode_shot_count(episode_id)` - 更新剧集计数

##### Scenes 管理 (7 个方法)
- `list_scenes(episode_id)` - 获取场景列表
- `get_next_scene_number(episode_id)` - 获取下一个场景编号
- `create_scene(...)` - 创建场景
- `get_scene(scene_id)` - 获取场景详情
- `update_scene(...)` - 更新场景
- `update_scene_master(...)` - 更新 Master 节点
- `delete_scene(scene_id)` - 删除场景

##### Shot Connections 管理 (3 个方法)
- `list_shot_connections(episode_id)` - 获取连线列表
- `create_shot_connection(...)` - 创建连线
- `delete_shot_connection(connection_id)` - 删除连线

#### 技术特点

1. **级联操作**: 删除剧集时自动清理分镜、场景、连线
2. **自动计数**: 创建/删除分镜时自动更新剧集的分镜计数
3. **批量操作**: 支持批量创建分镜和批量更新位置
4. **编号管理**: 自动递增剧集、分镜、场景的编号
5. **事务安全**: 使用 Supabase PostgREST API 的原子操作

#### 状态

✅ **所有 v6.0 数据库方法已实现完毕**

---

## [v6.1.1] - 2026-02-03

### Backend - OpenAPI Schema Completeness Fix

**Problem**: Backend OpenAPI schema was incomplete with generic `dict` and `list[dict]` types, making it impossible to generate accurate TypeScript types using `openapi-typescript`.

**Solution**: Added comprehensive response schemas and fixed all API endpoints to use proper Pydantic models.

#### Files Created
- **backend/schemas/responses.py** - New comprehensive response schemas:
  - `NodeWithLayout`, `NodeTreeResponseData`, `LayoutUpdateResponseData`, `BatchLayoutUpdateResponseData`
  - `AssetResponseData`, `AssetExtractResponseData`
  - `TopologyResponse`
  - `SSEEventBase` and derived event types (SSENodeStartEvent, SSENodeEndEvent, SSETokenEvent, SSEDoneEvent, SSEErrorEvent)
  - `BranchInfo`, `RollbackResponseData`, `StatePatchResponseData`, `CheckpointInfo`
  - `ToolListResponse`, `ToolStatusResponse`
  - `ProviderResponseData`, `MappingResponseData`, `TaskTypeInfo`

#### Files Modified
- **backend/api/nodes.py**
  - Changed `SuccessResponse[list[dict]]` → `SuccessResponse[list[NodeWithLayout]]`
  - Changed `SuccessResponse[dict]` → `SuccessResponse[LayoutUpdateResponseData]` (layout update)
  - Changed `SuccessResponse[dict]` → `SuccessResponse[BatchLayoutUpdateResponseData]` (batch layout)
  - Changed `SuccessResponse[dict]` → `SuccessResponse[NodeTreeResponseData]` (tree)
  - Added `response_model=None` to DELETE endpoint

- **backend/api/models.py**
  - Changed `SuccessResponse[dict]` → `SuccessResponse[ProviderResponseData]` (create/update provider)
  - Changed `SuccessResponse[list[dict]]` → `SuccessResponse[list[ProviderResponseData]]` (list providers)
  - Changed `SuccessResponse[dict]` → `SuccessResponse[MappingResponseData]` (create/update mapping)
  - Changed `SuccessResponse[list[dict]]` → `SuccessResponse[list[MappingResponseData]]` (list mappings)
  - Changed `SuccessResponse[list[dict]]` → `SuccessResponse[list[TaskTypeInfo]]` (task types)
  - Added `response_model=None` to DELETE endpoints

- **backend/api/assets.py**
  - Changed `PaginatedResponse[dict]` → `PaginatedResponse[AssetResponseData]` (list assets)
  - Changed `SuccessResponse[dict]` → `SuccessResponse[AssetResponseData]` (get/create/update asset)
  - Changed `SuccessResponse[dict]` → `SuccessResponse[AssetExtractResponseData]` (extract)
  - Added `response_model=None` to DELETE endpoint

- **backend/api/graph.py**
  - Added `response_model=TopologyResponse` to `/topology` endpoint
  - Enhanced `/chat` endpoint documentation with SSE event types
  - Added OpenAPI response specification for streaming endpoint

- **backend/api/graph_branch.py**
  - Changed `SuccessResponse[list[dict]]` → `SuccessResponse[list[BranchInfo]]` (list branches)
  - Changed `SuccessResponse[dict]` → `SuccessResponse[RollbackResponseData]` (rollback)
  - Changed `SuccessResponse[dict]` → `SuccessResponse[StatePatchResponseData]` (patch state)
  - Changed `SuccessResponse[list[dict]]` → `SuccessResponse[list[CheckpointInfo]]` (history)

- **backend/api/tools.py**
  - Added `response_model=ToolListResponse` to `/` endpoint
  - Added `response_model=ToolStatusResponse` to `/status` endpoint

- **backend/api/projects.py**
  - Added `response_model=None` to DELETE endpoint

- **backend/api/jobs.py**
  - Added `response_model=None` to cancel endpoint

#### Impact
Backend now exposes a **complete OpenAPI schema** at `/openapi.json` that can be used with:
```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts
```

This generates fully typed TypeScript definitions for all 57 API endpoints.

---

## [v6.1.2] - 2026-02-03

### Backend - v6.0 API 完整实现

**目标**: 实现 Product-Spec.md v6.0 定义的所有后端 API，支持每集独立画布架构。

**实现内容**:

#### 1. Schema 定义层 (4个文件)

**backend/schemas/episode.py**
- `EpisodeBase`, `EpisodeCreate`, `EpisodeUpdate`
- `EpisodeListResponse` - 列表响应（精简）
- `EpisodeResponse` - 详情响应（含 canvas_data）
- `from_db()` 工厂方法用于数据库模型转换

**backend/schemas/shot.py**
- `ShotDetails` - 嵌套详情（对白、音效、运镜、生成参数、参考图）
- `ShotCreate`, `ShotUpdate`
- `ShotResponse` - 完整 ShotNode 响应
- `ShotBatchCreate`, `ShotBatchUpdate` - 批量操作

**backend/schemas/canvas.py**
- `CanvasViewport` - 视口状态 (x, y, zoom)
- `Connection` - 节点连线 (source, target, type)
- `CanvasData` - 完整画布数据 (viewport + nodes + connections)
- `CanvasSaveRequest` - 保存请求

**backend/schemas/scene.py**
- `SceneCreate`, `SceneUpdate`
- `SceneResponse` - 场景响应（含 master_node_id）
- `from_db()` 工厂方法

#### 2. API 路由层 (5个文件，20个端点)

**backend/api/episodes.py** - 剧集管理 (5 endpoints)
```
GET    /projects/{project_id}/episodes          - 获取剧集列表
POST   /projects/{project_id}/episodes          - 创建剧集
GET    /projects/{project_id}/episodes/{id}     - 获取剧集详情
PUT    /projects/{project_id}/episodes/{id}     - 更新剧集
DELETE /projects/{project_id}/episodes/{id}     - 删除剧集
```

**backend/api/canvas.py** - 画布状态 (3 endpoints)
```
GET    /episodes/{episode_id}/canvas            - 获取画布状态
PUT    /episodes/{episode_id}/canvas            - 保存画布状态
PATCH  /episodes/{episode_id}/canvas/viewport   - 更新视口
```

**backend/api/shots.py** - 分镜节点 (7 endpoints)
```
GET    /episodes/{episode_id}/shots             - 获取分镜列表
POST   /episodes/{episode_id}/shots             - 创建分镜
POST   /episodes/{episode_id}/shots/batch      - 批量创建
GET    /episodes/{episode_id}/shots/{id}       - 获取分镜详情
PUT    /episodes/{episode_id}/shots/{id}       - 更新分镜
DELETE /episodes/{episode_id}/shots/{id}       - 删除分镜
PUT    /episodes/{episode_id}/shots/batch/position - 批量更新位置
```

**backend/api/scenes.py** - 场景管理 (5 endpoints)
```
GET    /episodes/{episode_id}/scenes            - 获取场景列表
POST   /episodes/{episode_id}/scenes            - 创建场景
GET    /episodes/{episode_id}/scenes/{id}       - 获取场景详情
PUT    /episodes/{episode_id}/scenes/{id}       - 更新场景
DELETE /episodes/{episode_id}/scenes/{id}       - 删除场景
```

**backend/api/connections.py** - 连线管理 (3 endpoints)
```
GET    /episodes/{episode_id}/connections       - 获取连线列表
POST   /episodes/{episode_id}/connections       - 创建连线
DELETE /episodes/{episode_id}/connections/{id}  - 删除连线
```

#### 3. 数据库迁移

**backend/supabase/migrations/003_v6_schema.sql**
- `episodes` 表 - 剧集管理（含 canvas_data JSONB）
- `shot_nodes` 表 - 分镜节点（极简结构）
- `scenes` 表 - 场景管理
- `shot_connections` 表 - 节点连线（sequence/reference）
- 自动更新 updated_at 触发器
- RLS 策略启用

#### 4. 路由注册更新

**backend/api/__init__.py**
- 导出 5 个新 router: episodes, shots, canvas, scenes, connections

**backend/main.py**
- 导入并注册 5 个新 router
- 所有 v6.0 API 统一前缀 `/api`

#### 关键特性

1. **自动编号**: 创建剧集/分镜/场景时自动递增编号
2. **级联删除**: 删除剧集时级联删除关联的分镜、场景、连线
3. **WebSocket 通知**: 画布保存时通知其他客户端
4. **批量操作**: 支持批量创建分镜和批量更新位置
5. **Scene Master**: 创建场景时可同时创建 Scene Master 节点

#### API 总览

| API 模块 | 端点数 | 前缀 |
|---------|--------|------|
| Episodes | 5 | `/api/projects/{id}/episodes` |
| Canvas | 3 | `/api/episodes/{id}/canvas` |
| Shots | 7 | `/api/episodes/{id}/shots` |
| Scenes | 5 | `/api/episodes/{id}/scenes` |
| Connections | 3 | `/api/episodes/{id}/connections` |
| **总计** | **23** | - |

---

## [v6.1 新前端 v6.0 架构实施计划] - 2026-02-03

### 概述
基于 **v6.0 画布架构重构**规范，制定新前端代码的实施计划。v6.0 定义了完整的 Node 架构和动态面板系统，但待实现功能列表显示这些功能**尚未实现**，需要按此计划执行开发。

### 实施基础
- **设计规范**: Frontend-Design-V3.md (v6.0 章节)
- **系统架构**: System-Architecture-V3.md (Node 系统)
- **产品规格**: Product-Spec-V3.md (分镜引擎 v6.0)
- **变更日志**: Product-Spec-CHANGELOG.md (v6.0 待实现清单)

### 核心实施内容

#### 1. 数据模型重构 (v6.0 规范)
- ✅ **废弃 Card 类型** - 完全删除 Card/ShotCard/CardContent 定义
- ✅ **采用 ShotNode** - 使用 v6.0 定义的极简节点结构
- ✅ **每集独立画布** - 实现 CanvasData 每集隔离架构
- ✅ **状态色标系统** - 5种状态颜色 (pending/processing/completed/approved/revision)

#### 2. 组件重构 (v6.0 规范)
- ✅ **ShotCard → ShotNode** - 280×200px → 120×80px，支持展开/折叠
- ✅ **SceneMasterCard → SceneMasterNode** - 25格缩略图总览
- ✅ **动态左侧面板** - 48px 图标窄条 ↔ 240px 展开面板
- ✅ **动态右侧面板** - 导演台/节点编辑/隐藏 三种模式
- ✅ **AIAssistantBar** - 底部浮动栏 (新组件)

#### 3. 交互模式重构 (v6.0 规范)
- ✅ **纯净画布优先** - 默认仅显示画布，无干扰
- ✅ **点击展开逻辑** - 点击节点 → 右侧面板编辑详情
- ✅ **每集画布切换** - 点击剧集切换独立画布数据
- ✅ **ESC/空白关闭** - 点击画布空白自动关闭面板

#### 4. API 对接 (V3 后端)
- ✅ **画布状态 API** - GET/PUT /api/storyboards/{episode_id}/canvas
- ✅ **节点 CRUD** - /api/nodes/* (V3 已实现)
- ✅ **图像编辑 API** - Inpaint/Outpaint/Virtual Camera (需后端实现)
- ✅ **AI 助手 API** - /api/graph/chat + SSE (V3 已实现)

### 实施路线图 (6周计划)

| 阶段 | 周期 | 任务 | 验收标准 |
|------|------|------|----------|
| **Phase 1** | 第1-2周 | 类型重构 + ShotNode 组件 | ShotNode 120×80px，展开/折叠正常 |
| **Phase 2** | 第3-4周 | 动态面板 + 每集画布 | 左右面板动态切换，画布按集隔离 |
| **Phase 3** | 第5-6周 | AI 助手 + 图像编辑 | 底部 AI 栏，图像编辑功能完整 |

### v6.0 待实现清单状态

| 功能 | v6.0 状态 | 本计划安排 | 预计完成 |
|------|----------|-----------|----------|
| ShotCard → ShotNode | 🔴 待实现 | Phase 1 | 第2周 |
| LeftSidebar 收缩/展开 | 🔴 待实现 | Phase 2 | 第3周 |
| RightPanel 动态模式 | 🔴 待实现 | Phase 2 | 第3周 |
| AIAssistantBar 底部栏 | 🔴 待实现 | Phase 3 | 第5周 |
| 每集画布数据持久化 | 🔴 待实现 | Phase 2 | 第4周 |
| 画布切换动画 | 🔴 待实现 | Phase 2 | 第4周 |
| 双击聚焦动画 | 🔴 待实现 | Phase 2 | 第4周 |
| 节点展开/折叠动画 | 🔴 待实现 | Phase 1 | 第2周 |

---

## [v6.0 画布架构重构 (Canvas Architecture Refactor)] - 2026-02-03

### 架构重构 (Architecture Refactor)

**核心目标**: 将画布从卡片形式改为节点形式，实现动态面板交互，每集独立画布

**设计决策**:
- **节点形式**: ShotCard (280px×200px) → ShotNode (120px×80px)，信息密度更高
- **动态面板**: 左右面板默认收缩，按需展开，最大化画布空间
- **每集画布**: 每集拥有独立画布数据，点击剧集切换画布
- **AI位置**: 右侧边栏 → 底部浮动栏，始终可见

### 文档更新 (Documentation)

- **Frontend-Design-V3.md**
  - 重写章节 2: 整体布局架构 - 更新为动态面板架构
  - 重写章节 3.3: 分镜画布 - 卡片形式改为节点形式
  - 新增: AI助手底部浮动栏设计规范
  - 新增: 节点编辑面板设计规范
  - 新增: 每集独立画布数据模型

- **System-Architecture-V3.md**
  - 章节 5.2: 更新 JSONB 内容结构
  - 新增 Canvas 节点类型 (画布状态存储)
  - 新增 Shot 节点结构 (支持节点形式显示字段)

- **Product-Spec-V3.md**
  - 重写章节 3.5: 分镜拆分引擎 - 节点形式 + 每集画布
  - 重写章节 4.3: AI助手 - 底部浮动栏设计
  - 新增: 四种视图状态交互逻辑
  - 新增: 节点展开/折叠交互规范

### 前端架构变更 (Frontend Changes)

#### 类型定义扩展 (`frontend/types/index.ts`)
- 新增 `CanvasData` 接口 (每集画布数据)
- 新增 `ShotNode` 接口 (极简节点)
- 新增 `ShotDetails` 接口 (完整详情)
- 更新 `CanvasState` 添加 `currentCanvas`

#### 组件重构
- **`ShotCard.tsx` → `ShotNode.tsx`**
  - 尺寸: 280px×200px → 120px×80px (默认)
  - 支持展开状态 (280px×自适应)
  - 精简信息显示 (编号+缩略图+景别)
  - 详情移至右侧面板

- **`StoryboardCanvas.tsx`**
  - 支持每集画布切换
  - 新增 `SceneMasterNode` 组件
  - 更新连线系统适配节点形式
  - 双击聚焦动画

- **`LeftSidebar.tsx` → 动态左侧面板**
  - 默认收缩为图标窄条 (48px)
  - 点击图标展开功能列表 (240px)
  - 点击剧集触发右侧面板

- **`RightPanel.tsx` → 动态右侧面板**
  - 三种模式: 隐藏 / 导演台 / 节点编辑
  - 导演台: 剧本/分镜/卡片 三标签
  - 节点编辑: 显示选中节点的完整属性
  - 点击空白处自动关闭

- **新增 `AIAssistantBar.tsx`**
  - 底部浮动栏位置
  - 始终可见，可展开/收起
  - 上下文感知 (显示当前选中对象)
  - 快捷指令按钮组

#### 状态管理更新
- **UIStore 扩展**
  - `leftPanel`: 展开状态 + 选中标签 + 选中剧集
  - `rightPanel`: 打开状态 + 显示模式 + 数据
  - `canvas`: 当前剧集ID + 视口状态

### 交互逻辑变更 (Interaction Changes)

| 操作 | 旧版 (v5.x) | 新版 (v6.0) |
|------|-------------|-------------|
| **默认视图** | 三栏全部展开 | 仅画布可见 |
| **切换剧集** | 同一画布内容变化 | 切换独立画布 |
| **显示分镜详情** | 卡片内嵌完整信息 | 点击节点 → 右侧面板 |
| **AI助手位置** | 右侧边栏 | 底部浮动栏 |
| **关闭面板** | 手动点击关闭按钮 | 点击画布空白自动关闭 |

### 画布数据模型 (Canvas Data Model)

```typescript
// 每集独立画布
interface CanvasData {
  id: string;
  episodeId: string;
  nodes: ShotNode[];
  connections: Connection[];
  viewport: { x: number; y: number; zoom: number };
}

// 极简节点
interface ShotNode {
  id: string;
  type: 'scene_master' | 'shot';
  number: number;
  title: string;           // 景别
  subtitle?: string;       // 运镜
  thumbnailUrl?: string;   // 缩略图
  status: NodeStatus;
  position: { x: number; y: number };
  details?: ShotDetails;   // 完整详情
}
```

### 用户体验提升 (UX Improvements)

| 优化项 | 旧版 | 新版 | 提升 |
|--------|------|------|------|
| **画布容量** | 20-30个卡片拥挤 | 100+节点清晰 | ↑ 300% |
| **默认工作区** | 三栏占用 560px | 纯净画布 | ↑ 100% |
| **信息层级** | 所有信息平铺 | 精简+详情分层 | ↑ 可读性 |
| **切换效率** | 多步操作 | 点击即切换画布 | ↑ 50% |
| **AI可访问性** | 需展开侧边栏 | 始终可见 | ↑ 即时性 |

### 待实现功能 (Next Steps)

- [ ] ShotCard → ShotNode 组件重构
- [ ] LeftSidebar 收缩/展开逻辑
- [ ] RightPanel 动态模式切换
- [ ] AIAssistantBar 底部浮动栏
- [ ] 每集画布数据持久化
- [ ] 画布切换动画
- [ ] 双击聚焦动画
- [ ] 节点展开/折叠动画

---

## [v5.1 AI聊天系统全面检查与修复计划] - 2026-02-02

### 🔍 系统性检查报告

**执行时间**: 2026-02-02
**检查范围**: 前端聊天组件、后端API、LangGraph Agent节点、状态管理、WebSocket连接
**发现问题**: 21个 (Critical: 6, Major: 9, Minor: 6)

**新增发现** (来自深度后台分析):
- 前端: 4个新问题 (ui_interaction丢失、死代码、JSON解析脆弱、消息丢失)
- 后端: 3个新问题 (Redis连接泄漏、状态序列化丢失、线程安全问题)

---

### 🔴 Critical Issues (致命问题)

#### CI-001: SSE事件解析错误静默忽略
- **位置**: `frontend/services/api.ts` 第132-134行
- **影响**: JSON解析错误被静默忽略，导致事件丢失，用户看不到AI响应
- **修复状态**: 待修复
- **修复代码**:
```typescript
} catch (err) {
    console.error('[SSE] Parse error:', line, err);
    onEvent({ type: 'error', message: `Failed to parse event: ${err.message}` });
}
```

#### CI-002: 消息ID生成器冲突
- **位置**: `ChatConsole.tsx` 第69-73行 和 `ProjectContext.tsx` 第122-126行重复定义
- **影响**: 可能导致消息key重复，React渲染异常
- **修复状态**: 待修复
- **方案**: 统一使用全局ID生成器或uuid库

#### CI-003: Agent节点错误状态未更新
- **位置**: 多个节点文件 (master_router.py, story_planner.py 等)
- **影响**: 所有节点在异常时只记录日志，没有更新 `error_message` 状态字段，前端无法获知后端错误详情
- **修复状态**: 待修复
- **修复代码示例**:
```python
except (json.JSONDecodeError, IndexError) as e:
    logger.error("Failed to parse", error=str(e))
    return {
        "error_message": f"Failed to parse agent action: {str(e)}",
        "last_successful_node": "master_router",
    }
```

#### CI-004: ProjectContext丢失ui_interaction数据 [NEW]
- **位置**: `frontend/store/ProjectContext.tsx` 第396-414行
- **影响**: AI返回的交互组件(按钮、选择器)永远无法显示在新的聊天消息中，只有在刷新页面重载历史记录时才可能出现
- **严重度**: 🔴 这是SDUI功能完全失效的根本原因
- **修复状态**: 待修复
- **修复代码**:
```typescript
case 'done':
  if (accumulatedContent || event.state?.ui_interaction) {
    addMessage({
      id: aiMessageId,
      role: 'assistant',
      content: accumulatedContent,
      modelName: 'LangGraph',
      timestamp: Date.now(),
      type: 'chat',
      ui_interaction: event.state?.ui_interaction as any  // FIX: 提取ui_interaction
    });
  }
  break;
```

#### CI-005: Redis连接泄漏 [NEW]
- **位置**: `backend/api/websocket.py` 第77、137行
- **影响**: 每次WebSocket操作都创建新Redis连接且从不关闭，导致连接池耗尽，长时间运行后系统崩溃
- **严重度**: 🔴 系统稳定性威胁
- **修复状态**: 待修复
- **修复方案**: 使用连接池，确保finally中关闭连接

#### CI-006: 状态序列化导致数据丢失 [NEW]
- **位置**: `backend/api/graph.py` 第246-284行的 `_serialize_state`
- **影响**: 仅提取文本内容，丢失工具调用、多模态内容等元数据，前端收到的消息不完整，SDUI交互块无法正确渲染
- **严重度**: 🔴 数据完整性破坏
- **修复状态**: 待修复
- **修复方案**: 保留原始结构，只转换不可序列化类型

---

### 🟠 Major Issues (严重问题)

#### MA-001: 流式响应错误处理不完整
- **位置**: `api.ts` 第144-148行
- **问题**: 没有处理网络超时、CORS错误等场景
- **修复状态**: 待修复

#### MA-002: Graph未编译错误未优雅降级
- **位置**: `main_graph.py` 第198-200行
- **问题**: 直接抛出RuntimeError会导致整个请求失败
- **修复状态**: 待修复
- **方案**: 返回优雅的错误响应，触发自动编译

#### MA-003: Master Router路由失败未正确处理
- **位置**: `master_router.py` 第136-138行
- **问题**: JSON解析失败时 `routed_agent` 保持为None，会导致 `_route_after_master_router` 返回"end"
- **修复状态**: 待修复
- **方案**: 添加默认值或重试机制

#### MA-004: 历史消息内容类型处理不完整
- **位置**: `ProjectContext.tsx` 第211-221行
- **问题**: 对undefined、null、Symbol等特殊类型处理不够健壮
- **修复状态**: 待修复

#### MA-005: UI Interaction Block未在streaming时显示
- **位置**: `ChatConsole.tsx` 第206-210行
- **问题**: UI交互块只在完整消息中显示，streaming过程中无法操作
- **修复状态**: 待修复
- **方案**: 在streamingContent解析时提前提取ui_interaction

#### MA-006: useChat Hook是死代码 [NEW]
- **位置**: `frontend/hooks/useChat.ts`
- **问题**: 包含更完善的逻辑(情绪曲线处理、日志消息、节点状态管理)，但未在项目中任何地方被使用。`ProjectContext`重新实现了一套简略且有缺陷的流式处理逻辑
- **影响**: 代码维护分裂，且`ProjectContext`缺少`useChat`已实现的特性
- **修复状态**: 待重构
- **方案**: 废弃ProjectContext中的手动流式逻辑，统一使用useChat

#### MA-007: ChatConsole JSON解析逻辑脆弱 [NEW]
- **位置**: `frontend/components/ChatConsole.tsx` 第20-50行的`extractReadableText`
- **问题**: 使用简单的`{`计数器来提取JSON。如果JSON字符串内部包含大括号(例如`{"text": "something { bracket"}`)，解析将失败或截断
- **影响**: 复杂内容显示异常，或者直接显示原始JSON字符串
- **修复状态**: 待修复
- **方案**: 使用带字符串感知的括号计数器

#### MA-008: WebSocket ConnectionManager线程不安全 [NEW]
- **位置**: `backend/api/websocket.py` 第39-44行
- **问题**: `disconnect`方法没有锁保护，在并发场景下可能出现竞态条件
- **影响**: 高并发时可能抛出异常或导致连接管理混乱
- **修复状态**: 待修复
- **方案**: 添加asyncio.Lock保护

#### MA-009: approve端点astream调用不安全 [NEW]
- **位置**: `backend/api/graph.py` 第173行
- **问题**: `async for _ in graph.astream(None, config): pass` 没有明确的停止条件，如果没有interrupt会一直运行到END
- **影响**: 可能阻塞很长时间，用户不知道执行进度
- **修复状态**: 待修复
- **方案**: 添加超时控制和进度反馈

---

### 🟡 Minor Issues (轻微问题)

#### MI-001: 缺少WebSocket重连机制
- **位置**: `websocket.py`
- **问题**: 连接断开后需要手动刷新页面重连
- **修复状态**: 待评估

#### MI-002: 缺少请求超时控制
- **位置**: `api.ts` streamChat函数
- **问题**: 没有设置请求超时，可能导致无限等待
- **修复状态**: 待修复

#### MI-003: 日志消息过多
- **位置**: `ProjectContext.tsx` handleStreamingResponse
- **问题**: 每行都打印console.log，影响性能
- **修复状态**: 待优化

#### MI-004: ActionBlockRenderer图标动态加载无回退 [NEW]
- **位置**: `frontend/components/ActionBlockRenderer.tsx` 第58-60行
- **问题**: 如果后端返回的icon名称在Lucide中不存在，将导致IconComponent为undefined
- **修复状态**: 待优化
- **方案**: 添加默认图标回退逻辑

#### MI-005: 内存泄漏风险 [NEW]
- **位置**: `ProjectContext.tsx`
- **问题**: abortController存储在state中，但在组件卸载时没有触发abort()
- **修复状态**: 待优化

#### MI-006: 缺少详细的错误类型 [NEW]
- **位置**: `backend/api/graph.py` 错误处理
- **问题**: 所有错误都统一返回`{type: 'error', message: str(e)}`，前端无法区分验证错误、系统错误、LLM错误等
- **修复状态**: 待优化

---

### 📊 功能实现矩阵 (更新后)

| 功能模块 | 实现度 | 问题数 | 状态 |
|---------|-------|-------|------|
| SSE流式通信 | 70% | 4 | ❌ 需要修复 |
| 消息状态管理 | 65% | 5 | ❌ 需要修复 |
| Agent路由 | 75% | 3 | ⚠️ 需要修复 |
| UI交互块(SDUI) | 40% | 2 | ❌ 严重缺陷 |
| 错误处理 | 50% | 6 | ❌ 严重不足 |
| WebSocket推送 | 60% | 4 | ❌ 需要修复 |
| 状态序列化 | 60% | 2 | ❌ 数据丢失 |

---

### 🎯 修复优先级与时间线 (更新后)

**立即修复 (P0) - 本周完成**:
- CI-004: **ui_interaction丢失** (SDUI功能失效根本原因)
- CI-005: **Redis连接泄漏** (系统稳定性威胁)
- CI-006: **状态序列化数据丢失** (数据完整性破坏)
- CI-001: SSE事件解析错误处理

**本周修复 (P1) - 两周内完成**:
- CI-003: Agent节点错误状态更新
- MA-003: Master Router路由失败处理
- MA-006: useChat死代码重构
- MA-007: JSON解析逻辑脆弱
- MA-008: WebSocket线程安全问题

**下月修复 (P2) - 一个月内完成**:
- MA-001: 流式响应错误处理
- MA-009: approve端点安全调用
- CI-002: 消息ID生成器统一
- MA-004: 历史消息类型处理
- MA-002: Graph编译错误优雅降级
- MA-005: UI交互块streaming显示
- MI-001 ~ MI-006: 各项优化

---

## [v5.0 模型管理重构 (Simplified Model Management)] - 2026-02-02

### 用户体验重构 (UX Redesign)

**核心目标**: 解决原有设置页面"信息过载、操作复杂"的痛点

**设计决策**:
- **用户选择**: 采用方案 B (表格矩阵视图)
- **管理分离**: LLM Provider 和 Video Provider 完全分离管理
- **简化分类**: 15 个独立任务 → 4 大类别 (73% 决策成本降低)
- **无 fallback**: 精简架构，去掉备用模型逻辑

### 文档更新 (Documentation)

- **Product-Spec.md**
  - 新增章节 5.4: 简化版模型管理
  - 定义任务分类体系 (CREATIVE/CONTENT/QUALITY/VIDEO)
  - 描述三 Tab 设计架构
  - 添加用户体验提升对比表

- **Frontend-Design.md**
  - 重写章节 7: 全局模型管理 (v5.0 简化版)
  - 新增设计原则、任务分类体系、界面架构规范
  - 添加组件清单和状态管理规范

### 代码实现 (Implementation)

#### 类型定义扩展 (`frontend/types.ts`)
- 新增 `TaskCategory` 枚举 (4 大类别)
- 新增 `TaskCategoryConfig` 接口
- 新增 `TaskCategoryMapping` 映射表
- 新增 `CategoryRoute` 和 `TestResult` 类型

#### 状态管理重构 (`frontend/store/ModelContext.tsx`)
- 添加 `llmProviders` 和 `videoProviders` 派生状态
- 新增类别路由管理方法:
  - `updateCategoryRoute()`: 批量更新同类任务路由
  - `getCategoryRoute()`: 获取类别路由配置
  - `testCategoryRoute()`: 测试类别路由连通性
- 添加 `applySmartDefaults()`: 智能默认配置

#### 新增组件
- **`ProviderCard.tsx`**: 服务商卡片组件
  - 彩色状态指示、协议标签
  - 悬停显示编辑/删除操作
  - 模型列表预览

- **`RoutingMatrix.tsx`**: 任务路由矩阵
  - 表格布局展示 4 大类别
  - 级联选择 (服务商 → 模型)
  - Inline 测试按钮 + 结果展示

#### 设置页面重写 (`frontend/components/ModelSettingsModal.tsx`)
- 三 Tab 架构: LLM 服务商 / 视频服务商 / 任务路由
- 简化添加表单: 名称、协议、URL、Key
- 移除复杂的模型管理功能
- 表格矩阵直接配置 + 测试

### 用户体验提升 (UX Improvements)

| 优化项 | 原方案 | 新方案 | 提升 |
|--------|--------|--------|------|
| 配置项数量 | 15 个独立任务 | 4 大类别 | ↓ 73% |
| 操作步骤 | 5-7 步 | 2-3 步 | ↓ 60% |
| 界面切换 | 频繁 Tab 切换 | 单屏矩阵 | ↓ 100% |
| 模型输入 | 手动输入 | 下拉选择 | 错误归零 |
| 测试流程 | 跳转测试 | Inline 测试 | ↓ 50% 时间 |

### 向后兼容 (Backward Compatibility)
- 保留原有 `updateTaskRoute()` / `getRouteForTask()` API
- 类别路由自动展开为任务路由存储到后端
- 现有配置自动迁移到新的类别体系

---

## [v4.9 核心功能完善 (Core Features Complete)] - 2026-02-02

### 🔧 架构修复 (Architecture Fixes)
- **子图 END 问题修复** (`backend/graph/subgraphs/__init__.py`)
  - **问题**: 子图内部使用 `END` 会导致整个图终止，无法返回主图继续
  - **修复**: 替换 `END` 为 `__complete__` 节点，确保子图完成后控制权返回主图
  - **影响**: Module A/B/C 子图现在可以正确串联执行

- **视频生成 Provider 架构修正** (严重架构错误修复)
  - **问题**: 视频生成 API 密钥硬编码在 `.env` 文件中，无法通过前端动态配置
  - **问题**: 前端模型设置页面只支持 LLM Provider，没有视频生成 Provider 选项
  - **修复**:
    1. 扩展 `ProtocolType` 枚举，添加 `SORA`, `RUNWAY`, `PIKA` 视频协议
    2. 添加 `ProviderType` 枚举 (`llm` | `video`)
    3. 修改 `ModelProviderBase` 添加 `provider_type` 字段
    4. 重写 `VideoGenerator` 从数据库 `llm_providers` 表读取视频 Provider 配置
    5. 添加 `DatabaseService.list_providers_by_type()` 方法
    6. 前端 `types.ts` 扩展 `ProtocolType` 支持视频协议
    7. 前端 `ModelSettingsModal` 添加视频 Provider 协议选项
  - **影响**: 视频生成 API 现在和 LLM 一样，通过前端设置页面动态配置，存储在数据库中

### 架构完善 (Architecture)
- **子图集成到主图** (`backend/graph/main_graph.py`)
  - 导入并编译 Module A/B/C 子图
  - 替换原子节点为子图节点 (writer/editor/refiner -> module_a)
  - 添加 `_route_after_module_a` 路由函数
  - 更新 Master Router 映射支持子图路由
  - 更新 `interrupt_before` 配置支持子图入口

### 后端实现 (Backend)
- **视频生成引擎** (`backend/services/video_generator.py`)
  - 创建统一的 `VideoGenerator` 接口
  - 实现 SoraProvider (OpenAI Sora API)
  - 实现 RunwayProvider (Runway Gen-3 API)
  - 实现 PikaProvider (Pika API)
  - 支持异步生成 + 轮询状态
  - 统一的 `VideoGenerationRequest/Result` 数据模型

- **配置更新** (`backend/config.py`)
  - 添加 `SORA_API_KEY`, `RUNWAY_API_KEY`, `PIKA_API_KEY`
  - 添加 `default_video_provider` 配置
  - 添加 `video_generation_timeout` 配置

- **Job 处理器完善** (`backend/tasks/job_processor.py`)
  - 重写 `_process_video_generation` 函数
  - 实现真实视频生成逻辑
  - 添加生成状态轮询 (5秒间隔, 最多60次)
  - WebSocket 实时进度推送
  - 结果存储到 `video_results` 表

- **服务导出** (`backend/services/__init__.py`)
  - 导出 VideoGenerator 及所有相关类型

### 文档更新 (Documentation)
- **Product-Spec.md**
  - 更新章节 9 标记完成功能
  - 更新版本规划路线图

- **系统架构文档.md**
  - 更新章节 7 标记完成架构
  - 添加子图架构注意事项

---

## [v4.8 需求文档完善 (Spec Iteration)] - 2026-02-02

### 文档更新 (Documentation)
- **Product-Spec.md**
  - 新增章节 9: 未完成功能与路线图
  - 详细定义视频生成引擎需求 (Section 9.1)
  - 详细定义 Analysis Lab 可视化需求 (Section 9.2)
  - 详细定义 Provider 管理测试需求 (Section 9.3)
  - 详细定义子图集成优化需求 (Section 9.4)
  - 新增版本规划路线图 (Section 10)

- **系统架构文档.md**
  - 新增章节 7: 未完成功能架构设计
  - 视频生成引擎架构设计 (Section 7.1)
  - Analysis Lab 可视化架构设计 (Section 7.2)
  - 子图集成架构优化方案 (Section 7.3)
  - 包含数据库 Schema 设计和技术选型

### 需求澄清 (Requirements Clarification)
- ✅ MCP Client 工具箱已完成 (v4.7 验证通过)
  - DuckDuckGo 搜索
  - yt-dlp 视频工具
  - 抖音 MCP Server
  - Playwright 浏览器工具
- ✅ Canvas 数据绑定已修复 (Nodes API 已添加)
- ⚠️ 识别真正未完成项:
  1. 视频生成引擎 API 集成 (Sora/Runway/Pika)
  2. Analysis Lab 可视化组件 (情绪热力图)
  3. Provider UI 测试流程完善
  4. 子图集成到主图调用

---

## [v4.7 工具箱 (Toolbox) & Direct API] - 2026-02-02

### 新增 (Added)
- **Direct Tool Access API** (`backend/api/tools.py`)
  - 绕过 Agent 流程，直接暴露 LangChain/MCP 工具给前端调用
  - 支持 `/api/tools/search` (DuckDuckGo)
  - 支持 `/api/tools/video/info` (yt-dlp)
  - 支持 `/api/tools/douyin/info` (Douyin MCP)
  - 支持 `/api/tools/browser/scrape` (Playwright)

- **前端工具箱页面** (`frontend/components/ToolsPage.tsx`)
  - 新增独立页面，提供工具的可视化调用
  - 动态渲染工具表单 (Input/Select)
  - 实时显示工具执行结果
  - 从 Dashboard 头部 "🔧" 按钮进入

- **系统架构升级** (`系统架构文档.md`)
  - 新增 "4.3 Direct Tool Access" 章节，定义工具箱模式架构

### 修复 (Fixed)
- **Douyin MCP 集成**: 完善了后端对 `douyin-mcp-server` 的集成，支持免 Cookies 模式
- **工具注册表**: 实现了 `TOOL_REGISTRY` 机制，前端可动态获取可用工具列表

### 验证 (Verified)
- ✅ 后端 `/api/tools` 路由正常工作
- ✅ 前端工具箱页面可加载并执行工具
- ✅ 抖音无水印解析功能测试通过

---

## [v4.6 Prompt 节点补全 (Complete Prompt-Node Coverage)] - 2026-02-02

### 新增 (Added)
- **master_router_node** (`backend/graph/nodes/master_router.py`)
  - AI 驱动的智能路由节点，使用 `0_Master_Router.md`
  - 理解用户自然语言意图，提取结构化 `Agent_Action` JSON
  - 输出 `routed_agent`, `routed_function`, `routed_parameters`

- **analysis_lab_node** (`backend/graph/nodes/analysis_lab.py`)
  - 情绪曲线分析 + 定向修文节点，使用 `9_Analysis_Lab.md`
  - Task A: 生成可视化情绪热力图数据
  - Task B: 执行精准的局部内容改写

- **asset_inspector_node** (`backend/graph/nodes/asset_inspector.py`)
  - 资产提取 + 设定图 Prompt 生成节点，使用 `10_Asset_Inspector.md`
  - 从文本中提取角色、道具、场景资产
  - 生成 Nano Banana 格式的设定图提示词

- **API 路由触发修复** (`backend/api/graph.py`)
  - 修复 `/chat` 接口未触发智能路由的 BUG
  - 现在 `/chat` 强制设置 `use_master_router=True`
  - 现在 `/approve` 强制设置 `use_master_router=False`
  - 更新 `AgentState` 增加路由控制字段

- **Schema 更新** (`backend/schemas/agent_state.py`)
  - 新增 `use_master_router`, `routed_agent`, `routed_function`, `routed_parameters` (路由控制)
  - 新增 `emotion_curve`, `surgery_result` (Analysis Lab 输出)
  - 新增 `asset_prompts` (Asset Inspector 输出)

- **LangGraph 集成** (`backend/graph/main_graph.py`)
  - 添加 `master_router`, `analysis_lab`, `asset_inspector` 到图节点
  - 实现 `_route_after_master_router()` 路由函数
  - 更新入口路由 `_route_from_start()` 支持 `use_master_router` 标志

- **Frontend 更新** (`frontend/types.ts`)
  - 补全所有 `TaskType` 和 `TaskLabels`，确保前端能正确识别新节点状态

- **Frontend Hook 更新** (`frontend/hooks/useChat.ts`)
  - 完整重构 `useChat` hook，正确提取 `AgentState` 中的关键数据
  - 新增导出：`uiInteraction`, `emotionCurve`, `latestState`
  - 支持 `onStateUpdate` 回调，便于外部组件订阅状态变化

- **文档与规范** 
  - `Frontend-Design.md`: 新增 "Analysis Visualization" 和 "Asset Inspector UI" 设计规范
  - `系统架构文档.md`: 新增 "2.0.6 Prompt-Node Mapping" (11个 Prompt 完整映射表)
  - `系统架构文档.md`: 新增 "2.0.7 Dual Routing Modes" (双路由模式说明)

### 修复 (Fixed)
- **Prompt 覆盖不完整**: 现在 11 个 Prompt 文件全部有对应节点
- **路由模式缺失**: 补齐了 AI 驱动的智能路由 (`master_router_node`)
- **API 逻辑缺陷**: 修复了 `/chat` 接口未触发智能路由的关键 BUG
- **LangGraph 集成**: 新节点已正确添加到图中，有完整的边定义
- **类型定义不严谨**: `AgentState` 现在使用 strict `TypedDict` (`EmotionPoint`, `AssetPrompt`)
- **设计文档遗漏**: 补齐了新节点的前端 UI/UX 规范

### 技术说明 (Technical Notes)
**双路由模式工作原理**:
```
START
  ├─ use_master_router=True ──► master_router ──► (AI 解析) ──► 目标 Agent
  │
  └─ use_master_router=False ──► 条件路由 ──► 根据 stage 进入对应 Agent
```

- **条件路由**: 用于确定性流程（SDUI 按钮点击、阶段自动流转）
- **智能路由**: 用于自然语言意图理解（用户发送自由文本）

### 验证 (Verified)
- ✅ 所有 11 个 Prompt 文件都有对应节点
- ✅ nodes/__init__.py 导出了全部 12 个节点
- ✅ main_graph.py 包含所有节点和边定义
- ✅ TaskType 枚举包含所有必需类型
- ✅ 架构文档包含完整的映射表和集成说明

---


## [v4.5 全面集成修复 (Full Integration Fix)] - 2026-02-02

### 新增 (Added)

#### Phase D: 工具与子图实现 (Tools & Subgraphs)
- **LangGraph Tools (`backend/tools/__init__.py`)**
  - 集成 `TavilySearchResults` (Search)
  - 集成 `DuckDuckGoSearchRun` (Search)
  - 实现 `douyin_specialist_analyze` 桩代码 (MCP Client)

- **LangGraph Subgraphs (`backend/graph/subgraphs/__init__.py`)**
  - 实现 `Module A` (Writer Loop) 子图定义
  - 实现 `Module B` (Script Adapter) 子图定义
  - 实现 `Module C` (Storyboard) 子图定义

- **Job Processor 完善 (`backend/tasks/job_processor.py`)**
  - 实现视频生成基础逻辑 (`_process_video_generation`)
  - 实现 Watchdog 僵尸任务清理 (`_watchdog_scan_async`)

- **DatabaseService 增强**
  - 新增 `count_projects` 和 `count_jobs` 精确统计方法
  - 修复 API 列表接口的总数统计

#### Phase E: 验证与测试
- **全面验证**

#### Phase A: 模型管理集成 (Model Governance Integration)
- **Frontend API 层** (`frontend/services/api.ts`)
  - 新增 `createProvider`, `updateProvider`, `deleteProvider` 方法
  - 新增 `getMappings`, `createMapping`, `updateMapping`, `deleteMapping` 方法
  - 完善响应类型定义 (`ModelProviderResponse`, `ModelMappingResponse`)

- **Frontend 类型更新** (`frontend/types.ts`)
  - 更新 `ModelProvider` 接口，与后端 API 响应格式一致
  - 扩展 `TaskType` 枚举，包含所有 15 个 Agent 任务类型
  - 新增 `ModelProviderCreate`, `TaskRouteCreate` 接口

- **Frontend 状态管理重写** (`frontend/store/ModelContext.tsx`)
  - **移除 LocalStorage 依赖**：不再使用 `nc_providers` / `nc_routes` 本地存储
  - **API 驱动**：所有 CRUD 操作通过后端 API 执行
  - 新增 `isLoading`, `error` 状态用于 UI 反馈
  - 新增 `refreshProviders`, `refreshMappings` 刷新方法

- **ModelSettingsModal 重写** (`frontend/components/ModelSettingsModal.tsx`)
  - 适配新的 Context API
  - 新增创建供应商表单（替代编辑模式）
  - 新增连接测试结果显示
  - 改进加载状态和错误处理

#### Phase B: 服务端驱动 UI 协议 (SDUI Protocol)
- **Schema 定义** (`backend/schemas/common.py`)
  - 新增 `ActionButton` Pydantic Model
  - 新增 `UIInteractionBlock` Pydantic Model
  - 新增 `UIInteractionBlockType`, `ActionButtonStyle` 枚举

- **AgentState 更新** (`backend/schemas/agent_state.py`)
  - 新增 `ui_interaction: UIInteractionBlock | None` 字段
  - 更新 `create_initial_state()` 工厂函数

- **Agent 节点集成**
  - `story_planner.py`: 返回方案选择 SDUI 交互块 + SyncService
  - `skeleton_builder.py`: 返回骨架确认 SDUI 交互块 + 同步 beat_sheet
  - `writer.py`: 返回初稿操作 SDUI 交互块 + 同步 novel_content
  - `script_adapter.py`: 返回剧本操作 SDUI 交互块 + 同步 script_data

- **前端类型对齐** (`frontend/types.ts`)
  - 更新 `UIInteractionBlock` 接口，添加 `block_type`, `description`, `dismissible`, `timeout_seconds`
  - 更新 `ActionButton` 接口，添加 `disabled` 字段

- **ActionBlockRenderer 增强** (`frontend/components/ActionBlockRenderer.tsx`)
  - 支持 `description` 字段显示
  - 支持 `dismissible` 控制关闭按钮
  - 支持 `timeout_seconds` 自动消失
  - 修复 LucideIcons 类型转换问题

#### Phase C: 业务数据同步 (State-to-DB Sync)
- **SyncService** (`backend/services/sync_service.py`)
  - `sync_story_plans()`: 同步故事方案到 `story_nodes` 表
  - `sync_beat_sheet()`: 同步分集大纲
  - `sync_novel_content()`: 同步小说章节内容
  - `sync_script_data()`: 同步剧本场景
  - `sync_storyboard()`: 同步分镜数据
  - `sync_from_state()`: 批量同步 AgentState 产物

- **NodeType 扩展** (`backend/schemas/node.py`)
  - 新增 `EPISODE_OUTLINE`, `NOVEL_CHAPTER`, `SCRIPT_SCENE`, `STORYBOARD_SHOT` 类型

- **services 包更新** (`backend/services/__init__.py`)
  - 导出 `SyncService`, `get_sync_service`

### 修复 (Fixed)
- **模型管理断裂**: 前端配置现在通过 API 持久化到后端数据库
- **SDUI 协议缺失**: AgentState 现在包含 `ui_interaction` 字段
- **数据同步断裂**: LangGraph 产物现在同步到 `story_nodes` 业务表
- **类型不一致**: 前后端 ModelProvider/TaskRoute 类型定义统一

### 技术亮点 (Highlights)
- **端到端集成**: 前端 UI → API → 后端服务 → Supabase DB 完整链路
- **零 LocalStorage**: 模型配置完全服务端持久化
- **SDUI 协议激活**: Agent 可返回结构化 UI 指令
- **Graph-to-DB 桥接**: SyncService 连接 LangGraph 状态与业务表

### 验证清单 (Verification Checklist)
- [ ] 前端添加 Provider 后，`llm_providers` 表有记录
- [ ] 修改 Task Route 后，`model_mappings` 表有记录
- [ ] story_planner 返回的 `ui_interaction` 可被前端解析
- [ ] writer 生成内容后，`story_nodes` 表有对应记录
- [ ] Canvas 画布可加载 `story_nodes` 数据

---



## [v4.4 Prompt Engineering 架构 (Prompt as Code)] - 2026-02-02

### 新增 (Added)
- **PromptService 服务层** (`backend/services/prompt_service.py`)
  - 实现动态 Prompt 加载器，支持从 `prompts/*.md` 读取 System Prompt
  - 支持开发模式热重载（改 Markdown 立即生效，无需重启）
  - 生产模式启动预加载并缓存，保证高性能
  - 支持 `{variable}` 格式的变量注入
  - 自动转换为 LangChain `ChatPromptTemplate`

- **Agent 节点全面重构**
  - `market_analyst.py`: 使用 `prompts/1_Market_Analyst.md`（循证调研 + SWOT 分析）
  - `story_planner.py`: 使用 `prompts/2_Story_Planner.md`（反套路雷达 + 调性锁）
  - `skeleton_builder.py`: 使用 `prompts/3_Skeleton_Builder.md`（一致性锁 + 世界法则）
  - `writer.py`: 使用 `prompts/4_Novel_Writer.md`（质量四重锁 + 五感描写）
  - `script_adapter.py`: 使用 `prompts/5_Script_Adapter.md`（智能分场 + 资产绑定）
  - `storyboard_director.py`: 使用 `prompts/6_Storyboard_Director.md`（动态布局 + 资产注入）
  - `editor.py`: 使用 `prompts/7_Editor_Reviewer.md`（Skill 审阅矩阵）
  - `refiner.py`: 使用 `prompts/8_Refiner.md`（外科手术式精修）

- **架构文档更新** (`系统架构文档.md`)
  - 新增 "2.0 Prompt Engineering Strategy" 章节
  - 定义 Prompt 文件规范和变量命名规范
  - 文档化 PromptService API 和使用示例

### 修复 (Fixed)
- **Prompt 脱节问题**: 彻底解决 `prompts/` 文件夹中的高级 Prompt 未被代码使用的问题
- **硬编码移除**: 删除所有 Agent 节点中的硬编码 Prompt 字符串

### 技术亮点 (Highlights)
- **Prompt as Code**: System Prompt 成为可版本控制、可 Review 的代码资产
- **Document-Driven Development**: 改 Prompt Markdown = 改 AI 行为，无需触碰 Python 代码
- **Quality Control**: 反套路雷达、一致性锁、质量四重锁等高级功能全面激活

### 验证 (Verified)
- ✅ PromptService 单例正确初始化
- ✅ 所有 11 个 Prompt 文件可被正确加载
- ✅ 变量注入功能正常工作

## [v4.3 前端重构 (Frontend Refactor)] - 2026-02-02

### 新增 (Added)
- **服务端驱动 UI 协议 (Server-Driven UI Protocol)**
  - 新增 `UIInteractionBlock` 和 `ActionButton` 接口定义
  - 实现 `ActionBlockRenderer` 组件，支持动态交互按钮渲染
  - 集成至 `ChatConsole`，支持从 Agent 消息中解析并显示操作面板

- **状态持久化 (State Persistence)**
  - 在 `ProjectContext` 中实现 `fetchProjectState`
  - 新增 `restoreProjectState` 机制，实现前端与后端 LangGraph 状态同步 (支持 Time Travel)
  - 实现切换项目时自动恢复聊天记录和 Thread ID 的逻辑

- **Level 1 漏斗引导体验 (UX)**
  - 实现智能 AI 面试初始化逻辑：新建项目自动触发 "Market Analyst" 欢迎语
  - 在欢迎消息中添加 "热门题材 (Trending Genres)" 快捷操作按钮

### 修复 (Fixed)
- **类型安全 (Type Safety)**: 放宽 `CanvasBoard.tsx` 中的 `NodeTypes` 验证，解决 React Flow v12 类型不匹配问题。
- **循环依赖 (Circular Dependencies)**: 重构 `ProjectContext.tsx`，修复 `sendChatMessage` 与 `handleActionCommand` 之间的循环引用。
- **Linting**: 修复 `addEdge` 类型不匹配等多个 Lint 错误。

### 验证 (Verified)
- ✅ 项目构建成功 (`npm run build`)
- ✅ Action Block 渲染功能
- ✅ 聊天记录自动恢复逻辑

## [v4.2 前端集成 (Frontend Integration)] - 2026-02-02

### 新增 (Added)
- **ProjectContext 全面重写**
  - 对接后端 Projects API (CRUD)
  - 集成 SSE 流式聊天 (`sendChatMessage`)
  - 实现 Thread ID 会话管理
  - 自动加载项目列表

- **ChatConsole 实时对接**
  - 流式内容显示 (带光标动画)
  - 节点处理日志显示 (node_start/node_end)
  - 智能禁用状态管理 (未选择项目/生成中)

- **Dashboard 项目管理**
  - 从后端获取项目列表
  - 新建项目 Modal 交互
  - 项目选择后自动进入工作区

- **TypeScript 类型完善**
  - 添加 `env.d.ts` Vite 环境类型定义
  - 更新 `Project` 接口以匹配后端结构
  - 添加 `@types/react` `@types/react-dom` 依赖

### 修复 (Fixed)
- 修复 `streamChat` 参数顺序问题
- 修复 `ErrorBoundary` state 声明问题
- 重命名 Context API (`setCurrentProject` → `selectProject`)

## [v4.1 集成 (Integration)] - 2026-02-02

### 新增 (Added)
- **前端 API 层** (`frontend/services/api.ts`)
  - 封装所有后端 API 调用
  - 支持 SSE 流式响应处理 (`streamChat`)
  - 定义类型安全的 Project/Job/Graph API 接口

- **Chat Hook** (`frontend/hooks/useChat.ts`)
  - 处理 SSE 流式通信
  - 管理 thread_id 会话状态
  - 实时显示 token 流

- **Vite 代理** (`frontend/vite.config.ts`)
  - 配置开发环境 `/api` 代理转发至 `localhost:8000`

### 修复 (Fixed)
- **Self-hosted Supabase Supavisor 连接修复**
  - 问题: 连接 9432 端口报 "Tenant or user not found"
  - 原因: Supavisor 需要在用户名中包含 TENANT_ID
  - 解决: 使用格式 `postgres.your-tenant-id:password@host:6543/postgres`
  
- **配置最终版 `.env`**
  ```
  SUPABASE_URL=http://192.168.2.70:9000
  DATABASE_URL=postgresql://postgres.your-tenant-id:hanyu416@192.168.2.70:6543/postgres
  REDIS_URL=redis://192.168.2.70:6379/0
  ```

### 验证 (Verified)
- ✅ Supabase REST API (9000) 连通性
- ✅ PostgreSQL via Supavisor (6543) 连通性
- ✅ Redis (6379) 连通性
- ✅ 后端 Health Check 接口
- ✅ 前端 Vite Proxy 转发

## [v4.0 后端架构 (Backend Architecture)] - 2026-02-02

### 新增 (Added)
- **核心基础设施 (Core Infrastructure)**
  - `backend/config.py`: Pydantic Settings 配置管理
  - `backend/lifespan.py`: FastAPI 生命周期管理
  - `backend/main.py`: FastAPI 应用入口 (中间件、SPA模式)

- **Schema 层** (`backend/schemas/`)
  - `agent_state.py`: LangGraph AgentState TypedDict
  - `common.py`: 统一 API 响应格式
  - `project.py`: 项目 CRUD 模型
  - `node.py`: 通用节点系统
  - `job.py`: 异步任务模型
  - `model_config.py`: LLM 配置模型

- **数据库层** (`backend/supabase/migrations/`)
  - `001_initial_schema.sql`: 完整 DDL (11张表, RLS, 索引)
  - `002_vector_functions.sql`: pgvector 搜索函数

- **服务层** (`backend/services/`)
  - `database.py`: Supabase CRUD 封装
  - `storage.py`: 文件存储管理
  - `model_router.py`: 模型路由实现
  - `circuit_breaker.py`: 熔断器保护

- **LangGraph 层** (`backend/graph/`)
  - `checkpointer.py`: AsyncPostgresSaver 持久化
  - `main_graph.py`: 主状态图定义
  - `nodes/`: 6个 Agent 节点实现

- **API 层** (`backend/api/`)
  - 健康检查、项目管理、Graph 交互、任务管理、模型配置 API

- **异步任务** (`backend/tasks/`)
  - Celery 应用配置与任务处理器

### 架构亮点 (Highlights)
- **Type-First**: 全面采用强类型定义
- **Human-in-the-Loop**: 关键节点人工中断确认
- **Time Travel**: 支持状态回溯
- **Feature Flags**: 环境变量控制高级特性

## [v3.1 修复 (Fix)] - 2026-02-02
- **Spec**: 更新数据库 Schema 以匹配 Graph 架构
- **Spec**: 更新 AI 配置支持 BYOK 策略
- **Arch**: 向 AgentState 添加 `hero_state` 和 `unresolved_mysteries`

## [v3.2 修复 (Fix)] - 2026-02-02
- **Arch**: `llm_providers` 添加 `protocol` 字段
- **Frontend**: 在设置弹窗中添加协议选择器

## [v3.3 变更 (Change)] - 2026-02-02
- **技术栈变更**: 前端框架从 Next.js 迁移至 **Vite + React**
- **重构**: 修正目录拼写 `fronted` -> `frontend`
