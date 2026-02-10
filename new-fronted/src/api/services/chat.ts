import { client } from '../client';
import type { UIInteractionBlock } from '@/types/sdui';
import { cleanJsonFromContent } from '@/lib/ai-chat-helper';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  ui_interaction?: UIInteractionBlock;
  metadata?: {
    node_id?: string;
    action?: string;
    from_state?: boolean;
    from_ui_interaction?: boolean;
  };
}

export interface ChatInitResponse {
  thread_id: string;
  messages: Message[];
  is_cold_start: boolean;
  ui_interaction?: UIInteractionBlock;
  is_generating?: boolean;
  generating_node?: string;
}

export interface ChatStreamCallbacks {
  onMessage: (message: Message) => void;
  onThinking?: (thinking: string) => void;
  onToolCall?: (tool: { name: string; arguments: any }) => void;
  onNodeStart?: (node: string, desc?: string) => void;
  onNodeEnd?: (node: string) => void;
  onProgress?: (desc: string) => void;  // 新增：详细进度更新
  onStatus?: (status: string) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

// 后端 SSE 事件类型定义（与 backend/api/graph.py 对应）
interface BackendSSEEvent {
  type: 'node_start' | 'node_end' | 'token' | 'done' | 'error' | 'status' | 'ui_interaction' | 'progress';
  node?: string;
  content?: string;
  data?: any;
  error_type?: string;
  message?: string;
  state?: any;
  tool?: string;
  phase?: string;
  desc?: string;
}

// LangChain 消息格式（后端返回的格式）
interface LangChainMessage {
  type: 'ai' | 'human' | 'system';
  data: {
    content: string | Array<{ text?: string }>;
    additional_kwargs?: Record<string, any>;
    response_metadata?: Record<string, any>;
  };
}

/**
 * 将 LangChain 格式的消息转换为前端 Message 格式
 */
function convertLangChainMessage(lcMsg: LangChainMessage | any): Message | null {
  // 如果已经是正确格式，直接返回
  if (lcMsg.role && lcMsg.content !== undefined) {
    return {
      id: lcMsg.id || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role: lcMsg.role === 'ai' ? 'assistant' : lcMsg.role,
      content: typeof lcMsg.content === 'string' ? lcMsg.content : JSON.stringify(lcMsg.content),
      timestamp: new Date(lcMsg.timestamp || Date.now()),
      ui_interaction: lcMsg.ui_interaction,
      metadata: lcMsg.metadata,
    };
  }

  // 处理 LangChain 格式 (type + data)
  if (lcMsg.type && lcMsg.data) {
    const role = lcMsg.type === 'ai' ? 'assistant' : lcMsg.type === 'human' ? 'user' : lcMsg.type;
    let content = '';

    if (typeof lcMsg.data.content === 'string') {
      content = lcMsg.data.content;
    } else if (Array.isArray(lcMsg.data.content)) {
      content = lcMsg.data.content.map((item: any) =>
        typeof item === 'string' ? item : item.text || ''
      ).join('');
    }

    // 从 additional_kwargs 中提取 ui_interaction
    const uiInteraction = lcMsg.data.additional_kwargs?.ui_interaction;

    return {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role: role as 'user' | 'assistant' | 'system',
      content: cleanJsonFromContent(content),
      timestamp: new Date(),
      ui_interaction: uiInteraction,
    };
  }

  return null;
}

// 临时项目缓存
interface TempProjectCache {
  id: string;
  createdAt: number;
}

interface ThreadCache {
  threadId: string;
  projectId: string;
  createdAt: number;
}

const TEMP_PROJECT_KEY = 'temp_project';
const TEMP_PROJECT_MAX_AGE = 7 * 24 * 60 * 60 * 1000;
const THREAD_KEY_PREFIX = 'chat_thread_';

export const chatService = {
  /**
   * 初始化聊天 - 后端决定返回历史还是冷启动
   * 这是唯一需要调用的初始化方法
   */
  async initChat(projectId: string, userId?: string): Promise<ChatInitResponse> {
    const threadId = this.getThreadId(projectId) || `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/graph/chat/init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId || 'user-' + Math.random().toString(36).substr(2, 9),
        project_id: projectId,
        session_id: threadId,
      }),
    });

    if (!response.ok) {
      throw new Error(`初始化聊天失败: ${response.status}`);
    }

    const result: ChatInitResponse = await response.json();

    // 保存 thread_id
    this.saveThreadId(projectId, result.thread_id);

    // 转换消息格式（支持 LangChain 格式）
    result.messages = result.messages.map(msg => {
      const converted = convertLangChainMessage(msg);
      if (converted) {
        return converted;
      }
      // 后备：保持原有格式但确保 timestamp 是 Date
      return {
        ...msg,
        role: (msg.role as string) === 'ai' ? 'assistant' : msg.role,
        timestamp: new Date(msg.timestamp || Date.now()),
      };
    });

    return result;
  },

  /**
   * 获取或创建临时项目
   */
  async ensureProjectId(projectId?: string): Promise<string> {
    if (projectId) return projectId;

    // 检查 localStorage 是否有未过期的临时项目
    const cached = localStorage.getItem(TEMP_PROJECT_KEY);
    if (cached) {
      try {
        const tempProject: TempProjectCache = JSON.parse(cached);
        const age = Date.now() - tempProject.createdAt;

        if (age < TEMP_PROJECT_MAX_AGE) {
          console.log('Using cached temp project:', tempProject.id);
          return tempProject.id;
        } else {
          console.log('Temp project expired, creating new one');
          localStorage.removeItem(TEMP_PROJECT_KEY);
        }
      } catch (e) {
        localStorage.removeItem(TEMP_PROJECT_KEY);
      }
    }

    // 创建新的临时项目
    console.log('Creating new temp project...');
    try {
      const { data, error } = await client.POST('/api/projects/temp', {});

      if (error || !data?.data) {
        console.error('Failed to create temp project:', error);
        const fallbackProjectId = '00000000-0000-0000-0000-000000000001';
        console.warn('Using fallback project ID:', fallbackProjectId);
        return fallbackProjectId;
      }

      const newProjectId = data.data.id;

      localStorage.setItem(TEMP_PROJECT_KEY, JSON.stringify({
        id: newProjectId,
        createdAt: Date.now()
      }));

      console.log('Created temp project:', newProjectId);
      return newProjectId;
    } catch (e) {
      console.error('Exception creating temp project:', e);
      const fallbackProjectId = '00000000-0000-0000-0000-000000000001';
      console.warn('Using fallback project ID due to exception:', fallbackProjectId);
      return fallbackProjectId;
    }
  },

  /**
   * 获取临时项目 ID（只读取，不创建）
   */
  getTempProjectId(): string | null {
    const cached = localStorage.getItem(TEMP_PROJECT_KEY);
    if (!cached) return null;

    try {
      const tempProject: TempProjectCache = JSON.parse(cached);
      const age = Date.now() - tempProject.createdAt;

      if (age < TEMP_PROJECT_MAX_AGE) {
        return tempProject.id;
      } else {
        localStorage.removeItem(TEMP_PROJECT_KEY);
        return null;
      }
    } catch (e) {
      localStorage.removeItem(TEMP_PROJECT_KEY);
      return null;
    }
  },

  /**
   * 清除临时项目缓存
   */
  clearTempProject(): void {
    localStorage.removeItem(TEMP_PROJECT_KEY);
  },

  /**
   * 清除 thread ID（用于重置会话）
   */
  clearThreadId(projectId: string): void {
    localStorage.removeItem(this.getThreadCacheKey(projectId));
  },

  /**
   * 重置聊天 - 请求后端删除历史并清除本地状态
   */
  async resetChat(projectId: string): Promise<void> {
    const threadId = this.getThreadId(projectId);
    
    if (threadId) {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        console.log('[ChatService] Requesting backend reset for thread:', threadId);
        
        await fetch(`${apiUrl}/api/graph/chat/reset`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 'user-' + Math.random().toString(36).substr(2, 9),
            project_id: projectId,
            session_id: threadId,
          }),
        });
        console.log('[ChatService] Backend reset successful');
      } catch (error) {
        console.error('[ChatService] Failed to reset backend chat:', error);
        // Continue to clear local state even if backend fails
      }
    }

    // 清除现有 thread
    this.clearThreadId(projectId);
    
    // 不立即生成新 ID，让 initChat 去处理，或者这里生成也可以
    // 为了确保干净的状态，这里不生成，留给 initChat
  },

  /**
   * 【已废弃】请使用 initChat() 替代
   * 发送冷启动请求，获取欢迎消息
   * @deprecated 请使用 initChat() 方法，后端已统一处理冷启动逻辑
   */
  async sendColdStartRequest(projectId?: string): Promise<any> {
    const effectiveProjectId = await this.ensureProjectId(projectId);
    const threadId = `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    this.saveThreadId(effectiveProjectId, threadId);

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/graph/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'user-' + Math.random().toString(36).substr(2, 9),
        project_id: effectiveProjectId,
        session_id: threadId,
        action: 'cold_start',
        message: null,
      }),
    });

    if (!response.ok) {
      throw new Error(`冷启动请求失败: ${response.status}`);
    }

    return response.json();
  },

  /**
   * 彻底清除会话（重置）
   */
  clearSession(): void {
    this.clearTempProject();

    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.startsWith('chat_thread_') || key.startsWith('chat_history'))) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
    console.log('[ChatService] Session completely cleared');
  },

  /**
   * 将临时项目转为正式项目
   */
  async saveTempProject(projectId: string, name: string): Promise<void> {
    const { error } = await client.POST('/api/projects/{project_id}/save', {
      params: { path: { project_id: projectId } },
      body: { name }
    });

    if (error) {
      throw new Error('保存项目失败');
    }

    this.clearTempProject();
  },

  getThreadCacheKey(projectId: string): string {
    return `${THREAD_KEY_PREFIX}${projectId}`;
  },

  getThreadId(projectId: string): string | null {
    const key = this.getThreadCacheKey(projectId);
    const cached = localStorage.getItem(key);
    if (cached) {
      try {
        const threadCache: ThreadCache = JSON.parse(cached);
        // 只要能解析出来，就认为是有效的，不过期
        return threadCache.threadId;
      } catch {
        localStorage.removeItem(key);
      }
    }
    return null;
  },

  saveThreadId(projectId: string, threadId: string): void {
    const key = this.getThreadCacheKey(projectId);
    localStorage.setItem(key, JSON.stringify({
      threadId,
      projectId,
      createdAt: Date.now()
    }));
  },

  /**
   * 发送消息并获取流式回复（SSE）
   */
  async streamMessage(
    content: string,
    callbacks: ChatStreamCallbacks,
    projectId?: string,
    nodeId?: string,
    _context?: Record<string, any>
  ): Promise<() => void> {
    const effectiveProjectId = await this.ensureProjectId(projectId);

    const existingThreadId = this.getThreadId(effectiveProjectId);
    const threadId = existingThreadId || `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    if (!existingThreadId) {
      this.saveThreadId(effectiveProjectId, threadId);
    }

    const params = new URLSearchParams();
    params.append('message', content);
    params.append('project_id', effectiveProjectId);
    params.append('thread_id', threadId);
    if (nodeId) params.append('node_id', nodeId);

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const eventSource = new EventSource(
      `${apiUrl}/api/graph/chat?${params.toString()}`
    );

    let assistantMessage = '';
    let messageId = `ai-${Date.now()}`;

    eventSource.onmessage = (event) => {
      try {
        // 解析后端发送的 SSE 事件
        const data: BackendSSEEvent = JSON.parse(event.data);
        console.log('SSE event received:', data.type, data);

        switch (data.type) {
          case 'node_start':
            // 节点开始执行
            if (callbacks.onNodeStart && data.node) {
              callbacks.onNodeStart(data.node, data.desc);
            }
            break;

          case 'node_end':
            // 节点执行完成
            if (callbacks.onNodeEnd && data.node) {
              callbacks.onNodeEnd(data.node);
            }
            break;

          case 'progress':
            // 详细进度更新
            if (callbacks.onProgress && data.desc) {
              callbacks.onProgress(data.desc);
            }
            break;

          case 'status':
            // 状态更新（工具调用、处理阶段等）
            if (callbacks.onStatus && data.message) {
              callbacks.onStatus(data.message);
            }
            break;

          case 'token':
            // Token 流输出（对应 response）
            if (data.content) {
              assistantMessage += data.content;
              callbacks.onMessage({
                id: messageId,
                role: 'assistant',
                content: assistantMessage,
                timestamp: new Date(),
                metadata: {
                  node_id: nodeId,
                },
              });
            }
            break;

          case 'ui_interaction':
            // UI 交互块（按钮、选择器等）
            if (data.data) {
              // 立即发送带有 ui_interaction 的消息
              callbacks.onMessage({
                id: messageId,
                role: 'assistant',
                content: assistantMessage || ' ',
                timestamp: new Date(),
                ui_interaction: data.data,
                metadata: {
                  node_id: nodeId,
                  from_ui_interaction: true,
                },
              });
            }
            break;

          case 'done':
            // 获取 ui_interaction（如果存在）
            const uiInteraction = data.state?.ui_interaction || null;

            // 强制从状态中获取最终清洗过的消息内容，覆盖流式累积的内容
            // 这样既能支持缓存命中（无流式），也能支持后端的内容清洗逻辑（移除 JSON）
            if (data.state?.messages) {
              const messages = data.state.messages;
              // 注意：messages 是按顺序的，reverse 后找第一个 ai/assistant 消息
              // 支持两种格式：{role: 'ai', ...} 或 {type: 'ai', data: {...}}
              const lastAiMessage = [...messages].reverse().find((m: any) =>
                m.role === 'ai' || m.role === 'assistant' || m.type === 'ai'
              );

              if (lastAiMessage) {
                const converted = convertLangChainMessage(lastAiMessage);
                if (converted && converted.content) {
                  assistantMessage = converted.content;
                  console.log('Using final content from state (cleaned):', assistantMessage.length);

                  callbacks.onMessage({
                    id: messageId,
                    role: 'assistant',
                    content: assistantMessage,
                    timestamp: new Date(),
                    ui_interaction: uiInteraction,
                    metadata: {
                      node_id: nodeId,
                      from_state: true,
                    },
                  });
                }
              }
            } else if (uiInteraction && assistantMessage) {
              // 如果有流式内容且有 ui_interaction，更新最后一条消息
              callbacks.onMessage({
                id: messageId,
                role: 'assistant',
                content: assistantMessage,
                timestamp: new Date(),
                ui_interaction: uiInteraction,
                metadata: {
                  node_id: nodeId,
                },
              });
            }
            if (data.state?.thread_id) {
              chatService.saveThreadId(effectiveProjectId, data.state.thread_id);
            }
            eventSource.close();
            callbacks.onComplete?.();
            break;

          case 'error':
            // 错误事件
            eventSource.close();
            callbacks.onError?.(data.message || 'Unknown error');
            break;

          default:
            console.warn('Unknown SSE event type:', data.type);
        }
      } catch (err) {
        console.error('Failed to parse SSE event:', err, 'Raw data:', event.data);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
      callbacks.onError?.('Connection error');
    };

    // 返回取消函数
    return () => {
      eventSource.close();
    };
  },

  /**
   * 获取对话历史
   */
  async getHistory(threadId: string): Promise<Message[]> {
    // 使用完整的 API URL
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    try {
      const response = await fetch(`${apiUrl}/api/graph/messages/${encodeURIComponent(threadId)}`);

      if (!response.ok) {
        console.error('Failed to fetch history:', response.status, response.statusText);
        throw new Error('Failed to fetch history');
      }

      const result = await response.json();
      const messages = result?.data || [];
      console.log('Retrieved history messages:', messages.length);

      // 调试：检查是否有 ui_interaction
      const messagesWithUi = messages.filter((m: any) => m.ui_interaction);
      console.log('Messages with ui_interaction:', messagesWithUi.length);
      if (messagesWithUi.length > 0) {
        console.log('UI interaction types:', messagesWithUi.map((m: any) => m.ui_interaction?.block_type));
      }

      return messages.map((msg: any) => {
        const converted = convertLangChainMessage(msg);
        if (converted) {
          return converted;
        }
        return {
          id: msg.id,
        role: msg.role === 'ai' ? 'assistant' : msg.role as 'user' | 'assistant' | 'system',
          content: cleanJsonFromContent(msg.content),
          timestamp: new Date(msg.timestamp),
          metadata: msg.metadata,
          ui_interaction: msg.ui_interaction,
        };
      });
    } catch (error) {
      console.error('Error fetching history:', error);
      throw new Error('Failed to fetch history');
    }
  },

  /**
   * 【已废弃】请使用 initChat() 替代
   * 恢复聊天历史
   * @deprecated 请使用 initChat() 方法，后端已统一处理历史恢复逻辑
   */
  async recoverChatHistory(projectId: string): Promise<{ messages: Message[]; threadId: string | null }> {
    const threadId = this.getThreadId(projectId);
    if (!threadId) {
      return { messages: [], threadId: null };
    }

    try {
      const messages = await this.getHistory(threadId);
      return { messages, threadId };
    } catch (error) {
      console.error('Failed to recover chat history:', error);
      this.clearThreadId(projectId);
      return { messages: [], threadId: null };
    }
  },
};
