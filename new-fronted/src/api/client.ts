import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from '../types/api';

// 获取环境变量或使用代理路径
// 注意：API 类型中已包含 /api 前缀，所以 baseUrl 应该只是域名或 /
const baseUrl = import.meta.env.VITE_API_URL || '';

export const client = createClient<paths>({
  baseUrl,
});

const urlCleanupMiddleware: Middleware = {
  async onRequest({ request }) {
    console.log('[urlCleanupMiddleware] 原始请求:', request.method, request.url);

    if (request.method !== 'GET' && request.method !== 'HEAD') {
      console.log('[urlCleanupMiddleware] POST 请求，直接返回原始请求');
      return request;
    }

    const url = new URL(request.url);
    const searchParams = new URLSearchParams(url.search);
    const cleanedParams = new URLSearchParams();
    for (const [key, value] of searchParams) {
      if (value && value !== 'undefined' && value !== 'null' && key !== 'args' && key !== 'kwargs') {
        cleanedParams.append(key, value);
      }
    }
    url.search = cleanedParams.toString();

    return new Request(url, request);
  },
};

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    const token = localStorage.getItem('token');
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`);
    }
    return request;
  },
  async onResponse({ response }) {
    if (response.status === 401) {
      console.error('Unauthorized');
    }
    return response;
  },
};

const errorMiddleware: Middleware = {
  async onResponse({ response }) {
    if (!response.ok) {
      const body = await response.clone().json().catch(() => ({}));
      const errorMessage = body.detail || body.message || 'Request failed';
      console.error(`API Error: ${response.status} ${errorMessage}`);
    }
    return response;
  },
};

client.use(urlCleanupMiddleware);
client.use(authMiddleware);
client.use(errorMiddleware);

export default client;
