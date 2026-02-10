import { BookOpen, FileText, Grid3X3, ListTree } from 'lucide-react';
import { cn } from '@/lib/utils';

export type EditorModule = 'outline' | 'novel' | 'script' | 'storyboard';

interface ModuleTabsProps {
  activeModule: EditorModule;
  onModuleChange: (module: EditorModule) => void;
}

const modules = [
  { id: 'outline' as EditorModule, label: '大纲', icon: ListTree },
  { id: 'novel' as EditorModule, label: '小说', icon: BookOpen },
  { id: 'script' as EditorModule, label: '剧本', icon: FileText },
  { id: 'storyboard' as EditorModule, label: '分镜', icon: Grid3X3 },
];

export function ModuleTabs({ activeModule, onModuleChange }: ModuleTabsProps) {
  return (
    <div className="flex items-center gap-1 p-1 bg-surface rounded-lg border border-border">
      {modules.map((module) => {
        const Icon = module.icon;
        const isActive = activeModule === module.id;
        
        return (
          <button
            key={module.id}
            onClick={() => onModuleChange(module.id)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200',
              isActive
                ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                : 'text-text-secondary hover:text-text-primary hover:bg-elevated'
            )}
          >
            <Icon size={16} />
            <span>{module.label}</span>
          </button>
        );
      })}
    </div>
  );
}
