import { useState } from 'react';
import { ChevronRight, Loader2 } from 'lucide-react';
import { ProjectCard } from './ProjectCard';
import { NewProjectCard } from './NewProjectCard';
import { useProjectStore, useAppStore, useUIStore } from '@/hooks/useStore';
import { projectsService } from '@/api/services/projects';
import type { Project } from '@/types';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface ProjectListProps {
  onProjectClick?: (project: Project) => void;
  onNewProject?: () => void;
}

export function ProjectList({ onProjectClick, onNewProject }: ProjectListProps) {
  const projects = useProjectStore((state) => state.projects);
  const isLoading = useProjectStore((state) => state.isLoading);
  const fetchProjects = useProjectStore((state) => state.fetchProjects);
  const deleteProject = useProjectStore((state) => state.deleteProject);
  const addProject = useProjectStore((state) => state.addProject);
  const updateProject = useProjectStore((state) => state.updateProject);
  const setCurrentProject = useAppStore((state) => state.setCurrentProject);
  const addToast = useUIStore((state) => state.addToast);
  
  const [showAll, setShowAll] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null);
  const [renamingProject, setRenamingProject] = useState<Project | null>(null);
  const [newName, setNewName] = useState('');

  const displayProjects = showAll ? projects : projects.slice(0, 4);

  const handleProjectClick = (project: Project) => {
    setCurrentProject(project);
    onProjectClick?.(project);
  };

  const handleDelete = async (project: Project) => {
    setDeletingId(project.id);
    try {
      await deleteProject(project.id);
      addToast({ type: 'success', message: '项目已删除' });
    } catch (error) {
      addToast({ type: 'error', message: '删除项目失败' });
    } finally {
      setDeletingId(null);
    }
  };

  const handleDuplicate = async (project: Project) => {
    setDuplicatingId(project.id);
    try {
      // 先获取项目详情
      const response = await projectsService.getProject(project.id);
      const projectData = response.data;
      
      // 创建新项目，复制数据
      await addProject(
        `${projectData.name} (复制)`,
        projectData.meta
      );
      
      // 刷新项目列表
      await fetchProjects();
      
      addToast({ type: 'success', message: '项目已复制' });
    } catch (error) {
      console.error('Failed to duplicate project:', error);
      addToast({ type: 'error', message: '复制项目失败' });
    } finally {
      setDuplicatingId(null);
    }
  };

  const handleRename = (project: Project) => {
    setRenamingProject(project);
    setNewName(project.name);
  };

  const handleConfirmRename = async () => {
    if (!renamingProject || !newName.trim()) return;
    
    try {
      await updateProject(renamingProject.id, { name: newName.trim() });
      addToast({ type: 'success', message: '项目已重命名' });
      setRenamingProject(null);
    } catch (error) {
      console.error('Failed to rename project:', error);
      addToast({ type: 'error', message: '重命名失败' });
    }
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-5xl mx-auto">
        <div className="flex items-center justify-center py-12 text-text-secondary">
          <Loader2 className="animate-spin mr-2" size={20} />
          <span>加载项目中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto px-4 sm:px-0">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base sm:text-lg font-medium text-text-primary">
          我的项目 ({projects.length})
        </h2>
        {projects.length > 0 && (
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center gap-1 text-xs sm:text-sm hover:opacity-80 transition-opacity text-text-secondary"
          >
            {showAll ? '收起' : '查看全部'}
            <ChevronRight size={16} className={`transition-transform ${showAll ? 'rotate-90' : ''}`} />
          </button>
        )}
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <NewProjectCard onClick={onNewProject} />
        
        {projects.length === 0 ? (
          <div className="col-span-3 flex items-center justify-center py-12 text-text-tertiary">
            <p>暂无项目，点击上方"新建项目"开始创作</p>
          </div>
        ) : (
          displayProjects.map((project: Project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => handleProjectClick(project)}
              onDelete={() => handleDelete(project)}
              onDuplicate={() => handleDuplicate(project)}
              onRename={() => handleRename(project)}
              isDeleting={deletingId === project.id}
              isDuplicating={duplicatingId === project.id}
            />
          ))
        )}
      </div>

      {/* Rename Dialog */}
      <Dialog open={!!renamingProject} onOpenChange={() => setRenamingProject(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>重命名项目</DialogTitle>
          </DialogHeader>
          <Input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="输入新名称"
            className="mt-4"
          />
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setRenamingProject(null)}>
              取消
            </Button>
            <Button onClick={handleConfirmRename} disabled={!newName.trim()}>
              确认
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
