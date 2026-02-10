import { useEditor, EditorContent, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Typography from '@tiptap/extension-typography';
import Highlight from '@tiptap/extension-highlight';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import { Markdown } from '@tiptap/markdown';
import { useMemo, useEffect, useCallback } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { SceneNode } from '@/extensions/SceneNode';
import { DialogueNode } from '@/extensions/DialogueNode';
import { CharacterMark } from '@/extensions/CharacterMark';
import { Toolbar } from './Toolbar';
import { cn } from '@/lib/utils';
import { Bold, Italic, Highlighter, FileDown } from 'lucide-react';

interface NovelEditorProps {
  content: string;
  onChange: (content: string) => void;
  onJSONChange?: (json: any) => void;
  onMarkdownChange?: (markdown: string) => void;
  title: string;
  onTitleChange: (title: string) => void;
  characters?: string[];
  readOnly?: boolean;
}

export function NovelEditor({
  content,
  onChange,
  onJSONChange,
  onMarkdownChange,
  title,
  onTitleChange,
  characters = [],
  readOnly = false,
}: NovelEditorProps) {
  // 防抖处理保存
  const debouncedSave = useDebounce((html: string, json: any, markdown: string) => {
    onChange(html);
    onJSONChange?.(json);
    onMarkdownChange?.(markdown);
  }, 1000);

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
      }),

      // 占位符
      Placeholder.configure({
        placeholder: ({ node }) => {
          if (node.type.name === 'heading') {
            return '章节标题...';
          }
          return '开始创作你的小说...';
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
      
      // Markdown支持
      Markdown,
    ],

    content: content,
    editable: !readOnly,
    autofocus: true,

    // 事件处理
    onUpdate: ({ editor }: { editor: Editor }) => {
      const html = editor.getHTML();
      const json = editor.getJSON();
      const markdownStorage = (editor.storage as any).markdown;
      const markdown = markdownStorage?.getMarkdown?.() || '';
      debouncedSave(html, json, markdown);
    },

    onSelectionUpdate: ({ editor }: { editor: Editor }) => {
      const { from, to } = editor.state.selection;
      const text = editor.state.doc.textBetween(from, to, ' ');
      console.log('选中文字:', text.length);
    },

    // 性能优化配置
    enableInputRules: true,
    enablePasteRules: true,
    enableCoreExtensions: true,
  }), [readOnly]);

  // 创建编辑器
  const editor = useEditor(editorConfig);

  // 内容变化时更新编辑器
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  // 销毁编辑器
  useEffect(() => {
    return () => {
      editor?.destroy();
    };
  }, [editor]);

  // 插入场景命令
  const insertScene = useCallback(() => {
    if (!editor) return;
    const commands = editor.commands as any;
    if (commands.insertScene) {
      commands.insertScene({
        sceneNumber: (editor.$nodes('scene')?.length || 0) + 1,
        location: '',
        time: '',
        mood: '',
      });
    }
  }, [editor]);

  // 插入对话命令
  const insertDialogue = useCallback((character: string) => {
    if (!editor) return;
    const commands = editor.commands as any;
    if (commands.insertDialogue) {
      commands.insertDialogue({
        character,
        emotion: '',
        action: '',
      });
    }
  }, [editor]);

  // 导出Markdown
  const exportMarkdown = useCallback(() => {
    if (!editor) return '';
    const markdownStorage = (editor.storage as any).markdown;
    return markdownStorage?.getMarkdown?.() || '';
  }, [editor]);

  if (!editor) {
    return null;
  }

  // 获取选中的文本
  const { from, to } = editor.state.selection;
  const hasSelection = from !== to;

  return (
    <div className={cn(
      "flex flex-col h-full bg-surface",
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
          className="w-full text-2xl font-bold bg-transparent border-none outline-none placeholder:text-text-tertiary text-text-primary"
        />

        {/* 章节信息栏 */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-4 text-sm text-text-secondary">
            <span>字数: {editor.getText().length}</span>
            <span>场景: {editor.$nodes('scene')?.length || 0}</span>
            <span>对话: {editor.$nodes('dialogue')?.length || 0}</span>
          </div>
          {!readOnly && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  const md = exportMarkdown();
                  navigator.clipboard.writeText(md);
                  alert('Markdown已复制到剪贴板');
                }}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-elevated hover:bg-surface rounded transition-colors"
                title="导出Markdown"
              >
                <FileDown size={14} />
                导出MD
              </button>
            </div>
          )}
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
      <div className="flex-1 overflow-y-auto relative">
        <div className="max-w-3xl mx-auto p-6">
          <EditorContent
            editor={editor}
            className="prose prose-sm dark:prose-invert max-w-none focus:outline-none min-h-[400px]"
          />
        </div>
        
        {/* 选中文字时的浮动工具栏 */}
        {hasSelection && !readOnly && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-surface border border-border rounded-lg shadow-lg p-1 flex gap-1 z-10">
            <button
              onClick={() => editor.chain().focus().toggleBold().run()}
              className={cn(
                "p-2 rounded hover:bg-elevated",
                editor.isActive('bold') && "bg-primary/20 text-primary"
              )}
              title="加粗"
            >
              <Bold size={16} />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleItalic().run()}
              className={cn(
                "p-2 rounded hover:bg-elevated",
                editor.isActive('italic') && "bg-primary/20 text-primary"
              )}
              title="斜体"
            >
              <Italic size={16} />
            </button>
            <button
              onClick={() => editor.chain().focus().toggleHighlight().run()}
              className={cn(
                "p-2 rounded hover:bg-elevated",
                editor.isActive('highlight') && "bg-primary/20 text-primary"
              )}
              title="高亮"
            >
              <Highlighter size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default NovelEditor;
