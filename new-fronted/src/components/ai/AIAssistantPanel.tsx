import { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, Send, Sparkles, RotateCcw, Loader2 } from 'lucide-react';
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { chatService, type Message } from '@/api/services/chat';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ActionBlockRenderer } from './ActionBlockRenderer';
import { cleanJsonFromContent } from '@/lib/ai-chat-helper';
import { useAIChatInit } from '@/hooks/useAIChatInit';

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
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
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
    isInitialized,
    threadId,
    initChat,
    resetChat,
  } = useAIChatInit({
    projectId,
    onError: (error) => {
      console.error('[AIAssistantPanel] Init error:', error);
    }
  });

  // 合并 loading 状态
  const isTyping = isInitLoading || !!abortControllerRef.current;

  // 同步 threadId 到本地状态
  useEffect(() => {
    setCurrentThreadId(threadId);
  }, [threadId]);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

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
              setMessages(prev => [...prev, newMessage]);
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
    } else if (action === 'reset_genre') {
      displayLabel = '🔙 重新选择赛道';
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
            console.log('[AIAssistantPanel] Action complete, content length:', accumulatedContent.length);
            if (accumulatedContent) {
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

  const handleResetSession = () => {
    setShowResetDialog(true);
  };

  const confirmResetSession = async () => {
    const effectiveProjectId = currentProject?.id || chatService.getTempProjectId();

    if (abortControllerRef.current) {
      abortControllerRef.current();
      abortControllerRef.current = null;
    }

    setStreamingContent('');
    setShowResetDialog(false);
    addToast({ type: 'success', message: '会话已重置' });

    // 使用 resetChat 强制触发冷启动
    if (effectiveProjectId) {
      await resetChat(effectiveProjectId);
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
      <ScrollArea className="flex-1 min-h-0 px-4" ref={scrollRef}>
        <div className="py-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[90%] rounded-2xl px-4 py-3 ${message.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-br-md'
                  : 'bg-elevated border border-border rounded-bl-md'
                  }`}
              >
                {message.role === 'user' ? (
                  <p className="text-sm whitespace-pre-wrap">{cleanJsonFromContent(message.content)}</p>
                ) : (
                  <div className="prose prose-sm prose-invert w-full text-sm break-words whitespace-pre-wrap overflow-hidden [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:pl-4 [&>ol]:list-decimal [&>ol]:pl-4 [&>code]:bg-background [&>code]:px-1 [&>code]:rounded [&>pre]:overflow-x-auto [&>pre]:max-w-full [&_pre]:whitespace-pre-wrap [&_pre]:break-words [&_code]:break-all">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {cleanJsonFromContent(message.content)}
                    </ReactMarkdown>
                  </div>
                )}

                {message.ui_interaction && (
                  <div className="mt-4 pt-3 border-t border-border/50">
                    <ActionBlockRenderer block={message.ui_interaction} onActionClick={handleActionClick} />
                  </div>
                )}

                <p className={`text-xs mt-1.5 ${message.role === 'user' ? 'text-primary-foreground/60' : 'text-text-tertiary'}`}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* Streaming Content */}
          {streamingContent && (
            <div className="flex justify-start">
              <div className="bg-elevated border border-border rounded-2xl rounded-bl-md px-4 py-3 max-w-[90%]">
                <div className="prose prose-sm prose-invert w-full text-sm break-words whitespace-pre-wrap overflow-hidden [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:list-disc [&>ul]:pl-4 [&>ol]:list-decimal [&>ol]:pl-4 [&>pre]:overflow-x-auto [&>pre]:max-w-full [&_pre]:whitespace-pre-wrap [&_pre]:break-words [&_code]:break-all">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
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
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-surface">
        <div className="relative">
          <div className="flex flex-wrap gap-2 mb-3">
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
            <Button
              onClick={() => handleSendMessage()}
              disabled={!inputValue.trim() || isTyping}
              className="btn-primary h-10 w-10 p-0"
            >
              <Send size={16} />
            </Button>
          </div>
        </div>
      </div>

      {/* Reset Confirmation Dialog */}
      <AlertDialog open={showResetDialog} onOpenChange={setShowResetDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认重置会话？</AlertDialogTitle>
            <AlertDialogDescription>
              这将清空当前所有对话记录，并重新开始一个新的对话。此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={confirmResetSession}>确认重置</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
