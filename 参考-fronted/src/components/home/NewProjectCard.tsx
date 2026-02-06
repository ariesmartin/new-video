import { Plus } from 'lucide-react';

interface NewProjectCardProps {
  onClick?: () => void;
}

export function NewProjectCard({ onClick }: NewProjectCardProps) {
  return (
    <div 
      className="relative cursor-pointer rounded-lg overflow-hidden transition-all duration-200 hover:scale-[1.02] flex flex-col items-center justify-center"
      onClick={onClick}
      style={{ 
        width: '240px', 
        height: '200px',
        backgroundColor: 'var(--bg-card)',
        border: '2px dashed var(--border)'
      }}
    >
      <div 
        className="w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors"
        style={{ 
          backgroundColor: 'rgba(255, 215, 0, 0.1)',
          border: '1px dashed var(--primary)'
        }}
      >
        <Plus size={24} style={{ color: 'var(--primary)' }} />
      </div>
      <span 
        className="text-sm font-medium"
        style={{ color: 'var(--text-secondary)' }}
      >
        新建项目
      </span>
    </div>
  );
}
