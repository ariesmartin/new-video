import { client } from '../client';
import type { components } from '@/types/api';

type ModelProviderCreate = components['schemas']['ModelProviderCreate'];
type ModelProviderUpdate = components['schemas']['ModelProviderUpdate'];
type ModelTestRequest = components['schemas']['ModelTestRequest'];
type ModelTestResponse = components['schemas']['ModelTestResponse'];
type ModelMappingCreate = components['schemas']['ModelMappingCreate'];
type ModelMappingUpdate = components['schemas']['ModelMappingUpdate'];

interface ProviderResponseData {
  providerId: string;
  name: string;
  type: string;
  status: string;
  [key: string]: unknown;
}

interface MappingResponseData {
  mappingId: string;
  taskType: string;
  providerId: string;
  modelId: string;
  id?: string;
  task_type?: string;
  provider_id?: string;
  model_name?: string;
  created_at?: string;
  [key: string]: unknown;
}

// TaskCategory 到 TaskType 的映射（从后端动态获取）
type CategoryToTaskTypeMapping = Record<string, string>;

let cachedMapping: CategoryToTaskTypeMapping | null = null;

// 获取映射关系
async function fetchCategoryMapping(): Promise<CategoryToTaskTypeMapping> {
  if (cachedMapping) {
    return cachedMapping;
  }

  const { data, error } = await client.GET('/api/models/category-task-type-mapping');

  if (error) {
    console.error('Failed to fetch category mapping:', error);
    // 返回默认映射
    return {
      creative: 'novel_writer',
      content: 'script_formatter',
      quality: 'editor',
      video: 'storyboard_director',
      image_process: 'image_enhancer',
    };
  }

  cachedMapping = data?.data || {};
  return cachedMapping;
}

// 获取错误信息
function getErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null) {
    const err = error as { detail?: Array<{ msg: string }>; msg?: string; message?: string };
    if (err.detail && err.detail.length > 0) {
      return err.detail[0].msg;
    }
    if (err.msg) return err.msg;
    if (err.message) return err.message;
  }
  return 'Request failed';
}

export const modelsService = {
  // ===== Providers =====
  
  async listProviders(): Promise<ProviderResponseData[]> {
    const { data, error } = await client.GET('/api/models/providers');
    
    if (error) throw new Error(getErrorMessage(error));
    
    return (data?.data || []) as unknown as ProviderResponseData[];
  },

  async createProvider(provider: ModelProviderCreate & { is_active?: boolean }): Promise<ProviderResponseData> {
    const providerWithDefaults = {
      ...provider,
      is_active: provider.is_active ?? true,
    };
    
    const { data, error } = await client.POST('/api/models/providers', {
      body: providerWithDefaults as any,
    });

    if (error) throw new Error(getErrorMessage(error));
    if (!data?.data) throw new Error('No data returned');
    
    return data.data as unknown as ProviderResponseData;
  },

  async updateProvider(id: string, updates: ModelProviderUpdate): Promise<ProviderResponseData> {
    const { data, error } = await client.PATCH('/api/models/providers/{provider_id}', {
      params: { 
        path: { provider_id: id }, 
      },
      body: updates,
    });

    if (error) throw new Error(getErrorMessage(error));
    if (!data?.data) throw new Error('No data returned');
    
    return data.data as unknown as ProviderResponseData;
  },

  async deleteProvider(id: string): Promise<void> {
    const { error } = await client.DELETE('/api/models/providers/{provider_id}', {
      params: { 
        path: { provider_id: id }, 
      },
    });

    if (error) throw new Error(getErrorMessage(error));
  },

  async testProvider(providerId: string, modelName: string): Promise<ModelTestResponse> {
    const testRequest: ModelTestRequest = {
      provider_id: providerId,
      model_name: modelName,
      prompt: 'Hello, this is a test message. Please respond with "Test successful".',
    };
    
    const { data, error } = await client.POST('/api/models/providers/test', {
      body: testRequest,
    });

    if (error) throw new Error(getErrorMessage(error));
    if (!data) throw new Error('No data returned');
    
    return data;
  },

  async refreshProviderModels(providerId: string): Promise<string[]> {
    const { data, error } = await client.POST('/api/models/providers/{provider_id}/refresh', {
      params: { 
        path: { provider_id: providerId }, 
      },
    });

    if (error) throw new Error(getErrorMessage(error));
    
    return data?.data || [];
  },

  // ===== Mappings =====

  async listMappings(projectId?: string): Promise<MappingResponseData[]> {
    const { data, error } = await client.GET('/api/models/mappings', {
      params: projectId ? { query: { project_id: projectId } } : undefined,
    });
    
    if (error) throw new Error(getErrorMessage(error));
    
    return (data?.data || []) as unknown as MappingResponseData[];
  },

  async createMapping(
    category: string,
    providerId: string,
    modelId: string,
    projectId?: string
  ): Promise<MappingResponseData> {
    const mapping = await fetchCategoryMapping();
    const taskType = mapping[category] || 'editor'; // 默认 fallback

    const mappingData: ModelMappingCreate = {
      task_type: taskType as any,
      provider_id: providerId,
      model_name: modelId,
      project_id: projectId,
    };

    const { data, error } = await client.POST('/api/models/mappings', {
      body: mappingData,
    });

    if (error) throw new Error(getErrorMessage(error));
    if (!data?.data) throw new Error('No data returned');

    return data.data as unknown as MappingResponseData;
  },

  async updateMapping(
    mappingId: string, 
    providerId: string, 
    modelId: string
  ): Promise<MappingResponseData> {
    const updateData: ModelMappingUpdate = {
      provider_id: providerId,
      model_name: modelId,
    };
    
    const { data, error } = await client.PATCH('/api/models/mappings/{mapping_id}', {
      params: { 
        path: { mapping_id: mappingId }, 
      },
      body: updateData,
    });

    if (error) throw new Error(getErrorMessage(error));
    if (!data?.data) throw new Error('No data returned');
    
    return data.data as unknown as MappingResponseData;
  },

  async deleteMapping(mappingId: string): Promise<void> {
    const { error } = await client.DELETE('/api/models/mappings/{mapping_id}', {
      params: { 
        path: { mapping_id: mappingId }, 
      },
    });

    if (error) throw new Error(getErrorMessage(error));
  },

  // ===== Task Types =====

  async listTaskTypes(): Promise<Array<{ value: string; label: string }>> {
    const { data, error } = await client.GET('/api/models/task-types');
    
    if (error) throw new Error(getErrorMessage(error));
    
    const result = data?.data || [];
    return result.map((item: { value?: string; label?: string }) => ({
      value: item.value || '',
      label: item.label || '',
    }));
  },

  // 获取 category 到 task_type 的映射
  async getCategoryTaskTypeMapping(): Promise<CategoryToTaskTypeMapping> {
    return await fetchCategoryMapping();
  },
};
