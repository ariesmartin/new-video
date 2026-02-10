import { useState, useEffect, useRef, useCallback } from 'react';
import { chatService, type Message } from '@/api/services/chat';

interface UseAIChatInitOptions {
  projectId?: string;
  onError?: (error: Error) => void;
}

interface UseAIChatInitReturn {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  isLoading: boolean;
  isInitialized: boolean;
  threadId: string | null;
  initChat: (projectId: string) => Promise<void>;
  resetChat: (projectId: string) => Promise<void>;
  isGenerating: boolean;
  generatingNode: string | null;
}

/**
 * 极简的 AI 聊天初始化 Hook
 * 
 * 核心原则：前端只调用 API，所有逻辑在后端
 * - 后端决定返回历史消息还是冷启动欢迎消息
 * - 前端只负责显示后端返回的内容
 * - 不做任何业务逻辑判断
 */
export function useAIChatInit(options: UseAIChatInitOptions): UseAIChatInitReturn {
  const { projectId, onError } = options;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingNode, setGeneratingNode] = useState<string | null>(null);

  const isCancelledRef = useRef(false);
  const hasInitializedRef = useRef(false);
  const onErrorRef = useRef(onError);
  
  // 保持 onError 引用最新
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const initChat = useCallback(async (targetProjectId: string) => {
    if (isCancelledRef.current) return;
    
    setIsLoading(true);

    try {
      const response = await chatService.initChat(targetProjectId);
      
      if (isCancelledRef.current) return;

      console.log('[useAIChatInit] Init response:', {
        is_cold_start: response.is_cold_start,
        message_count: response.messages.length,
        thread_id: response.thread_id,
        is_generating: response.is_generating,
        generating_node: response.generating_node,
      });

      setMessages(response.messages);
      setThreadId(response.thread_id);
      setIsGenerating(response.is_generating || false);
      setGeneratingNode(response.generating_node || null);
      setIsInitialized(true);
      hasInitializedRef.current = true;
    } catch (error) {
      console.error('[useAIChatInit] Init failed:', error);
      
      if (onErrorRef.current) {
        onErrorRef.current(error instanceof Error ? error : new Error(String(error)));
      }
      
      setIsInitialized(true);
      hasInitializedRef.current = true;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 重置聊天 - 清除历史并强制冷启动
   */
  const resetChat = useCallback(async (targetProjectId: string) => {
    setIsInitialized(false);
    setMessages([]);
    setThreadId(null);
    hasInitializedRef.current = false;
    
    await chatService.resetChat(targetProjectId);
    
    await initChat(targetProjectId);
  }, [initChat]);

  useEffect(() => {
    if (!projectId || hasInitializedRef.current) return;

    isCancelledRef.current = false;
    hasInitializedRef.current = false;

    initChat(projectId);

    return () => {
      isCancelledRef.current = true;
    };
  }, [projectId]);

  // 当检测到后端正在生成时，自动轮询检查生成状态
  useEffect(() => {
    if (!isGenerating || !projectId) return;

    console.log('[useAIChatInit] Auto-polling for generation status...');

    // 每隔3秒轮询检查生成状态
    const interval = setInterval(async () => {
      if (isCancelledRef.current) return;

      try {
        const response = await chatService.initChat(projectId);

        if (isCancelledRef.current) return;

        // 如果生成完成（is_generating 变为 false）
        if (!response.is_generating && isGenerating) {
          console.log('[useAIChatInit] Generation completed, updating messages');
          setMessages(response.messages);
          setIsGenerating(false);
          setGeneratingNode(null);
        }
      } catch (error) {
        console.error('[useAIChatInit] Polling error:', error);
      }
    }, 3000);

    return () => {
      clearInterval(interval);
    };
  }, [isGenerating, projectId, isGenerating]);

  return {
    messages,
    setMessages,
    isLoading,
    isInitialized,
    threadId,
    initChat,
    resetChat,
    isGenerating,
    generatingNode,
  };
}
