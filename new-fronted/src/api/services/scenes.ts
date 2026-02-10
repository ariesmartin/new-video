import { client } from '../client';
import type { components } from '@/types/api';

// 使用生成的类型
type SceneResponse = components['schemas']['SceneResponse'];
type SceneCreate = components['schemas']['SceneCreate'];
type SceneUpdate = components['schemas']['SceneUpdate'];

/**
 * 场景服务 - 直接使用 OpenAPI 生成类型
 */
export const scenesService = {
  /**
   * 获取剧集的所有场景
   */
  async listScenes(episodeId: string) {
    const { data, error } = await client.GET('/api/episodes/{episode_id}/scenes', {
      params: {
        path: { episode_id: episodeId },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 获取单个场景详情
   */
  async getScene(episodeId: string, sceneId: string) {
    const { data, error } = await client.GET('/api/episodes/{episode_id}/scenes/{scene_id}', {
      params: {
        path: { 
          episode_id: episodeId,
          scene_id: sceneId 
        },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 创建场景
   */
  async createScene(episodeId: string, scene: SceneCreate) {
    const { data, error } = await client.POST('/api/episodes/{episode_id}/scenes', {
      params: {
        path: { episode_id: episodeId },
      },
      body: scene,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 更新场景
   */
  async updateScene(episodeId: string, sceneId: string, updates: SceneUpdate) {
    const { data, error } = await client.PATCH('/api/episodes/{episode_id}/scenes/{scene_id}', {
      params: {
        path: { 
          episode_id: episodeId,
          scene_id: sceneId 
        },
      },
      body: updates,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 删除场景
   */
  async deleteScene(episodeId: string, sceneId: string) {
    const { error } = await client.DELETE('/api/episodes/{episode_id}/scenes/{scene_id}', {
      params: {
        path: { 
          episode_id: episodeId,
          scene_id: sceneId 
        },
      },
    });

    if (error) throw error;
  },
};

export type { SceneResponse, SceneCreate, SceneUpdate };
