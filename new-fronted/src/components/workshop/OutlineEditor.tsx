import { useEditor, EditorContent, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Typography from '@tiptap/extension-typography';
import Highlight from '@tiptap/extension-highlight';
import { Markdown } from '@tiptap/markdown';
import { useMemo, useEffect, useCallback } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { cn } from '@/lib/utils';
import { Bold, Italic, Highlighter, List, ListOrdered, Heading2, Heading3 } from 'lucide-react';

interface OutlineEditorProps {
  content: string;
  onChange: (content: string) => void;
  onJSONChange?: (json: any) => void;
  onMarkdownChange?: (markdown: string) => void;
  title: string;
  onTitleChange: (title: string) => void;
  nodeType: 'episode' | 'scene' | 'shot';
  nodeNumber?: number;
  readOnly?: boolean;
}

export function OutlineEditor({
  content,
  onChange,
  onJSONChange,
  onMarkdownChange,
  title,
  onTitleChange,
  nodeType,
  nodeNumber,
  readOnly = false,
}: OutlineEditorProps) {
  const debouncedSave = useDebounce((html: string, json: any, markdown: string) => {
    onChange(html);
    onJSONChange?.(json);
    onMarkdownChange?.(markdown);
  }, 1000);

  const editorConfig = useMemo(() => ({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [2, 3],
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

      Placeholder.configure({
        placeholder: ({ node }) => {
          if (node.type.name === 'heading') {
            return '标题...';
          }
          return '输入内容...';
        },
      }),

      Typography.configure({
        openDoubleQuote: '「',
        closeDoubleQuote: '」',
        openSingleQuote: '『',
        closeSingleQuote: '』',
      }),

      Highlight.configure({
        multicolor: true,
      }),

      Markdown,
    ],

    content: content,
    editable: !readOnly,
    autofocus: true,

    onUpdate: ({ editor }: { editor: Editor }) => {
      const html = editor.getHTML();
      const json = editor.getJSON();
      const markdownStorage = (editor.storage as any).markdown;
      const markdown = markdownStorage?.getMarkdown?.() || '';
      debouncedSave(html, json, markdown);
    },

    enableInputRules: true,
    enablePasteRules: true,
    enableCoreExtensions: true,
  }), [readOnly]);

  const editor = useEditor(editorConfig);

  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  useEffect(() => {
    return () => {
      editor?.destroy();
    };
  }, [editor]);

  if (!editor) {
    return null;
  }

  const typeLabels = {
    episode: '剧集',
    scene: '场景',
    shot: '镜头',
  };

  const typeColors = {
    episode: 'bg-blue-500/20 text-blue-400',
    scene: 'bg-green-500/20 text-green-400',
    shot: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <div className={cn(
      "flex flex-col h-full bg-surface",
      readOnly && "opacity-80"
    )}>
      {/* 标题栏 */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3 mb-3">
          <span className={cn(
            "px-2 py-1 rounded text-xs font-medium",
            typeColors[nodeType]
          )}>
            {typeLabels[nodeType]}
            {nodeNumber !== undefined && ` ${nodeNumber}`}
          </span>
        </div>

        <input
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder={`输入${typeLabels[nodeType]}标题...`}
          disabled={readOnly}
          className="w-full text-xl font-bold bg-transparent border-none outline-none placeholder:text-text-tertiary text-text-primary"
        />

        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-4 text-sm text-text-secondary">
            <span>字数: {editor.getText().length}</span>
          </div>
        </div>
      </div>

      {/* 工具栏 */}
      {!readOnly && (
        <div className="px-6 py-2 border-b border-border bg-elevated/50 flex items-center gap-1">
          <button
            onClick={() => editor.chain().focus().toggleBold().run()}
            className={cn(
              "p-2 rounded hover:bg-surface transition-colors",
              editor.isActive('bold') && "bg-primary/20 text-primary"
            )}
            title="加粗"
          >
            <Bold size={16} />
          </button>

          <button
            onClick={() => editor.chain().focus().toggleItalic().run()}
            className={cn(
              "p-2 rounded hover:bg-surface transition-colors",
              editor.isActive('italic') && "bg-primary/20 text-primary"
            )}
            title="斜体"
          >
            <Italic size={16} />
          </button>

          <button
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            className={cn(
              "p-2 rounded hover:bg-surface transition-colors",
              editor.isActive('highlight') && "bg-primary/20 text-primary"
            )}
            title="高亮"
          >
            <Highlighter size={16} />
          </button>

          <div className="w-px h-6 bg-border mx-2" />

          <button
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            className={cn(
              "p-2 rounded hover:bg-surface transition-colors",
              editor.isActive('heading', { level: 2 }) && "bg-primary/20 text-primary"
            )}
            title="二级标题"
          >
            <Heading2 size={16} />
          </button>

          <button
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            className={cn(
              "p-2 rounded hover:bg-surface transition-colors",
              editor.isActive('heading', { level: 3 }) && "bg-primary/20 text-primary"
            )}
            title="三级标题"
          >
            <Heading3 size={16} />
          </button>

          <div className="w-px h-6 bg-border mx-2" />

          <button
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            className={cn(
              "p-2 rounded hover:bg-surface transition-colors",
              editor.isActive('bulletList') && "bg-primary/20 text-primary"
            )}
            title="无序列表"
          >
            <List size={16} />
          </button>

          <button
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            className={cn(
              "p-2 rounded hover:bg-surface transition-colors",
              editor.isActive('orderedList') && "bg-primary/20 text-primary"
            )}
            title="有序列表"
          >
            <ListOrdered size={16} />
          </button>
        </div>
      )}

      {/* 编辑器主体 */}
      <div className="flex-1 overflow-y-auto relative">
        <div className="max-w-3xl mx-auto p-6">
          <EditorContent
            editor={editor}
            className="prose prose-sm dark:prose-invert max-w-none focus:outline-none min-h-[300px]"
          />
        </div>
      </div>
    </div>
  );
}

export default OutlineEditor;
