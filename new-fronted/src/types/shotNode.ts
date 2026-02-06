export type ShotNodeType = 'shot' | 'scene_master';

export type NodeStatus = 'pending' | 'processing' | 'completed' | 'approved' | 'revision';

export const statusColors: Record<NodeStatus, string> = {
  pending: '#94a3b8',   // slate-400
  processing: '#3b82f6', // blue-500
  completed: '#22c55e',  // green-500
  approved: '#10b981',   // emerald-500
  revision: '#f59e0b',   // amber-500
};

export interface ShotDetails {
  dialogue?: string;
  sound?: string;
  cameraMove?: string;
  description?: string;
  prompt?: string;
  negativePrompt?: string;
  resolution?: string;
  aspectRatio?: string;
  style?: string;
  referenceImages?: {
    sketch?: string;
    material?: string;
    threeD?: string;
  };
  generationParams?: Record<string, any>;
}

export interface ShotConnection {
  id: string;
  source: string;
  target: string;
  type: 'sequence' | 'reference';
}

export interface ShotNode {
  shotId: string;
  episodeId: string;
  sceneId?: string;
  nodeType: ShotNodeType;
  shotNumber: number;
  title: string;
  subtitle?: string;
  thumbnailUrl?: string;
  imageUrl?: string;
  status: NodeStatus;
  position: { x: number; y: number };
  details?: ShotDetails;
}

export interface CanvasData {
  episodeId: string;
  viewport: { x: number; y: number; zoom: number };
  nodes: ShotNode[];
  connections: ShotConnection[];
}

export interface ShotCreate {
  episodeId: string;
  sceneId?: string;
  nodeType: ShotNodeType;
  shotNumber: number;
  title: string;
  subtitle?: string;
  position: { x: number; y: number };
  details?: ShotDetails;
}

export interface ShotUpdate {
  title?: string;
  subtitle?: string;
  status?: NodeStatus;
  position?: { x: number; y: number };
  thumbnailUrl?: string;
  imageUrl?: string;
  details?: ShotDetails;
}

export interface ShotPositionUpdate {
  id: string;
  position: { x: number; y: number };
}

export type CanvasSaveRequest = Omit<CanvasData, 'episodeId'>;
