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

export interface StorySettingSection {
  markdown: string;
  parsed: Record<string, string>;
}

// 故事设定
export interface StorySettings {
  metadata?: StorySettingSection;
  coreSetting?: StorySettingSection;
  characters?: Array<{
    name: string;
    description: string;
    markdown: string;
  }>;
  plotArchitecture?: StorySettingSection;
  adaptationMapping?: StorySettingSection;
  writingGuidelines?: StorySettingSection;
  paywallDesign?: StorySettingSection;
  tensionCurve?: {
    markdown: string;
    parsed: any[];
    dataPoints: Array<{ chapter: number; tension: number }>;
  };
}

// 大纲数据
export interface OutlineData {
  projectId: string;
  episodes: Episode[];
  totalEpisodes: number;
  createdAt: string;
  updatedAt: string;
  content?: string;
  storySettings?: StorySettings;
  metadata?: {
    chapter_map?: Array<{ chapter: number; episodes: string }>;
    paywall_info?: { chapter?: number; episode?: number };
    source?: string;
    total_batches?: number;
    current_batch?: number;
    needs_next_batch?: boolean;
    skeleton_content?: string;
    story_settings?: StorySettings;
    [key: string]: any;
  };
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
    content?: string;   // 场景内容/剧集摘要
    summary?: string;   // 剧集摘要
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
