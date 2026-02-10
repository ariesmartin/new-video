import { Editor } from '@tiptap/react';
import { 
  Bold, 
  Italic, 
  Heading1, 
  Heading2, 
  Quote, 
  List, 
  ListOrdered,
  Highlighter,
  MapPin,
  MessageSquare,
  Undo,
  Redo
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToolbarProps {
  editor: Editor;
  characters?: string[];
  onInsertScene?: () => void;
  onInsertDialogue?: (character: string) => void;
}

export function Toolbar({ 
  editor, 
  characters = [], 
  onInsertScene, 
  onInsertDialogue 
}: ToolbarProps) {
  if (!editor) {
    return null;
  }

  return (
    <div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-surface/50 flex-wrap">
      {/* 基础格式化 */}
      <ToolbarButton
        icon={Bold}
        label="粗体"
        onClick={() => editor.chain().focus().toggleBold().run()}
        isActive={editor.isActive('bold')}
      />
      <ToolbarButton
        icon={Italic}
        label="斜体"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        isActive={editor.isActive('italic')}
      />
      <ToolbarButton
        icon={Highlighter}
        label="高亮"
        onClick={() => editor.chain().focus().toggleHighlight().run()}
        isActive={editor.isActive('highlight')}
      />
      
      <div className="w-px h-4 bg-border mx-1" />
      
      {/* 标题 */}
      <ToolbarButton
        icon={Heading1}
        label="标题1"
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        isActive={editor.isActive('heading', { level: 1 })}
      />
      <ToolbarButton
        icon={Heading2}
        label="标题2"
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        isActive={editor.isActive('heading', { level: 2 })}
      />
      
      <div className="w-px h-4 bg-border mx-1" />
      
      {/* 列表和引用 */}
      <ToolbarButton
        icon={Quote}
        label="引用"
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        isActive={editor.isActive('blockquote')}
      />
      <ToolbarButton
        icon={List}
        label="无序列表"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        isActive={editor.isActive('bulletList')}
      />
      <ToolbarButton
        icon={ListOrdered}
        label="有序列表"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        isActive={editor.isActive('orderedList')}
      />
      
      <div className="w-px h-4 bg-border mx-1" />
      
      {/* 小说专用功能 */}
      {onInsertScene && (
        <ToolbarButton
          icon={MapPin}
          label="插入场景"
          onClick={onInsertScene}
        />
      )}
      
      {/* 角色对话按钮 */}
      {characters.length > 0 && onInsertDialogue && (
        <div className="flex items-center gap-1">
          {characters.slice(0, 3).map((char) => (
            <button
              key={char}
              onClick={() => onInsertDialogue(char)}
              title={`${char} 对话`}
              className="px-2 py-1 text-xs rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
            >
              <MessageSquare size={12} className="inline mr-1" />
              {char}
            </button>
          ))}
        </div>
      )}
      
      <div className="flex-1" />
      
      {/* 撤销重做 */}
      <ToolbarButton
        icon={Undo}
        label="撤销"
        onClick={() => editor.chain().focus().undo().run()}
        isActive={false}
      />
      <ToolbarButton
        icon={Redo}
        label="重做"
        onClick={() => editor.chain().focus().redo().run()}
        isActive={false}
      />
    </div>
  );
}

interface ToolbarButtonProps {
  icon: React.ElementType;
  label: string;
  onClick?: () => void;
  isActive?: boolean;
}

function ToolbarButton({ icon: Icon, label, onClick, isActive }: ToolbarButtonProps) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={cn(
        'p-2 rounded-md transition-all duration-200',
        isActive
          ? 'bg-primary/20 text-primary'
          : 'text-text-secondary hover:text-text-primary hover:bg-elevated'
      )}
    >
      <Icon size={16} />
    </button>
  );
}
