import { client } from '../client';
import type { components } from '@/types/api';

// 使用生成的类型
type AssetResponseData = components['schemas']['AssetResponseData'];
type AssetListResponse = components['schemas']['PaginatedResponse_AssetResponseData_'];

interface AssetCreate {
  name: string;
  asset_type: 'character' | 'location' | 'prop';
  description?: string;
  image_url?: string;
  project_id?: string;
  [key: string]: unknown;
}

interface AssetUpdate {
  name?: string;
  description?: string;
  image_url?: string;
  [key: string]: unknown;
}

/**
 * 资产服务 - 角色、场景、道具等视觉资产
 */
export const assetsService = {
  /**
   * 获取项目的资产列表
   * @param projectId 项目 ID
   * @param assetType 资产类型过滤
   * @param page 页码
   * @param pageSize 每页数量
   */
  async listAssets(
    projectId: string,
    assetType?: 'character' | 'location' | 'prop',
    page = 1,
    pageSize = 100
  ) {
    const { data, error } = await client.GET('/api/projects/{project_id}/assets', {
      params: {
        path: { project_id: projectId },
        query: {
          asset_type: assetType,
          page,
          page_size: pageSize,
        },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 获取单个资产详情
   */
  async getAsset(assetId: string) {
    const { data, error } = await client.GET('/api/projects/assets/{asset_id}', {
      params: {
        path: { asset_id: assetId },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 创建资产
   */
  async createAsset(projectId: string, asset: AssetCreate) {
    const { data, error } = await client.POST('/api/projects/{project_id}/assets', {
      params: {
        path: { project_id: projectId },
      },
      body: asset,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 更新资产
   */
  async updateAsset(assetId: string, updates: AssetUpdate) {
    const { data, error } = await client.PATCH('/api/projects/assets/{asset_id}', {
      params: {
        path: { asset_id: assetId },
      },
      body: updates,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 删除资产
   */
  async deleteAsset(assetId: string) {
    const { error } = await client.DELETE('/api/projects/assets/{asset_id}', {
      params: {
        path: { asset_id: assetId },
      },
    });

    if (error) throw error;
  },

  /**
   * 从内容中提取资产
   */
  async extractAssets(projectId: string, content: string, contentType: 'novel' | 'script' | 'outline') {
    const { data, error } = await client.POST('/api/projects/{project_id}/assets/extract', {
      params: {
        path: { project_id: projectId },
      },
      body: {
        content,
        content_type: contentType,
      },
    });

    if (error) throw error;
    return data!;
  },
};

export type { AssetResponseData, AssetListResponse, AssetCreate, AssetUpdate };
