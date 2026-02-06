import { useState } from 'react';
import { MoreVertical, Trash2, Copy, Edit } from 'lucide-react';
import type { Project } from '@/types';

interface ProjectCardProps {
  project: Project;
  onClick?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  onRename?: () => void;
}

export function ProjectCard({ 
  project, 
  onClick, 
  onDelete, 
  onDuplicate, 
  onRename 
}: ProjectCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  const formatDate = (date: Date) => {
    const d = new Date(date);
    return `${d.getMonth() + 1}-${d.getDate()}`;
  };

  return (
    <div 
      className="relative group cursor-pointer card overflow-hidden"
      onClick={onClick}
      style={{ width: '240px', height: '200px' }}
    >
      {/* 封面图 */}
      <div className="relative h-[135px] overflow-hidden">
        <img
          src={project.coverImage || `https://picsum.photos/400/225?random=${project.id}`}
          alt={project.name}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        <div className="absolute top-2 right-2">
          <span className="tag">影视短片</span>
        </div>
      </div>
      
      {/* 信息 */}
      <div className="p-3">
        <h3 
          className="font-medium text-sm truncate mb-1"
          style={{ color: 'var(--text-primary)' }}
        >
          {project.name}
        </h3>
        <div className="flex items-center justify-between">
          <span 
            className="text-xs"
            style={{ color: 'var(--text-tertiary)' }}
          >
            {formatDate(project.createdAt)}
          </span>
          <span 
            className="text-xs"
            style={{ color: 'var(--text-tertiary)' }}
          >
            {project.episodeCount || project.episodes?.length || 1} 集
          </span>
        </div>
      </div>
      
      {/* 右键菜单按钮 */}
      <button
        className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded"
        style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
        onClick={(e) => {
          e.stopPropagation();
          setShowMenu(!showMenu);
        }}
      >
        <MoreVertical size={16} className="text-white" />
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
            className="absolute top-8 left-2 z-50 rounded-lg py-1 shadow-xl"
            style={{ 
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border)',
              minWidth: '120px'
            }}
          >
            <button
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-white/5"
              style={{ color: 'var(--text-primary)' }}
              onClick={(e) => {
                e.stopPropagation();
                onRename?.();
                setShowMenu(false);
              }}
            >
              <Edit size={14} />
              重命名
            </button>
            <button
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-white/5"
              style={{ color: 'var(--text-primary)' }}
              onClick={(e) => {
                e.stopPropagation();
                onDuplicate?.();
                setShowMenu(false);
              }}
            >
              <Copy size={14} />
              复制
            </button>
            <button
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-white/5"
              style={{ color: 'var(--status-red)' }}
              onClick={(e) => {
                e.stopPropagation();
                onDelete?.();
                setShowMenu(false);
              }}
            >
              <Trash2 size={14} />
              删除
            </button>
          </div>
        </>
      )}
    </div>
  );
}
