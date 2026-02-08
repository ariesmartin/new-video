# TipTap 优化实现指南（基于 Context7 调研）

**版本**: v1.0  
**日期**: 2026-02-08  
**调研来源**: Context7 - TipTap 官方文档  
**适用场景**: AI 短剧生成引擎 - 小说编辑器

---

## 1. TipTap 最新版本信息

### 1.1 推荐版本

```json
{
  "@tiptap/core": "^2.1.0",
  "@tiptap/react": "^2.1.0",
  "@tiptap/starter-kit": "^2.1.0",
  "@tiptap/extension-collaboration": "^2.1.0",
  "@tiptap/extension-collaboration-cursor": "^2.1.0",
  "@tiptap/extension-placeholder": "^2.1.0",
  "yjs": "^13.6.0",
  "y-protocols": "^1.0.6"
}
```

### 1.2 核心设计理念

TipTap 是一个**无头（headless）**富文本编辑器框架：
- ✅ 不强制任何 UI，完全自定义样式
- ✅ 基于 ProseMirror，稳定可靠
- ✅ 扩展性强，支持自定义节点/Mark
- ✅ 支持实时协作（Yjs 集成）
- ✅ TypeScript 原生支持

---

## 2. 性能优化最佳实践（Context7 推荐）

### 2.1 大文档分块处理

对于小说这类长文本（可能数万字），使用**分块处理**避免性能问题：

```typescript
// 使用 Tiptap Content AI Toolkit 分块
import { createTiptapContentAiToolkit } from '@tiptap-pro/content-ai-toolkit'

const toolkit = createTiptapContentAiToolkit({
  editor,
  // 每块 1000 字符（默认 32000，小说建议调小）
  chunkSize: 1000,
})

// 获取分块内容
const textChunks = toolkit.getTextChunks()
const htmlChunks = toolkit.getHtmlChunks()
const jsonChunks = toolkit.getJsonChunks()

// 用于：
// 1. 逐块审阅
// 2. 增量保存
// 3. 懒加载渲染
```

### 2.2 虚拟滚动实现

```typescript
// 长文档虚拟滚动优化
import { useVirtualizer } from '@tanstack/react-virtual'

function VirtualNovelEditor({ content }: { content: string }) {
  const parentRef = useRef<HTMLDivElement>(null)
  
  // 将文档分成多个段落块
  const paragraphs = content.split('\n\n')
  
  const virtualizer = useVirtualizer({
    count: paragraphs.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // 每段预估高度
    overscan: 5, // 预渲染 5 个屏幕外的段落
  })
  
  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {/* 渲染单个段落编辑器实例 */}
            <ParagraphEditor content={paragraphs[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  )
}
```

### 2.3 内存管理最佳实践

```typescript
// ✅ 正确：组件卸载时销毁编辑器
useEffect(() => {
  return () => {
    if (editor) {
      editor.destroy()
    }
  }
}, [editor])

// ✅ 正确：使用 useMemo 缓存编辑器配置
const editorConfig = useMemo(() => ({
  extensions: [...],
  content: initialContent,
  // 限制历史记录数量，防止内存泄漏
  history: {
    depth: 100, // 最多保存 100 步历史
    newGroupDelay: 500, // 500ms 内的操作合并为一组
  },
}), [])

// ❌ 错误：不要在每次渲染时创建新的 Y.Doc
const doc = new Y.Doc() // 应该在组件外或 useMemo 中创建
```

---

## 3. 小说专用自定义节点实现

### 3.1 场景节点（SceneNode）

```typescript
// src/extensions/SceneNode.ts
import { Node, mergeAttributes } from '@tiptap/core'

export interface SceneAttributes {
  sceneNumber?: number
  location?: string
  time?: string
  mood?: string
}

export const SceneNode = Node.create<SceneAttributes>({
  name: 'scene',
  
  group: 'block',
  content: 'inline*',
  
  // 解析 HTML
  parseHTML() {
    return [
      {
        tag: 'div[data-scene]',
      },
    ]
  },
  
  // 渲染 HTML
  renderHTML({ HTMLAttributes, node }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-scene': '',
        'data-scene-number': node.attrs.sceneNumber,
        class: 'novel-scene',
      }),
      ['div', { class: 'scene-header' }, 
        ['span', { class: 'scene-number' }, `场景 ${node.attrs.sceneNumber}`],
        ['span', { class: 'scene-location' }, node.attrs.location],
        ['span', { class: 'scene-time' }, node.attrs.time],
      ],
      ['div', { class: 'scene-content' }, 0],
    ]
  },
  
  // 属性定义
  addAttributes() {
    return {
      sceneNumber: {
        default: 1,
        parseHTML: (element) => element.getAttribute('data-scene-number'),
        renderHTML: (attributes) => ({
          'data-scene-number': attributes.sceneNumber,
        }),
      },
      location: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-location'),
      },
      time: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-time'),
      },
      mood: {
        default: '',
        parseHTML: (element) => element.getAttribute('data-mood'),
      },
    }
  },
  
  // 添加命令
  addCommands() {
    return {
      insertScene: (attributes: SceneAttributes) => ({ chain }) => {
        return chain()
          .insertContent({
            type: this.name,
            attrs: attributes,
          })
          .focus()
          .run()
      },
      setSceneAttributes: (attributes: Partial<SceneAttributes>) => ({ chain }) => {
        return chain()
          .updateAttributes(this.name, attributes)
          .run()
      },
    }
  },
  
  // 键盘快捷键
  addKeyboardShortcuts() {
    return {
      'Mod-Shift-S': () => this.editor.commands.insertScene({
        sceneNumber: this.editor.$nodes('scene').length + 1,
      }),
    }
  },
})
```

### 3.2 对话节点（DialogueNode）

```typescript
// src/extensions/DialogueNode.ts
import { Node, mergeAttributes } from '@tiptap/core'

export interface DialogueAttributes {
  character: string
  emotion?: string
  action?: string
}

export const DialogueNode = Node.create<DialogueAttributes>({
  name: 'dialogue',
  
  group: 'block',
  content: 'text*',
  inline: false,
  
  parseHTML() {
    return [
      {
        tag: 'div[data-dialogue]',
      },
    ]
  },
  
  renderHTML({ HTMLAttributes, node }) {
    return [
      'div',
      mergeAttributes(HTMLAttributes, {
        'data-dialogue': '',
        class: 'novel-dialogue',
      }),
      ['div', { class: 'dialogue-character' }, node.attrs.character],
      node.attrs.emotion ? ['span', { class: 'dialogue-emotion' }, `(${node.attrs.emotion})`] : '',
      ['div', { class: 'dialogue-content' }, 0],
      node.attrs.action ? ['div', { class: 'dialogue-action' }, node.attrs.action] : '',
    ]
  },
  
  addAttributes() {
    return {
      character: {
        default: '',
        parseHTML: (element) => element.querySelector('.dialogue-character')?.textContent || '',
      },
      emotion: {
        default: '',
      },
      action: {
        default: '',
      },
    }
  },
  
  addCommands() {
    return {
      insertDialogue: (attributes: DialogueAttributes) => ({ chain }) => {
        return chain()
          .insertContent({
            type: this.name,
            attrs: attributes,
          })
          .focus()
          .run()
      },
    }
  },
})
```

### 3.3 角色标记（CharacterMark）

```typescript
// src/extensions/CharacterMark.ts
import { Mark, mergeAttributes } from '@tiptap/core'

export interface CharacterMarkAttributes {
  name: string
  id?: string
}

export const CharacterMark = Mark.create<CharacterMarkAttributes>({
  name: 'character',
  
  parseHTML() {
    return [
      {
        tag: 'span[data-character]',
      },
    ]
  },
  
  renderHTML({ HTMLAttributes, mark }) {
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-character': mark.attrs.name,
        'data-character-id': mark.attrs.id,
        class: 'novel-character-mark',
      }),
      0,
    ]
  },
  
  addAttributes() {
    return {
      name: {
        default: '',
      },
      id: {
        default: '',
      },
    }
  },
})
```

---

## 4. 完整优化的 NovelEditor 组件

```typescript
// src/components/workshop/NovelEditor-Optimized.tsx

import { useEditor, EditorContent, BubbleMenu, FloatingMenu } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Typography from '@tiptap/extension-typography'
import Highlight from '@tiptap/extension-highlight'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import { useMemo, useEffect, useCallback } from 'react'
import { useDebounce } from '@/hooks/useDebounce'
import { SceneNode } from '@/extensions/SceneNode'
import { DialogueNode } from '@/extensions/DialogueNode'
import { CharacterMark } from '@/extensions/CharacterMark'
import { Toolbar } from './Toolbar'
import { cn } from '@/lib/utils'

interface NovelEditorProps {
  content: string
  onChange: (content: string) => void
  onJSONChange?: (json: any) => void
  title: string
  onTitleChange: (title: string) => void
  chapterId: string
  characters?: string[]
  readOnly?: boolean
}

export function NovelEditorOptimized({
  content,
  onChange,
  onJSONChange,
  title,
  onTitleChange,
  chapterId,
  characters = [],
  readOnly = false,
}: NovelEditorProps) {
  // 防抖处理保存
  const debouncedSave = useDebounce((html: string, json: any) => {
    onChange(html)
    onJSONChange?.(json)
  }, 1000)
  
  // 编辑器配置（使用 useMemo 缓存）
  const editorConfig = useMemo(() => ({
    extensions: [
      // 基础功能
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
        bulletList: {
          keepMarks: true,
          keepAttributes: false,
        },
        orderedList: {
          keepMarks: true,
          keepAttributes: false,
        },
        // 限制历史记录防止内存泄漏
        history: {
          depth: 100,
          newGroupDelay: 500,
        },
      }),
      
      // 占位符
      Placeholder.configure({
        placeholder: ({ node }) => {
          if (node.type.name === 'heading') {
            return '章节标题...'
          }
          return '开始创作你的小说...'
        },
      }),
      
      // 排版优化
      Typography.configure({
        openDoubleQuote: '「',
        closeDoubleQuote: '」',
        openSingleQuote: '『',
        closeSingleQuote: '』',
      }),
      
      // 高亮
      Highlight.configure({
        multicolor: true,
      }),
      
      // 任务列表（用于大纲标记）
      TaskList,
      TaskItem.configure({
        nested: true,
      }),
      
      // 小说专用扩展
      SceneNode,
      DialogueNode,
      CharacterMark,
    ],
    
    content: content,
    editable: !readOnly,
    autofocus: 'end',
    
    // 事件处理
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      const json = editor.getJSON()
      debouncedSave(html, json)
    },
    
    onSelectionUpdate: ({ editor }) => {
      // 可用于实时显示选中字数
      const { from, to } = editor.state.selection
      const text = editor.state.doc.textBetween(from, to, ' ')
      // 可以 dispatch 到状态管理
    },
    
    // 性能优化配置
    enableInputRules: true,
    enablePasteRules: true,
    enableCoreExtensions: true,
  }), [chapterId, readOnly])
  
  // 创建编辑器
  const editor = useEditor(editorConfig)
  
  // 内容变化时更新编辑器
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, false)
    }
  }, [content, editor])
  
  // 销毁编辑器
  useEffect(() => {
    return () => {
      editor?.destroy()
    }
  }, [editor])
  
  // 插入场景命令
  const insertScene = useCallback(() => {
    editor?.commands.insertScene({
      sceneNumber: editor.$nodes('scene').length + 1,
      location: '',
      time: '',
      mood: '',
    })
  }, [editor])
  
  // 插入对话命令
  const insertDialogue = useCallback((character: string) => {
    editor?.commands.insertDialogue({
      character,
      emotion: '',
      action: '',
    })
  }, [editor])
  
  if (!editor) {
    return null
  }
  
  return (
    <div className={cn(
      "flex flex-col h-full bg-background",
      readOnly && "opacity-80"
    )}>
      {/* 标题栏 */}
      <div className="px-6 py-4 border-b border-border">
        <input
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="输入章节标题..."
          disabled={readOnly}
          className="w-full text-2xl font-bold bg-transparent border-none outline-none placeholder:text-muted-foreground text-foreground"
        />
        
        {/* 章节信息栏 */}
        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
          <span>字数: {editor.storage.characterCount?.characters() || 0}</span>
          <span>场景: {editor.$nodes('scene').length}</span>
          <span>对话: {editor.$nodes('dialogue').length}</span>
        </div>
      </div>
      
      {/* 工具栏 */}
      {!readOnly && (
        <Toolbar 
          editor={editor}
          characters={characters}
          onInsertScene={insertScene}
          onInsertDialogue={insertDialogue}
        />
      )}
      
      {/* 编辑器主体 */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto p-6">
          <EditorContent 
            editor={editor}
            className="prose prose-sm dark:prose-invert max-w-none focus:outline-none"
          />
        </div>
      </div>
      
      {/* Bubble Menu（选中文本时显示） */}
      {editor && (
        <BubbleMenu 
          editor={editor} 
          tippyOptions={{ duration: 100 }}
          className="bg-popover border rounded-lg shadow-lg p-1 flex gap-1"
        >
          <button
            onClick={() => editor.chain().focus().toggleBold().run()}
            className={cn(
              "p-2 rounded hover:bg-accent",
              editor.isActive('bold') && "bg-accent"
            )}
          >
            加粗
          </button>
          <button
            onClick={() => editor.chain().focus().toggleItalic().run()}
            className={cn(
              "p-2 rounded hover:bg-accent",
              editor.isActive('italic') && "bg-accent"
            )}
          >
            斜体
          </button>
          <button
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            className={cn(
              "p-2 rounded hover:bg-accent",
              editor.isActive('highlight') && "bg-accent"
            )}
          >
            高亮
          </button>
        </BubbleMenu>
      )}
      
      {/* Floating Menu（空行时显示） */}
      {editor && (
        <FloatingMenu 
          editor={editor}
          tippyOptions={{ duration: 100 }}
          className="bg-popover border rounded-lg shadow-lg p-2"
        >
          <div className="flex flex-col gap-1">
            <button
              onClick={insertScene}
              className="px-3 py-2 text-left hover:bg-accent rounded"
            >
              📍 插入场景
            </button>
            {characters.map((char) => (
              <button
                key={char}
                onClick={() => insertDialogue(char)}
                className="px-3 py-2 text-left hover:bg-accent rounded"
              >
                💬 {char} 对话
              </button>
            ))}
          </div>
        </FloatingMenu>
      )}
    </div>
  )
}
```

---

## 5. 实时协作功能集成（Yjs）

```typescript
// src/components/workshop/CollaborativeNovelEditor.tsx

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Collaboration from '@tiptap/extension-collaboration'
import CollaborationCursor from '@tiptap/extension-collaboration-cursor'
import { TiptapCollabProvider } from '@tiptap-pro/provider'
import * as Y from 'yjs'
import { useEffect, useState } from 'react'
import { useUserStore } from '@/stores/user'

interface CollaborativeEditorProps {
  projectId: string
  chapterId: string
  initialContent?: string
}

// Yjs 文档在组件外创建，保持状态
const ydoc = new Y.Doc()

export function CollaborativeNovelEditor({
  projectId,
  chapterId,
  initialContent,
}: CollaborativeEditorProps) {
  const [isSynced, setIsSynced] = useState(false)
  const user = useUserStore((state) => state.user)
  
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // 协作时必须禁用默认历史记录
        history: false,
      }),
      
      // 协作扩展
      Collaboration.configure({
        document: ydoc,
      }),
      
      // 协作光标显示
      CollaborationCursor.configure({
        provider: null as any, // 将在 provider 创建后设置
        user: {
          name: user?.name || '匿名用户',
          color: user?.color || '#958DF1',
        },
      }),
    ],
  })
  
  useEffect(() => {
    if (!editor) return
    
    // 创建协作 Provider
    const provider = new TiptapCollabProvider({
      name: `${projectId}-${chapterId}`,
      appId: import.meta.env.VITE_TIPTAP_APP_ID,
      token: user?.token,
      document: ydoc,
      
      onSynced() {
        setIsSynced(true)
        
        // 只在首次同步时设置初始内容
        if (!ydoc.getMap('config').get('initialContentLoaded')) {
          ydoc.getMap('config').set('initialContentLoaded', true)
          
          if (initialContent && editor.isEmpty) {
            editor.commands.setContent(initialContent)
          }
        }
      },
      
      onAuthenticationFailed() {
        console.error('协作认证失败')
      },
    })
    
    // 更新协作光标 provider
    editor.extensionManager.extensions.find(
      (ext) => ext.name === 'collaborationCursor'
    )?.options.provider = provider
    
    return () => {
      provider.destroy()
    }
  }, [editor, projectId, chapterId, user, initialContent])
  
  if (!isSynced) {
    return <div>正在连接协作服务器...</div>
  }
  
  return (
    <div className="relative">
      {/* 协作用户列表 */}
      <div className="absolute top-2 right-2 flex -space-x-2">
        {Array.from(ydoc.getMap('users')?.entries() || []).map(([id, userData]: [string, any]) => (
          <div
            key={id}
            className="w-8 h-8 rounded-full border-2 border-background flex items-center justify-center text-xs font-medium"
            style={{ backgroundColor: userData.color }}
            title={userData.name}
          >
            {userData.name[0]}
          </div>
        ))}
      </div>
      
      <EditorContent editor={editor} />
    </div>
  )
}
```

---

## 6. 导入导出功能实现

### 6.1 JSON 格式（推荐）

```typescript
// 导出为 JSON（TipTap 原生格式）
const json = editor.getJSON()
// 存储到数据库或文件

// 从 JSON 导入
editor.commands.setContent({
  type: 'doc',
  content: [
    {
      type: 'heading',
      attrs: { level: 1 },
      content: [{ type: 'text', text: '第一章' }],
    },
    {
      type: 'paragraph',
      content: [{ type: 'text', text: '这是正文...' }],
    },
  ],
})
```

### 6.2 HTML 格式

```typescript
// 导出为 HTML
const html = editor.getHTML()

// 从 HTML 导入（支持 Word 等外部编辑器内容）
const externalContent = '<p>Hello <strong>world</strong>!</p>'
editor.commands.setContent(externalContent)
```

### 6.3 Markdown 格式（需要扩展）

```bash
npm install @tiptap-pro/extension-markdown
```

```typescript
import { Markdown } from '@tiptap-pro/extension-markdown'

const editor = useEditor({
  extensions: [
    StarterKit,
    Markdown.configure({
      html: true,
      tightLists: true,
      tightListClass: 'tight',
      bulletListMarker: '-',
      linkify: false,
    }),
  ],
})

// 导出为 Markdown
const markdown = editor.storage.markdown.getMarkdown()

// 从 Markdown 导入
editor.commands.setContent('# Hello\n\nThis is **bold**.')
```

---

## 7. 完整安装命令

```bash
# 1. 安装核心包
npm install @tiptap/react @tiptap/core @tiptap/starter-kit

# 2. 安装扩展包
npm install @tiptap/extension-placeholder \
  @tiptap/extension-typography \
  @tiptap/extension-highlight \
  @tiptap/extension-task-list \
  @tiptap/extension-task-item

# 3. 安装协作功能（可选）
npm install @tiptap/extension-collaboration \
  @tiptap/extension-collaboration-cursor \
  @tiptap-pro/provider \
  yjs y-protocols

# 4. 安装 Markdown 支持（可选）
npm install @tiptap-pro/extension-markdown

# 5. 安装 Content AI Toolkit（大文档分块）
npm install @tiptap-pro/content-ai-toolkit

# 6. 安装虚拟滚动（大文档优化）
npm install @tanstack/react-virtual
```

---

## 8. 性能对比

| 方案 | 10万字文档 | 内存占用 | 协作支持 | 扩展性 |
|------|-----------|---------|---------|--------|
| **TipTap（优化后）** | ✅ 流畅 | 中等 | ✅ 原生支持 | ✅ 极强 |
| Draft.js | ⚠️ 卡顿 | 高 | ❌ 需自行实现 | 中等 |
| Slate.js | ⚠️ 卡顿 | 高 | ⚠️ 社区方案 | 中等 |
| 自研 | ❌ 需2-4周开发 | 低 | ❌ 极难实现 | 取决于实现 |

---

## 9. 关键决策总结

基于 Context7 调研，**强烈推荐使用 TipTap**：

1. **性能优化**：使用分块处理（`getTextChunks`）应对大文档
2. **自定义能力**：通过 `Node.create()` 和 `Mark.create()` 实现小说专用功能
3. **协作就绪**：原生 Yjs 集成，多人编辑无需额外开发
4. **生态丰富**：Pro 版本提供 Markdown、AI 等高级功能
5. **长期维护**：活跃社区，持续更新，ProseMirror 底层稳定

**自研编辑器 vs TipTap**：
- 开发周期：2-4周 vs 1-2天
- 功能完整性：基础 vs 完整
- 维护成本：高 vs 低
- 协作能力：需数月开发 vs 开箱即用

**结论**：使用 TipTap 并针对性优化，是小说编辑器的最佳选择。

---

**文档状态**: 基于 Context7 实时检索生成  
**最后更新**: 2026-02-08