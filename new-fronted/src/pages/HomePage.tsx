import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import {
  WelcomeHeader,
  CreativeInput,
  QuickActions,
  ProjectList
} from '@/components/home';
import { projectAutoCreate } from '@/api/services/projectAutoCreate';
import { chatService } from '@/api/services/chat';
import { useAppStore, useUIStore, useProjectStore } from '@/hooks/useStore';
import type { Project } from '@/types';

export function HomePage() {
  const navigate = useNavigate();
    const { theme, currentProject } = useAppStore();
  const { addProject, fetchProjects } = useProjectStore();
  const setCurrentProject = useAppStore((state: { setCurrentProject: (p: Project | null) => void }) => state.setCurrentProject);
  const setCurrentEpisode = useAppStore((state: { setCurrentEpisode: (e: any) => void }) => state.setCurrentEpisode);
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);

  const [isLoading, setIsLoading] = useState(false);

  // 页面加载时获取项目列表
  useEffect(() => {
    fetchProjects().catch(console.error);
  }, [fetchProjects]);

  useEffect(() => {
    // 应用主题
    document.body.className = theme;
  }, [theme]);

  const handleGenerate = async (prompt: string, fastMode: boolean) => {
    sessionStorage.setItem('startup_prompt', prompt);
    chatService.clearSession();

    setIsLoading(true);
    addToast({
      type: 'success',
      message: fastMode ? '极速模式：正在构思宏大叙事...' : '正在为你创建创作空间...'
    });

    try {
      const { project } = await projectAutoCreate.createTemporaryProject();

      setCurrentProject(project as unknown as Project);
      setCurrentEpisode(null);

      navigate(`/project/${project.id}/script-workshop`);
    } catch (error) {
      console.error('Failed to create project:', error);
      addToast({ type: 'error', message: '创建项目失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTutorial = () => {
    addToast({ type: 'info', message: '快速入门教程开发中' });
  };

  const handleNavigateToProject = (project: Project) => {
    navigate(`/project/${project.id}`);
  };

  const handleNewProject = async () => {
    try {
      const newProject = await addProject('新项目');
      // 不要在首页设置 currentProject，交给 ProjectPage 根据 URL ID 加载和设置
      // 这样可以避免状态竞争和数据不一致
      addToast({ type: 'success', message: '新项目已创建' });
      navigate(`/project/${newProject.id}`);
    } catch (error) {
      addToast({ type: 'error', message: '创建项目失败' });
    }
  };

  const handleNavigateToScriptWorkshop = async () => {
    if (isLoading) return;

    if (currentProject?.id) {
      navigate(`/project/${currentProject.id}/script-workshop`);
      return;
    }

    setIsLoading(true);

    try {
      const { project } = await projectAutoCreate.createTemporaryProject();

      setCurrentProject(project as unknown as Project);
      setCurrentEpisode(null);

      addToast({ type: 'success', message: '已进入剧本工坊，开始创作吧！' });
      navigate(`/project/${project.id}/script-workshop`);

    } catch (error) {
      console.error('创建临时项目失败:', error);
      addToast({ type: 'error', message: '进入创作空间失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };



  return (
    <div className="h-screen w-screen fixed flex flex-col bg-background overflow-hidden">
      <Header variant="home" />

      <main className="flex-1 flex flex-col items-center justify-evenly px-4 sm:px-6 w-full max-w-full overflow-hidden">
        <div className="w-full max-w-3xl flex flex-col items-center gap-6 sm:gap-8 animate-fade-in relative z-10 shrink-0">
          <WelcomeHeader />
          <CreativeInput onGenerate={handleGenerate} />
          <QuickActions
            onTutorial={handleTutorial}
            onScriptWorkshop={handleNavigateToScriptWorkshop}
          />
        </div>

        <div className="w-full max-w-5xl animate-slide-up shrink-0" style={{ animationDelay: '0.1s' }}>
          <ProjectList onProjectClick={handleNavigateToProject} onNewProject={handleNewProject} />
        </div>
      </main>


    </div>
  );
}
