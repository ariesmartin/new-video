import { useState } from 'react';
import { Bold, Italic, Heading1, Heading2, Quote, List, Undo, Redo } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NovelEditorProps {
  content: string;
  onChange: (content: string) => void;
  title: string;
  onTitleChange: (title: string) => void;
}

export function NovelEditor({ content, onChange, title, onTitleChange }: NovelEditorProps) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-1 px-4 py-2 border-b border-border bg-surface/50">
        <ToolbarButton icon={Bold} label="粗体" />
        <ToolbarButton icon={Italic} label="斜体" />
        <div className="w-px h-4 bg-border mx-1" />
        <ToolbarButton icon={Heading1} label="标题1" />
        <ToolbarButton icon={Heading2} label="标题2" />
        <div className="w-px h-4 bg-border mx-1" />
        <ToolbarButton icon={Quote} label="引用" />
        <ToolbarButton icon={List} label="列表" />
        <div className="flex-1" />
        <ToolbarButton icon={Undo} label="撤销" />
        <ToolbarButton icon={Redo} label="重做" />
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          <input
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="输入章节标题..."
            className="w-full text-2xl font-bold bg-transparent border-none outline-none placeholder:text-text-tertiary text-text-primary"
          />

          <div
            className={cn(
              'min-h-[400px] rounded-lg transition-all duration-200',
              isFocused && 'ring-2 ring-primary/20'
            )}
          >
            <textarea
              value={content}
              onChange={(e) => onChange(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="开始创作你的小说..."
              className="w-full h-full min-h-[400px] bg-transparent border-none outline-none resize-none text-base leading-relaxed text-text-primary placeholder:text-text-tertiary font-sans"
              style={{ lineHeight: '1.75' }}
            />
          </div>
        </div>
      </div>
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
