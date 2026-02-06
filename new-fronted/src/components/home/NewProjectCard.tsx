import { Plus } from 'lucide-react';

interface NewProjectCardProps {
  onClick?: () => void;
}

export function NewProjectCard({ onClick }: NewProjectCardProps) {
  return (
    <div
      className="relative cursor-pointer rounded-lg overflow-hidden transition-all duration-200 hover:scale-[1.02] flex flex-col items-center justify-center bg-surface border-2 border-dashed border-border w-full aspect-[6/5]"
      onClick={onClick}
    >
      <div
        className="w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center mb-2 sm:mb-3 transition-colors border border-dashed text-primary"
        style={{
          backgroundColor: 'rgba(255, 215, 0, 0.1)'
        }}
      >
        <Plus size={20} className="sm:w-6 sm:h-6 text-primary" />
      </div>
      <span
        className="text-xs sm:text-sm font-medium text-text-secondary"
      >
        新建项目
      </span>
    </div>
  );
}
