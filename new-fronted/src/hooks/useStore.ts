import { useState, useCallback } from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { modelsService } from '@/api/services/models';
import { projectsService } from '@/api/services/projects';
import type {
  AppState,
  CanvasState,
  CanvasInteractionState,
  ModalState,
  Toast,
  Project,
  Episode,
  Theme,
  ShotNode,
  ShotConnection,
  CanvasData,
  NodeStatus,
  ModelProvider,
  ModelProviderCreate,
  ModelProviderUpdate,
  TaskCategory,
  CategoryRoute,
  TestResult,
  RightPanelMode
} from '@/types';

interface AppStore extends AppState {
  setTheme: (theme: Theme) => void;
  setUser: (user: AppState['user']) => void;
  setCurrentProject: (project: Project | null) => void;
  setCurrentEpisode: (episode: Episode | null) => void;
  addNotification: (notification: AppState['notifications'][0]) => void;
  removeNotification: (id: string) => void;
}

interface CanvasStore extends CanvasState, Omit<CanvasInteractionState, 'selectedCards' | 'clipboard' | 'connectionSource' | 'connectionTarget'> {
  selectedNodeIds: string[];
  clipboardNodes: ShotNode[];
  connectionSource: string | null;
  connectionTarget: string | null;
  setZoom: (zoom: number) => void;
  setOffset: (offset: { x: number; y: number }) => void;
  resetView: () => void;
  toggleGrid: () => void;
  selectNode: (nodeId: string, multi?: boolean) => void;
  deselectAll: () => void;
  setIsDragging: (isDragging: boolean) => void;
  setIsPanning: (isPanning: boolean) => void;
  setClipboardNodes: (nodes: ShotNode[]) => void;
  selectCard: (cardId: string, multi?: boolean) => void;
  setClipboard: (_unused: unknown[]) => void;
  startConnection: (nodeId: string) => void;
  endConnection: () => void;
  setConnectionTarget: (nodeId: string | null) => void;
  setMousePosition: (pos: { x: number; y: number }) => void;
}

interface EpisodeStore {
  currentCanvasData: CanvasData | null;
  shotNodes: ShotNode[];
  connections: ShotConnection[];
  setCurrentCanvasData: (data: CanvasData | null) => void;
  addShotNode: (node: ShotNode) => void;
  updateShotNode: (id: string, updates: Partial<ShotNode>) => void;
  deleteShotNode: (id: string) => void;
  moveShotNode: (id: string, position: { x: number; y: number }) => void;
  updateNodeStatus: (id: string, status: NodeStatus) => void;
  addConnection: (connection: ShotConnection) => void;
  deleteConnection: (id: string) => void;
  loadEpisodeCanvas: (canvasData: CanvasData) => void;
  clearEpisodeCanvas: () => void;
}

interface ContentStatus {
  hasNovelContent: boolean;
  hasScript: boolean;
  hasStoryboard: boolean;
  hasAnyContent: boolean;
}

interface UIStore {
  sidebarCollapsed: boolean;
  rightPanelVisible: boolean;
  rightPanelMode: RightPanelMode;
  selectedNodeId: string | null;
  activeTab: 'script' | 'storyboard' | 'card';
  modal: ModalState;
  toasts: Toast[];
  settingsModalOpen: boolean;
  backstageModalOpen: boolean;
  backstageActiveTab: string;
  contentStatus: ContentStatus;
  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  openDirectorPanel: () => void;
  openNodeEditPanel: (nodeId: string) => void;
  closeRightPanel: () => void;
  setActiveTab: (tab: 'script' | 'storyboard' | 'card') => void;
  openModal: (type: ModalState['type'], data?: any) => void;
  closeModal: () => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  openSettingsModal: () => void;
  closeSettingsModal: () => void;
  openBackstageModal: (tab?: string) => void;
  closeBackstageModal: () => void;
  setBackstageActiveTab: (tab: string) => void;
  updateContentStatus: (episode: Episode | null) => void;
}

interface ProjectStore {
  projects: Project[];
  isLoading: boolean;
  error: string | null;
  currentEpisodeId: string | null;
  setCurrentEpisodeId: (id: string | null) => void;
  fetchProjects: () => Promise<void>;
  addProject: (name: string, meta?: any) => Promise<Project>;
  updateProject: (id: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
}

interface ModelStore {
  providers: ModelProvider[];
  categoryRoutes: Record<TaskCategory, CategoryRoute | null>;
  isLoading: boolean;
  error: string | null;
  addProvider: (provider: ModelProviderCreate) => Promise<void>;
  updateProvider: (id: string, updates: ModelProviderUpdate) => Promise<void>;
  deleteProvider: (id: string) => Promise<void>;
  updateCategoryRoute: (category: TaskCategory, providerId: string, modelId: string) => Promise<void>;
  testProvider: (providerId: string, modelName: string) => Promise<TestResult>;
  refreshProviders: () => Promise<void>;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      theme: 'dark',
      user: {
        id: '1',
        name: 'admin',
        balance: 666666.00,
      },
      currentProject: null,
      currentEpisode: null,
      notifications: [],
      setTheme: (theme: Theme) => set({ theme }),
      setUser: (user: AppState['user']) => set({ user }),
      setCurrentProject: (project: Project | null) => set({ currentProject: project }),
      setCurrentEpisode: (episode: Episode | null) => set({ currentEpisode: episode }),
      addNotification: (notification: AppState['notifications'][0]) =>
        set((state: AppStore) => ({ notifications: [...state.notifications, notification] })),
      removeNotification: (id: string) =>
        set((state: AppStore) => ({
          notifications: state.notifications.filter((n) => n.id !== id)
        })),
    }),
    {
      name: 'storyboard-app-storage',
      version: 1,
      partialize: (state: AppStore) => ({ theme: state.theme, user: state.user }),
      onRehydrateStorage: () => (_state, error) => {
        if (error) {
          console.error('[useAppStore] Failed to rehydrate storage:', error);
          localStorage.removeItem('storyboard-app-storage');
        }
      },
    }
  )
);

export const useCanvasStore = create<CanvasStore>((set, get) => ({
  zoom: 1,
  offset: { x: 0, y: 0 },
  gridVisible: true,
  isDragging: false,
  isPanning: false,
  selectedNodeIds: [],
  clipboardNodes: [],
  isConnecting: false,
  connectionSource: null,
  connectionTarget: null,
  mousePosition: { x: 0, y: 0 },
  setZoom: (zoom: number) => set({ zoom: Math.max(0.1, Math.min(5, zoom)) }),
  setOffset: (offset: { x: number; y: number }) => set({ offset }),
  resetView: () => set({ zoom: 1, offset: { x: 0, y: 0 } }),
  toggleGrid: () => set((state: CanvasStore) => ({ gridVisible: !state.gridVisible })),
  selectNode: (nodeId: string, multi = false) => set((state: CanvasStore) => {
    if (multi) {
      const exists = state.selectedNodeIds.includes(nodeId);
      if (exists) {
        return { selectedNodeIds: state.selectedNodeIds.filter((id: string) => id !== nodeId) };
      }
      return { selectedNodeIds: [...state.selectedNodeIds, nodeId] };
    }
    return { selectedNodeIds: [nodeId] };
  }),
  selectCard: (cardId: string, multi = false) => get().selectNode(cardId, multi),
  deselectAll: () => set({ selectedNodeIds: [] }),
  setIsDragging: (isDragging: boolean) => set({ isDragging }),
  setIsPanning: (isPanning: boolean) => set({ isPanning }),
  setClipboardNodes: (clipboardNodes: ShotNode[]) => set({ clipboardNodes }),
  setClipboard: () => { },
  startConnection: (nodeId: string) => set({ isConnecting: true, connectionSource: nodeId, connectionTarget: null }),
  endConnection: () => set({ isConnecting: false, connectionSource: null, connectionTarget: null }),
  setConnectionTarget: (nodeId: string | null) => set({ connectionTarget: nodeId }),
  setMousePosition: (pos: { x: number; y: number }) => set({ mousePosition: pos }),
}));

export const useEpisodeStore = create<EpisodeStore>((set) => ({
  currentCanvasData: null,
  shotNodes: [],
  connections: [],
  setCurrentCanvasData: (data: CanvasData | null) => set({ currentCanvasData: data }),
  addShotNode: (node: ShotNode) => set((state: EpisodeStore) => ({
    shotNodes: [...state.shotNodes, node]
  })),
  updateShotNode: (id: string, updates: Partial<ShotNode>) => set((state: EpisodeStore) => ({
    shotNodes: state.shotNodes.map((n) =>
      n.shotId === id ? { ...n, ...updates } : n
    )
  })),
  deleteShotNode: (id: string) => set((state: EpisodeStore) => ({
    shotNodes: state.shotNodes.filter((n) => n.shotId !== id),
    connections: state.connections.filter((c) => c.source !== id && c.target !== id)
  })),
  moveShotNode: (id: string, position: { x: number; y: number }) => set((state: EpisodeStore) => ({
    shotNodes: state.shotNodes.map((n) =>
      n.shotId === id ? { ...n, position } : n
    )
  })),
  updateNodeStatus: (id: string, status: NodeStatus) => set((state: EpisodeStore) => ({
    shotNodes: state.shotNodes.map((n) =>
      n.shotId === id ? { ...n, status } : n
    )
  })),
  addConnection: (connection: ShotConnection) => set((state: EpisodeStore) => {
    const exists = state.connections.some(
      (c) => c.source === connection.source && c.target === connection.target
    );
    if (exists) return state;
    return { connections: [...state.connections, connection] };
  }),
  deleteConnection: (id: string) => set((state: EpisodeStore) => ({
    connections: state.connections.filter((c) => c.id !== id)
  })),
  loadEpisodeCanvas: (canvasData: CanvasData) => set({
    currentCanvasData: canvasData,
    shotNodes: canvasData.nodes || [],
    connections: canvasData.connections || []
  }),
  clearEpisodeCanvas: () => set({
    currentCanvasData: null,
    shotNodes: [],
    connections: []
  })
}));

export const useUIStore = create<UIStore>((set) => ({
  sidebarCollapsed: false,
  rightPanelVisible: false,
  rightPanelMode: 'director',
  selectedNodeId: null,
  activeTab: 'script',
  modal: { type: null, isOpen: false },
  toasts: [],
  settingsModalOpen: false,
  backstageModalOpen: false,
  backstageActiveTab: 'overview',
  contentStatus: {
    hasNovelContent: false,
    hasScript: false,
    hasStoryboard: false,
    hasAnyContent: false,
  },
  toggleSidebar: () => set((state: UIStore) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  toggleRightPanel: () => set((state: UIStore) => ({ rightPanelVisible: !state.rightPanelVisible })),
  openDirectorPanel: () => set({ rightPanelMode: 'director', rightPanelVisible: true }),
  openNodeEditPanel: (nodeId: string) => set({ rightPanelMode: 'node-edit', rightPanelVisible: true, selectedNodeId: nodeId }),
  closeRightPanel: () => set({ rightPanelMode: 'hidden', rightPanelVisible: false, selectedNodeId: null }),
  setActiveTab: (tab: 'script' | 'storyboard' | 'card') => set({ activeTab: tab }),
  openModal: (type: ModalState['type'], data?: any) => set({ modal: { type, isOpen: true, data } }),
  closeModal: () => set({ modal: { type: null, isOpen: false } }),
  addToast: (toast: Omit<Toast, 'id'>) => set((state: UIStore) => ({
    toasts: [...state.toasts, { ...toast, id: Math.random().toString(36).substr(2, 9) }],
  })),
  removeToast: (id: string) => set((state: UIStore) => ({
    toasts: state.toasts.filter((t: Toast) => t.id !== id),
  })),
  openSettingsModal: () => set({ settingsModalOpen: true }),
  closeSettingsModal: () => set({ settingsModalOpen: false }),
  openBackstageModal: (tab?: string) => set({
    backstageModalOpen: true,
    backstageActiveTab: tab || 'overview'
  }),
  closeBackstageModal: () => set({ backstageModalOpen: false }),
  setBackstageActiveTab: (tab: string) => set({ backstageActiveTab: tab }),
  updateContentStatus: (episode) => set({
    contentStatus: {
      hasNovelContent: !!episode?.novelContent && episode.novelContent.length > 0,
      hasScript: !!episode?.script && episode.script.length > 0,
      hasStoryboard: !!episode?.canvasData?.nodes && episode.canvasData.nodes.length > 0,
      hasAnyContent: !!(episode?.novelContent || episode?.script || episode?.canvasData),
    }
  }),
}));

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  isLoading: false,
  error: null,
  currentEpisodeId: null,
  setCurrentEpisodeId: (id: string | null) => set({ currentEpisodeId: id }),

  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await projectsService.listProjects();
      // response 结构是 { success: true, data: [...], total: ... }
      // 或者直接是 PaginatedResponse

      // 安全获取项目数组
      const apiProjects = response.data || [];

      const projects = apiProjects.map((apiProject: any) => ({
        id: apiProject.id,
        name: apiProject.name,
        coverImage: apiProject.coverImage || undefined,
        description: '',
        type: 'film' as const, // Force type literal
        status: 'draft' as const,
        isTemporary: apiProject.isTemporary || apiProject.is_temporary || false,
        createdAt: new Date(apiProject.createdAt || apiProject.created_at || Date.now()),
        updatedAt: new Date(apiProject.updatedAt || apiProject.updated_at || Date.now()),
        episodes: [],
        characters: [],
        scenes: [],
      }));

      set({ projects, isLoading: false });
    } catch (error) {
      console.error('Fetch projects error:', error);
      set({ error: 'Failed to fetch projects', isLoading: false });
      // 不抛出错误，以免阻塞 UI
    }
  },

  addProject: async (name: string, meta?: any) => {
    set({ isLoading: true });
    try {
      const requestBody: any = { name };
      if (meta && Object.keys(meta).length > 0) {
        requestBody.meta = meta;
      }

      const response = await projectsService.createProject(requestBody);
      const apiProject = response.data as any; // Cast to any to handle flexible fields

      const newProject: Project = {
        id: apiProject.id,
        name: apiProject.name,
        coverImage: apiProject.coverImage || undefined,
        description: '',
        type: 'film',
        status: 'draft',
        isTemporary: apiProject.isTemporary || apiProject.is_temporary || false,
        createdAt: new Date(apiProject.createdAt || apiProject.created_at || Date.now()),
        updatedAt: new Date(apiProject.updatedAt || apiProject.updated_at || Date.now()),
        episodes: [],
        characters: [],
        scenes: [],
      };

      set((state: ProjectStore) => ({
        projects: [newProject, ...state.projects], // 新项目放在最前
        isLoading: false,
      }));
      return newProject;
    } catch (error) {
      set({ error: 'Failed to create project', isLoading: false });
      throw error;
    }
  },

  updateProject: async (id: string, updates: Partial<Project>) => {
    try {
      await projectsService.updateProject(id, {
        name: updates.name,
        cover_image: updates.coverImage,
      });
      set((state: ProjectStore) => ({
        projects: state.projects.map((p: Project) =>
          p.id === id ? { ...p, ...updates, updatedAt: new Date() } : p
        ),
      }));
    } catch (error) {
      set({ error: 'Failed to update project' });
      throw error;
    }
  },

  deleteProject: async (id: string) => {
    try {
      await projectsService.deleteProject(id);
      set((state: ProjectStore) => ({
        projects: state.projects.filter((p: Project) => p.id !== id),
      }));
    } catch (error) {
      set({ error: 'Failed to delete project' });
      throw error;
    }
  },
}));

export const useModelStore = create<ModelStore>((set) => ({
  providers: [],
  categoryRoutes: {
    creative: null,
    content: null,
    quality: null,
    video: null,
    image_process: null,
  },
  isLoading: false,
  error: null,
  addProvider: async (provider: ModelProviderCreate) => {
    set({ isLoading: true });
    try {
      const providerWithDefault = {
        ...provider,
        is_active: provider.is_active ?? true,
      };
      const newProvider = await modelsService.createProvider(providerWithDefault);
      set((state: ModelStore) => ({
        providers: [...state.providers, newProvider as unknown as ModelProvider],
        isLoading: false,
      }));
    } catch (error) {
      set({ error: 'Failed to add provider', isLoading: false });
      throw error;
    }
  },
  updateProvider: async (id: string, updates: ModelProviderUpdate) => {
    try {
      const updatedProvider = await modelsService.updateProvider(id, updates);
      set((state: ModelStore) => ({
        providers: state.providers.map((p) =>
          p.id === id ? (updatedProvider as unknown as ModelProvider) : p
        ),
      }));
    } catch (error) {
      set({ error: 'Failed to update provider' });
      throw error;
    }
  },
  deleteProvider: async (id: string) => {
    try {
      await modelsService.deleteProvider(id);
      set((state: ModelStore) => ({
        providers: state.providers.filter((p) => p.id !== id),
      }));
    } catch (error) {
      set({ error: 'Failed to delete provider' });
      throw error;
    }
  },
  updateCategoryRoute: async (category: TaskCategory, providerId: string, modelId: string) => {
    try {
      const mapping = await modelsService.createMapping(category, providerId, modelId);
      set((state: ModelStore) => ({
        categoryRoutes: {
          ...state.categoryRoutes,
          [category]: {
            id: mapping.id,
            category: mapping.task_type,
            providerId: mapping.provider_id,
            modelId: mapping.model_name,
          },
        },
      }));
      // 保存成功提示
      const { useUIStore } = await import('./useStore');
      const { addToast } = useUIStore.getState();
      addToast?.({ type: 'success', message: '设置已自动保存' });
    } catch (error) {
      set({ error: 'Failed to update route' });
      // 保存失败提示
      const { useUIStore } = await import('./useStore');
      const { addToast } = useUIStore.getState();
      addToast?.({ type: 'error', message: '保存失败，请重试' });
      throw error;
    }
  },
  testProvider: async (providerId: string, modelName: string): Promise<TestResult> => {
    try {
      return await modelsService.testProvider(providerId, modelName);
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : String(error) };
    }
  },
  refreshProviders: async () => {
    set({ isLoading: true });
    try {
      // 同时加载 providers 和 mappings
      const [providers, mappings] = await Promise.all([
        modelsService.listProviders(),
        modelsService.listMappings(),
      ]);

      // 获取 category 到 task_type 的映射关系
      const categoryToTaskType = await modelsService.getCategoryTaskTypeMapping?.() || {
        creative: 'novel_writer',
        content: 'script_formatter',
        quality: 'editor',
        video: 'storyboard_director',
        image_process: 'image_enhancer',
      };

      // 构建 task_type 到 category 的反向映射
      const taskTypeToCategory: Record<string, TaskCategory> = {};
      Object.entries(categoryToTaskType).forEach(([cat, taskType]) => {
        taskTypeToCategory[taskType] = cat as TaskCategory;
      });

      // 从 mappings 构建 categoryRoutes
      const categoryRoutes: Record<TaskCategory, CategoryRoute | null> = {
        creative: null,
        content: null,
        quality: null,
        video: null,
        image_process: null,
      };

      // 使用最新的 mapping（按创建时间倒序，取第一个）
      const sortedMappings = [...mappings].sort((a, b) => {
        const dateA = (a as any).created_at ? new Date((a as any).created_at).getTime() : 0;
        const dateB = (b as any).created_at ? new Date((b as any).created_at).getTime() : 0;
        return dateB - dateA;
      });

      for (const mapping of sortedMappings) {
        const m = mapping as any;
        const category = taskTypeToCategory[m.task_type as string];
        if (category && !categoryRoutes[category]) {
          categoryRoutes[category] = {
            id: m.id,
            category: category,
            providerId: m.provider_id,
            modelId: m.model_name,
          };
        }
      }

      set({
        providers: providers as unknown as ModelProvider[],
        categoryRoutes,
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to refresh providers:', error);
      set({ error: 'Failed to refresh providers', isLoading: false });
    }
  },
}));

export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
}
