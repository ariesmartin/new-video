import { client } from '../client';
import type { components } from '@/types/api';

// 使用生成的类型
type ShotResponse = components['schemas']['ShotResponse'];
type ShotCreate = components['schemas']['ShotCreate'];
type ShotUpdate = components['schemas']['ShotUpdate'];
type ShotBatchCreate = components['schemas']['ShotBatchCreate'];
type ShotBatchUpdate = components['schemas']['ShotBatchUpdate'];

/**
 * 分镜服务 - 直接使用 OpenAPI 生成类型
 */
export const shotsService = {
  /**
   * 获取剧集的所有分镜
   */
  async listShots(episodeId: string, sceneId?: string, nodeType?: string) {
    const { data, error } = await client.GET('/api/episodes/{episode_id}/shots', {
      params: {
        path: { episode_id: episodeId },
        query: { 
          scene_id: sceneId,
          node_type: nodeType 
        },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 获取单个分镜详情
   */
  async getShot(episodeId: string, shotId: string) {
    const { data, error } = await client.GET('/api/episodes/{episode_id}/shots/{shot_id}', {
      params: {
        path: { 
          episode_id: episodeId,
          shot_id: shotId 
        },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 创建分镜
   */
  async createShot(episodeId: string, shot: ShotCreate) {
    const { data, error } = await client.POST('/api/episodes/{episode_id}/shots', {
      params: {
        path: { episode_id: episodeId },
      },
      body: shot,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 批量创建分镜
   */
  async batchCreateShots(episodeId: string, batch: ShotBatchCreate) {
    const { data, error } = await client.POST('/api/episodes/{episode_id}/shots/batch', {
      params: {
        path: { episode_id: episodeId },
      },
      body: batch,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 更新分镜
   */
  async updateShot(episodeId: string, shotId: string, updates: ShotUpdate) {
    const { data, error } = await client.PUT('/api/episodes/{episode_id}/shots/{shot_id}', {
      params: {
        path: { 
          episode_id: episodeId,
          shot_id: shotId 
        },
      },
      body: updates,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 批量更新分镜位置
   */
  async batchUpdatePositions(episodeId: string, updates: ShotBatchUpdate) {
    const { data, error } = await client.PUT('/api/episodes/{episode_id}/shots/batch/position', {
      params: {
        path: { episode_id: episodeId },
      },
      body: updates,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 删除分镜
   */
  async deleteShot(episodeId: string, shotId: string) {
    const { error } = await client.DELETE('/api/episodes/{episode_id}/shots/{shot_id}', {
      params: {
        path: { 
          episode_id: episodeId,
          shot_id: shotId 
        },
      },
    });

    if (error) throw error;
  },
};

export type { ShotResponse, ShotCreate, ShotUpdate, ShotBatchCreate, ShotBatchUpdate };
