# 前后端功能对接 - 使用指南

## 已完成的组件

### 1. API 服务层

```typescript
// 大纲服务 - 对接 skeleton_builder_graph
import { outlineService } from '@/api/services/outline';

// 小说服务 - 对接 novel_writer_graph  
import { novelService } from '@/api/services/novel';

// 审阅服务 - 对接 quality_control_graph
import { reviewService } from '@/api/services/review';
```

### 2. 状态管理

```typescript
// 工作坊全局状态
import { useWorkshopStore } from '@/store';

const {
  // 状态
  activeModule,
  outline,
  outlineNodes,
  globalReview,
  chapters,
  currentChapterId,
  chapterReviews,
  
  // Actions
  generateOutline,
  loadOutline,
  selectNode,
  reviewOutline,
  loadChapters,
  selectChapter,
  saveChapter,
} = useWorkshopStore();
```

### 3. UI 组件

```typescript
// 章节树组件（左侧大纲导航）
import { ChapterTree } from '@/components/workshop';

// 全局审阅面板（底部 - 大纲模式）
import { GlobalReviewPanel } from '@/components/workshop';

// 单章审阅面板（底部 - 小说模式）
import { ChapterReviewPanel } from '@/components/workshop';
```

## 使用示例

### 大纲模式布局

```tsx
import { useWorkshopStore } from '@/store';
import { ChapterTree, GlobalReviewPanel } from '@/components/workshop';

function OutlineView({ projectId }: { projectId: string }) {
  const { 
    outlineNodes, 
    selectedNodeId, 
    globalReview,
    selectNode,
    reviewOutline,
    loadGlobalReview 
  } = useWorkshopStore();

  return (
    <div className="flex flex-col h-full">
      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧大纲树 */}
        <div className="w-64 border-r bg-card">
          <ChapterTree
            nodes={outlineNodes}
            selectedId={selectedNodeId}
            onSelect={(id, node) => selectNode(id)}
          />
        </div>
        
        {/* 中间编辑器 */}
        <div className="flex-1">
          {/* ... 大纲编辑器内容 ... */}
        </div>
      </div>
      
      {/* 底部全局审阅面板 */}
      <GlobalReviewPanel
        review={globalReview}
        onReReview={() => reviewOutline(projectId)}
        onViewDetails={(category) => console.log(category)}
      />
    </div>
  );
}
```

### 小说模式布局

```tsx
import { useWorkshopStore } from '@/store';
import { NovelEditor, ChapterReviewPanel } from '@/components/workshop';

function NovelView({ projectId }: { projectId: string }) {
  const {
    chapters,
    currentChapterId,
    currentChapterContent,
    chapterReviews,
    selectChapter,
    saveChapter,
    reviewChapter,
  } = useWorkshopStore();

  const currentReview = currentChapterId 
    ? chapterReviews.get(currentChapterId) 
    : null;

  const handleSave = async (content: string) => {
    if (!currentChapterId) return;
    await saveChapter(projectId, currentChapterId, content, true);
  };

  return (
    <div className="flex flex-col h-full">
      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧章节列表 */}
        <div className="w-64 border-r bg-card">
          {chapters.map(chapter => (
            <div
              key={chapter.chapterId}
              onClick={() => selectChapter(chapter.chapterId)}
              className={cn(
                "p-3 cursor-pointer hover:bg-accent/50",
                currentChapterId === chapter.chapterId && "bg-accent"
              )}
            >
              <span>{chapter.title}</span>
              <span>{chapter.reviewScore}</span>
            </div>
          ))}
        </div>
        
        {/* 中间编辑器 */}
        <div className="flex-1">
          <NovelEditor
            content={currentChapterContent}
            onChange={handleSave}
            title={currentChapter?.title || ''}
            onTitleChange={(title) => {}}
          />
        </div>
      </div>
      
      {/* 底部单章审阅面板 */}
      <ChapterReviewPanel
        chapterId={currentChapterId || ''}
        chapterTitle={currentChapter?.title}
        review={currentReview}
        onReReview={() => currentChapterId && reviewChapter(projectId, currentChapterId)}
        onApplySuggestion={(id) => console.log('应用建议:', id)}
        onIgnoreIssue={(id) => console.log('忽略问题:', id)}
      />
    </div>
  );
}
```

## 与后端 API 对接

### 需要后端实现的 API 端点

根据 ARCHITECTURE_DESIGN_v4_FINAL.md，需要后端在 `backend/api/graph.py` 中添加以下端点：

```python
# 大纲相关
@router.post("/skeleton-builder/generate")
@router.get("/skeleton-builder/{project_id}")
@router.patch("/skeleton-builder/{project_id}/nodes/{node_id}")
@router.post("/skeleton-builder/{project_id}/review")
@router.post("/skeleton-builder/{project_id}/confirm")

# 小说相关
@router.get("/novel-writer/{project_id}/chapters")
@router.get("/novel-writer/{project_id}/chapters/{chapter_id}")
@router.put("/novel-writer/{project_id}/chapters/{chapter_id}")
@router.get("/novel-writer/{project_id}/chapters/{chapter_id}/review")
@router.post("/novel-writer/{project_id}/chapters/{chapter_id}/apply")
@router.post("/novel-writer/{project_id}/generate-next")

# 审阅相关
@router.get("/review/{project_id}/global")
@router.get("/review/{project_id}/chapters/{chapter_id}")
@router.post("/review/{project_id}/re_review")
@router.get("/review/{project_id}/tension_curve")
```

## 数据流

```
用户操作
  ↓
调用 workshopStore actions
  ↓
调用 API 服务层 (outlineService/novelService/reviewService)
  ↓
HTTP 请求到后端 API
  ↓
后端 LangGraph 工作流执行
  ↓
返回结果
  ↓
更新 workshopStore 状态
  ↓
UI 组件自动更新
```

## 下一步

1. 在 `ScriptWorkshopPage.tsx` 中集成新组件
2. 后端实现对应的 API 端点
3. 测试完整的端到端流程
