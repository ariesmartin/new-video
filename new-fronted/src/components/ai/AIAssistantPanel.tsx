import { useState, useRef, useCallback, useEffect } from 'react';
import { Bot, Send, Sparkles, RotateCcw, Loader2, Maximize2, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { chatService, type Message } from '@/api/services/chat';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ActionBlockRenderer } from './ActionBlockRenderer';
import { ScriptRenderer } from './ScriptRenderer';
import { cleanJsonFromContent } from '@/lib/ai-chat-helper';
import { useAIChatInit } from '@/hooks/useAIChatInit';
import { useChatScroll } from '@/hooks/useChatScroll';
import { AIReaderDialog } from './AIReaderDialog';

interface AIAssistantPanelProps {
  projectId?: string;
  sceneContext?: {
    id: string;
    number: string | number;
    location: string;
    description: string;
  };
}

export function AIAssistantPanel({ projectId: externalProjectId, sceneContext }: AIAssistantPanelProps) {
  const [inputValue, setInputValue] = useState('');
  const [streamingContent, setStreamingContent] = useState('');
  const [thinkingStatus, setThinkingStatus] = useState('AI 正在思考中...');
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [readerContent, setReaderContent] = useState<string | null>(null);

  const abortControllerRef = useRef<(() => void) | null>(null);

  const { currentEpisode, currentProject } = useAppStore();
  const addToast = useUIStore((state) => state.addToast);

  // 确定项目 ID
  const projectId = externalProjectId || currentProject?.id || chatService.getTempProjectId() || undefined;

  // 使用统一的 Hook 处理初始化 - 后端决定返回历史还是冷启动
  const {
    messages,
    setMessages,
    isLoading: isInitLoading,
    resetChat,
    isGenerating: isBackendGenerating,
    generatingNode,
  } = useAIChatInit({
    projectId,
    onError: (error) => {
      console.error('[AIAssistantPanel] Init error:', error);
    }
  });

  // 合并 loading 状态
  const isTyping = isInitLoading || !!abortControllerRef.current || isBackendGenerating;

  // 当检测到后端正在生成时，更新状态提示
  useEffect(() => {
    if (isBackendGenerating && generatingNode) {
      setThinkingStatus(`AI 正在生成中 (${generatingNode})...`);
    }
  }, [isBackendGenerating, generatingNode]);

  // 使用统一的自动滚动 hook
  const messagesEndRef = useChatScroll({
    messages,
    isStreaming: !!streamingContent
  });

  // 发送用户消息
  const handleSendMessage = useCallback(async (content?: string) => {
    const messageContent = content || inputValue;
    if (!messageContent.trim() || isTyping) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setThinkingStatus('AI 正在思考中...');
    setStreamingContent('');

    let accumulatedContent = '';
    let lastUiInteraction: Message['ui_interaction'] = undefined;

    const effectiveProjectId = externalProjectId || currentProject?.id || chatService.getTempProjectId();

    try {
      const cancelFn = await chatService.streamMessage(
        userMessage.content,
        {
          onNodeStart: (_node, desc) => {
            if (desc) setThinkingStatus(desc);
          },
          onProgress: (desc) => {
            setThinkingStatus(desc);
          },
          onStatus: (status) => {
            setThinkingStatus(status);
          },
          onMessage: (message) => {
            accumulatedContent = message.content;
            if (message.ui_interaction) {
              lastUiInteraction = message.ui_interaction;
            }
            setStreamingContent(accumulatedContent);
          },
          onComplete: () => {
            console.log('[AIAssistantPanel] Message complete, content length:', accumulatedContent.length);
            if (accumulatedContent) {
              const newMessage: Message = {
                id: `ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                role: 'assistant',
                content: accumulatedContent,
                timestamp: new Date(),
                ui_interaction: lastUiInteraction,
              };
              setMessages(prev => {
                if (lastUiInteraction?.buttons?.some((b: any) => b.action === 'select_plan')) {
                  const filtered = prev.filter(m => 
                    !(m.role === 'assistant' && m.ui_interaction?.buttons?.some((b: any) => b.action === 'select_plan'))
                  );
                  return [...filtered, newMessage];
                }
                return [...prev, newMessage];
              });
            }
            setStreamingContent('');
            abortControllerRef.current = null;
          },
          onError: (error) => {
            console.error('[AIAssistantPanel] Message error:', error);
            setMessages(prev => [...prev, {
              id: `error-${Date.now()}`,
              role: 'assistant',
              content: `抱歉，发生了错误：${error}`,
              timestamp: new Date(),
            }]);
            setStreamingContent('');
            abortControllerRef.current = null;
          },
        },
        effectiveProjectId ?? undefined,
        currentEpisode?.id ?? sceneContext?.id
      );
      abortControllerRef.current = cancelFn;
    } catch (error) {
      console.error('[AIAssistantPanel] Send message error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `抱歉，请求失败：${error}`,
        timestamp: new Date(),
      }]);
    }
  }, [inputValue, isTyping, externalProjectId, currentProject?.id, currentEpisode?.id, sceneContext?.id, setMessages]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickActions = [
    { label: '续写下文', icon: <Sparkles size={12} />, prompt: '续写当前场景的后续内容' },
    { label: '扩写场景', icon: <Sparkles size={12} />, prompt: '扩写当前场景的描述和细节' },
    { label: '润色对白', icon: <Sparkles size={12} />, prompt: '润色场景中的对白' },
    { label: '生成分镜', icon: <Sparkles size={12} />, prompt: '为当前场景生成分镜方案' },
  ];

  const handleQuickAction = (prompt: string) => {
    setInputValue(prompt);
    handleSendMessage(prompt);
  };

  // 处理 SDUI Action 按钮点击
  const handleActionClick = useCallback(async (action: string, payload?: Record<string, unknown>) => {
    const actionMessage = JSON.stringify({ action, payload });

    // Action 到友好标签的映射
    const actionLabels: Record<string, string> = {
      'CMD:start_market_analysis': '🚀 开始市场分析',
      'CMD:start_story_planning': '📝 开始故事构思',
      'CMD:start_novel_writing': '🎬 开始写作',
      'select_genre': '选择赛道',
      'start_custom': '✨ 自由创作',
      'proceed_to_planning': '✨ AI 自动选题',
      'reset_genre': '🔙 重选背景',
      'random_plan': '🎲 随机生成方案',
      'select_plan': '选择方案',
      'regenerate_plans': '🔄 重新生成方案',
      'fuse_plans': '🔀 融合方案',
      'custom_fusion': '⚡ 自定义融合',
      'start_creation': '🎬 开始创作',
      'adapt_script': '📜 剧本改编',
      'create_storyboard': '🎨 分镜制作',
      'inspect_assets': '👤 资产探查',
      'set_episode_config': '✅ 确认剧集配置',
      'custom_episode_config': '⚙️ 自定义剧集配置',
      'start_skeleton_building': '📋 开始大纲拆解',
      'confirm_skeleton': '✅ 确认大纲',
      'regenerate_skeleton': '🔄 重新生成大纲',
      'select_ending': '🎭 选择结局类型',
    };

    let displayLabel = actionLabels[action] || action;
    if (action === 'select_genre' && payload?.genre) {
      displayLabel = `选择：${payload.genre}`;
    } else if (action === 'random_plan' && payload?.genre) {
      displayLabel = `🎲 生成 ${payload.genre} 方案`;
    } else if (action === 'select_plan' && payload?.label) {
      displayLabel = `选择：${payload.label}`;
    } else if (action === 'reset_genre') {
      displayLabel = '🔙 重新选择赛道';
    } else if (action === 'set_episode_config' && payload?.episode_count) {
      displayLabel = `✅ 配置：${payload.episode_count}集，每集${payload.episode_duration}分钟`;
    } else if (action === 'custom_episode_config') {
      displayLabel = '⚙️ 自定义剧集配置';
    }

    const userMessage: Message = {
      id: `action-${Date.now()}`,
      role: 'user',
      content: displayLabel,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    setThinkingStatus('AI 正在处理...');
    setStreamingContent('');

    let accumulatedContent = '';
    let lastUiInteraction: Message['ui_interaction'] = undefined;

    const effectiveProjectId = externalProjectId || currentProject?.id || chatService.getTempProjectId();

    try {
      const cancelFn = await chatService.streamMessage(
        actionMessage,
        {
          onNodeStart: (_node, desc) => {
            if (desc) setThinkingStatus(desc);
          },
          onProgress: (desc) => {
            setThinkingStatus(desc);
          },
          onStatus: (status) => {
            setThinkingStatus(status);
          },
          onMessage: (message) => {
            accumulatedContent = message.content;
            if (message.ui_interaction) {
              lastUiInteraction = message.ui_interaction;
            }
            setStreamingContent(accumulatedContent);
          },
          onComplete: () => {
            console.log('[AIAssistantPanel] Action complete, content length:', accumulatedContent.length, 'has UI:', !!lastUiInteraction);
            if (accumulatedContent || lastUiInteraction) {
              const newMessage: Message = {
                id: `ai-action-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                role: 'assistant',
                content: accumulatedContent || '',
                timestamp: new Date(),
                ui_interaction: lastUiInteraction,
              };
              setMessages(prev => {
                // 如果新消息包含方案按钮，替换掉之前包含方案的消息（重新生成场景）
                if (lastUiInteraction?.buttons?.some((b: any) => b.action === 'select_plan')) {
                  const filtered = prev.filter(m => 
                    !(m.role === 'assistant' && m.ui_interaction?.buttons?.some((b: any) => b.action === 'select_plan'))
                  );
                  return [...filtered, newMessage];
                }
                return [...prev, newMessage];
              });
            }
            setStreamingContent('');
            abortControllerRef.current = null;
          },
          onError: (error) => {
            console.error('[AIAssistantPanel] Action error:', error);
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
        effectiveProjectId ?? undefined,
        currentEpisode?.id ?? sceneContext?.id
      );
      abortControllerRef.current = cancelFn;
    } catch (error) {
      console.error('[AIAssistantPanel] Action error:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `抱歉，请求失败：${error}`,
        timestamp: new Date(),
      }]);
    }
  }, [externalProjectId, currentProject?.id, currentEpisode?.id, sceneContext?.id, setMessages]);

  const handleStopGenerating = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current();
      abortControllerRef.current = null;
      setStreamingContent('');
      setThinkingStatus('已停止');
    }
  }, []);

  const handleResetSession = () => {
    setShowResetDialog(true);
  };

  const confirmResetSession = async () => {
    const effectiveProjectId = currentProject?.id || chatService.getTempProjectId();

    if (!effectiveProjectId) {
      addToast({ type: 'error', message: '无法重置：未找到项目 ID' });
      setShowResetDialog(false);
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current();
      abortControllerRef.current = null;
    }

    setStreamingContent('');
    setShowResetDialog(false);

    try {
      await resetChat(effectiveProjectId);
      addToast({ type: 'success', message: '会话已重置' });
    } catch (error) {
      console.error('Reset chat failed:', error);
      addToast({ type: 'error', message: '重置失败，请重试' });
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-surface border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between px-3 sm:px-4 py-3 border-b border-border shrink-0">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary flex items-center justify-center">
            <Bot size={16} className="sm:w-[18px] sm:h-[18px] text-primary-foreground" />
          </div>
          <div>
            <p className="font-medium text-xs sm:text-sm">AI 创作助手</p>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-[10px] sm:text-xs text-text-tertiary">在线</span>
            </div>
          </div>
        </div>
        <TooltipProvider delayDuration={300}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 hover:bg-muted text-text-tertiary hover:text-text-primary transition-colors"
                onClick={handleResetSession}
                disabled={isTyping}
              >
                <RotateCcw size={14} />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>重置会话</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Scene Context Badge */}
      {sceneContext && (
        <div className="px-4 py-2 border-b border-border bg-primary/5 shrink-0">
          <Badge variant="outline" className="text-xs w-full justify-center">
            场景 {sceneContext.number}：{sceneContext.location}
          </Badge>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 min-h-0 px-4 w-full">
        <div className="py-4 space-y-4 w-full min-w-0">
          {/* 找到最后一条包含 ui_interaction 的 AI 消息索引 */}
          {(() => {
            const lastUiInteractionIndex = messages.findLastIndex(m => m.role === 'assistant' && m.ui_interaction);
            
            return messages.map((message, index) => {
            const isLongContent = message.role === 'assistant' && cleanJsonFromContent(message.content).length > 150;
            // ✅ 修复：在所有有 ui_interaction 的消息上都显示按钮，不只是最后一个
            // 这样可以保留历史交互按钮的状态
            const shouldShowButtons = message.ui_interaction;
            // ✅ 修复：只有最后一条包含 ui_interaction 的 AI 消息的按钮可点击
            const isLatestUiInteraction = index === lastUiInteractionIndex;

            return (
              <div
                key={message.id}
                className={`flex flex-col w-full ${message.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-full rounded-2xl px-4 py-3 group relative min-w-0 overflow-hidden ${message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-br-md'
                    : 'bg-elevated border border-border rounded-bl-md'
                    }`}
                  style={{ width: 'auto', maxWidth: 'min(90%, calc(100% - 32px))' }}
                >
                  {message.role === 'user' ? (
                    <p className="text-sm whitespace-pre-wrap break-all max-h-[60vh] overflow-y-auto min-w-0 overflow-wrap-anywhere">{cleanJsonFromContent(message.content)}</p>
                  ) : (
                    <div className="w-full text-sm break-all overflow-hidden max-h-[60vh] overflow-y-auto min-w-0" style={{ overflowWrap: 'anywhere' }}>
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ScriptRenderer,
                          h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1.5 text-primary/90 border-b border-border/30 pb-1">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-sm font-bold mt-2.5 mb-1 text-primary/80">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 text-text-primary">{children}</h3>,
                          h4: ({ children }) => <h4 className="text-xs font-semibold mt-1.5 mb-0.5 text-text-primary">{children}</h4>,
                          h5: ({ children }) => <h5 className="text-xs font-medium mt-1 mb-0.5 text-text-secondary">{children}</h5>,
                          h6: ({ children }) => <h6 className="text-xs font-medium mt-1 mb-0.5 text-text-tertiary">{children}</h6>,
                          table: ({ children }) => <div className="overflow-x-auto my-2"><table className="w-full text-xs border-collapse">{children}</table></div>,
                          thead: ({ children }) => <thead className="bg-elevated">{children}</thead>,
                          tbody: ({ children }) => <tbody>{children}</tbody>,
                          tr: ({ children }) => <tr className="border-b border-border/20">{children}</tr>,
                          th: ({ children }) => <th className="border border-border/30 px-2 py-1 text-left font-medium text-text-secondary bg-elevated/50">{children}</th>,
                          td: ({ children }) => <td className="border border-border/30 px-2 py-1 text-text-tertiary">{children}</td>,
                          ul: ({ children }) => <ul className="list-disc list-inside my-1 space-y-0.5 text-text-secondary">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside my-1 space-y-0.5 text-text-secondary">{children}</ol>,
                          li: ({ children }) => <li className="text-text-secondary">{children}</li>,
                          hr: () => <hr className="my-3 border-border/30" />,
                          blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/30 pl-3 my-2 text-text-secondary italic">{children}</blockquote>,
                          strong: ({ children }) => <strong className="font-semibold text-text-primary">{children}</strong>,
                          pre: ({ children }) => (
                            <pre className="overflow-x-auto max-w-full text-xs bg-black/5 rounded p-2 my-2">{children}</pre>
                          ),
                          code: ({ children }) => (
                            <code className="text-xs bg-black/5 rounded px-1 py-0.5">{children}</code>
                          )
                        }}
                      >
                        {cleanJsonFromContent(message.content)}
                      </ReactMarkdown>
                    </div>
                  )}

                  {isLongContent && (
                    <>
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 bg-surface/80 hover:bg-surface text-text-secondary shadow-sm backdrop-blur-sm"
                          onClick={() => setReaderContent(cleanJsonFromContent(message.content))}
                          title="全屏阅读"
                        >
                          <Maximize2 size={12} />
                        </Button>
                      </div>
                      <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 bg-surface/80 hover:bg-surface text-text-secondary shadow-sm backdrop-blur-sm"
                          onClick={() => setReaderContent(cleanJsonFromContent(message.content))}
                          title="全屏阅读"
                        >
                          <Maximize2 size={12} />
                        </Button>
                      </div>
                    </>
                  )}

                  {shouldShowButtons && (
                    <div className="mt-4 pt-3 border-t border-border/50 w-full min-w-0 overflow-hidden">
                      <ActionBlockRenderer
                        block={message.ui_interaction}
                        onActionClick={handleActionClick}
                        isHistorical={!isLatestUiInteraction}
                      />
                    </div>
                  )}

                  <p className={`text-xs mt-1.5 ${message.role === 'user' ? 'text-primary-foreground/60' : 'text-text-tertiary'}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            );
          })}
          )()}

          {/* Streaming Content */}
          {streamingContent && (
            <div className="flex justify-start w-full">
              <div className="bg-elevated border border-border rounded-2xl rounded-bl-md px-4 py-3 max-h-[60vh] overflow-y-auto min-w-0 overflow-hidden"
                style={{ width: 'auto', maxWidth: 'min(90%, calc(100% - 32px))' }}>
                <div className="w-full text-sm break-all overflow-hidden min-w-0" style={{ overflowWrap: 'anywhere' }}>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ScriptRenderer,
                      h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1.5 text-primary/90 border-b border-border/30 pb-1">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-sm font-bold mt-2.5 mb-1 text-primary/80">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 text-text-primary">{children}</h3>,
                      h4: ({ children }) => <h4 className="text-xs font-semibold mt-1.5 mb-0.5 text-text-primary">{children}</h4>,
                      h5: ({ children }) => <h5 className="text-xs font-medium mt-1 mb-0.5 text-text-secondary">{children}</h5>,
                      h6: ({ children }) => <h6 className="text-xs font-medium mt-1 mb-0.5 text-text-tertiary">{children}</h6>,
                      table: ({ children }) => <div className="overflow-x-auto my-2"><table className="w-full text-xs border-collapse">{children}</table></div>,
                      thead: ({ children }) => <thead className="bg-elevated">{children}</thead>,
                      tbody: ({ children }) => <tbody>{children}</tbody>,
                      tr: ({ children }) => <tr className="border-b border-border/20">{children}</tr>,
                      th: ({ children }) => <th className="border border-border/30 px-2 py-1 text-left font-medium text-text-secondary bg-elevated/50">{children}</th>,
                      td: ({ children }) => <td className="border border-border/30 px-2 py-1 text-text-tertiary">{children}</td>,
                      ul: ({ children }) => <ul className="list-disc list-inside my-1 space-y-0.5 text-text-secondary">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside my-1 space-y-0.5 text-text-secondary">{children}</ol>,
                      li: ({ children }) => <li className="text-text-secondary">{children}</li>,
                      hr: () => <hr className="my-3 border-border/30" />,
                      blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/30 pl-3 my-2 text-text-secondary italic">{children}</blockquote>,
                      strong: ({ children }) => <strong className="font-semibold text-text-primary">{children}</strong>,
                      pre: ({ children }) => (
                        <pre className="overflow-x-auto max-w-full text-xs bg-black/5 rounded p-2 my-2">{children}</pre>
                      ),
                      code: ({ children }) => (
                        <code className="text-xs bg-black/5 rounded px-1 py-0.5">{children}</code>
                      )
                    }}
                  >
                    {cleanJsonFromContent(streamingContent)}
                  </ReactMarkdown>
                </div>
                <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />
              </div>
            </div>
          )}

          {/* Thinking Indicator */}
          {isTyping && !streamingContent && (
            <div className="flex justify-start">
              <div className="bg-elevated border border-border rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex items-center gap-2 text-text-tertiary text-sm">
                  <Loader2 size={14} className="animate-spin" />
                  <span>{thinkingStatus}</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-surface w-full">
        <div className="relative w-full">
          <div className="flex flex-wrap gap-2 mb-3 w-full min-w-0">
            {quickActions.map((action) => (
              <Button
                key={action.label}
                variant="outline"
                size="sm"
                onClick={() => handleQuickAction(action.prompt)}
                className="text-xs h-7 gap-1 flex-1 min-w-[80px]"
                disabled={isTyping}
              >
                {action.icon}
                {action.label}
              </Button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入指令或问题..."
              className="flex-1 h-10 bg-background"
              disabled={isTyping}
            />
            {isTyping ? (
              <Button
                onClick={handleStopGenerating}
                className="h-10 w-10 p-0 bg-red-500 hover:bg-red-600 text-white"
                title="停止生成"
              >
                <Square size={16} />
              </Button>
            ) : (
              <Button
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim()}
                className="btn-primary h-10 w-10 p-0"
              >
                <Send size={16} />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Reset Confirmation Dialog */}
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

      {/* AI Reader Dialog */}
      {readerContent && (
        <AIReaderDialog
          open={!!readerContent}
          onOpenChange={(open) => !open && setReaderContent(null)}
          content={readerContent}
        />
      )}
    </div>
  );
}
