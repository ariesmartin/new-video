/**
 * 小说 API 服务层
 * 后端 novel_writer_graph 尚未构建，使用模拟实现
 */

import type {
  Chapter,
  SaveChapterRequest,
  SaveChapterResponse,
  ListChaptersResponse,
  GenerateNextChapterRequest,
  GenerationProgress,
} from '@/types/novel';

export const novelService = {
  async listChapters(_projectId: string): Promise<ListChaptersResponse | null> {
    console.warn('[novelService] 后端尚未构建，返回模拟数据');
    return {
      chapters: [],
      total: 0,
      totalWordCount: 0,
    };
  },

  async getChapter(_projectId: string, _chapterId: string): Promise<Chapter | null> {
    console.warn('[novelService] 后端尚未构建，返回 null');
    return null;
  },

  async saveChapter(
    _projectId: string,
    _chapterId: string,
    _request: SaveChapterRequest
  ): Promise<SaveChapterResponse> {
    console.warn('[novelService] 后端尚未构建，返回模拟响应');
    return { success: true };
  },

  async getChapterReview(_projectId: string, _chapterId: string) {
    console.warn('[novelService] 后端尚未构建，返回 null');
    return null;
  },

  async applySuggestion(
    _projectId: string,
    _chapterId: string,
    _suggestionId: string
  ): Promise<boolean> {
    console.warn('[novelService] 后端尚未构建，返回 true');
    return true;
  },

  async generateNextChapter(_request: GenerateNextChapterRequest): Promise<{ success: boolean; chapterId?: string; error?: string }> {
    console.warn('[novelService] 后端尚未构建，返回模拟响应');
    return { success: false, error: '后端尚未构建' };
  },

  streamGeneration(
    _projectId: string,
    callbacks: {
      onProgress?: (progress: GenerationProgress) => void;
      onComplete?: (chapter: Chapter) => void;
      onError?: (error: string) => void;
    }
  ): () => void {
    console.warn('[novelService] 后端尚未构建，流式生成不可用');
    callbacks.onError?.('后端尚未构建');
    return () => {};
  },
};
