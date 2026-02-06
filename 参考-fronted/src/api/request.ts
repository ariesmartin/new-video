/**
 * API 请求工具
 * 
 * 封装 fetch API，统一处理请求和响应
 */

import { API_BASE_URL, DEFAULT_HEADERS, REQUEST_TIMEOUT } from './config';

// API 响应格式
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  meta?: {
    page: number;
    page_size: number;
    total: number;
  };
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// API 错误类
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status?: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * 通用请求函数
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // 合并请求头
  const headers = {
    ...DEFAULT_HEADERS,
    ...options.headers,
  };
  
  // 创建 AbortController 用于超时控制
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    // 解析响应
    const data: ApiResponse<T> = await response.json();
    
    // 检查业务错误
    if (!response.ok || !data.success) {
      throw new ApiError(
        data.error?.code || 'UNKNOWN_ERROR',
        data.error?.message || '请求失败',
        response.status
      );
    }
    
    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof ApiError) {
      throw error;
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError('NETWORK_ERROR', '网络连接失败，请检查后端服务是否运行');
    }
    
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('TIMEOUT_ERROR', '请求超时，请稍后重试');
    }
    
    throw new ApiError('UNKNOWN_ERROR', '请求发生未知错误');
  }
}

/**
 * GET 请求
 */
export function get<T>(endpoint: string, params?: Record<string, string | number>) {
  let url = endpoint;
  
  // 构建查询参数
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }
  
  return request<T>(url, { method: 'GET' });
}

/**
 * POST 请求
 */
export function post<T>(endpoint: string, body: unknown) {
  return request<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * PATCH 请求
 */
export function patch<T>(endpoint: string, body: unknown) {
  return request<T>(endpoint, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

/**
 * DELETE 请求
 */
export function del(endpoint: string) {
  return request<void>(endpoint, { method: 'DELETE' });
}
