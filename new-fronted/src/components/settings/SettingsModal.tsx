import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Settings,
  Cpu,
  Video,
  Route,
  Plus,
  Server,
  Image as ImageIcon,
} from 'lucide-react';
import { useUIStore, useModelStore } from '@/hooks/useStore';
import { toast } from 'sonner';
import type {
  ModelProvider,
  ModelProviderCreate,
  ModelProviderUpdate,
  ProviderType,
  ProtocolType,
  TaskCategory,
  CategoryRoute,
  TestResult,
} from '@/types';
import { TaskCategoryMapping } from '@/types';
import { ProviderCard } from './ProviderCard';

const llmProtocols: { value: ProtocolType; label: string }[] = [
  { value: 'openai', label: 'OpenAI Compatible' },
  { value: 'anthropic', label: 'Anthropic (Claude)' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'azure', label: 'Azure OpenAI' },
];



const categoryIcons: Record<TaskCategory, React.ReactNode> = {
  creative: <Cpu size={16} />,
  content: <Server size={16} />,
  quality: <Settings size={16} />,
  video: <Video size={16} />,
  image_process: <ImageIcon size={16} />,
};

type TabType = 'routing' | 'llm' | 'video';

export function SettingsModal() {
  const { settingsModalOpen, closeSettingsModal } = useUIStore();
  const {
    providers,
    categoryRoutes,
    addProvider,
    updateProvider,
    deleteProvider,
    updateCategoryRoute,
    testProvider,
    refreshProviders,
  } = useModelStore();

  useEffect(() => {
    if (settingsModalOpen) {
      refreshProviders().catch(console.error);
    }
  }, [settingsModalOpen, refreshProviders]);

  const [activeTab, setActiveTab] = useState<TabType>('routing');
  const [editingProvider, setEditingProvider] = useState<{
    provider?: ModelProvider;
    isNew: boolean;
    type: ProviderType;
  } | null>(null);

  const llmProviders = providers.filter(
    (p) => !['sora', 'runway', 'pika'].includes(p.protocol)
  );
  const videoProviders = providers.filter((p) =>
    ['sora', 'runway', 'pika'].includes(p.protocol)
  );

  const handleAddProvider = (type: ProviderType) => {
    setEditingProvider({ isNew: true, type });
  };

  const handleEditProvider = (provider: ModelProvider) => {
    setEditingProvider({ provider, isNew: false, type: provider.provider_type });
  };

  const handleSaveProvider = async (
    data: ModelProviderCreate | ModelProviderUpdate
  ) => {
    try {
      if (editingProvider?.isNew) {
        await addProvider(data as ModelProviderCreate);
        toast.success('服务商添加成功');
      } else if (editingProvider?.provider) {
        await updateProvider(editingProvider.provider.id, data as ModelProviderUpdate);
        toast.success('服务商保存成功');
      }
      await refreshProviders();
      setEditingProvider(null);
    } catch (err) {
      console.error('Failed to save provider:', err);
      toast.error('保存服务商失败，请重试');
    }
  };

  const handleDeleteProvider = async (id: string) => {
    try {
      await deleteProvider(id);
      await refreshProviders();
      setEditingProvider(null);
      toast.success('服务商已删除');
    } catch (err) {
      console.error('Failed to delete provider:', err);
      toast.error('删除服务商失败，请重试');
    }
  };

  const handleTest = async (providerId: string, modelName: string) => {
    return await testProvider(providerId, modelName);
  };

  const handleUpdateRoute = async (
    category: TaskCategory,
    providerId: string,
    modelId: string
  ) => {
    await updateCategoryRoute(category, providerId, modelId);
  };

  const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'routing', label: '任务路由', icon: <Route size={16} /> },
    { id: 'llm', label: 'LLM 服务商', icon: <Cpu size={16} /> },
    { id: 'video', label: '视频服务商', icon: <Video size={16} /> },
  ];

  return (
    <Dialog open={settingsModalOpen} onOpenChange={closeSettingsModal}>
      <DialogContent className="w-full max-w-4xl sm:max-w-4xl h-[600px] sm:h-[600px] max-h-[80vh] bg-surface border-border flex flex-col p-0 overflow-hidden">
        <DialogHeader className="flex-shrink-0 px-6 pt-6 pb-2">
          <DialogTitle className="flex items-center gap-2 text-text-primary">
            <Settings size={20} />
            系统设置
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex-shrink-0 px-6 pb-2">
            <div className="flex bg-elevated rounded-lg p-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setEditingProvider(null);
                  }}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                    activeTab === tab.id
                      ? 'bg-surface text-text-primary shadow-sm'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 min-h-0 px-6 py-2 overflow-hidden">
            {activeTab === 'routing' && (
              <RoutingTab
                llmProviders={llmProviders}
                videoProviders={videoProviders}
                categoryRoutes={categoryRoutes}
                onUpdateRoute={handleUpdateRoute}
                onClose={closeSettingsModal}
              />
            )}
            {activeTab === 'llm' && (
              <LLMTab
                providers={llmProviders}
                editingProvider={editingProvider}
                onAddProvider={() => handleAddProvider('llm')}
                onEditProvider={handleEditProvider}
                onSaveProvider={handleSaveProvider}
                onDeleteProvider={handleDeleteProvider}
                onTest={handleTest}
                onCancelEdit={() => setEditingProvider(null)}
              />
            )}
            {activeTab === 'video' && (
              <VideoTab
                providers={videoProviders}
                editingProvider={editingProvider}
                onAddProvider={() => handleAddProvider('video')}
                onEditProvider={handleEditProvider}
                onSaveProvider={handleSaveProvider}
                onDeleteProvider={handleDeleteProvider}
                onTest={handleTest}
                onCancelEdit={() => setEditingProvider(null)}
              />
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface RoutingTabProps {
  llmProviders: ModelProvider[];
  videoProviders: ModelProvider[];
  categoryRoutes: Record<TaskCategory, CategoryRoute | null>;
  onUpdateRoute: (category: TaskCategory, providerId: string, modelId: string) => Promise<void>;
  onClose: () => void;
}

function RoutingTab({
  llmProviders,
  videoProviders,
  categoryRoutes,
  onUpdateRoute,
  onClose,
}: RoutingTabProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-4 pr-4 py-2 pb-4">
            <p className="text-sm text-text-secondary">
              为不同类型的任务配置默认的 AI 模型路由
            </p>
            {(Object.keys(TaskCategoryMapping) as TaskCategory[]).map(
              (category) => (
                <RoutingConfigRow
                  key={category}
                  category={category}
                  providers={
                    category === 'video' ? videoProviders : llmProviders
                  }
                  currentRoute={categoryRoutes[category]}
                  onUpdateRoute={onUpdateRoute}
                />
              )
            )}
          </div>
        </ScrollArea>
      </div>
      
      <div className="flex-shrink-0 pt-4 border-t border-border flex justify-end gap-2 mt-4">
        <Button variant="outline" onClick={onClose}>
          关闭
        </Button>
        <Button onClick={onClose}>
          完成
        </Button>
      </div>
    </div>
  );
}

interface LLMTabProps {
  providers: ModelProvider[];
  editingProvider: {
    provider?: ModelProvider;
    isNew: boolean;
    type: ProviderType;
  } | null;
  onAddProvider: () => void;
  onEditProvider: (provider: ModelProvider) => void;
  onSaveProvider: (data: ModelProviderCreate | ModelProviderUpdate) => Promise<void>;
  onDeleteProvider: (id: string) => Promise<void>;
  onTest: (providerId: string, modelName: string) => Promise<TestResult>;
  onCancelEdit: () => void;
}

function LLMTab({
  providers,
  editingProvider,
  onAddProvider,
  onEditProvider,
  onSaveProvider,
  onDeleteProvider,
  onTest,
  onCancelEdit,
}: LLMTabProps) {
  const isEditingLLM = editingProvider?.type === 'llm';

  return (
    <div className="flex flex-col h-full">
      {/* 可滚动内容区域 */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-4 pr-4 py-2 pb-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-text-secondary">
                管理 LLM 服务商和 API 密钥
              </p>
              <Button
                onClick={onAddProvider}
                size="sm"
                className="gap-2"
              >
                <Plus size={16} />
                添加服务商
              </Button>
            </div>

            {isEditingLLM && (
              <ProviderCard
                provider={editingProvider?.provider}
                isNew={editingProvider?.isNew}
                type="llm"
                protocols={llmProtocols}
                onSave={onSaveProvider}
                onCancel={onCancelEdit}
                onDelete={
                  editingProvider?.provider
                    ? () => onDeleteProvider(editingProvider.provider!.id)
                    : undefined
                }
                onTest={onTest}
              />
            )}

            {providers.length === 0 ? (
              <div className="text-center py-8 text-text-tertiary">
                <Server size={48} className="mx-auto mb-4 opacity-50" />
                <p>暂无 LLM 服务商</p>
                <p className="text-sm mt-2">点击上方按钮添加</p>
              </div>
            ) : (
              providers.map((provider) => (
                <ProviderCard
                  key={provider.id}
                  provider={provider}
                  isNew={false}
                  type="llm"
                  protocols={llmProtocols}
                  onSave={onSaveProvider}
                  onCancel={onCancelEdit}
                  onDelete={() => onDeleteProvider(provider.id)}
                  onTest={onTest}
                  onEdit={() => onEditProvider(provider)}
                  isCollapsed={editingProvider?.provider?.id !== provider.id}
                />
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

interface VideoTabProps {
  providers: ModelProvider[];
  editingProvider: {
    provider?: ModelProvider;
    isNew: boolean;
    type: ProviderType;
  } | null;
  onAddProvider: () => void;
  onEditProvider: (provider: ModelProvider) => void;
  onSaveProvider: (data: ModelProviderCreate | ModelProviderUpdate) => Promise<void>;
  onDeleteProvider: (id: string) => Promise<void>;
  onTest: (providerId: string, modelName: string) => Promise<TestResult>;
  onCancelEdit: () => void;
}

function VideoTab({
  providers,
  editingProvider,
  onAddProvider,
  onEditProvider,
  onSaveProvider,
  onDeleteProvider,
  onTest,
  onCancelEdit,
}: VideoTabProps) {
  const isEditingVideo = editingProvider?.type === 'video';

  return (
    <div className="flex flex-col h-full">
      {/* 可滚动内容区域 */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="space-y-4 pr-4 py-2 pb-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-text-secondary">
                管理视频生成服务商
              </p>
              <Button
                onClick={onAddProvider}
                size="sm"
                className="gap-2"
              >
                <Plus size={16} />
                添加服务商
              </Button>
            </div>

            {isEditingVideo && (
              <ProviderCard
                provider={editingProvider?.provider}
                isNew={editingProvider?.isNew}
                type="video"
                protocols={llmProtocols}
                onSave={onSaveProvider}
                onCancel={onCancelEdit}
                onDelete={
                  editingProvider?.provider
                    ? () => onDeleteProvider(editingProvider.provider!.id)
                    : undefined
                }
                onTest={onTest}
              />
            )}

            {providers.length === 0 ? (
              <div className="text-center py-8 text-text-tertiary">
                <Video size={48} className="mx-auto mb-4 opacity-50" />
                <p>暂无视频服务商</p>
                <p className="text-sm mt-2">点击上方按钮添加</p>
              </div>
            ) : (
              providers.map((provider) => (
                <ProviderCard
                  key={provider.id}
                  provider={provider}
                  isNew={false}
                  type="video"
                  protocols={llmProtocols}
                  onSave={onSaveProvider}
                  onCancel={onCancelEdit}
                  onDelete={() => onDeleteProvider(provider.id)}
                  onTest={onTest}
                  onEdit={() => onEditProvider(provider)}
                  isCollapsed={editingProvider?.provider?.id !== provider.id}
                />
              ))
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

interface RoutingConfigRowProps {
  category: TaskCategory;
  providers: ModelProvider[];
  currentRoute: CategoryRoute | null;
  onUpdateRoute: (category: TaskCategory, providerId: string, modelId: string) => Promise<void>;
}

function RoutingConfigRow({
  category,
  providers,
  currentRoute,
  onUpdateRoute,
}: RoutingConfigRowProps) {
  const config = TaskCategoryMapping[category];
  const selectedProvider = currentRoute?.providerId || '';
  const selectedModel = currentRoute?.modelId || '';

  const selectedProviderData = providers.find((p) => p.id === selectedProvider);
  const availableModels = selectedProviderData?.available_models || [];

  const handleProviderChange = async (providerId: string) => {
    if (providerId) {
      const provider = providers.find((p) => p.id === providerId);
      if (provider?.available_models?.[0]) {
        const firstModel = provider.available_models[0];
        await onUpdateRoute(category, providerId, firstModel);
      } else {
        await onUpdateRoute(category, providerId, '');
      }
    } else {
      await onUpdateRoute(category, '', '');
    }
  };

  const handleModelChange = async (modelId: string) => {
    if (selectedProvider && modelId) {
      await onUpdateRoute(category, selectedProvider, modelId);
    }
  };

  return (
    <div className="p-4 rounded-lg border border-border bg-elevated">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
          {categoryIcons[category]}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h4 className="font-medium text-text-primary">{config.name}</h4>
              <p className="text-xs text-text-secondary">{config.description}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-text-secondary block mb-1">
                服务商
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => handleProviderChange(e.target.value)}
                className="w-full px-3 py-2 rounded-md bg-surface border border-border text-sm text-text-primary"
              >
                <option value="">选择服务商...</option>
                {providers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-text-secondary block mb-1">
                模型
              </label>
              <select
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                disabled={!selectedProvider}
                className="w-full px-3 py-2 rounded-md bg-surface border border-border text-sm text-text-primary disabled:opacity-50"
              >
                <option value="">选择模型...</option>
                {availableModels.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
