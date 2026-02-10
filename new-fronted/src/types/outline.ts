/**
 * 大纲数据结构
 */

// 场景
type Scene = {
  sceneId: string;
  sceneNumber: number;
  title: string;
  content?: string;
  shots?: Shot[];
};

// 镜头
type Shot = {
  shotId: string;
  shotNumber: number;
  description?: string;
  dialog?: string;
};

// 剧集/章
type Episode = {
  episodeId: string;
  episodeNumber: number;
  title: string;
  summary?: string;
  scenes: Scene[];
  reviewStatus?: 'pending' | 'passed' | 'warning' | 'error';
  reviewScore?: number;
  isPaidWall?: boolean;
};

// 大纲数据
export interface OutlineData {
  projectId: string;
  episodes: Episode[];
  totalEpisodes: number;
  createdAt: string;
  updatedAt: string;
}

// 大纲节点（用于树形结构）
export interface OutlineNode {
  id: string;
  type: 'episode' | 'scene' | 'shot';
  title: string;
  episodeNumber?: number;
  sceneNumber?: number;
  shotNumber?: number;
  children?: OutlineNode[];
  metadata: {
    reviewScore?: number;
    reviewStatus: 'pending' | 'passed' | 'warning' | 'error';
    wordCount?: number;
    isPaidWall?: boolean;
    lastModified?: string;
  };
}

// 大纲生成请求
export interface GenerateOutlineRequest {
  projectId: string;
  planId: string;
  userInput?: string;
}

// 大纲生成响应
export interface GenerateOutlineResponse {
  success: boolean;
  data?: OutlineData;
  error?: string;
}

// 更新节点请求
export interface UpdateNodeRequest {
  nodeId: string;
  title?: string;
  content?: string;
  metadata?: Partial<OutlineNode['metadata']>;
}

// 确认大纲响应
export interface ConfirmOutlineResponse {
  success: boolean;
  message?: string;
  nextStep?: 'novel_writer';
}
