/**
 * 项目 API 服务
 * 
 * 项目 CRUD 操作
 */

import { get, post, patch, del, ApiResponse, PaginatedResponse } from './request';
import type { Project } from '@/types';

// 后端返回的项目数据结构（snake_case）
export interface BackendProject {
  id: string;
  user_id: string;
  name: string;
  cover_image: string | null;
  meta: {
    genre?: string;
    sub_tags?: string[];
    tone?: string[];
    target_word_count?: number;
    total_episodes?: number;
    ending_type?: string;
    aspect_ratio?: string;
    drawing_type?: string | null;
    visual_style?: string | null;
    style_dna?: string | null;
    avoid_tags?: string[];
  };
  created_at: string;
  updated_at: string;
  node_count: number;
  episode_count: number;
}

// 创建项目请求
export interface CreateProjectRequest {
  name: string;
  cover_image?: string;
  meta?: {
    genre?: string;
    sub_tags?: string[];
    tone?: string[];
    target_word_count?: number;
    total_episodes?: number;
    ending_type?: string;
    aspect_ratio?: string;
    drawing_type?: string;
    visual_style?: string;
    style_dna?: string;
    avoid_tags?: string[];
  };
}

// 更新项目请求
export interface UpdateProjectRequest {
  name?: string;
  cover_image?: string;
  meta?: CreateProjectRequest['meta'];
}

/**
 * 将后端项目数据转换为前端格式
 */
function convertBackendToFrontend(backendProject: BackendProject): Project {
  return {
    id: backendProject.id,
    name: backendProject.name,
    description: backendProject.meta?.genre || '',  // 用 genre 作为描述
    type: 'film',  // 默认值
    status: 'in_progress',  // 默认值
    coverImage: backendProject.cover_image || `https://picsum.photos/400/225?random=${backendProject.id}`,
    createdAt: new Date(backendProject.created_at),
    updatedAt: new Date(backendProject.updated_at),
    episodes: [],  // 需要单独获取
    characters: [],
    scenes: [],
    // 扩展字段
    nodeCount: backendProject.node_count,
    episodeCount: backendProject.episode_count,
    meta: backendProject.meta,
  };
}

/**
 * 获取项目列表
 */
export async function getProjects(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedResponse<Project>> {
  const response = await get<PaginatedResponse<BackendProject>>('/projects', {
    page,
    page_size: pageSize,
  });
  
  return {
    items: response.data!.items.map(convertBackendToFrontend),
    total: response.data!.total,
    page: response.data!.page,
    page_size: response.data!.page_size,
  };
}

/**
 * 获取单个项目
 */
export async function getProject(projectId: string): Promise<Project> {
  const response = await get<BackendProject>(`/projects/${projectId}`);
  return convertBackendToFrontend(response.data!);
}

export async function createProject(
  prompt: string,
  _fastMode: boolean = false
): Promise<Project> {
  const name = prompt.slice(0, 50) + (prompt.length > 50 ? '...' : '');
  
  const request: CreateProjectRequest = {
    name,
    cover_image: `https://picsum.photos/400/225?random=${Date.now()}`,
    meta: {
      genre: prompt,
      target_word_count: 500,
      total_episodes: 3,
      aspect_ratio: '9:16',
    },
  };
  
  const response = await post<BackendProject>('/projects', request);
  return convertBackendToFrontend(response.data!);
}

/**
 * 更新项目
 */
export async function updateProject(
  projectId: string,
  updates: UpdateProjectRequest
): Promise<Project> {
  const response = await patch<BackendProject>(`/projects/${projectId}`, updates);
  return convertBackendToFrontend(response.data!);
}

/**
 * 删除项目
 */
export async function deleteProject(projectId: string): Promise<void> {
  await del(`/projects/${projectId}`);
}
