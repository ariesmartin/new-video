import { BookOpen, Film } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface QuickActionsProps {
  onTutorial?: () => void;
  onScriptWorkshop?: () => void;
}

export function QuickActions({ onTutorial, onScriptWorkshop }: QuickActionsProps) {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-6 sm:mb-12 w-full px-4 max-w-2xl mx-auto">
      <Button
        variant="outline"
        onClick={onTutorial}
        className="flex items-center justify-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg transition-all duration-200 border-border text-text-secondary bg-transparent w-full sm:w-auto text-sm sm:text-base h-auto"
      >
        <BookOpen size={16} className="sm:w-[18px] sm:h-[18px]" />
        <span className="whitespace-nowrap">快速入门教程</span>
      </Button>

      <Button
        variant="outline"
        onClick={onScriptWorkshop}
        className="flex items-center justify-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg transition-all duration-200 border-border text-text-secondary bg-transparent w-full sm:w-auto text-sm sm:text-base h-auto"
      >
        <Film size={16} className="sm:w-[18px] sm:h-[18px]" />
        <span className="whitespace-nowrap">进入剧本工坊</span>
      </Button>
    </div>
  );
}
