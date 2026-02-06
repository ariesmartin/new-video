// 项目类型
export interface Project {
  id: string;
  name: string;
  description: string;
  type: 'film' | 'short' | 'ad' | 'animation';
  status: 'draft' | 'in_progress' | 'completed';
  coverImage?: string;
  createdAt: Date;
  updatedAt: Date;
  episodes: Episode[];
  characters: Character[];
  scenes: Scene[];
  // 后端扩展字段
  nodeCount?: number;
  episodeCount?: number;
  meta?: {
    genre?: string;
    sub_tags?: string[];
    tone?: string[];
    target_word_count?: number;
    total_episodes?: number;
    ending_type?: string;
    aspect_ratio?: string;
    drawing_type?: string;
    visual_style?: string;
    style_dna?: string;
    avoid_tags?: string[];
  };
}

// 剧集类型
export interface Episode {
  id: string;
  projectId: string;
  title: string;
  order: number;
  script: string;
  story: string;
  wordCount: number;
  estimatedDuration: string;
  storyboard?: Storyboard;
  createdAt: Date;
  updatedAt: Date;
}

// 分镜类型
export interface Storyboard {
  id: string;
  episodeId: string;
  cards: Card[];
  canvasState: CanvasState;
}

// 连线类型
export interface Connection {
  id: string;
  source: string;
  target: string;
  type?: 'default' | 'reference';
}

// 卡片类型
export interface Card {
  id: string;
  type: 'shot' | 'scene_master' | 'reference';
  number: number;
  title: string;
  subtitle?: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  imageUrl?: string;
  thumbnailUrl?: string;
  status: 'pending' | 'processing' | 'completed' | 'approved' | 'revision';
  content: CardContent;
  params: GenerationParams;
  links: CardLinks;
  // 参考图
  referenceImages?: {
    sketch?: string;
    material?: string;
    threeD?: string;
  };
}

// 卡片内容
export interface CardContent {
  dialogue?: string;
  sound?: string;
  visualPrompt?: string;
  shotType?: string;
  cameraMove?: string;
  description?: string;
}

// 生成参数
export interface GenerationParams {
  resolution: '2K' | '4K';
  aspectRatio: '16:9' | '9:16' | '1:1' | '4:3';
  style: string;
  referenceImages?: string[];
}

// 卡片链接
export interface CardLinks {
  parent?: string;
  children: string[];
  references: string[];
}

// 画布状态
export interface CanvasState {
  zoom: number;
  offset: { x: number; y: number };
  gridVisible: boolean;
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

// 画布交互状态
export interface CanvasInteractionState {
  isDragging: boolean;
  isPanning: boolean;
  selectedCards: string[];
  clipboard: Card[];
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
export type CanvasContextMenuType = 'card' | 'canvas' | 'connection';

// 参考图类型
export type ReferenceImageType = 'sketch' | 'material' | 'threeD';
