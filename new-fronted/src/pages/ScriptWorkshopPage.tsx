import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Play,
  Save,
  Settings,
  Plus,
  Clock,
  Users,
  Mic,
  Music,
  Loader2,
  Sparkles,
  BookOpen
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Logo } from '@/components/ui/Logo';
import { ResizablePanel } from '@/components/ui/ResizablePanel';
import { AIAssistantPanel } from '@/components/ai/AIAssistantPanel';
import { useUIStore } from '@/hooks/useStore';
import { scenesService } from '@/api/services/scenes';
import { shotsService } from '@/api/services/shots';
import { episodesService } from '@/api/services/episodes';
import { projectsService } from '@/api/services/projects';
import {
  ModuleTabs,
  type EditorModule,
  NovelEditor,
  ScriptEditor,
  StoryboardEditor,
  OutlineEditor,
  ChapterTree,
  UnifiedReviewPanel
} from '@/components/workshop';
import { useWorkshopStore } from '@/store/workshopStore';
import { reviewService } from '@/api/services/review';
import { ConfirmNovelNameDialog } from '@/components/modals/ConfirmNovelNameDialog';
import type { components } from '@/types/api';
import type { OutlineNode } from '@/types/outline';
import type { ChapterReview, GlobalReview } from '@/types/review';

type SceneResponse = components['schemas']['SceneResponse'];
type ShotResponse = components['schemas']['ShotResponse'];
type EpisodeResponse = components['schemas']['EpisodeResponse'];
type ProjectResponse = components['schemas']['ProjectResponse'];

export function ScriptWorkshopPage() {
  const navigate = useNavigate();
  const { projectId, episodeId } = useParams<{ projectId: string; episodeId?: string }>();
  const { openBackstageModal, addToast } = useUIStore();
  const abortControllerRef = useRef<AbortController | null>(null);
  const isAICreationMode = !episodeId;

  const {
    outlineNodes,
    selectedNodeId,
    selectNode,
    globalReview,
    isReviewing,
    reReview,
    applySuggestion,
    ignoreIssue,
    loadGlobalReview,
    loadOutline,
    batchStatus,
    continueOutlineGeneration,
    isGenerating,
    updateOutlineNode,
  } = useWorkshopStore();

  const [activeModule, setActiveModule] = useState<EditorModule>('script');
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [scenes, setScenes] = useState<SceneResponse[]>([]);
  const [shots, setShots] = useState<ShotResponse[]>([]);
  const [episode, setEpisode] = useState<EpisodeResponse | null>(null);
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved');
  const [error, setError] = useState<string | null>(null);

  const [novelContent, setNovelContent] = useState('');
  const [novelTitle, setNovelTitle] = useState('');
  const [storyContent, setStoryContent] = useState('');
  const [scriptContent, setScriptContent] = useState('');
  const [storyboardShots, setStoryboardShots] = useState<Array<{
    shotNumber: number;
    title: string;
    subtitle?: string;
    shotType?: string;
    cameraMove?: string;
    description?: string;
    dialog?: string;
  }>>([]);
  const [isGeneratingShots, setIsGeneratingShots] = useState(false);

  const lastSavedTextRef = useRef('');

  useEffect(() => {
    if (!projectId) return;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        if (isAICreationMode) {
          const projectRes = await projectsService.getProject(projectId);
          setProject(projectRes.data);
          await loadOutline(projectId);
          setIsLoading(false);
          return;
        }

        const [episodeRes, scenesRes, projectRes] = await Promise.all([
          episodesService.getEpisode(projectId, episodeId!),
          scenesService.listScenes(episodeId!),
          projectsService.getProject(projectId),
        ]);

        setEpisode(episodeRes.data);
        setScenes(scenesRes.data);
        setProject(projectRes.data);

        const scriptText = episodeRes.data.scriptText || '';
        setStoryContent(scriptText);
        setScriptContent(scriptText);
        setNovelContent(scriptText);
        setNovelTitle(episodeRes.data.title || '');

        if (scenesRes.data.length > 0) {
          setSelectedSceneId(String(scenesRes.data[0].sceneId));
        }

        await loadOutline(projectId);

        await loadGlobalReview(projectId);
      } catch (err) {
        console.error('Failed to load data:', err);
        setError('加载数据失败，请稍后重试');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [projectId, episodeId, loadGlobalReview, isAICreationMode]);

  useEffect(() => {
    if (!episodeId || !selectedSceneId) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    const loadShots = async () => {
      try {
        const shotsRes = await shotsService.listShots(episodeId, selectedSceneId);
        if (signal.aborted) return;
        setShots(shotsRes.data);
      } catch (err: any) {
        if (err.name === 'AbortError' || signal.aborted) return;
        console.error('Failed to load shots:', err);
      }
    };

    loadShots();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [episodeId, selectedSceneId]);

  // 状态引入
  const [showConfirmNameDialog, setShowConfirmNameDialog] = useState(false);
  const [projectIsTemp, setProjectIsTemp] = useState(false);
  // ... 其他状态 ...

  useEffect(() => {
    // 识别是否为临时项目
    if (project?.isTemporary || project?.name?.startsWith('新小说项目-') || project?.name === '未命名项目') {
      setProjectIsTemp(true);
    } else {
      setProjectIsTemp(false);
    }
  }, [project]);

  const handleSave = async (force: boolean = false) => {
    if (!projectId || !episodeId) return;

    // 如果是临时项目且不是强制保存（比如自动保存），则拦截并弹窗
    if (projectIsTemp && !force) {
      setShowConfirmNameDialog(true);
      return;
    }

    setIsSaving(true);
    setAutoSaveStatus('saving');

    try {
      let contentToSave = '';
      switch (activeModule) {
        case 'novel':
          contentToSave = novelContent;
          break;
        case 'script':
          contentToSave = scriptContent;
          break;
        default:
          contentToSave = storyContent;
      }

      await episodesService.updateEpisode(projectId, episodeId, {
        scriptText: contentToSave,
      });
      lastSavedTextRef.current = contentToSave;
      setAutoSaveStatus('saved');
      addToast?.({ type: 'success', message: '内容已保存' });
    } catch (err) {
      console.error('Failed to save:', err);
      setError('保存失败');
      setAutoSaveStatus('unsaved');
      addToast?.({ type: 'error', message: '保存失败' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirmProjectName = async (name: string) => {
    if (!projectId) return;
    try {
      await projectsService.saveTempProject(projectId, { name });
      // 更新本地项目状态
      if (project) {
        setProject({ ...project, name, isTemporary: false });
        setProjectIsTemp(false);
      }
      setShowConfirmNameDialog(false);
      // 转正后立即保存内容
      await handleSave(true);
      addToast?.({ type: 'success', message: `项目已转正为: ${name}` });
    } catch (err) {
      console.error("Failed to convert project:", err);
      addToast?.({ type: 'error', message: '转正项目失败' });
    }
  };

  // 自动保存逻辑：目前为简单起见，仅在非临时项目时启用，或者可以设计为临时项目也自动保存内容但不弹窗
  // 这里策略：临时项目也自动保存内容（不依赖项目名），只有手动点击保存按钮才触发转正弹窗
  useEffect(() => {
    const autoSaveInterval = setInterval(async () => {
      if (
        autoSaveStatus === 'unsaved' &&
        projectId &&
        episodeId
      ) {
        // 调用 handleSave(true) 强制保存内容，不弹窗
        handleSave(true);
      }
    }, 30000);

    return () => clearInterval(autoSaveInterval);
  }, [autoSaveStatus, projectId, episodeId, projectIsTemp]);

  const handleContentChange = (content: string) => {
    switch (activeModule) {
      case 'novel':
        setNovelContent(content);
        break;
      case 'script':
        setScriptContent(content);
        setStoryContent(content);
        break;
    }
    if (content !== lastSavedTextRef.current) {
      setAutoSaveStatus('unsaved');
    }
  };

  const renderSaveStatus = () => {
    switch (autoSaveStatus) {
      case 'saved':
        return <span className="text-xs text-green-500">已保存</span>;
      case 'saving':
        return <span className="text-xs text-yellow-500">保存中...</span>;
      case 'unsaved':
        return <span className="text-xs text-orange-500">未保存</span>;
      default:
        return null;
    }
  };

  const handleAddScene = async () => {
    if (!episodeId) return;

    try {
      const newScene = await scenesService.createScene(episodeId, {
        location: '新场景',
        description: '',
        createMasterNode: true,
      });
      setScenes(prev => [...prev, newScene.data]);
      setSelectedSceneId(String(newScene.data.sceneId));
    } catch (err) {
      console.error('Failed to create scene:', err);
      setError('创建场景失败');
    }
  };

  const handleGenerateShots = async () => {
    setIsGeneratingShots(true);

    await new Promise(resolve => setTimeout(resolve, 2000));

    const mockShots = [
      { shotNumber: 1, title: '开场全景', shotType: '全景', cameraMove: '静止', description: '展示场景全貌，建立空间感' },
      { shotNumber: 2, title: '主角登场', shotType: '中景', cameraMove: '推近', description: '主角从远处走来，表情凝重' },
      { shotNumber: 3, title: '眼神特写', shotType: '特写', cameraMove: '静止', description: '眼神中透露出决心' },
      { shotNumber: 4, title: '对话场景', shotType: '中景', cameraMove: '摇移', description: '两人对话，气氛紧张' },
    ];

    setStoryboardShots(mockShots);
    setIsGeneratingShots(false);
    addToast?.({ type: 'success', message: '分镜生成完成' });
  };

  const selectedScene = scenes.find(s => String(s.sceneId) === selectedSceneId);

  const handleNodeSelect = useCallback((nodeId: string, node: OutlineNode) => {
    selectNode(nodeId);
    if (node.type === 'scene' || node.type === 'shot') {
      setSelectedSceneId(nodeId);
    }
  }, [selectNode]);

  const handleReReview = useCallback(async () => {
    if (!projectId) return;

    if (activeModule === 'outline') {
      if (outlineNodes.length === 0) {
        addToast?.({ type: 'warning', message: '暂无大纲数据，请先完成故事策划' });
        return;
      }

      if (globalReview) {
        await reReview(projectId);
      } else {
        await reviewService.triggerOutlineReview(projectId);
        await loadGlobalReview(projectId);
      }
    } else if (selectedNodeId) {
      await reReview(projectId, selectedNodeId);
    }
  }, [projectId, activeModule, selectedNodeId, reReview, globalReview, loadGlobalReview, outlineNodes, addToast]);

  const handleApplySuggestion = useCallback(async (suggestionId: string) => {
    if (!projectId || !selectedNodeId) return;
    await applySuggestion(projectId, selectedNodeId, suggestionId);
  }, [projectId, selectedNodeId, applySuggestion]);

  const handleIgnoreIssue = useCallback(async (issueId: string) => {
    if (!projectId || !selectedNodeId) return;
    await ignoreIssue(projectId, selectedNodeId, issueId);
  }, [projectId, selectedNodeId, ignoreIssue]);

  const selectedNode = outlineNodes.find(n => n.id === selectedNodeId);

  const renderLeftPanel = () => {
    if (activeModule === 'outline' || activeModule === 'novel') {
      return (
        <ChapterTree
          nodes={outlineNodes}
          selectedId={selectedNodeId}
          onSelect={handleNodeSelect}
          batchStatus={batchStatus}
          onContinueGeneration={() => projectId && continueOutlineGeneration(projectId)}
          isGenerating={isGenerating}
        />
      );
    }
    
    return (
      <>
        <div className="p-4 border-b border-border">
          <Button
            variant="outline"
            className="w-full gap-2"
            onClick={handleAddScene}
          >
            <Plus size={16} />
            添加场景
          </Button>
        </div>
        <ScrollArea className="flex-1 min-h-0">
          {scenes.map((scene) => (
            <div
              key={String(scene.sceneId)}
              onClick={() => setSelectedSceneId(String(scene.sceneId))}
              className={`p-4 cursor-pointer border-b border-border transition-all duration-200 ${selectedSceneId === String(scene.sceneId)
                ? 'bg-primary/10 border-l-2 border-l-primary'
                : 'hover:bg-elevated border-l-2 border-l-transparent'
                }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className="text-xs">
                  {scene.sceneNumber}
                </Badge>
                <span className="text-xs text-text-tertiary flex items-center gap-1">
                  <Clock size={12} />
                  夜晚
                </span>
              </div>
              <p className="text-sm font-medium text-text-primary mb-1">
                {scene.location}
              </p>
              <p className="text-xs text-text-secondary line-clamp-2">
                {scene.description || '暂无描述'}
              </p>
              <div className="flex items-center gap-1 mt-2">
                <Badge variant="secondary" className="text-xs">
                  {scene.shotCount} 镜头
                </Badge>
              </div>
            </div>
          ))}
        </ScrollArea>
      </>
    );
  };

  const renderBottomPanel = () => {
    let review: GlobalReview | ChapterReview | null = null;

    if (activeModule === 'outline') {
      review = globalReview;
    } else if (selectedNodeId && globalReview?.chapterReviews?.[selectedNodeId]) {
      const chapterData = globalReview.chapterReviews[selectedNodeId];
      review = {
        chapterId: selectedNodeId,
        reviewedAt: globalReview.generatedAt,
        score: chapterData.score,
        categories: {} as ChapterReview['categories'],
        issues: chapterData.issues || [],
        tensionCurve: [],
        summary: '',
      };
    }
    
    const chapterTitle = activeModule !== 'outline' && selectedNode
      ? selectedNode.title
      : undefined;

    return (
      <UnifiedReviewPanel
        review={review}
        chapterTitle={chapterTitle}
        isLoading={isReviewing}
        onReReview={handleReReview}
        onApplySuggestion={handleApplySuggestion}
        onIgnoreIssue={handleIgnoreIssue}
      />
    );
  };

  const renderEditorContent = () => {
    if (isAICreationMode) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <Sparkles className="w-20 h-20 mb-6 text-primary/60" />
          <h2 className="text-2xl font-semibold mb-3 text-text-primary">开始你的创作之旅</h2>
          <p className="text-base text-text-secondary max-w-lg mb-6">
            告诉我你想创作什么类型的故事？AI助手会帮你生成选题方案、大纲和剧本。
          </p>
          <Button variant="outline" size="lg" onClick={() => navigate(`/project/${projectId}`)}>
            返回画布
          </Button>
        </div>
      );
    }

    switch (activeModule) {
      case 'outline':
        if (!selectedNode) {
          return (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
              <BookOpen className="w-16 h-16 mb-4 opacity-50" />
              <h2 className="text-lg font-medium mb-2">大纲编辑模式</h2>
              <p className="text-sm max-w-md">
                请在左侧选择章节进行编辑。大纲数据将自动同步到剧本医生进行审阅。
              </p>
            </div>
          );
        }

        return (
          <OutlineEditor
            content={selectedNode.metadata?.content || selectedNode.metadata?.summary || ''}
            onChange={(html) => updateOutlineNode(selectedNode.id, {
              metadata: { ...selectedNode.metadata, content: html }
            })}
            title={selectedNode.title}
            onTitleChange={(title) => updateOutlineNode(selectedNode.id, { title })}
            nodeType={selectedNode.type}
            nodeNumber={selectedNode.episodeNumber || selectedNode.sceneNumber || selectedNode.shotNumber}
          />
        );
      case 'novel':
        return (
          <NovelEditor
            content={novelContent}
            onChange={handleContentChange}
            title={novelTitle}
            onTitleChange={setNovelTitle}
          />
        );
      case 'script':
        return (
          <ScriptEditor
            storyContent={storyContent}
            scriptContent={scriptContent}
            onStoryChange={setStoryContent}
            onScriptChange={setScriptContent}
            title={episode?.title || ''}
          />
        );
      case 'storyboard':
        return (
          <StoryboardEditor
            shots={storyboardShots}
            onShotsChange={setStoryboardShots}
            onGenerate={handleGenerateShots}
            isGenerating={isGeneratingShots}
          />
        );
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex items-center gap-2 text-text-secondary">
          <Loader2 className="animate-spin" size={20} />
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-error mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>重试</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen supports-[height:100dvh]:h-[100dvh] flex flex-col overflow-hidden bg-background">
      <header className="flex-shrink-0 flex items-center justify-between px-4 py-3 bg-surface border-b border-border">
        <div className="flex items-center gap-3">
          <div
            onClick={() => navigate('/')}
            className="cursor-pointer hover:opacity-80 transition-opacity flex items-center"
            title="返回工作台"
          >
            <Logo size="sm" showText={false} />
          </div>

          <span className="text-text-tertiary text-sm">/</span>

          <button
            onClick={() => navigate(`/project/${projectId}`)}
            className="text-sm font-medium text-text-secondary hover:text-text-primary transition-colors truncate max-w-[150px]"
            title="返回项目详情"
          >
            {project?.name || '加载中...'}
          </button>

          <span className="text-text-tertiary text-sm">/</span>

          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <h1 className="font-semibold text-sm text-text-primary">剧本工坊</h1>
              <Badge variant="outline" className="text-[10px] h-4 px-1 text-text-tertiary border-border">
                Ep.{episode?.episodeNumber}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="gap-1 hidden sm:inline-flex">
            <Clock size={14} />
            {scenes.length} 场景
          </Badge>
          <Badge variant="secondary" className="gap-1 hidden sm:inline-flex">
            <Users size={14} />
            {shots.length} 镜头
          </Badge>
          <Separator orientation="vertical" className="h-6 hidden sm:block" />
          <Button
            variant="outline"
            size="sm"
            className="gap-2 hidden sm:flex"
            onClick={() => handleSave(false)}
            disabled={isSaving}
          >
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            保存
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 hidden sm:flex border-primary text-primary hover:bg-primary/10"
          >
            <Sparkles size={16} />
            同步到分镜台
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => openBackstageModal('settings')}
          >
            <Settings size={18} />
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <ResizablePanel
          minWidth={200}
          maxWidth={400}
          defaultWidth={224}
          side="left"
          storageKey="script-workshop-left"
          className="hidden md:flex flex-col bg-surface border-r border-border"
        >
          {renderLeftPanel()}
        </ResizablePanel>

        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-border bg-surface/50">
            <ModuleTabs activeModule={activeModule} onModuleChange={setActiveModule} />
            <div className="flex items-center gap-4">
              {renderSaveStatus()}
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" className="gap-2 hidden lg:flex">
                  <Mic size={16} />
                  配音
                </Button>
                <Button variant="ghost" size="sm" className="gap-2 hidden lg:flex">
                  <Music size={16} />
                  音乐
                </Button>
                <Button className="btn-primary gap-2">
                  <Play size={16} />
                  预览
                </Button>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-hidden">
            {renderEditorContent()}
          </div>

          {renderBottomPanel()}
        </div>

        <ResizablePanel
          minWidth={280}
          maxWidth={800}
          defaultWidth={400}
          side="right"
          storageKey="script-workshop-right"
          className="hidden xl:flex flex-col bg-surface border-l border-border"
        >
          <AIAssistantPanel
            projectId={projectId}
            sceneContext={(() => {
              if (!selectedScene) return undefined;
              return {
                id: String(selectedScene.sceneId),
                number: selectedScene.sceneNumber,
                location: selectedScene.location,
                description: selectedScene.description || '',
              };
            })()}
          />
        </ResizablePanel>
      </div>

      <ConfirmNovelNameDialog
        isOpen={showConfirmNameDialog}
        onClose={() => setShowConfirmNameDialog(false)}
        suggestedName={project?.name?.startsWith("新小说项目") ? "" : (project?.name || "")}
        onConfirm={handleConfirmProjectName}
      />
    </div>
  );
}
