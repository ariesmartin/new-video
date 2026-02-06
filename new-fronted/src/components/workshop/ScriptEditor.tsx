import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ScriptModeToggle, type ScriptMode } from './ScriptModeToggle';

interface ScriptEditorProps {
  storyContent: string;
  scriptContent: string;
  onStoryChange: (content: string) => void;
  onScriptChange: (content: string) => void;
  title: string;
}

export function ScriptEditor({ 
  storyContent, 
  scriptContent, 
  onStoryChange, 
  onScriptChange,
  title 
}: ScriptEditorProps) {
  const [mode, setMode] = useState<ScriptMode>('story');
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface/50">
        <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
        <ScriptModeToggle mode={mode} onModeChange={setMode} />
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto">
          {mode === 'story' ? (
            <StoryModeView 
              content={storyContent} 
              onChange={onStoryChange}
              isFocused={isFocused}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
          ) : (
            <ScriptModeView 
              content={scriptContent} 
              onChange={onScriptChange}
              isFocused={isFocused}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

interface StoryModeViewProps {
  content: string;
  onChange: (content: string) => void;
  isFocused: boolean;
  onFocus: () => void;
  onBlur: () => void;
}

function StoryModeView({ content, onChange, isFocused, onFocus, onBlur }: StoryModeViewProps) {
  return (
    <div
      className={cn(
        'min-h-[500px] rounded-lg transition-all duration-200 p-6',
        isFocused && 'ring-2 ring-primary/20'
      )}
    >
      <textarea
        value={content}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        onBlur={onBlur}
        placeholder="在此输入故事内容..."
        className="w-full h-full min-h-[500px] bg-transparent border-none outline-none resize-none text-base leading-relaxed text-text-primary placeholder:text-text-tertiary font-sans"
        style={{ lineHeight: '1.8' }}
      />
    </div>
  );
}

interface ScriptModeViewProps {
  content: string;
  onChange: (content: string) => void;
  isFocused: boolean;
  onFocus: () => void;
  onBlur: () => void;
}

function ScriptModeView({ content, onChange, isFocused, onFocus, onBlur }: ScriptModeViewProps) {
  return (
    <div
      className={cn(
        'min-h-[500px] rounded-lg transition-all duration-200 p-6 font-mono text-sm',
        isFocused && 'ring-2 ring-primary/20'
      )}
    >
      <textarea
        value={content}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        onBlur={onBlur}
        placeholder={`【场次】EXT. 场景 - 时间\n\n【人物】角色名称（描述）\n\n【正文】\n△ 动作描述\n角色：对白内容\n△ 镜头指示`}
        className="w-full h-full min-h-[500px] bg-transparent border-none outline-none resize-none leading-relaxed text-text-primary placeholder:text-text-tertiary"
        style={{ lineHeight: '1.8' }}
      />
    </div>
  );
}
