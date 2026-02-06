import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { ProjectHeader } from '@/components/layout/ProjectHeader';
import { LeftSidebar } from '@/components/panels/LeftSidebar';
import { RightPanel } from '@/components/panels/RightPanel';
import { StoryboardCanvas } from '@/components/canvas/StoryboardCanvas';
import { BatchGenerateModal } from '@/components/modals/BatchGenerateModal';
import { BackstageModal } from '@/components/modals/BackstageModal';
import { InpaintModal } from '@/components/modals/InpaintModal';
import { OutpaintModal } from '@/components/modals/OutpaintModal';
import { VirtualCameraModal } from '@/components/modals/VirtualCameraModal';
import { CameraMoveModal } from '@/components/modals/CameraMoveModal';
import { ConfirmNovelNameDialog } from '@/components/modals/ConfirmNovelNameDialog';
import { CreateScriptOptionsDialog } from '@/components/modals/CreateScriptOptionsDialog';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import { projectsService } from '@/api/services/projects';
import { episodesService } from '@/api/services/episodes';
import { projectAutoCreate } from '@/api/services/projectAutoCreate';
import type { ShotNode, Project, Episode } from '@/types';

export function ProjectPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { theme, currentEpisode, setCurrentProject, setCurrentEpisode } = useAppStore();
  const { modal, closeModal, addToast } = useUIStore();
  const [selectedNode, setSelectedNode] = useState<ShotNode | null>(null);
  const [isBatchGenerateOpen, setIsBatchGenerateOpen] = useState(false);
  const [isBackstageOpen, setIsBackstageOpen] = useState(false);
  const [isCameraMoveOpen, setIsCameraMoveOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);

  const [isCreateOptionsOpen, setIsCreateOptionsOpen] = useState(false);
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [suggestedNovelName, setSuggestedNovelName] = useState('');
  const [tempProjectId, setTempProjectId] = useState<string | null>(null);
  const [tempEpisodeId, setTempEpisodeId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadProject = async () => {
      if (!projectId) {
        navigate('/', { replace: true });
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const [projectRes, episodesRes] = await Promise.all([
          projectsService.getProject(projectId),
          episodesService.listEpisodes(projectId),
        ]);

        if (!isMounted) return;

        // 防御性编程：确保 data 存在
        if (!projectRes || !projectRes.data) {
          throw new Error('Project data is missing');
        }

        const apiProject = projectRes.data;
        const loadedProject: Project = {
          id: apiProject.id,
          name: apiProject.name,
          coverImage: apiProject.coverImage || undefined,
          description: '',
          type: 'film',
          status: 'draft',
          createdAt: new Date(apiProject.createdAt),
          updatedAt: new Date(apiProject.updatedAt),
          episodes: [],
          characters: [],
          scenes: [],
        };

        // 处理 episodesRes 可能的空值情况
        const rawEpisodes = episodesRes?.data || [];
        const loadedEpisodes = Array.isArray(rawEpisodes)
          ? rawEpisodes.map((ep: any) => ({
            id: ep.episodeId,
            projectId: ep.projectId,
            episodeNumber: ep.episodeNumber,
            title: ep.title,
            summary: ep.summary,
            script: ep.scriptText,
            novelContent: ep.novelContent,
            wordCount: ep.wordCount,
            status: ep.status,
            createdAt: new Date(ep.createdAt),
            updatedAt: new Date(ep.updatedAt),
          }))
          : [];

        setProject(loadedProject);
        setEpisodes(loadedEpisodes);
        setCurrentProject(loadedProject);

        // 如果没有加载到剧集，确保 currentEpisode 为 null
        if (loadedEpisodes.length === 0) {
          setCurrentEpisode(null);
        } else {
          // 如果当前没有选中剧集，或者选中的剧集不属于当前项目，则选中第一集
          if (!currentEpisode || !loadedEpisodes.find(ep => ep.id === currentEpisode.id)) {
            setCurrentEpisode(loadedEpisodes[0]);
          }
        }
      } catch (err) {
        if (!isMounted) return;
        console.error('Failed to load project:', err);
        setError('加载项目失败，请刷新重试');
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadProject();

    return () => {
      isMounted = false;
    };
  }, [projectId, navigate, setCurrentProject, setCurrentEpisode]);

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  const handleNodeSelect = (node: ShotNode) => {
    setSelectedNode(node);
  };

  const handleScriptWorkshop = async () => {
    if (!project?.id || isProcessing) return;

    if (currentEpisode?.id) {
      navigate(`/project/${project.id}/episode/${currentEpisode.id}/script-workshop`);
      return;
    }

    setIsCreateOptionsOpen(true);
  };

  const handleAICreation = async () => {
    setIsCreateOptionsOpen(false);
    setIsProcessing(true);

    try {
      const { project: newProject, episode } = await projectAutoCreate.createTemporaryProject();

      setTempProjectId(newProject.id);
      setTempEpisodeId(episode.episodeId);
      setSuggestedNovelName(newProject.name || '');
      setIsConfirmDialogOpen(true);
    } catch (error) {
      console.error('创建临时项目失败:', error);
      addToast({ type: 'error', message: '创建创作空间失败，请重试' });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleManualCreation = async () => {
    setIsCreateOptionsOpen(false);

    if (!project?.id) return;

    try {
      if (!currentEpisode?.id) {
        const episode = await episodesService.createEpisode(project.id, {
          title: '第一集',
          summary: '',
        });
        setCurrentEpisode(episode.data as unknown as Episode);
        navigate(`/project/${project.id}/episode/${episode.data.episodeId}/script-workshop`);
      } else {
        navigate(`/project/${project.id}/episode/${currentEpisode.id}/script-workshop`);
      }
    } catch (error) {
      console.error('创建剧集失败:', error);
      addToast({ type: 'error', message: '创建剧集失败' });
    }
  };

  const handleConfirmNovelName = async (confirmedName: string) => {
    if (!tempProjectId || !tempEpisodeId) return;

    try {
      await projectAutoCreate.convertToFormalProject(tempProjectId, confirmedName);
      addToast({ type: 'success', message: `项目已命名为《${confirmedName}》` });
      navigate(`/project/${tempProjectId}/episode/${tempEpisodeId}/script-workshop`);
    } catch (error) {
      console.error('更新项目名称失败:', error);
      addToast({ type: 'error', message: '保存项目名称失败' });
    } finally {
      setIsConfirmDialogOpen(false);
    }
  };

  const handleBatchGenerate = () => {
    setIsBatchGenerateOpen(true);
  };

  const handleBackstage = () => {
    setIsBackstageOpen(true);
  };

  const handleExport = () => {
    console.log('Export');
  };

  const handleRenameProject = async (newName: string) => {
    if (!project) return;
    try {
      await projectsService.updateProject(project.id, { name: newName });
      const updatedProject = { ...project, name: newName };
      setProject(updatedProject);
      setCurrentProject(updatedProject);
      addToast({ type: 'success', message: '项目名称已更新' });
    } catch (error) {
      console.error('Failed to update project name:', error);
      addToast({ type: 'error', message: '更新项目名称失败' });
      throw error;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex items-center gap-2 text-text-secondary">
          <Loader2 className="animate-spin" size={20} />
          <span>加载项目中...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-error mb-4">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen supports-[height:100dvh]:h-[100dvh] flex flex-col overflow-hidden bg-background">
      <ProjectHeader
        project={project}
        onRename={handleRenameProject}
        onScriptWorkshop={handleScriptWorkshop}
        onBatchGenerate={handleBatchGenerate}
        onExport={handleExport}
        onBackstage={handleBackstage}
      />

      <div className="flex-1 flex overflow-hidden relative">
        <LeftSidebar episodes={episodes} />

        <StoryboardCanvas
          episodeId={currentEpisode?.id || ''}
          onNodeSelect={handleNodeSelect}
        />

        <RightPanel />
      </div>

      <BatchGenerateModal
        isOpen={isBatchGenerateOpen}
        onClose={() => setIsBatchGenerateOpen(false)}
      />

      <BackstageModal
        isOpen={isBackstageOpen}
        onClose={() => setIsBackstageOpen(false)}
      />

      <CameraMoveModal
        isOpen={isCameraMoveOpen || modal.type === 'cameraMove'}
        onClose={() => {
          setIsCameraMoveOpen(false);
          closeModal();
        }}
        imageUrl={selectedNode?.imageUrl}
      />

      <InpaintModal
        isOpen={modal.type === 'inpaint'}
        onClose={closeModal}
        imageUrl={selectedNode?.imageUrl}
      />

      <OutpaintModal
        isOpen={modal.type === 'outpaint'}
        onClose={closeModal}
        imageUrl={selectedNode?.imageUrl}
      />

      <VirtualCameraModal
        isOpen={modal.type === 'virtualCamera'}
        onClose={closeModal}
        imageUrl={selectedNode?.imageUrl}
      />

      <CreateScriptOptionsDialog
        isOpen={isCreateOptionsOpen}
        onClose={() => setIsCreateOptionsOpen(false)}
        onAICreation={handleAICreation}
        onManualCreation={handleManualCreation}
      />

      <ConfirmNovelNameDialog
        isOpen={isConfirmDialogOpen}
        onClose={() => setIsConfirmDialogOpen(false)}
        suggestedName={suggestedNovelName}
        onConfirm={handleConfirmNovelName}
        isLoading={isProcessing}
      />
    </div>
  );
}
