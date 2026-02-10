/**
 * 小说数据结构
 */

// 章节
export interface Chapter {
  chapterId: string;
  projectId: string;
  episodeId?: string;
  chapterNumber: number;
  title: string;
  content: string;
  wordCount: number;
  sceneCount: number;
  dialogueCount: number;
  status: 'draft' | 'reviewing' | 'completed';
  reviewScore?: number;
  reviewStatus?: 'pending' | 'passed' | 'warning' | 'error';
  createdAt: string;
  updatedAt: string;
}

// 小说内容格式
export interface NovelContent {
  html: string;
  json: any;
  markdown: string;
  plainText: string;
}

// 保存章节请求
export interface SaveChapterRequest {
  content: string;
  title?: string;
  autoReview?: boolean;
}

// 保存章节响应
export interface SaveChapterResponse {
  success: boolean;
  data?: {
    chapter: Chapter;
    review?: import('./review').ChapterReview;
  };
  error?: string;
}

// 章节列表响应
export interface ListChaptersResponse {
  chapters: Chapter[];
  total: number;
  totalWordCount: number;
}

// 生成下一章请求
export interface GenerateNextChapterRequest {
  projectId: string;
  previousChapterId?: string;
}

// 生成进度
export interface GenerationProgress {
  status: 'pending' | 'generating' | 'reviewing' | 'completed' | 'error';
  progress: number;  // 0-100
  currentAgent?: string;
  message?: string;
}
