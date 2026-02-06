import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { 
  AppState, 
  CanvasState, 
  CanvasInteractionState, 
  ModalState, 
  Toast,
  Project,
  Episode,
  Card,
  Theme,
  Connection
} from '@/types';

// 应用状态 Store 类型
interface AppStore extends AppState {
  setTheme: (theme: Theme) => void;
  setUser: (user: AppState['user']) => void;
  setCurrentProject: (project: Project | null) => void;
  setCurrentEpisode: (episode: Episode | null) => void;
  addNotification: (notification: AppState['notifications'][0]) => void;
  removeNotification: (id: string) => void;
}

// 画布状态 Store 类型
interface CanvasStore extends CanvasState, CanvasInteractionState {
  setZoom: (zoom: number) => void;
  setOffset: (offset: { x: number; y: number }) => void;
  resetView: () => void;
  toggleGrid: () => void;
  selectCard: (cardId: string, multi?: boolean) => void;
  deselectAll: () => void;
  setIsDragging: (isDragging: boolean) => void;
  setIsPanning: (isPanning: boolean) => void;
  setClipboard: (cards: Card[]) => void;
  startConnection: (cardId: string) => void;
  endConnection: () => void;
  setConnectionTarget: (cardId: string | null) => void;
  setMousePosition: (pos: { x: number; y: number }) => void;
}

// UI 状态 Store 类型
interface UIStore {
  sidebarCollapsed: boolean;
  rightPanelVisible: boolean;
  activeTab: 'script' | 'storyboard' | 'card';
  modal: ModalState;
  toasts: Toast[];
  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  setActiveTab: (tab: 'script' | 'storyboard' | 'card') => void;
  openModal: (type: ModalState['type'], data?: any) => void;
  closeModal: () => void;
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

// 项目数据 Store 类型
interface ProjectStore {
  projects: Project[];
  cards: Card[];
  connections: Connection[];
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  deleteProject: (id: string) => void;
  addCard: (card: Card) => void;
  updateCard: (id: string, updates: Partial<Card>) => void;
  deleteCard: (id: string) => void;
  moveCard: (id: string, position: { x: number; y: number }) => void;
  addConnection: (connection: Connection) => void;
  deleteConnection: (id: string) => void;
  duplicateCard: (id: string) => void;
}

// 应用状态 Store
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
      partialize: (state: AppStore) => ({ theme: state.theme, user: state.user }),
    }
  )
);

// 画布状态 Store
export const useCanvasStore = create<CanvasStore>((set, get) => ({
  // CanvasState
  zoom: 1,
  offset: { x: 0, y: 0 },
  gridVisible: true,
  
  // CanvasInteractionState
  isDragging: false,
  isPanning: false,
  selectedCards: [],
  clipboard: [],
  isConnecting: false,
  connectionSource: null,
  connectionTarget: null,
  mousePosition: { x: 0, y: 0 },
  
  setZoom: (zoom: number) => set({ zoom: Math.max(0.1, Math.min(5, zoom)) }),
  setOffset: (offset: { x: number; y: number }) => set({ offset }),
  resetView: () => set({ zoom: 1, offset: { x: 0, y: 0 } }),
  toggleGrid: () => set((state: CanvasStore) => ({ gridVisible: !state.gridVisible })),
  
  selectCard: (cardId: string, multi = false) => set((state: CanvasStore) => {
    if (multi) {
      const exists = state.selectedCards.includes(cardId);
      if (exists) {
        return { selectedCards: state.selectedCards.filter((id: string) => id !== cardId) };
      }
      return { selectedCards: [...state.selectedCards, cardId] };
    }
    return { selectedCards: [cardId] };
  }),
  
  deselectAll: () => set({ selectedCards: [] }),
  setIsDragging: (isDragging: boolean) => set({ isDragging }),
  setIsPanning: (isPanning: boolean) => set({ isPanning }),
  setClipboard: (clipboard: Card[]) => set({ clipboard }),
  
  startConnection: (cardId: string) => set({ isConnecting: true, connectionSource: cardId, connectionTarget: null }),
  endConnection: () => {
    const state = get();
    if (state.connectionSource && state.connectionTarget && state.connectionSource !== state.connectionTarget) {
      // Connection will be created by the project store
    }
    set({ isConnecting: false, connectionSource: null, connectionTarget: null });
  },
  setConnectionTarget: (cardId: string | null) => set({ connectionTarget: cardId }),
  setMousePosition: (pos: { x: number; y: number }) => set({ mousePosition: pos }),
}));

// UI 状态 Store
export const useUIStore = create<UIStore>((set) => ({
  sidebarCollapsed: false,
  rightPanelVisible: true,
  activeTab: 'script',
  modal: { type: null, isOpen: false },
  toasts: [],
  
  toggleSidebar: () => set((state: UIStore) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  toggleRightPanel: () => set((state: UIStore) => ({ rightPanelVisible: !state.rightPanelVisible })),
  setActiveTab: (tab: 'script' | 'storyboard' | 'card') => set({ activeTab: tab }),
  
  openModal: (type: ModalState['type'], data?: any) => set({ modal: { type, isOpen: true, data } }),
  closeModal: () => set({ modal: { type: null, isOpen: false } }),
  
  addToast: (toast: Omit<Toast, 'id'>) => set((state: UIStore) => ({
    toasts: [...state.toasts, { ...toast, id: Math.random().toString(36).substr(2, 9) }],
  })),
  
  removeToast: (id: string) => set((state: UIStore) => ({
    toasts: state.toasts.filter((t: Toast) => t.id !== id),
  })),
}));

// 项目数据 Store
export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  cards: [],
  connections: [],
  
  addProject: (project: Project) => set((state: ProjectStore) => ({ 
    projects: [...state.projects, project] 
  })),
  
  updateProject: (id: string, updates: Partial<Project>) => set((state: ProjectStore) => ({
    projects: state.projects.map((p: Project) => 
      p.id === id ? { ...p, ...updates } : p
    ),
  })),
  
  deleteProject: (id: string) => set((state: ProjectStore) => ({
    projects: state.projects.filter((p: Project) => p.id !== id),
  })),
  
  addCard: (card: Card) => set((state: ProjectStore) => ({ 
    cards: [...state.cards, card] 
  })),
  
  updateCard: (id: string, updates: Partial<Card>) => set((state: ProjectStore) => ({
    cards: state.cards.map((c: Card) => 
      c.id === id ? { ...c, ...updates } : c
    ),
  })),
  
  deleteCard: (id: string) => set((state: ProjectStore) => ({
    cards: state.cards.filter((c: Card) => c.id !== id),
    connections: state.connections.filter((conn: Connection) => 
      conn.source !== id && conn.target !== id
    ),
  })),
  
  moveCard: (id: string, position: { x: number; y: number }) => set((state: ProjectStore) => ({
    cards: state.cards.map((c: Card) => 
      c.id === id ? { ...c, position } : c
    ),
  })),
  
  addConnection: (connection: Connection) => set((state: ProjectStore) => {
    // Check if connection already exists
    const exists = state.connections.some(
      (c: Connection) => c.source === connection.source && c.target === connection.target
    );
    if (exists) return state;
    return { connections: [...state.connections, connection] };
  }),
  
  deleteConnection: (id: string) => set((state: ProjectStore) => ({
    connections: state.connections.filter((c: Connection) => c.id !== id),
  })),
  
  duplicateCard: (id: string) => set((state: ProjectStore) => {
    const card = state.cards.find((c: Card) => c.id === id);
    if (!card) return state;
    const newCard: Card = {
      ...card,
      id: `card_${Date.now()}`,
      number: state.cards.length + 1,
      position: { x: card.position.x + 50, y: card.position.y + 50 },
    };
    return { cards: [...state.cards, newCard] };
  }),
}));
