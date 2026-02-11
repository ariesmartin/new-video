import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Bot, 
  X, 
  Send, 
  Sparkles, 
  Wand2, 
  FileText, 
  Image,
  Maximize2,
  Minimize2,
  Command
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface ActionButton {
  label: string;
  action: string;
  payload?: Record<string, unknown>;
  style?: 'primary' | 'secondary' | 'danger' | 'ghost';
  icon?: string;
  disabled?: boolean;
  disabled_reason?: string;
}

interface UIInteractionBlock {
  block_type: 'action_group' | 'selection' | 'confirmation' | 'input' | 'form';
  title?: string;
  description?: string;
  buttons?: ActionButton[];
  data?: Record<string, unknown>;
  dismissible?: boolean;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  actions?: string[];
  ui_interaction?: UIInteractionBlock;
  timestamp: Date;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  prompt: string;
}

const quickActions: QuickAction[] = [
  { id: 'continue', label: '续写', icon: <FileText size={14} />, prompt: '续写下文' },
  { id: 'expand', label: '扩写', icon: <Sparkles size={14} />, prompt: '扩写选中片段' },
  { id: 'polish', label: '润色', icon: <Wand2 size={14} />, prompt: '润色优化' },
  { id: 'storyboard', label: '生成分镜', icon: <Image size={14} />, prompt: '为当前场景生成分镜' },
];

import { chatService } from '@/api/services/chat';
import { useAppStore } from '@/hooks/useStore';
import { useAIChatInit } from '@/hooks/useAIChatInit';

// 保持对 chatService 的引用以便未来使用
void chatService;

const iconMap: Record<string, React.ReactNode> = {
  'Play': <span className="mr-1">▶</span>,
  'FileText': <span className="mr-1">📄</span>,
  'Image': <span className="mr-1">🖼</span>,
  'Users': <span className="mr-1">👥</span>,
  'Building': <span className="mr-1">🏙</span>,
  'Crown': <span className="mr-1">👑</span>,
  'History': <span className="mr-1">📜</span>,
  'Rocket': <span className="mr-1">🚀</span>,
  'Shuffle': <span className="mr-1">🎲</span>,
};

export function AIAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, _setIsLoading] = useState(false);
  const [contentStatus, _setContentStatus] = useState({
    hasNovelContent: false,
    hasScript: false,
    hasStoryboard: false,
    hasAnyContent: false,
  });
  const scrollRef = useRef<HTMLDivElement>(null);
  const resizeRef = useRef<HTMLDivElement>(null);
  const { currentProject } = useAppStore();
  
  const [dimensions, setDimensions] = useState({
    width: 400,
    height: 500,
    minWidth: 320,
    minHeight: 400,
    maxWidth: 800,
    maxHeight: 800
  });

  const [isResizing, setIsResizing] = useState(false);

  // 使用新的 Hook 处理初始化 - 后端决定返回历史还是冷启动
  const {
    messages: initMessages,
    isLoading: _isInitLoading,
    isInitialized,
    initChat,
  } = useAIChatInit({
    projectId: currentProject?.id,
    onError: (error) => {
      console.error('[AIAssistant] Init error:', error);
    }
  });

  // 当组件打开且有初始化消息时，设置到本地状态
  useEffect(() => {
    if (isOpen && isInitialized && initMessages.length > 0 && messages.length === 0) {
      // 转换消息格式
      const convertedMessages: Message[] = initMessages.map(msg => ({
        id: msg.id,
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        ui_interaction: msg.ui_interaction,
        timestamp: msg.timestamp,
      }));
      setMessages(convertedMessages);
    }
  }, [isOpen, isInitialized, initMessages, messages.length]);

  // 当打开聊天窗口时，触发初始化
  useEffect(() => {
    if (isOpen && !isInitialized && currentProject?.id) {
      initChat(currentProject.id);
    }
  }, [isOpen, isInitialized, currentProject?.id, initChat]);

  // 处理功能入口按钮点击
  const handleActionButton = (button: ActionButton) => {
    // 检查按钮是否禁用
    if (button.disabled) {
      return;
    }

    // 构建用户消息
    let userContent = '';
    switch (button.action) {
      case 'start_creation':
        userContent = '我想开始创作一部短剧';
        break;
      case 'adapt_script':
        userContent = '将当前小说转换为剧本';
        break;
      case 'create_storyboard':
        userContent = '为当前剧本生成分镜';
        break;
      case 'inspect_assets':
        userContent = '提取当前内容的所有资产';
        break;
      case 'select_genre':
        const genre = button.payload?.genre as string;
        userContent = `我想创作一部${genre}题材的短剧`;
        break;
      case 'random_plan':
        userContent = '请为我生成一个AI随机方案';
        break;
      default:
        userContent = button.label;
    }

    // 添加用户消息
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userContent,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsExpanded(true);
    setIsTyping(true);

    // TODO: 调用后端 API 发送消息
    setTimeout(() => {
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: `收到！你选择了：${button.label}\n\n正在为你处理...`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1000);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = Math.max(
        dimensions.minWidth,
        Math.min(dimensions.maxWidth, window.innerWidth - e.clientX + 20)
      );
      const newHeight = Math.max(
        dimensions.minHeight,
        Math.min(dimensions.maxHeight, window.innerHeight - e.clientY + 20)
      );
      
      setDimensions(prev => ({ ...prev, width: newWidth, height: newHeight }));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, dimensions.minWidth, dimensions.maxWidth, dimensions.minHeight, dimensions.maxHeight]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    setIsExpanded(true);

    setTimeout(() => {
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: `我收到了你的消息："${inputValue}"。\n\n这是一个示例回复。在实际应用中，这里会调用后端 API 获取 AI 的回复内容。`,
        actions: ['应用修改', '继续对话', '换一个方案'],
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleQuickAction = (action: QuickAction) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: action.prompt,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsExpanded(true);
    setIsTyping(true);

    setTimeout(() => {
      const responses: Record<string, string> = {
        continue: '我已经为你续写了下文：\n\n林恩深吸一口气，推开了那扇沉重的门。门后是一片漆黑，只有远处微弱的红光在闪烁...',
        expand: '扩写后的内容：\n\n原本简短的动作描述被扩展成了详细的场景描写，增加了环境氛围和人物心理活动。',
        polish: '润色后的版本：\n\n原文的表达已经优化，使用了更加生动的词汇和流畅的句式。',
        storyboard: '已为你生成了 3 个分镜：\n\n1. 全景 - 展示场景全貌\n2. 中景 - 聚焦主角动作\n3. 特写 - 强调表情细节',
      };

      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: responses[action.id] || '已处理你的请求。',
        actions: ['✓ 应用', '✎ 自定义', '↻ 重试'],
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-[100]">
        <Button
          onClick={() => setIsOpen(true)}
          className="w-14 h-14 rounded-full btn-primary shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110"
        >
          <Bot size={24} />
        </Button>
      </div>
    );
  }

  const currentWidth = isExpanded ? dimensions.width : 400;
  const currentHeight = isExpanded ? dimensions.height : 320;

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end gap-3">
      <div 
        className="bg-surface border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        style={{
          width: currentWidth,
          height: currentHeight,
          transition: isResizing ? 'none' : 'all 0.3s ease'
        }}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-gradient-to-r from-primary/10 to-transparent shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <Bot size={18} className="text-primary-foreground" />
            </div>
            <div>
              <p className="font-medium text-sm">AI 创作助手</p>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs text-text-tertiary">在线</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-8 w-8 p-0"
            >
              {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
              className="h-8 w-8 p-0"
            >
              <X size={18} />
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1 overflow-auto" ref={scrollRef}>
          <div className="p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 min-w-0 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground rounded-br-md'
                      : 'bg-background border border-border rounded-bl-md'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap break-words min-w-0">{message.content}</p>
                  
                  {message.ui_interaction && message.role === 'assistant' && (
                    <div className="mt-4 space-y-3 min-w-0">
                      {message.ui_interaction.title && (
                        <p className="text-sm font-medium text-text-secondary">{message.ui_interaction.title}</p>
                      )}
                      
                      {message.ui_interaction.buttons && message.ui_interaction.buttons.length > 0 && (
                        <div className="flex flex-wrap gap-2 min-w-0">
                          {message.ui_interaction.buttons.map((button, idx) => {
                            const isDisabled = button.disabled || 
                              (button.action === 'adapt_script' && !contentStatus.hasNovelContent) ||
                              (button.action === 'create_storyboard' && !contentStatus.hasScript) ||
                              (button.action === 'inspect_assets' && !contentStatus.hasAnyContent);
                            
                            return (
                              <Button
                                key={idx}
                                variant={button.style === 'primary' ? 'default' : 'outline'}
                                size="sm"
                                disabled={isDisabled}
                                onClick={() => handleActionButton(button)}
                                className="text-xs h-8 gap-1 break-words whitespace-normal"
                              >
                                {button.icon && iconMap[button.icon]}
                                {button.label}
                              </Button>
                            );
                          })}
                        </div>
                      )}
                      

                    </div>
                  )}
                  
                  <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-primary-foreground/70' : 'text-text-tertiary'}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-background border border-border rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center gap-2 text-sm text-text-secondary">
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                    <span className="ml-2">正在初始化...</span>
                  </div>
                </div>
              </div>
            )}
            
            {isTyping && !isLoading && (
              <div className="flex justify-start">
                <div className="bg-background border border-border rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {!isExpanded && (
          <div className="px-4 py-2 border-t border-border shrink-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-text-tertiary shrink-0">快捷:</span>
              {quickActions.slice(0, 3).map((action) => (
                <Button
                  key={action.id}
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction(action)}
                  className="text-xs h-7 gap-1"
                >
                  {action.icon}
                  {action.label}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div className="p-4 border-t border-border bg-surface/50 shrink-0">
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs shrink-0">
              <Command size={12} className="mr-1" />
              项目
            </Badge>
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={messages.length === 0 && !isLoading ? "告诉我你想创作什么类型的短剧..." : "输入指令或问题..."}
              className="flex-1 h-10"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="btn-primary h-10 w-10 p-0 shrink-0"
            >
              <Send size={18} />
            </Button>
          </div>
        </div>

        {isExpanded && (
          <div
            ref={resizeRef}
            onMouseDown={handleResizeStart}
            className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize z-10"
            style={{
              background: 'linear-gradient(135deg, transparent 50%, hsl(var(--border)) 50%)',
              borderBottomRightRadius: '16px'
            }}
          />
        )}
      </div>
    </div>
  );
}
