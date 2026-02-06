import { cn } from '@/lib/utils';

export type ScriptMode = 'story' | 'script';

interface ScriptModeToggleProps {
  mode: ScriptMode;
  onModeChange: (mode: ScriptMode) => void;
}

export function ScriptModeToggle({ mode, onModeChange }: ScriptModeToggleProps) {
  return (
    <div className="inline-flex items-center gap-1 p-1 bg-surface rounded-lg border border-border">
      <button
        onClick={() => onModeChange('story')}
        className={cn(
          'px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200',
          mode === 'story'
            ? 'bg-accent text-accent-foreground font-semibold'
            : 'text-text-secondary hover:text-text-primary'
        )}
      >
        故事模式
      </button>
      <button
        onClick={() => onModeChange('script')}
        className={cn(
          'px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200',
          mode === 'script'
            ? 'bg-accent text-accent-foreground font-semibold'
            : 'text-text-secondary hover:text-text-primary'
        )}
      >
        剧本模式
      </button>
    </div>
  );
}
