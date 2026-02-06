# 新前端样式迁移与后端对接方案

## 📋 项目背景

**目标**: 将新前端 (new-fronted) 的样式和组件完全替换为 V3 设计规范，并对接 V3 后端实现核心功能。

**策略**:
1. ✅ 保留新前端功能逻辑（不阉割）
2. ✅ 样式完全按 V3 设计规范替换
3. ✅ 先对接 V3 后端测试所有功能
4. ✅ 后续补充新前端特有功能（Inpaint/Outpaint 等）

---

## 📦 第一步：创建备份

### 1.1 当前新前端状态备份

**代码位置**: `/media/martin/HDD2/new-video/new-fronted/`

**备份内容**:
```
backup/
├── new-frontend-original/          # 完整代码备份
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── styles-original/                # 原始样式提取
│   ├── index.css                   # 原始 CSS 变量
│   ├── color-palette.md            # 原始色彩系统
│   └── component-styles.md         # 原始组件样式
│
├── features-inventory.md           # 功能清单
└── api-requirements.md             # API 需求清单
```

**备份命令**:
```bash
cd /media/martin/HDD2/new-video
mkdir -p backup/new-frontend-original
cp -r new-fronted/* backup/new-frontend-original/
```

### 1.2 功能清单备份

#### 已实现功能

| 模块 | 功能 | 组件 | 状态 |
|------|------|------|------|
| **工作台** | 首页布局 | HomePage | ✅ 完成 |
| | 创意输入 | CreativeInput | ✅ 完成 |
| | 项目列表 | ProjectList | ✅ 完成 |
| | 极速模式 | CreativeInput | ✅ 完成 |
| **项目编辑器** | 三栏布局 | ProjectPage | ✅ 完成 |
| | 左侧边栏 | LeftSidebar | ✅ 完成 |
| | 画布 | StoryboardCanvas | ✅ 完成 |
| | 右侧面板 | RightPanel | ✅ 完成 |
| **卡片系统** | 镜头卡片 | ShotCard | ✅ 完成 |
| | Scene Master | SceneMasterCard | ✅ 完成 |
| | 卡片拖拽 | useCanvasStore | ✅ 完成 |
| | 连线系统 | ConnectionLines | ✅ 完成 |
| | 右键菜单 | ContextMenu | ✅ 完成 |
| **弹窗功能** | 剧本工坊 | ScriptWorkshopModal | ✅ 完成 |
| | 批量生成 | BatchGenerateModal | ✅ 完成 |
| | 后台管理 | BackstageModal | ✅ 完成 |
| | 局部重绘 | InpaintModal | ✅ 完成 |
| | 智能扩图 | OutpaintModal | ✅ 完成 |
| | 虚拟摄像机 | VirtualCameraModal | ✅ 完成 |
| | 运镜生成 | CameraMoveModal | ✅ 完成 |
| **状态管理** | App Store | useAppStore | ✅ 完成 |
| | Canvas Store | useCanvasStore | ✅ 完成 |
| | UI Store | useUIStore | ✅ 完成 |
| | Project Store | useProjectStore | ✅ 完成 |

#### 依赖后端 API 的功能

| 功能 | 需要 API | 当前状态 |
|------|----------|----------|
| 项目 CRUD | `/api/projects/*` | ❌ 未对接 |
| 剧集管理 | `/api/episodes/*` | ❌ 未对接 |
| 卡片 CRUD | `/api/cards/*` | ❌ 未对接 |
| 画布状态保存 | `/api/storyboards/*/canvas` | ❌ 未对接 |
| 图片生成 | `/api/images/generate` | ❌ 未对接 |
| 批量生成 | `/api/jobs/batch` | ❌ 未对接 |
| 智能分集 | `/api/episodes/*/split` | ❌ 未对接 |
| AI 提取资产 | `/api/projects/*/extract-assets` | ❌ 未对接 |
| Inpaint | `/api/images/*/inpaint` | ❌ 未对接 |
| Outpaint | `/api/images/*/outpaint` | ❌ 未对接 |
| Virtual Camera | `/api/images/*/virtual-camera` | ❌ 未对接 |
| 视频生成 | `/api/videos/generate` | ❌ 未对接 |

---

## 🎨 第二步：样式迁移计划

### 2.1 色彩系统替换

**原始 (new-fronted)**:
```css
/* 未知原始变量，需要提取 */
```

**目标 (V3 规范)**:
```css
:root {
  /* 品牌色 - 科技蓝 */
  --primary: 217 91% 60%;           /* #3B82F6 */
  --primary-hover: 221 83% 53%;     /* #2563EB */
  --primary-active: 224 76% 48%;    /* #1D4ED8 */
  
  /* 强调色 - 橙色 */
  --accent: 24 95% 53%;             /* #F97316 */
  --accent-hover: 20 90% 48%;       /* #EA580C */
  
  /* 背景色 - Dark Mode */
  --background: 220 25% 4%;         /* #0A0E14 */
  --surface: 220 20% 10%;           /* #111827 */
  --elevated: 220 14% 18%;          /* #1F2937 */
  
  /* 文字色 */
  --text-primary: 220 13% 98%;      /* #F9FAFB */
  --text-secondary: 220 9% 65%;     /* #9CA3AF */
  --text-tertiary: 220 9% 46%;      /* #6B7280 */
}
```

**替换文件**: `src/index.css`

### 2.2 布局系统替换

**原始布局**:
- 间距：未知
- 圆角：未知
- 阴影：未知

**目标布局 (V3)**:
```css
:root {
  /* 间距 - 4px 基础 */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  
  /* 圆角 */
  --radius-sm: 0.25rem;   /* 4px */
  --radius-md: 0.5rem;    /* 8px */
  --radius-lg: 0.75rem;   /* 12px */
  --radius-xl: 1rem;      /* 16px */
}
```

### 2.3 组件样式替换清单

| 组件 | 当前样式 | 目标样式 | 修改文件 |
|------|----------|----------|----------|
| **Button** | 默认 shadcn | V3 规范 (primary/accent/ghost) | `components/ui/button.tsx` |
| **Card** | 默认 | V3 Elevated Card | `components/ui/card.tsx` |
| **Dialog** | 默认 | V3 暗色 Dialog | `components/ui/dialog.tsx` |
| **Input** | 默认 | V3 暗色 Input | `components/ui/input.tsx` |
| **Select** | 默认 | V3 暗色 Select | `components/ui/select.tsx` |
| **Tabs** | 默认 | V3 暗色 Tabs | `components/ui/tabs.tsx` |
| **Header** | 自定义 | V3 Header (56px) | `components/layout/Header.tsx` |
| **Sidebar** | 自定义 | V3 Sidebar (240px) | `components/layout/LeftSidebar.tsx` |
| **AI Panel** | ❌ 缺失 | 新增 V3 AI 助手 | `components/layout/AIAssistant.tsx` |

### 2.4 页面布局调整

#### HomePage 调整

**当前**:
```
全屏居中布局
- Header
- WelcomeHeader
- CreativeInput
- QuickActions
- ProjectList
```

**目标 (V3 Dashboard)**:
```
┌─────────────────────────────────────────────────────┐
│  [Logo] AI 短剧台                          [用户]   │  ← Header (56px)
├─────────────────────────────────────────────────────┤
│                                                     │
│              下午好, {username}.                     │
│           灵感稍纵即逝，抓住它。                     │
│                                                     │
│    ┌─────────────────────────────────────────┐     │
│    │  描述你的创意...                        │     │
│    │                                         │     │
│    │  [⚡ 极速模式 OFF]        [开始生成 →]  │     │
│    └─────────────────────────────────────────┘     │
│                                                     │
│    [📖 小说] [🎬 剧本] [🖼️ 分镜] [🎭 资产] [⚙️ 设置]│
│                                                     │
│    我的项目 (3)                              [全部>]
│    ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │
│    │  + │ │ P1 │ │ P2 │ │ P3 │                   │
│    │新建│ │... │ │... │ │... │                   │
│    └────┘ └────┘ └────┘ └────┘                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**修改点**:
1. 背景色改为 `var(--background)` (#0A0E14)
2. 输入框改为 V3 样式（圆角、边框、聚焦状态）
3. 按钮改为 V3 Primary/Accent 样式
4. 项目卡片改为 V3 Card 样式
5. 添加快捷入口图标组

#### ProjectPage 调整

**当前**:
```
三栏布局 (自适应)
- ProjectHeader
- LeftSidebar (自适应)
- StoryboardCanvas (自适应)
- RightPanel (自适应)
```

**目标 (V3 规范)**:
```
┌─────────────────────────────────────────────────────────────────────┐
│  [Logo] 分镜台          [剧本工坊] [批量图] [导出]  [通知] [用户]    │  ← Header
├─────┬───────────────────────────────────────────────────────┬───────┤
│     │                                                       │       │
│ 左  │                    画布 (Canvas)                      │  右   │
│ 侧  │                                                       │  侧   │
│ 边  │              (无限画布 + 卡片矩阵)                     │  面   │
│ 栏  │                                                       │  板   │
│     │  ┌────────┐  ┌────────┐  ┌────────┐                  │       │
│     │  │Scene 1 │  │Scene 2 │  │Shot 11│                   │       │
│     │  │[生成25]│  │[生成25]│  │ [图]  │                   │       │
│     │  └────────┘  └────────┘  └────────┘                  │       │
│     │                                                       │       │
│(240 │                                                       │(400   │
│ px) │                                                       │ px)   │
│     │                                                       │       │
└─────┴───────────────────────────────────────────────────────┴───────┘
```

**修改点**:
1. 左侧边栏固定宽度 240px (可折叠到 64px)
2. 右侧边栏固定宽度 400px (可折叠)
3. Header 固定高度 56px
4. 画布区域自适应宽度
5. 所有面板使用 V3 色彩系统

---

## 🔌 第三步：后端对接计划

### 3.1 V3 后端 API 清单

根据 `System-Architecture-V3.md`，已实现的后端 API：

#### 核心 API (✅ 已实现)

```
✅ GET    /api/health                    # 健康检查
✅ GET    /api/projects                  # 项目列表
✅ POST   /api/projects                  # 创建项目
✅ GET    /api/projects/{id}             # 项目详情
✅ PUT    /api/projects/{id}             # 更新项目
✅ DELETE /api/projects/{id}             # 删除项目
✅ GET    /api/projects/{id}/nodes       # 获取项目节点
✅ POST   /api/projects/{id}/nodes       # 创建节点
✅ GET    /api/nodes/{id}                # 节点详情
✅ PUT    /api/nodes/{id}                # 更新节点
✅ DELETE /api/nodes/{id}                # 删除节点
✅ POST   /api/graph/chat                # 聊天消息 (SSE)
✅ POST   /api/graph/approve              # 用户确认
✅ GET    /api/graph/state                # 获取 Graph 状态
✅ GET    /api/jobs                       # 任务列表
✅ POST   /api/jobs                       # 创建任务
✅ POST   /api/jobs/{id}/cancel           # 取消任务
```

#### 需要确认的 API (🟡 状态不明)

```
🟡 POST   /api/action                     # SDUI Action 处理
🟡 GET    /api/models/providers           # 模型服务商
🟡 POST   /api/models/mappings            # 任务模型映射
```

### 3.2 API 适配层设计

由于新前端使用 Card 数据模型，V3 使用 Node 数据模型，需要转换层：

```typescript
// utils/apiAdapter.ts

// Card → Node 转换
export function cardToNode(card: Card): Node {
  return {
    id: card.id,
    project_id: currentProjectId,
    node_type: card.type === 'scene_master' ? 'scene' : 'shot',
    content: {
      title: card.title,
      description: card.content.description,
      dialogue: card.content.dialogue,
      sound: card.content.sound,
      visual_prompt: card.content.visualPrompt,
      shot_type: card.content.shotType,
      camera_move: card.content.cameraMove,
      params: card.params,
    },
    position: card.position,
    status: card.status,
  };
}

// Node → Card 转换
export function nodeToCard(node: Node): Card {
  const content = node.content || {};
  return {
    id: node.id,
    type: node.node_type === 'scene' ? 'scene_master' : 'shot',
    number: extractNumber(node),
    title: content.title || '',
    position: node.position || { x: 0, y: 0 },
    size: getDefaultSize(node.node_type),
    status: node.status || 'pending',
    content: {
      description: content.description,
      dialogue: content.dialogue,
      sound: content.sound,
      visualPrompt: content.visual_prompt,
      shotType: content.shot_type,
      cameraMove: content.camera_move,
    },
    params: content.params || {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'cinematic_realistic',
    },
    links: { children: [], references: [] },
  };
}
```

### 3.3 API 服务封装

```typescript
// services/api.ts

import { cardToNode, nodeToCard } from '@/utils/apiAdapter';

export class APIService {
  private baseURL = '/api';

  // 项目 API
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${this.baseURL}/projects`);
    return res.json();
  }

  async createProject(project: Partial<Project>): Promise<Project> {
    const res = await fetch(`${this.baseURL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(project),
    });
    return res.json();
  }

  // 节点/卡片 API (适配层)
  async getCards(projectId: string): Promise<Card[]> {
    const res = await fetch(`${this.baseURL}/projects/${projectId}/nodes`);
    const nodes = await res.json();
    return nodes.map(nodeToCard);
  }

  async createCard(projectId: string, card: Card): Promise<Card> {
    const node = cardToNode(card);
    const res = await fetch(`${this.baseURL}/projects/${projectId}/nodes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(node),
    });
    const newNode = await res.json();
    return nodeToCard(newNode);
  }

  async updateCard(cardId: string, updates: Partial<Card>): Promise<Card> {
    const node = cardToNode(updates as Card);
    const res = await fetch(`${this.baseURL}/nodes/${cardId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(node),
    });
    const updatedNode = await res.json();
    return nodeToCard(updatedNode);
  }

  async deleteCard(cardId: string): Promise<void> {
    await fetch(`${this.baseURL}/nodes/${cardId}`, {
      method: 'DELETE',
    });
  }

  // SSE 聊天 (V3 核心功能)
  async chat(message: string, projectId: string, onMessage: (data: any) => void): Promise<void> {
    const response = await fetch(`${this.baseURL}/graph/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, projectId }),
    });

    const reader = response.body?.getReader();
    if (!reader) return;

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            onMessage(data);
          } catch (e) {
            console.error('Parse SSE data error:', e);
          }
        }
      }
    }
  }
}

export const api = new APIService();
```

---

## 📅 第四步：实施计划

### Phase 1: 样式迁移 (3天)

| 天 | 任务 | 产出 |
|---|------|------|
| 1 | 替换色彩系统 + 全局样式 | 更新 index.css |
| 1 | 替换 Button/Card/Dialog 组件 | 更新 ui/*.tsx |
| 2 | 替换 Input/Select/Tabs 组件 | 更新 ui/*.tsx |
| 2 | 调整 HomePage 布局 | 更新 HomePage.tsx |
| 3 | 调整 ProjectPage 布局 | 更新 ProjectPage.tsx |
| 3 | 调整 Header/Sidebar 尺寸 | 更新 layout/*.tsx |

### Phase 2: API 对接 (5天)

| 天 | 任务 | 产出 |
|---|------|------|
| 1 | 创建 API 适配层 | apiAdapter.ts |
| 1 | 封装 API 服务 | api.ts |
| 2 | 对接项目 CRUD | ProjectList + useProjectStore |
| 2 | 对接节点/卡片 CRUD | StoryboardCanvas + useProjectStore |
| 3 | 对接画布状态 | Canvas 保存/恢复 |
| 3 | 对接 SSE 聊天 | AI 助手组件 |
| 4 | 对接图片生成 | ShotCard 生成按钮 |
| 4 | 对接批量生成 | BatchGenerateModal |
| 5 | 对接智能分集 | LeftSidebar 分集 |
| 5 | 对接资产提取 | RightPanel 提取按钮 |

### Phase 3: 功能测试 (3天)

| 天 | 任务 | 产出 |
|---|------|------|
| 1 | 测试项目 CRUD | 测试报告 |
| 1 | 测试卡片操作 | 测试报告 |
| 2 | 测试 AI 聊天 | 测试报告 |
| 2 | 测试图片生成 | 测试报告 |
| 3 | 集成测试 + Bug 修复 | 修复清单 |

### Phase 4: 功能补充 (后续)

| 功能 | 说明 | 优先级 |
|------|------|--------|
| Inpaint | 局部重绘 | P1 |
| Outpaint | 智能扩图 | P1 |
| Virtual Camera | 虚拟摄像机 | P1 |
| Camera Move | 运镜生成 | P2 |
| 视频生成 | 图转视频 | P2 |

---

## 🎯 立即行动清单

### 今天完成

1. ✅ 创建完整备份
2. ✅ 确认后端 API 状态
3. ✅ 开始样式迁移

### 本周完成

1. 🎯 样式系统完全替换
2. 🎯 API 适配层完成
3. 🎯 项目/卡片基础对接

### 下周完成

1. 🎯 AI 聊天对接
2. 🎯 图片生成对接
3. 🎯 基础功能测试通过

---

## 📁 文档索引

- **备份目录**: `/backup/`
- **原始代码**: `/backup/new-frontend-original/`
- **实施方案**: 本文档
- **V3 设计规范**: `/docs/Frontend-Design-V3.md`
- **V3 架构文档**: `/docs/System-Architecture-V3.md`

---

**创建时间**: 2026-02-02
**版本**: v1.0
**状态**: 待执行
