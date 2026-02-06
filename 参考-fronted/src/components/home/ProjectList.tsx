import { useState, useEffect } from 'react';
import { ChevronRight, Loader2 } from 'lucide-react';
import { ProjectCard } from './ProjectCard';
import { NewProjectCard } from './NewProjectCard';
import { useProjectStore, useAppStore, useUIStore } from '@/hooks/useStore';
import { getProjects, deleteProject, ApiError } from '@/api';
import type { Project } from '@/types';

interface ProjectListProps {
  onProjectClick?: (project: Project) => void;
  onNewProject?: () => void;
}

export function ProjectList({ onProjectClick, onNewProject }: ProjectListProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  
  const setCurrentProject = useAppStore((state: { setCurrentProject: (p: Project | null) => void }) => state.setCurrentProject);
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);
  
  // ✅ 从后端获取项目列表
  useEffect(() => {
    fetchProjects();
  }, [page]);
  
  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getProjects(page, 20);
      
      setProjects(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('获取项目列表失败:', err);
      
      if (err instanceof ApiError) {
        if (err.code === 'NETWORK_ERROR') {
          setError('无法连接到后端服务，请确保后端服务已启动');
        } else {
          setError(err.message);
        }
      } else {
        setError('获取项目列表失败');
      }
      
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };
  
  // ✅ 调用后端删除 API
  const handleDelete = async (projectId: string) => {
    try {
      await deleteProject(projectId);
      
      // 删除成功后刷新列表
      await fetchProjects();
      
      addToast({ type: 'success', message: '项目已删除' });
    } catch (err) {
      console.error('删除项目失败:', err);
      
      if (err instanceof ApiError) {
        addToast({ type: 'error', message: err.message || '删除失败' });
      } else {
        addToast({ type: 'error', message: '删除项目时发生错误' });
      }
    }
  };
  
  const handleProjectClick = (project: Project) => {
    setCurrentProject(project);
    onProjectClick?.(project);
  };
  
  // 根据 showAll 决定显示数量
  const displayCount = showAll ? projects.length : Math.min(projects.length, 4);
  const displayProjects = projects.slice(0, displayCount);
  
  // 是否还有更多项目
  const hasMore = projects.length > 4 || total > projects.length;
  
  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 
          className="text-lg font-medium"
          style={{ color: 'var(--text-primary)' }}
        >
          我的项目 {loading ? '' : `(${total})`}
        </h2>
        
        {!loading && hasMore && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-1 text-sm hover:opacity-80 transition-opacity"
            style={{ color: 'var(--text-secondary)' }}
          >
            {showAll ? '收起' : '查看全部'}
            <ChevronRight 
              size={16} 
              className={`transition-transform ${showAll ? 'rotate-90' : ''}`}
            />
          </button>
        )}
      </div>
      
      {/* 错误提示 */}
      {error && (
        <div 
          className="rounded-lg p-4 mb-4"
          style={{ 
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)'
          }}
        >
          <p style={{ color: 'var(--status-red)' }}>{error}</p>
          <button
            onClick={fetchProjects}
            className="mt-2 text-sm underline"
            style={{ color: 'var(--status-red)' }}
          >
            重试
          </button>
        </div>
      )}
      
      {/* 加载状态 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin mr-2" style={{ color: 'var(--text-secondary)' }} />
          <span style={{ color: 'var(--text-secondary)' }}>加载中...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <NewProjectCard onClick={onNewProject} />
          
          {displayProjects.map((project: Project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => handleProjectClick(project)}
              onDelete={() => handleDelete(project.id)}
              onDuplicate={() => console.log('Duplicate', project.id)}
              onRename={() => console.log('Rename', project.id)}
            />
          ))}
        </div>
      )}
      
      {/* 空状态 */}
      {!loading && !error && projects.length === 0 && (
        <div 
          className="text-center py-12 rounded-lg"
          style={{ 
            backgroundColor: 'var(--bg-card)',
            border: '1px dashed var(--border)'
          }}
        >
          <p style={{ color: 'var(--text-secondary)' }}>
            还没有项目，点击上方"新建项目"开始创作吧
          </p>
        </div>
      )}
    </div>
  );
}
