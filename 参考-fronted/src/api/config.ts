/**
 * API 配置
 * 
 * 后端服务配置
 */

// API 基础 URL
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// 请求超时时间（毫秒）
export const REQUEST_TIMEOUT = 30000;

// 默认请求头
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};
