import { client } from '../client';
import type { components } from '@/types/api';

// 使用生成的类型
type EpisodeResponse = components['schemas']['EpisodeResponse'];
type EpisodeListResponse = components['schemas']['EpisodeListResponse'];
type EpisodeCreate = components['schemas']['EpisodeCreate'];
type EpisodeUpdate = components['schemas']['EpisodeUpdate'];

/**
 * 剧集服务 - 直接使用 OpenAPI 生成类型
 */
export const episodesService = {
  /**
   * 获取项目的所有剧集
   */
  async listEpisodes(projectId: string) {
    const { data, error } = await client.GET('/api/projects/{project_id}/episodes', {
      params: {
        path: { project_id: projectId },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 获取单个剧集详情
   */
  async getEpisode(projectId: string, episodeId: string) {
    const { data, error } = await client.GET('/api/projects/{project_id}/episodes/{episode_id}', {
      params: {
        path: { 
          project_id: projectId,
          episode_id: episodeId 
        },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 创建剧集
   */
  async createEpisode(projectId: string, episode: EpisodeCreate) {
    const { data, error } = await client.POST('/api/projects/{project_id}/episodes', {
      params: {
        path: { project_id: projectId },
      },
      body: episode,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 更新剧集
   */
  async updateEpisode(projectId: string, episodeId: string, updates: EpisodeUpdate) {
    const { data, error } = await client.PATCH('/api/projects/{project_id}/episodes/{episode_id}', {
      params: {
        path: { 
          project_id: projectId,
          episode_id: episodeId 
        },
      },
      body: updates,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 删除剧集
   */
  async deleteEpisode(projectId: string, episodeId: string) {
    const { error } = await client.DELETE('/api/projects/{project_id}/episodes/{episode_id}', {
      params: {
        path: { 
          project_id: projectId,
          episode_id: episodeId 
        },
      },
    });

    if (error) throw error;
  },
};

export type { EpisodeResponse, EpisodeListResponse, EpisodeCreate, EpisodeUpdate };
