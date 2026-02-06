import { client } from '../client';
import type { components } from '@/types/api';

// 使用生成的类型
type ProjectResponse = components['schemas']['ProjectResponse'];
type ProjectCreate = components['schemas']['ProjectCreate'];
type ProjectUpdate = components['schemas']['ProjectUpdate'];

/**
 * 项目服务 - 直接使用 OpenAPI 生成类型
 * 后端已配置 camelCase alias，无需手动转换
 */
export const projectsService = {
  /**
   * 获取项目列表
   */
  async listProjects(page = 1, pageSize = 20) {
    const { data, error } = await client.GET('/api/projects', {
      params: {
        query: { page, page_size: pageSize },
      },
    });

    if (error) throw error;
    // 直接返回 data，它是 PaginatedResponse 结构，包含 data (数组) 和分页信息
    return data!;
  },

  /**
   * 获取单个项目
   */
  async getProject(projectId: string) {
    const { data, error } = await client.GET('/api/projects/{project_id}', {
      params: {
        path: { project_id: projectId },
      },
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 创建项目
   */
  async createProject(project: ProjectCreate) {
    console.log('[createProject] 发送请求体:', project);
    console.log('[createProject] 请求体类型:', typeof project);

    const { data, error } = await client.POST('/api/projects', {
      body: project,
    });

    console.log('[createProject] 响应:', { data, error });

    if (error) throw error;
    return data!;
  },

  /**
   * 更新项目
   */
  async updateProject(projectId: string, updates: ProjectUpdate) {
    const { data, error } = await client.PATCH('/api/projects/{project_id}', {
      params: {
        path: { project_id: projectId },
      },
      body: updates,
    });

    if (error) throw error;
    return data!;
  },

  /**
   * 删除项目
   */
  async deleteProject(projectId: string) {
    const { error } = await client.DELETE('/api/projects/{project_id}', {
      params: {
        path: { project_id: projectId },
      },
    });

    if (error) throw error;
  },
  /**
   * 创建临时项目
   * 调用后端原生接口，支持自动清理
   */
  async createTempProject() {
    const { data, error } = await client.POST('/api/projects/temp');
    if (error) throw error;
    return data!;
  },

  /**
   * 将临时项目转正
   */
  async saveTempProject(projectId: string, updates: ProjectUpdate) {
    const { data, error } = await client.POST('/api/projects/{project_id}/save', {
      params: {
        path: { project_id: projectId },
      },
      body: updates,
    });

    if (error) throw error;
    return data!;
  },
};

export type { ProjectResponse, ProjectCreate, ProjectUpdate };
