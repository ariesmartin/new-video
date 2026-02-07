# AI 短剧台 - 前端设计规范 V3.0

## 文档信息

| 项目 | 内容 |
|------|------|
| 产品名称 | AI 短剧台 (AI Drama Studio) |
| 版本号 | V3.0 |
| 文档类型 | 前端设计规范 / 开发指南 |
| 创建日期 | 2026-02-02 |
| 技术栈 | Vite + React 19 + TypeScript + TailwindCSS + Shadcn/UI |
| 状态 | 开发阶段，与代码实现同步 |

---

## 1. 设计系统 (Design System)

### 1.1 设计原则

| 原则 | 描述 | 实现方式 |
|------|------|----------|
| **暗黑优先** | 默认深色主题，减少视觉疲劳 | Tailwind dark mode |
| **内容为王** | UI 服务于内容创作，不喧宾夺主 | 最小化装饰元素 |
| **渐进复杂** | 简单入口，深度功能按需展开 | 分层导航 + 快捷操作 |
| **即时反馈** | 每个操作都有明确的视觉反馈 | Toast + 加载状态 |
| **可预测性** | 一致的交互模式，降低学习成本 | 统一组件规范 |

### 1.2 色彩系统

#### CSS Variables (globals.css)

```css
@layer base {
  :root {
    /* ===== 品牌色 ===== */
    --primary: 217 91% 60%;           /* #3B82F6 科技蓝 */
    --primary-hover: 221 83% 53%;     /* #2563EB */
    --primary-active: 224 76% 48%;    /* #1D4ED8 */
    --primary-muted: 217 91% 60% / 0.15;
    
    --secondary: 213 94% 68%;         /* #60A5FA */
    --accent: 24 95% 53%;             /* #F97316 橙色 */
    --accent-hover: 20 90% 48%;       /* #EA580C */
    
    /* ===== 背景色 (Dark Mode) ===== */
    --background: 220 25% 4%;         /* #0A0E14 */
    --surface: 220 20% 10%;           /* #111827 */
    --elevated: 220 14% 18%;          /* #1F2937 */
    --overlay: 0 0% 0% / 0.7;
    
    /* ===== 文字色 ===== */
    --text-primary: 220 13% 98%;      /* #F9FAFB */
    --text-secondary: 220 9% 65%;     /* #9CA3AF */
    --text-tertiary: 220 9% 46%;      /* #6B7280 */
    --text-inverse: 220 20% 10%;      /* #111827 */
    
    /* ===== 状态色 ===== */
    --success: 160 84% 39%;           /* #10B981 */
    --warning: 38 92% 50%;            /* #F59E0B */
    --error: 0 84% 60%;               /* #EF4444 */
    --info: 217 91% 60%;              /* #3B82F6 */
    
    /* ===== 边框色 ===== */
    --border: 220 13% 26%;            /* #374151 */
    --border-subtle: 220 14% 18%;     /* #1F2937 */
    --border-focus: 217 91% 60%;      /* #3B82F6 */
    
    /* ===== 圆角 ===== */
    --radius-sm: 0.25rem;   /* 4px */
    --radius-md: 0.5rem;    /* 8px */
    --radius-lg: 0.75rem;   /* 12px */
    --radius-xl: 1rem;      /* 16px */
  }
}
```

#### Tailwind Config

```typescript
// tailwind.config.ts
const config = {
  darkMode: ["class"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--text-primary))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          hover: "hsl(var(--primary-hover))",
          muted: "hsl(var(--primary-muted))",
        },
        surface: "hsl(var(--surface))",
        elevated: "hsl(var(--elevated))",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
      },
    },
  },
}
```

### 1.3 字体系统

```css
/* Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  /* 字体栈 */
  --font-heading: 'Plus Jakarta Sans', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --font-body: 'Inter', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Source Han Mono', monospace;
}
```

#### 字体规格

| 级别 | 大小 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| Display | 48px | 700 | 1.1 | 首页标题 |
| H1 | 32px | 700 | 1.2 | 页面标题 |
| H2 | 24px | 600 | 1.3 | 区块标题 |
| H3 | 18px | 600 | 1.4 | 卡片标题 |
| H4 | 16px | 500 | 1.5 | 小标题 |
| Body | 14px | 400 | 1.6 | 正文内容 |
| Body-sm | 13px | 400 | 1.5 | 辅助正文 |
| Caption | 12px | 400 | 1.5 | 标注文字 |
| Mono | 13px | 400 | 1.5 | 代码/剧本 |

### 1.4 间距系统

```css
:root {
  /* 4px 基础单位 */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
}
```

### 1.5 动画系统

```css
:root {
  /* 时长 */
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 350ms;
  
  /* 缓动曲线 */
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* 预设动画类 */
.animate-fade-in { animation: fadeIn var(--duration-normal) var(--ease-out); }
.animate-slide-up { animation: slideUp var(--duration-normal) var(--ease-out); }
.animate-scale-in { animation: scaleIn var(--duration-normal) var(--ease-out); }
```

---

## 2. 整体布局架构 (v6.0 动态面板)

### 2.1 设计原则

**动态面板架构**: 面板按需展开，最大化画布工作空间。

| 原则 | 描述 | 实现 |
|------|------|------|
| **纯净画布优先** | 默认状态只显示画布，无干扰 | 左右面板默认收缩 |
| **上下文感知** | 面板内容随选中对象变化 | 点击剧集→导演台，点击节点→编辑器 |
| **即时响应** | 点击立即展开，关闭立即隐藏 | 无延迟动画，ESC 快速关闭 |
| **空间复用** | 右侧面板复用，不同模式切换 | 导演台/节点编辑/AI 助手共享空间 |

### 2.2 四种视图状态

#### 状态 1: 纯净画布模式 (默认)
```
┌─────────────────────────────────────────────────────┐
│ [Logo] AI 短剧台 > 第一集:深井的回响  [🔔] [💎] [👤] │  ← Header
├─────────────────────────────────────────────────────┤
│ ← │                                                 │
│[📁│              中央无限画布                       │
│[📄│                                                 │
│[📊│        ┌───┐      ┌───┐      ┌───┐             │
│[😊│        │01 │─────→│02 │─────→│03 │             │
│[🖼️│        │[图│      │[图│      │[图│             │
│ > │        └───┘      └───┘      └───┘             │
│   │                                                 │
│   │  ← 左边缘窄条 (48px)                            │
└─────────────────────────────────────────────────────┘
```

#### 状态 2: 左侧面板展开
```
┌───────────────────────────────────────────────────────┐
│ Header                                                │
├───────────┬───────────────────────────────────────────┤
│ 📁 项目   │                                           │
│           │              中央画布                      │
│ ▼ Ep.1    │                                           │
│   ├─ S01  │        ┌───┐      ┌───┐                   │
│   └─ S02  │        │01 │─────→│02 │                   │
│           │        └───┘      └───┘                   │
│ [智能分集]│                                           │
│ [导入剧本]│  ← 左边缘窄条保持                          │
└───────────┴───────────────────────────────────────────┘
      ↑
  点击 [📁] 展开 (240px)
```

#### 状态 3: 点击左侧剧集 → 右侧面板滑出
```
┌──────────────────────────────┬────────────────────────┐
│ Header                       │                        │
├──────────┬───────────────────┼────────────────────────┤
│ 📁 项目   │                   │ Ep.1 导演台        ✕   │
│          │                   │ ┌──────────────────┐   │
│ ▼ Ep.1 ◀─┼─→ 中央画布        │ │ [剧本][分镜][卡片]│   │
│  (选中)  │                   │ │                  │   │
│   ├─ S01 │                   │ │ 剧本内容...       │   │
│   └─ S02 │                   │ │                  │   │
│          │                   │ │ [生成分镜表]      │   │
│          │                   │ └──────────────────┘   │
└──────────┴───────────────────┴────────────────────────┘
```

#### 状态 4: 点击画布节点 → 右侧切换为节点编辑
```
┌──────────────────────────────┬────────────────────────┐
│ 📁 项目   │                   │ 镜头 #01           ✕   │
│          │     中央画布       │ ┌──────────────────┐   │
│ ▼ Ep.1   │   ┌───┐  ┌───┐    │ │    [预览图]      │   │
│   ├─ S01 │   │01◀┼──┼───┼──→│ │    俯视镜头       │   │
│   │      │   │(选)│  └───┘    │ │    旋转(Orbit)   │   │
│   └─ S02 │   └───┘            │ ├──────────────────┤   │
│          │                    │ │ 对白: [输入...]  │   │
│          │                    │ │ 音效: [输入...]  │   │
│          │                    │ │ [生图] [局部重绘]│   │
└──────────┴────────────────────┴────────────────────────┘
```

### 2.3 布局组件结构 (重构后)

```typescript
// 布局层级 - v6.0 动态面板
<App>
  <Header />                    // 56px 固定高度
  <MainLayout>
    {/* 左侧图标窄条 - 始终可见 */}
    <LeftNarrowBar />          // 48px
    
    {/* 左侧面板 - 点击图标展开 */}
    <AnimatePresence>
      {leftPanel.isExpanded && <LeftExpandedPanel />}  // 240px
    </AnimatePresence>
    
    {/* 中央工作区 */}
    <Workspace>
      <StoryboardCanvas />     // 无限画布，按剧集隔离
    </Workspace>
    
    {/* 右侧面板 - 动态滑出 */}
    <AnimatePresence>
      {rightPanel.isOpen && (
        <RightPanel mode={rightPanel.mode}>
          {rightPanel.mode === 'director' && <DirectorConsole />}
          {rightPanel.mode === 'node-edit' && <NodeEditor />}
        </RightPanel>
      )}
    </AnimatePresence>
  </MainLayout>
  
  {/* AI 助手 - 底部浮动栏 */}
  <AIAssistantBar />           // 底部浮动，始终可见
</App>
```

### 2.4 面板状态管理

```typescript
// store/uiStore.ts
interface UIState {
  // 左侧面板
  leftPanel: {
    isExpanded: boolean;
    activeTab: 'project' | 'script' | 'storyboard' | 'assets';
    selectedEpisode: Episode | null;
    selectedScene: Scene | null;
  };
  
  // 右侧面板 (互斥模式)
  rightPanel: {
    isOpen: boolean;
    mode: 'hidden' | 'director' | 'node-edit' | 'ai-chat';
    data: {
      episode?: Episode;           // 导演台模式
      node?: ShotNode;             // 节点编辑模式
    };
  };
  
  // 画布状态
  canvas: {
    currentEpisodeId: string | null;
    viewport: { x: number; y: number; zoom: number };
    selectedNodes: string[];
  };
}

// 面板切换逻辑
const handleEpisodeClick = (episode: Episode) => {
  // 1. 选中剧集
  setSelectedEpisode(episode);
  
  // 2. 加载该剧集画布
  loadCanvasData(episode.id);
  
  // 3. 右侧面板显示导演台
  openRightPanel({
    mode: 'director',
    data: { episode }
  });
};

const handleNodeClick = (node: ShotNode) => {
  // 1. 选中节点
  selectNode(node.id);
  
  // 2. 右侧面板切换为节点编辑
  openRightPanel({
    mode: 'node-edit',
    data: { node }
  });
};

const handleCanvasBlankClick = () => {
  // 取消选择
  deselectNode();
  
  // 关闭右侧面板
  closeRightPanel();
};
```

### 2.5 响应式断点

| 断点 | 宽度 | 布局策略 |
|------|------|----------|
| xl | ≥1600px | 支持左右面板同时展开 |
| lg | 1280-1599px | 面板互斥，只展开一侧 |
| md | 768-1279px | 左侧面板抽屉式覆盖 |
| sm | <768px | 全屏画布，面板底部抽屉 |

### 2.6 AI 助手位置 (底部浮动栏)

```
┌─────────────────────────────────────────────────────┐
│                  中央画布                            │
│                                                     │
│        ┌───┐      ┌───┐      ┌───┐                │
│        │01 │─────→│02 │─────→│03 │                │
│        └───┘      └───┘      └───┘                │
│                                                     │
├─────────────────────────────────────────────────────┤
│ 🤖 AI 助手 (底部浮动)                                │
│ ┌───────────────────────────────────────────────┐   │
│ │ [@场景 S01] [快捷 ▼]  输入指令...        [→] │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**AIAssistantBar 规范**:
- 位置: 固定底部，距离底部 24px，居中
- 宽度: 最大 720px，自适应
- 高度: 48px (收起) / 400px (展开)
- 始终可见，可折叠为仅输入框
- 上下文感知: 显示 @当前选中对象

**Status Indicator (Thinking UI)**:
- **组件结构**: `<div className="bg-elevated/50 text-text-tertiary">`
- **图标**: `Loader2` (lucide-react) + `animate-spin`
- **文本**: 动态渲染后端 `desc` 或 `status` (如 "🔍 正在分析市场趋势...")
- **显示逻辑**: 当 `isTyping=true` 且 `streamingContent` 为空时显示
- **数据流**: SSE (node_start.desc | tool.status) -> chatService -> setThinkingStatus

---

## 3. 核心页面设计

### 3.1 工作台 (Dashboard)

#### 布局结构

```tsx
<DashboardLayout>
  {/* 问候区域 */}
  <GreetingSection className="mb-8">
    <TimeGreeting username={user.name} />
    <Tagline>灵感稍纵即逝，抓住它。</Tagline>
  </GreetingSection>
  
  {/* 创意输入 */}
  <CreativeInput className="mb-8">
    <Textarea 
      placeholder="描述你的创意... (例如: 复仇题材，女主逆袭，10集短剧)"
      maxLength={500}
    />
    <div className="flex justify-between">
      <Toggle label="⚡ 极速模式" />
      <Button variant="accent">开始生成 →</Button>
    </div>
  </CreativeInput>
  
  {/* 快捷入口 */}
  <QuickAccess className="mb-8">
    <QuickButton icon={BookOpen} label="小说" to="/novel" />
    <QuickButton icon={Clapperboard} label="剧本" to="/script" />
    <QuickButton icon={Image} label="分镜" to="/storyboard" />
    <QuickButton icon={Box} label="资产" to="/assets" />
    <QuickButton icon={Settings} label="设置" to="/settings" />
  </QuickAccess>
  
  {/* 项目列表 */}
  <ProjectGrid>
    <NewProjectCard onClick={createProject} />
    {projects.map(project => (
      <ProjectCard 
        key={project.id}
        title={project.name}
        cover={project.coverImage}
        updatedAt={project.updatedAt}
      />
    ))}
  </ProjectGrid>
</DashboardLayout>
```

#### 项目卡片规格

```
尺寸: 256px × 220px
封面比例: 16:9 (256px × 144px)
圆角: var(--radius-lg) = 12px
阴影: shadow-card
悬停: translateY(-4px) + shadow-card-hover
```

### 3.2 小说编写工坊 (NovelWorkshop)

#### 布局结构 (400px 侧边栏)

```tsx
<NovelWorkshopLayout>
  {/* 左侧：章节列表 */}
  <ChapterSidebar className="w-[200px]">
    <Button variant="ghost" onClick={addChapter}>+ 新增章节</Button>
    <ChapterList>
      {chapters.map((chapter, index) => (
        <ChapterItem
          key={chapter.id}
          number={index + 1}
          title={chapter.title}
          status={chapter.status}
          active={currentChapter === chapter.id}
          onClick={() => selectChapter(chapter.id)}
        />
      ))}
    </ChapterList>
  </ChapterSidebar>
  
  {/* 中央：编辑器 */}
  <EditorArea className="flex-1">
    <MarkdownEditor 
      value={currentContent}
      onChange={updateContent}
      toolbar={['bold', 'italic', 'heading', 'divider']}
    />
    <EditorFooter>
      <Button>保存</Button>
      <Button variant="secondary">导出</Button>
      <Button variant="ghost">版本历史</Button>
      <span className="text-text-secondary">字数: {wordCount}</span>
    </EditorFooter>
  </EditorArea>
  
  {/* 右侧：AI 助手 (400px) */}
  <AIAssistantPanel className="w-[400px]">
    <ChatHistory />
    <AIResponse />
    <QuickActions>
      <QuickButton action="continue" shortcut="Ctrl+Enter">续写下文</QuickButton>
      <QuickButton action="expand" shortcut="Ctrl+E">扩写片段</QuickButton>
      <QuickButton action="polish" shortcut="Ctrl+L">润色优化</QuickButton>
      <QuickButton action="emotion">情绪曲线</QuickButton>
      <QuickButton action="arc">角色弧光</QuickButton>
    </QuickActions>
    <ChatInput />
  </AIAssistantPanel>
</NovelWorkshopLayout>
```

### 3.3 分镜画布 (StoryboardCanvas) - v6.0 节点形式

#### 架构变化

**从卡片形式到节点形式的转变**:

| 维度 | 旧版 (v5.x) | 新版 (v6.0) |
|------|-------------|-------------|
| **显示单元** | ShotCard (280px × 200px) | ShotNode (120px × 80px) |
| **信息密度** | 完整信息内嵌 | 精简信息 + 右侧面板详情 |
| **画布容量** | 20-30个卡片开始拥挤 | 100+ 节点仍可清晰显示 |
| **交互模式** | 卡片内直接编辑 | 点击节点 → 右侧面板编辑 |
| **组织结构** | 单画布所有内容 | 每集独立画布 |

#### 每集独立画布架构

```typescript
// 画布数据模型
interface CanvasData {
  id: string;
  episodeId: string;       // 关联剧集
  nodes: ShotNode[];       // 该集所有节点
  connections: Connection[];
  viewport: {
    x: number; y: number; zoom: number;
  };
}

// 极简节点形式
interface ShotNode {
  id: string;
  type: 'scene_master' | 'shot';
  episodeId: string;
  sceneId: string;
  
  // 显示信息 (精简)
  number: number;          // #01
  title: string;           // "俯视镜头"
  subtitle?: string;       // "旋转(Orbit)"
  thumbnailUrl?: string;   // 缩略图 80×45px
  status: NodeStatus;      // 状态色标
  
  // 布局
  position: { x: number; y: number };
  
  // 详情在右侧面板显示
  details?: ShotDetails;
}

// 节点状态色标
const statusColors = {
  pending: '#EF4444',      // 红色 - 待处理
  processing: '#F59E0B',   // 黄色 - 处理中
  completed: '#10B981',    // 绿色 - 已完成
  approved: '#3B82F6',     // 蓝色 - 已批准
  revision: '#F97316',     // 橙色 - 需修改
};
```

#### 布局结构 (v6.0)

```tsx
<StoryboardCanvas>
  {/* 中央：无限画布 */}
  <CanvasContainer className="flex-1 relative overflow-hidden">
    {/* 工具栏 */}
    <CanvasToolbar className="absolute top-4 left-4 z-10">
      <ToolButton tool="select" icon={MousePointer} />
      <ToolButton tool="pan" icon={Hand} />
      <ToolButton tool="connect" icon={GitBranch} />
      <ZoomControls />
      <span className="text-xs text-text-secondary ml-4">
        Ep.{currentEpisode?.number} - {nodes.length} 节点
      </span>
    </CanvasToolbar>
    
    {/* 画布内容 - 按剧集隔离 */}
    <InfiniteCanvas
      zoom={zoom}
      offset={offset}
      onPan={handlePan}
      onZoom={handleZoom}
      onBlankClick={handleCanvasBlankClick}
    >
      {/* Scene Master (25格概览) */}
      {sceneMasters.map(master => (
        <SceneMasterNode
          key={master.id}
          node={master}
          isSelected={selectedNodes.includes(master.id)}
          onClick={(e) => handleNodeClick(master, e)}
          onDoubleClick={() => handleSceneMasterExpand(master)}
          onDrag={(pos) => updateNodePosition(master.id, pos)}
        />
      ))}
      
      {/* Shot Nodes (单镜头节点) */}
      {shotNodes.map(shot => (
        <ShotNode
          key={shot.id}
          node={shot}
          isSelected={selectedNodes.includes(shot.id)}
          isConnecting={isConnecting && connectionSource === shot.id}
          onClick={(e) => handleNodeClick(shot, e)}
          onDrag={(pos) => updateNodePosition(shot.id, pos)}
        />
      ))}
      
      {/* 连线层 */}
      <ConnectionLines 
        connections={connections}
        nodes={[...sceneMasters, ...shotNodes]}
      />
    </InfiniteCanvas>
    
    {/* 缩放控制 */}
    <ZoomControls 
      zoom={zoom}
      onZoomChange={setZoom}
      onReset={() => { setZoom(1); resetViewport(); }}
    />
  </CanvasContainer>
</StoryboardCanvas>
```

#### ShotNode 组件规格

```tsx
// 极简节点 - 120px × 80px (默认折叠)
┌─────────────────────┐
│ #13         ●       │  ← 编号 + 状态色标 (12px)
│ ┌───────────────┐   │
│ │    [缩略图]    │   │  ← 80×45px 预览图
│ │               │   │
│ └───────────────┘   │
│ 俯视镜头            │  ← 景别 (10px)
└─────────────────────┘
      ↓ 点击展开
┌─────────────────────────────────────┐
│ #13 俯视镜头              ●      ✕ │  ← 标题栏 + 关闭
│ ┌─────────────────────────────┐     │
│ │                             │     │
│ │       [预览图]               │     │  ← 160×90px
│ │                             │     │
│ └─────────────────────────────┘     │
│ 旋转(Orbit)                         │  ← 运镜方式
├─────────────────────────────────────┤
│ 对白: 林恩(画外): "来..."           │  ← 关键对白
│ 音效: 风啸声                        │  ← 环境音
├─────────────────────────────────────┤
│ ○────────────────────────────○     │  ← 输入/输出锚点
│ [编辑详情] → 打开右侧面板            │
└─────────────────────────────────────┘
```

```tsx
interface ShotNodeProps {
  node: ShotNode;
  isSelected: boolean;
  isConnecting: boolean;
  onClick: (e: React.MouseEvent) => void;
  onContextMenu: (e: React.MouseEvent) => void;
  onDrag: (position: { x: number; y: number }) => void;
  zoom: number;
}

export function ShotNode({ node, isSelected, ...props }: ShotNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <motion.div
      className={`
        absolute rounded-lg overflow-hidden select-none
        transition-shadow duration-200
        ${isSelected ? 'ring-2 ring-primary' : ''}
        ${isConnecting ? 'ring-2 ring-dashed ring-yellow-500' : ''}
      `}
      style={{
        left: node.position.x,
        top: node.position.y,
        width: isExpanded ? 280 : 120,
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border)',
        boxShadow: isSelected 
          ? '0 8px 24px rgba(0,0,0,0.3)' 
          : '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: isSelected ? 10 : 1,
      }}
      onClick={(e) => {
        props.onClick(e);
        if (!isExpanded) setIsExpanded(true);
      }}
      layout
    >
      {/* 节点头部 */}
      <div className="flex items-center justify-between p-1.5">
        <span className="text-xs font-medium text-text-tertiary">
          #{node.number}
        </span>
        {/* 状态色标 */}
        <div 
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: statusColors[node.status] }}
        />
      </div>
      
      {/* 缩略图 */}
      <div className="relative px-1.5">
        {node.thumbnailUrl ? (
          <img
            src={node.thumbnailUrl}
            alt={`Shot ${node.number}`}
            className="w-full rounded object-cover"
            style={{ height: isExpanded ? 90 : 45 }}
          />
        ) : (
          <div 
            className="w-full rounded flex items-center justify-center"
            style={{ 
              height: isExpanded ? 90 : 45,
              backgroundColor: 'var(--bg-night)',
            }}
          >
            <span className="text-lg text-primary">+</span>
          </div>
        )}
      </div>
      
      {/* 标题 (始终显示) */}
      <div className="p-1.5 pt-1">
        <p className="text-[10px] font-medium text-text-primary truncate">
          {node.title}
        </p>
        {node.subtitle && (
          <p className="text-[9px] text-text-secondary truncate">
            {node.subtitle}
          </p>
        )}
      </div>
      
      {/* 展开内容 */}
      <AnimatePresence>
        {isExpanded && node.details && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border px-1.5 py-2 space-y-1.5"
          >
            {node.details.dialogue && (
              <p className="text-[10px] text-text-secondary line-clamp-2">
                对白: {node.details.dialogue}
              </p>
            )}
            {node.details.sound && (
              <p className="text-[10px] text-text-tertiary">
                音效: {node.details.sound}
              </p>
            )}
            
            {/* 连接线锚点 */}
            <div className="flex items-center justify-between pt-1">
              <div className="w-3 h-3 rounded-full border-2 border-primary" />
              <button 
                className="text-[10px] text-primary hover:underline"
                onClick={(e) => {
                  e.stopPropagation();
                  openNodeEditor(node);
                }}
              >
                编辑详情 →
              </button>
              <div className="w-3 h-3 rounded-full border-2 border-primary" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
```

#### SceneMasterNode (25格概览) 组件

```tsx
// Scene Master 节点 - 280px × 320px
┌─────────────────────────────────┐
│ SCENE 01 Master        ●     ✕ │  ← 标题 + 状态 + 关闭
│ ┌───┬───┬───┬───┬───┐          │
│ │ 1 │ 2 │ 3 │ 4 │ 5 │          │  ← 25格缩略图
│ ├───┼───┼───┼───┼───┤          │    (5×5 网格)
│ │ 6 │ 7 │ 8 │ 9 │10 │          │
│ ├───┼───┼───┼───┼───┤          │
│ │11 │12 │13 │14 │15 │          │
│ ├───┼───┼───┼───┼───┤          │
│ │16 │17 │18 │19 │20 │          │
│ ├───┼───┼───┼───┼───┤          │
│ │21 │22 │23 │24 │25 │          │
│ └───┴───┴───┴───┴───┘          │
│ [查看详情] [展开镜头]           │  ← 操作按钮
└─────────────────────────────────┘

// 双击 Scene Master → 展开/聚焦该场景的所有镜头
const handleSceneMasterDoubleClick = (master: SceneMasterNode) => {
  const sceneShots = getShotsByScene(master.sceneId);
  
  // 动画聚焦到这些节点
  focusNodes(sceneShots);
  
  // 右侧面板显示场景详情
  openRightPanel('scene-detail', master);
};
```

#### 节点连线系统

```tsx
// 连线定义
interface Connection {
  id: string;
  source: string;      // 源节点ID
  target: string;      // 目标节点ID
  type: 'sequence' | 'reference';  // 顺序连线 / 引用连线
}

// 连线样式
const connectionStyles = {
  sequence: {
    stroke: 'var(--primary)',
    strokeWidth: 2,
    strokeDasharray: 'none',
  },
  reference: {
    stroke: 'var(--text-tertiary)',
    strokeWidth: 1,
    strokeDasharray: '5,5',
  },
};

// 连线交互
const handleConnectionClick = (connection: Connection) => {
  // 显示删除确认
  confirmDeleteConnection(connection);
};

const handleStartConnection = (nodeId: string, anchor: 'input' | 'output') => {
  if (anchor === 'output') {
    startConnecting(nodeId);
  }
};
```

#### 画布导航增强

```typescript
// 剧集切换
const switchEpisode = (episodeId: string) => {
  // 1. 保存当前画布状态
  saveCanvasState(currentEpisodeId, {
    nodes: currentNodes,
    connections: currentConnections,
    viewport: { x, y, zoom },
  });
  
  // 2. 加载新剧书画布
  const canvasData = loadCanvasData(episodeId);
  setCurrentEpisodeId(episodeId);
  setNodes(canvasData.nodes);
  setConnections(canvasData.connections);
  
  // 3. 动画过渡
  animateViewportTransition(canvasData.viewport);
  
  // 4. 更新面包屑
  updateBreadcrumb(episodeId);
};

// 聚焦到特定节点
const focusNode = (nodeId: string) => {
  const node = nodes.find(n => n.id === nodeId);
  if (!node) return;
  
  // 平滑移动到节点位置
  animatePanTo({
    x: -node.position.x + canvasWidth / 2 - 60,
    y: -node.position.y + canvasHeight / 2 - 40,
  });
  
  // 高亮节点
  selectNode(nodeId);
};

// 批量聚焦 (Scene Master 双击)
const focusNodes = (nodeIds: string[]) => {
  const targetNodes = nodes.filter(n => nodeIds.includes(n.id));
  if (targetNodes.length === 0) return;
  
  // 计算节点群边界
  const bounds = calculateBounds(targetNodes);
  
  // 调整视口以包含所有节点
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  const newZoom = Math.min(
    canvasWidth / (bounds.maxX - bounds.minX + 200),
    canvasHeight / (bounds.maxY - bounds.minY + 200),
    1.5  // 最大缩放限制
  );
  
  animateViewportTo({
    x: -centerX * newZoom + canvasWidth / 2,
    y: -centerY * newZoom + canvasHeight / 2,
    zoom: newZoom,
  });
};
```

#### 与右侧面板的联动

```typescript
// 点击节点 → 右侧面板
const handleNodeClick = (node: ShotNode, e: React.MouseEvent) => {
  e.stopPropagation();
  
  if (isConnecting && connectionSource && connectionSource !== node.id) {
    // 完成连线
    completeConnection(connectionSource, node.id);
  } else {
    // 选中节点并打开编辑器
    selectNode(node.id, e.ctrlKey || e.metaKey);
    
    // 右侧面板切换到节点编辑模式
    openRightPanel({
      mode: 'node-edit',
      data: { node },
    });
  }
};

// 节点编辑器面板内容
<NodeEditorPanel>
  {/* 预览图 */}
  <NodePreview imageUrl={node.details?.imageUrl} />
  
  {/* 基本属性 */}
  <PropertyGroup title="基本信息">
    <Select label="景别" value={node.title} options={shotTypes} />
    <Select label="运镜" value={node.subtitle} options={cameraMoves} />
  </PropertyGroup>
  
  {/* 内容 */}
  <PropertyGroup title="内容">
    <TextInput label="对白" value={node.details?.dialogue} />
    <TextInput label="音效" value={node.details?.sound} />
  </PropertyGroup>
  
  {/* 生图参数 */}
  <PropertyGroup title="生图参数">
    <Select label="分辨率" value={node.details?.params?.resolution} />
    <Select label="比例" value={node.details?.params?.aspectRatio} />
    <Select label="风格" value={node.details?.params?.style} />
    <TextArea label="AI提示词" value={node.details?.prompt} rows={3} />
  </PropertyGroup>
  
  {/* 操作按钮 */}
  <ActionButtons>
    <Button variant="primary">生图</Button>
    <Button variant="outline">局部重绘</Button>
    <Button variant="outline">生成视频</Button>
  </ActionButtons>
</NodeEditorPanel>
```

---

## 4. SDUI (Server-Driven UI) 实现

### 4.1 类型定义

```typescript
// types/sdui.ts

export type UIBlockType = 
  | 'action_group'
  | 'selector' 
  | 'confirmation'
  | 'form'
  | 'card_grid'
  | 'progress'
  | 'text_display';

export interface ActionButton {
  label: string;
  action: string;
  payload?: Record<string, any>;
  style?: 'primary' | 'secondary' | 'danger' | 'ghost';
  icon?: string;
  disabled?: boolean;
  tooltip?: string;
  shortcut?: string;
}

export interface UIInteractionBlock {
  blockType: UIBlockType;
  title?: string;
  description?: string;
  
  // Action Group
  buttons?: ActionButton[];
  
  // Selector
  options?: Array<{ label: string; value: string; description?: string }>;
  multiSelect?: boolean;
  defaultValue?: string | string[];
  
  // Form
  fields?: FormField[];
  
  // Card Grid
  cards?: Array<{
    id: string;
    title: string;
    content: string;
    tags?: string[];
    image?: string;
  }>;
  
  // Progress
  percent?: number;
  status?: 'active' | 'success' | 'error';
  steps?: string[];
  currentStep?: number;
  
  // Display
  content?: string;  // Markdown
  
  // Common
  dismissible?: boolean;
  timeout?: number;
}
```

### 4.2 ActionBlockRenderer 组件

```tsx
// components/ActionBlockRenderer.tsx

import React from 'react';
import { UIInteractionBlock } from '@/types/sdui';
import { ActionGroupBlock } from './blocks/ActionGroupBlock';
import { SelectorBlock } from './blocks/SelectorBlock';
import { ConfirmationBlock } from './blocks/ConfirmationBlock';
import { FormBlock } from './blocks/FormBlock';
import { CardGridBlock } from './blocks/CardGridBlock';
import { ProgressBlock } from './blocks/ProgressBlock';
import { TextDisplayBlock } from './blocks/TextDisplayBlock';

interface ActionBlockRendererProps {
  block: UIInteractionBlock;
  onAction: (action: string, payload?: any) => void;
}

export const ActionBlockRenderer: React.FC<ActionBlockRendererProps> = ({
  block,
  onAction,
}) => {
  const renderBlock = () => {
    switch (block.blockType) {
      case 'action_group':
        return <ActionGroupBlock buttons={block.buttons} onAction={onAction} />;
      case 'selector':
        return (
          <SelectorBlock
            options={block.options}
            multiSelect={block.multiSelect}
            defaultValue={block.defaultValue}
            onSelect={(value) => onAction('select', { value })}
          />
        );
      case 'confirmation':
        return (
          <ConfirmationBlock
            title={block.title}
            description={block.description}
            buttons={block.buttons}
            onAction={onAction}
          />
        );
      case 'form':
        return <FormBlock fields={block.fields} onSubmit={(data) => onAction('submit', data)} />;
      case 'card_grid':
        return <CardGridBlock cards={block.cards} onSelect={(id) => onAction('select_card', { id })} />;
      case 'progress':
        return (
          <ProgressBlock
            percent={block.percent}
            status={block.status}
            steps={block.steps}
            currentStep={block.currentStep}
          />
        );
      case 'text_display':
        return <TextDisplayBlock content={block.content} />;
      default:
        return null;
    }
  };

  return (
    <div className="rounded-lg border border-border bg-surface p-4 my-2">
      {block.title && (
        <h4 className="text-lg font-semibold text-text-primary mb-2">
          {block.title}
        </h4>
      )}
      {block.description && (
        <p className="text-sm text-text-secondary mb-4">
          {block.description}
        </p>
      )}
      {renderBlock()}
    </div>
  );
};
```

### 4.3 Action Group Block

```tsx
// components/blocks/ActionGroupBlock.tsx

import React from 'react';
import { Button } from '@/components/ui/button';
import { ActionButton } from '@/types/sdui';
import { Loader2 } from 'lucide-react';

interface ActionGroupBlockProps {
  buttons?: ActionButton[];
  onAction: (action: string, payload?: any) => void;
}

export const ActionGroupBlock: React.FC<ActionGroupBlockProps> = ({
  buttons,
  onAction,
}) => {
  const [loading, setLoading] = React.useState<string | null>(null);

  const handleClick = async (button: ActionButton) => {
    if (button.disabled || loading) return;
    
    setLoading(button.action);
    try {
      await onAction(button.action, button.payload);
    } finally {
      setLoading(null);
    }
  };

  if (!buttons?.length) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {buttons.map((button, index) => (
        <Button
          key={index}
          variant={button.style || 'primary'}
          disabled={button.disabled || loading === button.action}
          onClick={() => handleClick(button)}
          title={button.tooltip}
        >
          {loading === button.action && (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          )}
          {button.label}
        </Button>
      ))}
    </div>
  );
};
```

---

## 5. 状态管理 (Zustand)

### 5.1 Store 结构

```typescript
// store/useAppStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
  // 用户状态
  user: User | null;
  isAuthenticated: boolean;
  
  // 项目状态
  currentProject: Project | null;
  projects: Project[];
  
  // UI 状态
  sidebarCollapsed: boolean;
  aiPanelVisible: boolean;
  theme: 'light' | 'dark' | 'system';
  
  // Actions
  setCurrentProject: (project: Project) => void;
  toggleSidebar: () => void;
  toggleAIPanel: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      currentProject: null,
      projects: [],
      sidebarCollapsed: false,
      aiPanelVisible: true,
      theme: 'dark',
      
      setCurrentProject: (project) => set({ currentProject: project }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      toggleAIPanel: () => set((state) => ({ aiPanelVisible: !state.aiPanelVisible })),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({ 
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);
```

### 5.2 Chat Store

```typescript
// store/useChatStore.ts

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  uiInteraction?: UIInteractionBlock;
  timestamp: Date;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  context: {
    projectId?: string;
    module?: string;
    episodeId?: string;
  };
  
  sendMessage: (content: string) => Promise<void>;
  handleAction: (action: string, payload?: any) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      messages: [],
      isLoading: false,
      context: {},
      
      sendMessage: async (content) => {
        const { messages, context } = get();
        
        // 添加用户消息
        const userMessage: Message = {
          id: crypto.randomUUID(),
          role: 'user',
          content,
          timestamp: new Date(),
        };
        set({ messages: [...messages, userMessage], isLoading: true });
        
        try {
          // 调用 SSE API
          const response = await fetch('/api/graph/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: content,
              projectId: context.projectId,
            }),
          });
          
          // 处理 SSE 流
          const reader = response.body?.getReader();
          if (!reader) throw new Error('No response body');
          
          // 读取并处理事件...
          
        } finally {
          set({ isLoading: false });
        }
      },
      
      handleAction: async (action, payload) => {
        set({ isLoading: true });
        try {
          const response = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, payload }),
          });
          
          const result = await response.json();
          
          // 添加 AI 回复
          const aiMessage: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: result.message,
            uiInteraction: result.uiInteraction,
            timestamp: new Date(),
          };
          
          set((state) => ({
            messages: [...state.messages, aiMessage],
          }));
        } finally {
          set({ isLoading: false });
        }
      },
      
      clearMessages: () => set({ messages: [] }),
    }),
    { name: 'chat-store' }
  )
);
```

### 5.3 Canvas Store

```typescript
// store/useCanvasStore.ts

import { create } from 'zustand';

interface CanvasState {
  zoom: number;
  offset: { x: number; y: number };
  selectedNodes: string[];
  clipboard: Node[];
  
  // History
  history: CanvasSnapshot[];
  historyIndex: number;
  
  // Actions
  setZoom: (zoom: number) => void;
  panTo: (x: number, y: number) => void;
  selectNodes: (ids: string[]) => void;
  updateNodePosition: (id: string, x: number, y: number) => void;
  undo: () => void;
  redo: () => void;
}

export const useCanvasStore = create<CanvasState>((set, get) => ({
  zoom: 1,
  offset: { x: 0, y: 0 },
  selectedNodes: [],
  clipboard: [],
  history: [],
  historyIndex: -1,
  
  setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(5, zoom)) }),
  
  panTo: (x, y) => set({ offset: { x, y } }),
  
  selectNodes: (ids) => set({ selectedNodes: ids }),
  
  updateNodePosition: (id, x, y) => {
    // Update node position logic
    // Push to history
  },
  
  undo: () => {
    const { history, historyIndex } = get();
    if (historyIndex > 0) {
      set({ historyIndex: historyIndex - 1 });
      // Restore snapshot
    }
  },
  
  redo: () => {
    const { history, historyIndex } = get();
    if (historyIndex < history.length - 1) {
      set({ historyIndex: historyIndex + 1 });
      // Restore snapshot
    }
  },
}));
```

---

## 6. 组件库规范

### 6.1 按钮组件

```tsx
// components/ui/button.tsx

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary-hover active:bg-primary-active',
        secondary: 'bg-surface border border-border hover:bg-elevated',
        accent: 'bg-accent text-white hover:bg-accent-hover',
        ghost: 'hover:bg-elevated',
        danger: 'bg-error text-white hover:bg-error/90',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4',
        lg: 'h-12 px-6 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading, children, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={props.disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </Comp>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
```

### 6.2 卡片组件

```tsx
// components/ui/card.tsx

import * as React from 'react';
import { cn } from '@/lib/utils';

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'rounded-xl border border-border bg-surface text-text-primary shadow-sm transition-all',
      'hover:shadow-md hover:-translate-y-1',
      className
    )}
    {...props}
  />
));
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3 ref={ref} className={cn('font-semibold leading-none tracking-tight', className)} {...props} />
));
CardTitle.displayName = 'CardTitle';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
));
CardContent.displayName = 'CardContent';

export { Card, CardHeader, CardTitle, CardContent };
```

---

## 7. 性能优化

### 7.1 渲染优化

```typescript
// 使用 React.memo 优化组件
export const ShotCard = React.memo<ShotCardProps>(({ shot, ...props }) => {
  // 组件实现
}, (prevProps, nextProps) => {
  // 自定义比较函数
  return prevProps.shot.id === nextProps.shot.id &&
         prevProps.selected === nextProps.selected;
});

// 使用 useMemo 缓存计算
const processedData = useMemo(() => {
  return expensiveOperation(data);
}, [data]);

// 使用 useCallback 缓存回调
const handleClick = useCallback(() => {
  onAction(action);
}, [onAction, action]);
```

### 7.2 画布性能

```typescript
// Canvas 优化策略
const canvasOptimizations = {
  // 1. 节流更新
  throttleMs: 16,  // 60fps
  
  // 2. 视口裁剪
  viewportCulling: true,
  
  // 3. 缩放降级
  degradeOnZoom: {
    threshold: 0.5,
    hideText: true,
    hideDetails: true,
  },
  
  // 4. 离屏渲染
  offscreenRendering: true,
};
```

### 7.3 虚拟滚动

```tsx
// 长列表使用虚拟滚动
import { Virtuoso } from 'react-virtuoso';

<Virtuoso
  style={{ height: '400px' }}
  data={items}
  itemContent={(index, item) => (
    <ListItem key={item.id} data={item} />
  )}
/>
```

---

## 8. 错误处理

### 8.1 错误边界

```tsx
// components/ErrorBoundary.tsx

import React from 'react';
import { Button } from '@/components/ui/button';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // 发送错误到监控服务
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex flex-col items-center justify-center h-full p-8">
          <h2 className="text-xl font-semibold mb-4">出错了</h2>
          <p className="text-text-secondary mb-4">
            {this.state.error?.message || '未知错误'}
          </p>
          <Button onClick={() => window.location.reload()}>
            刷新页面
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 8.2 API 错误处理

```typescript
// lib/api.ts

import { toast } from '@/components/ui/toast';

export async function apiFetch<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error.message, response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      toast.error(error.message);
    } else {
      toast.error('网络错误，请检查连接');
    }
    throw error;
  }
}

class APIError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = 'APIError';
  }
}
```

---

## 9. 文件组织

```
frontend/
├── components/
│   ├── ui/                    # 基础 UI 组件
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── blocks/                # SDUI Block 组件
│   │   ├── ActionGroupBlock.tsx
│   │   ├── SelectorBlock.tsx
│   │   ├── CardGridBlock.tsx
│   │   └── ...
│   ├── layout/                # 布局组件
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── MainLayout.tsx
│   │   └── AIAssistant.tsx
│   ├── modules/               # 功能模块组件
│   │   ├── Dashboard/
│   │   ├── NovelWorkshop/
│   │   ├── ScriptExtractor/
│   │   ├── StoryboardCanvas/
│   │   └── ModelSettings/
│   └── common/                # 通用组件
│       ├── ProjectCard.tsx
│       ├── ShotCard.tsx
│       └── LoadingState.tsx
├── pages/                     # 页面组件
│   ├── Dashboard.tsx
│   ├── NovelWorkshop.tsx
│   └── ...
├── hooks/                     # 自定义 Hooks
│   ├── useChat.ts
│   ├── useCanvas.ts
│   └── useProjects.ts
├── store/                     # Zustand Store
│   ├── useAppStore.ts
│   ├── useChatStore.ts
│   ├── useCanvasStore.ts
│   └── useProjectStore.ts
├── services/                  # API 服务
│   ├── api.ts
│   ├── chat.ts
│   └── projects.ts
├── types/                     # TypeScript 类型
│   ├── sdui.ts
│   ├── project.ts
│   └── api.ts
├── lib/                       # 工具函数
│   ├── utils.ts
│   └── constants.ts
└── styles/                    # 样式文件
    ├── globals.css
    └── animations.css
```

---

**文档结束**

*本文档是 AI 短剧台项目的前端设计规范和开发指南。结合 System-Architecture-V3.md 和 Product-Spec-V3.md 进行开发实施。*

**关联文档**：
- System-Architecture-V3.md - 系统架构设计
- Product-Spec-V3.md - 产品需求文档
- Implementation-Roadmap.md - 实现路线图

### 3.6 智能剧本渲染 (Smart Script Highlighting)

**设计目标**: 在前端自动识别并美化剧本格式文本，无需后端特殊标记，提供 IDE 级的阅读体验。

**识别规则 (Regex Patterns)**:

| 类型 | 规则特征 | 样式定义 (Tailwind) | 视觉效果 |
|------|----------|---------------------|----------|
| **场景标题** (Scene) | `^(INT\.|EXT\.|内景|外景|场景)\s+.*` | `text-amber-500 font-bold block mt-4 mb-2` | 🟡 琥珀色高亮，加粗，增加间距 |
| **角色对白** (Dialogue) | `^([A-Z\u4e00-\u9fa5]+)(\s*\(.*\))?\s*[：:]\s*(.*)` | 名称:`text-sky-400 font-bold` 内容:`text-sky-100 font-serif` | 🔵 天蓝色系，衬线体，名称加粗 |
| **动作/旁白** (Action) | 普通段落 | `text-gray-300` | ⚪ 浅灰色 |
| **思考过程** (Thinking) | `<thinking>...</thinking>` | `text-xs text-gray-500 border-l-2 border-gray-700 pl-2 italic` | 🧠 暗灰，斜体，左侧边框 |

**实现方案**:
- 作为 `ReactMarkdown` 的自定义 `p` (paragraph) 组件插入
- 实时解析文本行，应用样式
- 保持对 Markdown 格式的兼容支持

```tsx
// 渲染示例
<div className="script-line scene">INT. 废弃医院 - 夜</div>
<div className="script-line action">闪电划破夜空...</div>
<div className="script-line dialogue">
  <span className="role">林恩</span>: <span className="content">终于结束了。</span>
</div>
```

**最后更新**: 2026-02-02