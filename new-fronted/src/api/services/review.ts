/**
 * 审阅 API 服务层
 * 调用后端真实的审阅 API
 */

import type { GlobalReview, ChapterReview } from '@/types/review';

interface ApplySuggestionRequest {
  projectId: string;
  chapterId: string;
  suggestionId: string;
}

// 后端 API 基础 URL
const API_BASE = '/api';

export const reviewService = {
  /**
   * 获取大纲全局审阅
   * GET /api/skeleton/{project_id}/review
   */
  async getGlobalReview(projectId: string): Promise<GlobalReview | null> {
    try {
      const response = await fetch(`${API_BASE}/skeleton/${projectId}/review`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error(`Failed to get global review: ${response.status}`);
      }

      const data = await response.json();
      return data as GlobalReview;
    } catch (error) {
      console.error('[reviewService] getGlobalReview error:', error);
      return null;
    }
  },

  /**
   * 获取单章审阅
   * GET /api/review/{project_id}/chapters/{chapter_id}
   */
  async getChapterReview(projectId: string, chapterId: string): Promise<ChapterReview | null> {
    try {
      const response = await fetch(`${API_BASE}/review/${projectId}/chapters/${chapterId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to get chapter review: ${response.status}`);
      }

      const data = await response.json();
      return data.review as ChapterReview;
    } catch (error) {
      console.error('[reviewService] getChapterReview error:', error);
      return null;
    }
  },

  /**
   * 触发首次审阅（大纲）
   * POST /api/skeleton/{project_id}/review
   */
  async triggerOutlineReview(projectId: string): Promise<GlobalReview | null> {
    try {
      const response = await fetch(`${API_BASE}/skeleton/${projectId}/review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to trigger review: ${response.status}`);
      }

      const data = await response.json();
      return data.review as GlobalReview;
    } catch (error) {
      console.error('[reviewService] triggerOutlineReview error:', error);
      return null;
    }
  },

  /**
   * 触发重新审阅
   * POST /api/review/{project_id}/re_review
   */
  async reReview(projectId: string, chapterId?: string): Promise<GlobalReview | null> {
    try {
      const response = await fetch(`${API_BASE}/review/${projectId}/re_review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ chapterId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to re-review: ${response.status}`);
      }

      const data = await response.json();
      return data.review as GlobalReview;
    } catch (error) {
      console.error('[reviewService] reReview error:', error);
      return null;
    }
  },

  /**
   * 获取张力曲线
   * GET /api/review/{project_id}/chapters/{chapter_id}/tension
   */
  async getTensionCurve(projectId: string, chapterId?: string): Promise<number[] | null> {
    try {
      const url = chapterId
        ? `${API_BASE}/review/${projectId}/chapters/${chapterId}/tension`
        : `${API_BASE}/review/${projectId}/tension`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return data.tensionCurve || null;
    } catch (error) {
      console.error('[reviewService] getTensionCurve error:', error);
      return null;
    }
  },

  /**
   * 应用建议
   * POST /api/review/{project_id}/chapters/{chapter_id}/suggestions/{suggestion_id}/apply
   */
  async applySuggestion(request: ApplySuggestionRequest): Promise<boolean> {
    try {
      const { projectId, chapterId, suggestionId } = request;
      const response = await fetch(
        `${API_BASE}/review/${projectId}/chapters/${chapterId}/suggestions/${suggestionId}/apply`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to apply suggestion: ${response.status}`);
      }

      return true;
    } catch (error) {
      console.error('[reviewService] applySuggestion error:', error);
      return false;
    }
  },

  /**
   * 忽略问题
   * POST /api/review/{project_id}/chapters/{chapter_id}/issues/{issue_id}/ignore
   */
  async ignoreIssue(projectId: string, chapterId: string, issueId: string): Promise<boolean> {
    try {
      const response = await fetch(
        `${API_BASE}/review/${projectId}/chapters/${chapterId}/issues/${issueId}/ignore`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to ignore issue: ${response.status}`);
      }

      return true;
    } catch (error) {
      console.error('[reviewService] ignoreIssue error:', error);
      return false;
    }
  },
};
