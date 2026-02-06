import type { CanvasData } from './shotNode';
import type { components } from './api';

export * from './shotNode';
export * from './canvas';

export type RightPanelMode = 'hidden' | 'director' | 'node-edit';

// 项目类型
export interface Project {
  id: string;
  name: string;
  description: string;
  type: 'film' | 'short' | 'ad' | 'animation';
  status: 'draft' | 'in_progress' | 'completed';
  isTemporary?: boolean;
  coverImage?: string;
  createdAt: Date;
  updatedAt: Date;
  episodes: Episode[];
  characters: Character[];
  scenes: Scene[];
}

// 剧集类型
export interface Episode {
  id: string;
  projectId: string;
  episodeNumber: number;
  title: string;
  summary?: string;
  script?: string;
  novelContent?: string;
  wordCount: number;
  status: 'draft' | 'writing' | 'editing' | 'completed';
  canvasData?: CanvasData;
  scenes?: Scene[];
  createdAt: Date;
  updatedAt: Date;
}

export interface EpisodeCreate {
  title: string;
  summary?: string;
}

export interface EpisodeUpdate {
  title?: string;
  summary?: string;
  scriptText?: string;
  novelContent?: string;
}

// 角色类型
export interface Character {
  id: string;
  projectId: string;
  name: string;
  gender: 'male' | 'female' | 'other';
  description: string;
  referenceImages: string[];
  avatar?: string;
}

// 场景类型
export interface Scene {
  id: string;
  projectId: string;
  name: string;
  description: string;
  referenceImages: string[];
}

export interface SceneCreate {
  projectId: string;
  name: string;
  description?: string;
  referenceImages?: string[];
}

// 用户类型
export interface User {
  id: string;
  name: string;
  avatar?: string;
  balance: number;
}

// 主题类型
export type Theme = 'light' | 'dark';

// 应用状态
export interface AppState {
  theme: Theme;
  user: User | null;
  currentProject: Project | null;
  currentEpisode: Episode | null;
  notifications: Notification[];
}

export interface CanvasState {
  zoom: number;
  offset: { x: number; y: number };
  gridVisible: boolean;
}

export interface CanvasInteractionState {
  isDragging: boolean;
  isPanning: boolean;
  selectedNodeIds: string[];
  clipboardNodes: import('./shotNode').ShotNode[];
  isConnecting: boolean;
  connectionSource: string | null;
  connectionTarget: string | null;
  mousePosition: { x: number; y: number };
}

// 通知类型
export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  createdAt: Date;
}

// 画面风格
export interface ArtStyle {
  id: string;
  name: string;
  sub: string;
  category: string;
}

// 镜头类型
export interface ShotType {
  id: string;
  name: string;
  description: string;
}

// 运镜类型
export interface CameraMove {
  id: string;
  name: string;
  description: string;
}

// 右键菜单项
export interface ContextMenuItem {
  id: string;
  label: string;
  icon?: string;
  shortcut?: string;
  action: () => void;
  disabled?: boolean;
  divider?: boolean;
}

// 弹窗类型
export type ModalType =
  | 'inpaint'
  | 'outpaint'
  | 'virtualCamera'
  | 'videoGen'
  | 'tts'
  | 'music'
  | 'cameraMove'
  | 'confirm'
  | null;

// 弹窗状态
export interface ModalState {
  type: ModalType;
  isOpen: boolean;
  data?: any;
}

// Toast 类型
export interface Toast {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  duration?: number;
}

// 画布右键菜单类型
export type CanvasContextMenuType = 'node' | 'canvas' | 'connection';

// 参考图类型
export type ReferenceImageType = 'sketch' | 'material' | 'threeD';

export type ProviderType = 'llm' | 'video' | 'image';
export type ProtocolType = 'openai' | 'anthropic' | 'gemini' | 'azure';

export interface ModelProvider {
  id: string;
  name: string;
  provider_type: ProviderType;
  protocol: ProtocolType;
  base_url?: string;
  api_key?: string;
  is_active: boolean;
  available_models: string[];
  created_at?: string;
  updated_at?: string;
}

export interface ModelProviderCreate {
  name: string;
  provider_type: ProviderType;
  protocol: ProtocolType;
  base_url?: string;
  api_key: string;
  is_active?: boolean;
}

export interface ModelProviderUpdate {
  name?: string;
  base_url?: string;
  api_key?: string;
  is_active?: boolean;
}

// 从 OpenAPI 生成的类型导入，保持类型统一
export type TaskType = components['schemas']['TaskType'];

export type TaskCategory = 'creative' | 'content' | 'quality' | 'video' | 'image_process';

export interface TaskRoute {
  id: string;
  task: TaskType;
  providerId: string;
  modelId: string;
  parameters?: Record<string, any>;
}

export interface CategoryRoute {
  id: string;
  category: TaskCategory;
  providerId: string;
  modelId: string;
}

export interface TestResult {
  success: boolean;
  response?: string | null;
  error?: string | null;
  latency_ms?: number | null;
}

export const TaskCategoryMapping: Record<TaskCategory, { name: string; description: string; icon: string }> = {
  creative: {
    name: '创意生成',
    description: '创意构思和故事生成',
    icon: 'Cpu'
  },
  content: {
    name: '内容处理',
    description: '文本和内容处理任务',
    icon: 'Server'
  },
  quality: {
    name: '质量提升',
    description: '质量检查和优化',
    icon: 'Settings'
  },
  video: {
    name: '视频生成',
    description: '视频和多媒体生成',
    icon: 'Video'
  },
  image_process: {
    name: '图像处理',
    description: '图像增强、补全、外扩等处理任务',
    icon: 'Image'
  }
};
