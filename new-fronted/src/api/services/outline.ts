/**
 * 大纲 API 服务层
 * 调用后端真实的 skeleton API
 */

import type { OutlineData } from '@/types/outline';

const API_BASE = '/api';

interface GenerateOutlineRequest {
  projectId: string;
  planId: string;
}

interface UpdateNodeRequest {
  nodeId: string;
  title?: string;
  content?: string;
  [key: string]: unknown;
}

export const outlineService = {
  /**
   * 生成大纲
   * POST /api/skeleton/generate
   */
  async generate(request: GenerateOutlineRequest): Promise<{ success: boolean; data?: OutlineData }> {
    try {
      const response = await fetch(`${API_BASE}/skeleton/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectId: request.projectId,
          planId: request.planId,
        }),
      });

      if (!response.ok) {
        console.error('[outlineService] generate failed:', response.status);
        return { success: false };
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('[outlineService] generate error:', error);
      return { success: false };
    }
  },

  /**
   * 获取大纲
   * GET /api/skeleton/{project_id}
   */
  async get(projectId: string): Promise<OutlineData | null> {
    try {
      const response = await fetch(`${API_BASE}/skeleton/${projectId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // 大纲不存在
          return null;
        }
        throw new Error(`Failed to get outline: ${response.status}`);
      }

      const data = await response.json();
      return data as OutlineData;
    } catch (error) {
      console.error('[outlineService] get error:', error);
      return null;
    }
  },

  /**
   * 更新节点
   * PATCH /api/skeleton/{project_id}/nodes/{node_id}
   */
  async updateNode(projectId: string, nodeId: string, updates: UpdateNodeRequest): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/skeleton/${projectId}/nodes/${nodeId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        console.error('[outlineService] updateNode failed:', response.status);
        return false;
      }

      return true;
    } catch (error) {
      console.error('[outlineService] updateNode error:', error);
      return false;
    }
  },

  /**
   * 触发大纲审阅
   * POST /api/skeleton/{project_id}/review
   */
  async review(projectId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/skeleton/${projectId}/review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        console.error('[outlineService] review failed:', response.status);
        return false;
      }

      return true;
    } catch (error) {
      console.error('[outlineService] review error:', error);
      return false;
    }
  },

  /**
   * 确认大纲
   * POST /api/skeleton/{project_id}/confirm
   */
  async confirm(projectId: string): Promise<{ success: boolean }> {
    try {
      const response = await fetch(`${API_BASE}/skeleton/${projectId}/confirm`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        console.error('[outlineService] confirm failed:', response.status);
        return { success: false };
      }

      const data = await response.json();
      return { success: data.success || true };
    } catch (error) {
      console.error('[outlineService] confirm error:', error);
      return { success: false };
    }
  },

  async continueGeneration(projectId: string): Promise<{ success: boolean }> {
    try {
      const response = await fetch(`${API_BASE}/graph/chat?project_id=${projectId}&message=${encodeURIComponent(JSON.stringify({ action: 'continue_skeleton_generation' }))}&user_id=dev-user`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Accept': 'text/event-stream',
        },
      });

      if (!response.ok) {
        console.error('[outlineService] continueGeneration failed:', response.status);
        return { success: false };
      }

      const reader = response.body?.getReader();
      if (!reader) {
        return { success: false };
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'done') {
                return { success: true };
              }
              if (data.type === 'error') {
                console.error('[outlineService] continueGeneration error:', data.message);
                return { success: false };
              }
            } catch {
            }
          }
        }
      }

      return { success: true };
    } catch (error) {
      console.error('[outlineService] continueGeneration error:', error);
      return { success: false };
    }
  },
};

export type { UpdateNodeRequest };
