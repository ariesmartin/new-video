import { useState } from 'react';
import { MoreVertical, Trash2, Copy, Edit, Loader2 } from 'lucide-react';
import type { Project } from '@/types';

interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  onRename?: () => void;
  isDeleting?: boolean;
  isDuplicating?: boolean;
}

export function ProjectCard({ 
  project, 
  onClick, 
  onDelete, 
  onDuplicate, 
  onRename,
  isDeleting,
  isDuplicating
}: ProjectCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  if (isDeleting || isDuplicating) {
    return (
      <div 
        className="relative group overflow-hidden opacity-50 w-full aspect-[6/5]"
      >
        <div className="flex items-center justify-center h-full">
          <Loader2 className="animate-spin text-text-secondary" size={20} />
          <span className="ml-2 text-xs sm:text-sm text-text-secondary">
            {isDeleting ? '删除中...' : '复制中...'}
          </span>
        </div>
      </div>
    );
  }

  const formatDate = (date: Date) => {
    const d = new Date(date);
    return `${d.getMonth() + 1}-${d.getDate()}`;
  };

  return (
    <div 
      className="relative group cursor-pointer card overflow-hidden w-full aspect-[6/5]"
      onClick={onClick}
    >
      {/* 封面图 */}
      <div className="relative h-[65%] sm:h-[68%] overflow-hidden">
        <img
          src={project.coverImage || `https://picsum.photos/400/225?random=${project.id}`}
          alt={project.name}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        <div className="absolute top-1.5 sm:top-2 right-1.5 sm:right-2">
          <span className="tag text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1">影视短片</span>
        </div>
      </div>
      
      {/* 信息 */}
      <div className="p-2 sm:p-3">
        <h3
          className="font-medium text-xs sm:text-sm truncate mb-0.5 sm:mb-1 text-text-primary"
        >
          {project.name}
        </h3>
        <div className="flex items-center justify-between">
          <span
            className="text-[10px] sm:text-xs text-text-tertiary"
          >
            {formatDate(project.createdAt)}
          </span>
          <span
            className="text-[10px] sm:text-xs text-text-tertiary"
          >
            {project.episodes?.length || 1} 集
          </span>
        </div>
      </div>
      
      {/* 右键菜单按钮 */}
      <button
        className="absolute top-1.5 sm:top-2 left-1.5 sm:left-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded bg-black/50"
        onClick={(e) => {
          e.stopPropagation();
          setShowMenu(!showMenu);
        }}
      >
        <MoreVertical size={14} className="sm:w-4 sm:h-4 text-white" />
      </button>
      
      {/* 菜单 */}
      {showMenu && (
        <>
          <div 
            className="fixed inset-0 z-40"
            onClick={(e) => {
              e.stopPropagation();
              setShowMenu(false);
            }}
          />
          <div
            className="absolute top-6 sm:top-8 left-1.5 sm:left-2 z-50 rounded-lg py-1 shadow-xl bg-surface border border-border min-w-[100px] sm:min-w-[120px]"
          >
            <button
              className="w-full px-2.5 sm:px-3 py-1.5 sm:py-2 text-left text-xs sm:text-sm flex items-center gap-1.5 sm:gap-2 hover:bg-white/5 text-text-primary"
              onClick={(e) => {
                e.stopPropagation();
                onRename?.();
                setShowMenu(false);
              }}
            >
              <Edit size={12} className="sm:w-3.5 sm:h-3.5" />
              重命名
            </button>
            <button
              className="w-full px-2.5 sm:px-3 py-1.5 sm:py-2 text-left text-xs sm:text-sm flex items-center gap-1.5 sm:gap-2 hover:bg-white/5 text-text-primary"
              onClick={(e) => {
                e.stopPropagation();
                onDuplicate?.();
                setShowMenu(false);
              }}
            >
              <Copy size={12} className="sm:w-3.5 sm:h-3.5" />
              复制
            </button>
            <button
              className="w-full px-2.5 sm:px-3 py-1.5 sm:py-2 text-left text-xs sm:text-sm flex items-center gap-1.5 sm:gap-2 hover:bg-white/5 text-red-500"
              onClick={(e) => {
                e.stopPropagation();
                onDelete?.();
                setShowMenu(false);
              }}
            >
              <Trash2 size={12} className="sm:w-3.5 sm:h-3.5" />
              删除
            </button>
          </div>
        </>
      )}
    </div>
  );
}
