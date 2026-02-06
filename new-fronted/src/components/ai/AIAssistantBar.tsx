import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Send, Sparkles, ChevronUp, ChevronDown, Command, RotateCcw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { chatService, type Message } from '@/api/services/chat';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ActionBlockRenderer } from './ActionBlockRenderer';
import { cleanJsonFromContent } from '@/lib/ai-chat-helper';
import { useAIChatInit } from '@/hooks/useAIChatInit';

const STORAGE_KEY = 'ai-assistant-height';
const MIN_HEIGHT = 48;
const MAX_HEIGHT = 600;
const DEFAULT_EXPANDED_HEIGHT = 400;

function getInitialHeight(): number {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? parseInt(saved, 10) : DEFAULT_EXPANDED_HEIGHT;
  }
  return DEFAULT_EXPANDED_HEIGHT;
}

export function AIAssistantBar() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [height, setHeight] = useState(() => getInitialHeight());
  const [inputValue, setInputValue] = useState('');
  const [isResizing, setIsResizing] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [thinkingStatus, setThinkingStatus] = useState('AI 正在思考中...');
  const [showResetDialog, setShowResetDialog] = useState(false);
  
  const resizeStartY = useRef(0);
  const resizeStartHeight = useRef(height);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<(() => void) | null>(null);
  const streamPromiseRef = useRef<Promise<() => void> | null>(null);

  const { currentEpisode, currentProject } = useAppStore();
  const addToast = useUIStore((state) => state.addToast);
  
  // 使用统一的 Hook 处理初始化 - 后端决定返回历史还是冷启动
  const projectId = currentProject?.id || chatService.getTempProjectId() || undefined;
  const {
    messages,
    setMessages,
    isLoading: isInitLoading,
    isInitialized,
    resetChat,
  } = useAIChatInit({ projectId });

  // 合并 loading 状态（初始化或消息发送中）
  const isTyping = isInitLoading || !!abortControllerRef.current;

  // 自动发送 Startup Prompt
  useEffect(() => {
    if (isInitialized && currentProject) {
      const startupPrompt = sessionStorage.getItem('startup_prompt');
      if (startupPrompt) {
        sessionStorage.removeItem('startup_prompt');
        setIsExpanded(true);
        setTimeout(() => {
          sendMessage(startupPrompt);
        }, 800);
      }
    }
  }, [isInitialized, currentProject]);

  // 使用 Callback Ref 来监听元素挂载
  const scrollIntoViewRef = useCallback((node: HTMLDivElement | null) => {
    messagesEndRef.current = node;
    if (node) {
      setTimeout(() => {
        node.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }, 300);
    }
  }, []);

  // 监听消息更新自动滚动
  useEffect(() => {
    if (messagesEndRef.current && isExpanded) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages, streamingContent, isExpanded]);

  useEffect(() => {
    if (!isResizing && height !== DEFAULT_EXPANDED_HEIGHT) {
      localStorage.setItem(STORAGE_KEY, height.toString());
    }
  }, [height, isResizing]);

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);
    resizeStartY.current = e.clientY;
    resizeStartHeight.current = height;
  }, [height]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const deltaY = resizeStartY.current - e.clientY;
      const newHeight = Math.max(
        MIN_HEIGHT,
        Math.min(MAX_HEIGHT, resizeStartHeight.current + deltaY)
      );

      setHeight(newHeight);

      if (newHeight > MIN_HEIGHT + 50 && !isExpanded) {
        setIsExpanded(true);
      }
    };

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
        localStorage.setItem(STORAGE_KEY, height.toString());
      }
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, height, isExpanded]);

  const handleActionClick = useCallback(async (action: string, payload?: Record<string, unknown>) => {
    const actionMessage = JSON.stringify({ action, payload });

    // 根据 action 生成友好标签
    const actionLabels: Record<string, string> = {
      'CMD:start_market_analysis': '🚀 开始市场分析',
      'CMD:start_story_planning': '📝 开始故事构思',
      'CMD:start_novel_writing': '🎬 开始写作',
      'select_genre': '选择赛道',
      'start_custom': '✨ 自由创作',
      'proceed_to_planning': '✨ AI 自动选题',
      'reset_genre': '🔙 重选赛道',
      'random_plan': '🎲 随机生成方案',
      'select_plan': '选择方案',
      'start_creation': '🎬 开始创作',
      'adapt_script': '📜 剧本改编',
      'create_storyboard': '🎨 分镜制作',
      'inspect_assets': '👤 资产探查',
    };

    let displayLabel = actionLabels[action] || action;
    if (action === 'select_genre' && payload?.genre) {
      displayLabel = `选择：${payload.genre}`;
    } else if (action === 'random_plan' && payload?.genre) {
      displayLabel = `🎲 生成 ${payload.genre} 方案`;
    }

    const userMessage: Message = {
      id: `action-${Date.now()}`,
      role: 'user',
      content: displayLabel,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    setThinkingStatus('AI 正在处理...');

    let accumulatedContent = '';
    let lastUiInteraction: Message['ui_interaction'] = undefined;

    try {
      const cancelFn = await chatService.streamMessage(
        actionMessage,
        {
          onNodeStart: (_node, desc) => {
            if (desc) setThinkingStatus(desc);
          },
          onStatus: (status) => setThinkingStatus(status),
          onMessage: (message) => {
            accumulatedContent = message.content;
            if (message.ui_interaction) {
              lastUiInteraction = message.ui_interaction;
            }
            setStreamingContent(accumulatedContent);
          },
          onComplete: () => {
            if (accumulatedContent || lastUiInteraction) {
              const newMessage: Message = {
                id: `ai-action-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                role: 'assistant',
                content: accumulatedContent,
                timestamp: new Date(),
                ui_interaction: lastUiInteraction,
              };
              setMessages(prev => [...prev, newMessage]);
            }
            setStreamingContent('');
            abortControllerRef.current = null;
          },
          onError: (error) => {
            console.error('Action error:', error);
            setMessages(prev => [...prev, {
              id: `error-${Date.now()}`,
              role: 'assistant',
              content: `抱歉，操作失败：${error}`,
              timestamp: new Date(),
            }]);
            setStreamingContent('');
            abortControllerRef.current = null;
          },
        },
        projectId ?? undefined,
        currentEpisode?.id
      );

      abortControllerRef.current = cancelFn;
    } catch (error) {
      console.error('Action error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `抱歉，请求失败：${error}`,
        timestamp: new Date(),
      }]);
    }
  }, [projectId, currentEpisode?.id, setMessages]);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setThinkingStatus('AI 正在思考中...');

    if (!isExpanded) {
      setIsExpanded(true);
    }

    let accumulatedContent = '';
    let hasReceivedContent = false;
    let lastUiInteraction: Message['ui_interaction'] = undefined;

    try {
      streamPromiseRef.current = chatService.streamMessage(
        userMessage.content,
        {
          onMessage: (message) => {
            accumulatedContent = message.content;
            hasReceivedContent = true;
            if (message.ui_interaction) {
              lastUiInteraction = message.ui_interaction;
            }
            setStreamingContent(message.content);
          },
          onComplete: () => {
            if (accumulatedContent || hasReceivedContent) {
              setMessages(prev => [...prev, {
                id: `ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                role: 'assistant',
                content: accumulatedContent,
                timestamp: new Date(),
                ui_interaction: lastUiInteraction,
              }]);
            }
            setStreamingContent('');
            abortControllerRef.current = null;
          },
          onError: (error) => {
            setMessages(prev => [...prev, {
              id: `error-${Date.now()}`,
              role: 'assistant',
              content: `抱歉，发生了错误：${error}`,
              timestamp: new Date(),
            }]);
            setStreamingContent('');
            abortControllerRef.current = null;
          },
          onNodeStart: (node, desc) => {
            setThinkingStatus(desc || `⚙️ AI 正在处理 (${node})...`);
          },
          onStatus: (status) => {
            setThinkingStatus(status);
          },
        },
        currentProject?.id,
        currentEpisode?.id
      );

      streamPromiseRef.current.then(cancelFn => {
        abortControllerRef.current = cancelFn;
      });
    } catch (error) {
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `抱歉，请求失败：${error}`,
        timestamp: new Date(),
      }]);
    }
  };

  const handleSendMessage = () => {
    sendMessage(inputValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickActions = [
    { label: '续写', prompt: '续写下文' },
    { label: '扩写', prompt: '扩写当前内容' },
    { label: '润色', prompt: '润色优化' },
    { label: '分镜', prompt: '为当前场景生成分镜' },
  ];

  const handleQuickAction = (prompt: string) => {
    setInputValue(prompt);
    handleSendMessage();
  };

  const handleResetSession = () => {
    setShowResetDialog(true);
  };

  const confirmResetSession = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current();
      abortControllerRef.current = null;
    }

    setStreamingContent('');
    setShowResetDialog(false);

    if (projectId) {
      try {
        await resetChat(projectId);
        addToast({ type: 'success', message: '会话已重置' });
      } catch (error) {
        console.error('Reset chat failed:', error);
        addToast({ type: 'error', message: '重置失败，请重试' });
      }
    } else {
      addToast({ type: 'error', message: '无法重置：未找到项目 ID' });
    }
  };

  const currentHeight = isExpanded ? height : MIN_HEIGHT;

  return (
    <motion.div
      className="fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-border"
      initial={false}
      animate={{ height: currentHeight }}
      transition={isResizing ? { duration: 0 } : { duration: 0.3, ease: 'easeInOut' }}
      style={{
        height: currentHeight,
        boxShadow: isExpanded ? '0 -4px 20px rgba(0,0,0,0.1)' : 'none'
      }}
    >
      {isExpanded && (
        <div
          className="absolute top-0 left-0 right-0 h-2 cursor-ns-resize flex items-center justify-center hover:bg-primary/5 transition-colors group"
          onMouseDown={handleResizeStart}
        >
          <div className="w-12 h-1 rounded-full bg-border group-hover:bg-primary/30 transition-colors" />
        </div>
      )}

      <AnimatePresence mode="wait">
        {!isExpanded ? (
          <motion.div
            key="collapsed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full flex items-center px-4 py-2"
          >
            <div className="flex-1 flex items-center gap-3 max-w-4xl mx-auto">
              <Badge
                variant="secondary"
                className="gap-1.5 px-3 py-1.5 cursor-pointer hover:bg-primary/10 transition-colors"
                onClick={() => setIsExpanded(true)}
              >
                <Bot size={14} className="text-primary" />
                <span className="text-xs">AI 助手</span>
                <ChevronUp size={12} className="text-text-tertiary" />
              </Badge>

              <Badge variant="outline" className="text-xs gap-1">
                <Command size={12} />
                场景 S01
              </Badge>

              <div className="flex items-center gap-1">
                {quickActions.map((action) => (
                  <Button
                    key={action.label}
                    variant="ghost"
                    size="sm"
                    onClick={() => handleQuickAction(action.prompt)}
                    className="text-xs h-7 px-2 text-text-secondary hover:text-primary"
                  >
                    {action.label}
                  </Button>
                ))}
              </div>

              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入指令，例如：优化这段对白..."
                className="flex-1 h-9 bg-background/50"
              />

              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isTyping}
                className="btn-primary h-9 w-9 p-0"
              >
                <Send size={16} />
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(true)}
                className="h-9 w-9 p-0 text-text-tertiary hover:text-primary"
              >
                <ChevronUp size={18} />
              </Button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="expanded"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="h-full flex flex-col overflow-hidden"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <Bot size={18} className="text-primary-foreground" />
                </div>
                <div>
                  <p className="font-medium text-sm">AI 创作助手</p>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-xs text-text-tertiary">在线</span>
                  </div>
                </div>

                <Badge variant="outline" className="ml-4 gap-1 text-xs">
                  <Command size={12} />
                  场景 S01 - 废弃医院
                </Badge>
              </div>

              <div className="flex items-center gap-1">
                <div className="flex items-center gap-1 mr-2 sm:mr-4 overflow-x-auto no-scrollbar max-w-[50vw] sm:max-w-none">
                  <div className="flex gap-1">
                    {quickActions.map((action) => (
                      <Button
                        key={action.label}
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickAction(action.prompt)}
                        className="text-xs h-7 sm:h-8 gap-1 whitespace-nowrap px-2"
                      >
                        <Sparkles size={12} />
                        {action.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 gap-1.5 text-xs text-text-tertiary hover:text-red-500 hover:bg-red-500/10 transition-colors mr-1 hidden sm:flex"
                  onClick={handleResetSession}
                  title="重新开始"
                >
                  <RotateCcw size={14} />
                  <span>重置</span>
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsExpanded(false)}
                  className="h-8 w-8 p-0"
                >
                  <ChevronDown size={18} />
                </Button>
              </div>
            </div>

            <ScrollArea className="flex-1 min-h-0 px-3 sm:px-4">
              <div className="py-3 sm:py-4 space-y-4 sm:space-y-6 max-w-6xl mx-auto">
                {messages.map((message) => {
                  const isAssistant = message.role === 'assistant';
                  const hasInteraction = !!message.ui_interaction;

                  if (isAssistant && hasInteraction) {
                    return (
                      <div key={message.id} className="flex flex-col items-start w-full">
                        <div className="flex flex-col lg:flex-row gap-3 w-full max-w-full">
                          <div className="flex-1 min-w-0 max-w-full lg:max-w-[calc(100%-340px)]">
                            <div className="bg-elevated border border-border rounded-2xl rounded-bl-md px-4 py-3 h-full">
                              <div className="prose prose-sm prose-invert max-w-none text-sm break-words [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:pl-4 [&>ol]:list-decimal [&>ol]:pl-4 [&>pre]:overflow-x-auto">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {cleanJsonFromContent(message.content)}
                                </ReactMarkdown>
                              </div>
                              <p className="text-[10px] sm:text-xs mt-2 text-text-tertiary">
                                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </p>
                            </div>
                          </div>

                          <div className="w-full lg:w-[320px] shrink-0">
                            <div className="-mt-3 lg:-mt-3">
                              <ActionBlockRenderer block={message.ui_interaction!} onActionClick={handleActionClick} />
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div
                      key={message.id}
                      className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}
                    >
                      <div
                        className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-3 py-2 sm:px-4 sm:py-3 ${message.role === 'user'
                          ? 'bg-primary text-primary-foreground rounded-br-md'
                          : 'bg-elevated border border-border rounded-bl-md'
                          }`}
                      >
                        {message.role === 'user' ? (
                          <p className="text-xs sm:text-sm whitespace-pre-wrap">{message.content}</p>
                        ) : (
                          <div className="prose prose-sm prose-invert max-w-none text-xs sm:text-sm overflow-hidden break-words [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:pl-4 [&>ol]:list-decimal [&>ol]:pl-4 [&>code]:bg-background [&>code]:px-1 [&>code]:rounded [&>pre]:overflow-x-auto">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {cleanJsonFromContent(message.content)}
                            </ReactMarkdown>
                          </div>
                        )}
                        <p className={`text-[10px] sm:text-xs mt-1 sm:mt-1.5 ${message.role === 'user' ? 'text-primary-foreground/60' : 'text-text-tertiary'}`}>
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  );
                })}

                {isTyping && !streamingContent && (
                  <div className="flex justify-start">
                    <div className="bg-elevated/50 border border-border/50 rounded-2xl rounded-bl-md px-4 py-3">
                      <div className="flex items-center gap-2 text-text-tertiary">
                        <Loader2 className="animate-spin w-4 h-4 text-primary" />
                        <span className="text-xs sm:text-sm">{thinkingStatus}</span>
                      </div>
                    </div>
                  </div>
                )}

                {streamingContent && (
                  <div className="flex justify-start">
                    <div className="bg-elevated border border-border rounded-2xl rounded-bl-md px-4 py-3 max-w-[85%] sm:max-w-[80%]">
                      <div className="prose prose-sm prose-invert max-w-none text-sm overflow-hidden break-words [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:pl-4 [&>ol]:list-decimal [&>ol]:pl-4 [&>pre]:overflow-x-auto">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {cleanJsonFromContent(streamingContent)}
                        </ReactMarkdown>
                      </div>
                      <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />
                      <p className="text-xs mt-1.5 text-text-tertiary">
                        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                )}

                <div ref={scrollIntoViewRef} />
              </div>
            </ScrollArea>

            <div className="px-4 py-3 border-t border-border bg-surface/50 shrink-0">
              <div className="flex items-center gap-3 max-w-4xl mx-auto">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入指令或问题..."
                  className="flex-1 h-10 bg-background"
                  disabled={isTyping}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isTyping}
                  className="btn-primary h-10 px-4 gap-2"
                >
                  <Send size={16} />
                  发送
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {isResizing && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-primary z-50" />
      )}

      <ConfirmDialog
        open={showResetDialog}
        onOpenChange={setShowResetDialog}
        title="确认重置会话？"
        description="这将清空当前所有对话记录，并重新开始一个新的对话。此操作无法撤销。"
        confirmText="确认重置"
        cancelText="取消"
        onConfirm={confirmResetSession}
        variant="destructive"
      />
    </motion.div>
  );
}
