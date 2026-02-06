import { BookOpen, Film } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface QuickActionsProps {
  onTutorial?: () => void;
  onScriptWorkshop?: () => void;
}

export function QuickActions({ onTutorial, onScriptWorkshop }: QuickActionsProps) {
  return (
    <div className="flex items-center justify-center gap-4 mb-12">
      <Button
        variant="outline"
        onClick={onTutorial}
        className="flex items-center gap-2 px-6 py-3 rounded-lg transition-all duration-200"
        style={{ 
          borderColor: 'var(--border)',
          color: 'var(--text-secondary)',
          backgroundColor: 'transparent'
        }}
      >
        <BookOpen size={18} />
        快速入门教程
      </Button>
      
      <Button
        variant="outline"
        onClick={onScriptWorkshop}
        className="flex items-center gap-2 px-6 py-3 rounded-lg transition-all duration-200"
        style={{ 
          borderColor: 'var(--border)',
          color: 'var(--text-secondary)',
          backgroundColor: 'transparent'
        }}
      >
        <Film size={18} />
        进入剧本工坊
      </Button>
    </div>
  );
}
