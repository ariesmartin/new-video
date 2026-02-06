/**
 * ActionBlockRenderer - SDUI 交互块渲染器
 * 
 * 渲染 AI 返回的可交互按钮组，实现 Server-Driven UI
 */

import { useState, useEffect } from 'react';
import * as LucideIcons from 'lucide-react';
import { X, Zap } from 'lucide-react';
import type { UIInteractionBlock } from '@/types/sdui';
import { chatService } from '@/api/services/chat';
import { useAppStore } from '@/hooks/useStore';

interface ActionBlockRendererProps {
    block: UIInteractionBlock;
    onActionClick?: (action: string, payload?: Record<string, unknown>) => void;
}

export function ActionBlockRenderer({ block, onActionClick }: ActionBlockRendererProps) {
    const [isDismissed, setIsDismissed] = useState(false);
    const [isLoading, setIsLoading] = useState<string | null>(null);
    const { currentProject, currentEpisode } = useAppStore();

    // 规范化 block 数据（处理从后端恢复时的各种格式）
    const normalizedBlock = (() => {
        if (!block) return null;

        // 如果 block 是字符串，尝试解析
        let parsedBlock = block;
        if (typeof block === 'string') {
            try {
                parsedBlock = JSON.parse(block);
            } catch {
                console.error('[ActionBlockRenderer] Failed to parse block string:', block);
                return null;
            }
        }

        // 确保 buttons 是数组
        let buttons = parsedBlock.buttons;
        if (typeof buttons === 'string') {
            try {
                buttons = JSON.parse(buttons);
            } catch {
                console.error('[ActionBlockRenderer] Failed to parse buttons string:', buttons);
                buttons = [];
            }
        }

        if (!Array.isArray(buttons) || buttons.length === 0) {
            console.warn('[ActionBlockRenderer] No valid buttons found:', { block: parsedBlock, buttons });
            return null;
        }

        return { ...parsedBlock, buttons };
    })();

    // 自动消失定时器
    useEffect(() => {
        if (normalizedBlock?.timeout_seconds && normalizedBlock.timeout_seconds > 0) {
            const timer = setTimeout(() => {
                setIsDismissed(true);
            }, normalizedBlock.timeout_seconds * 1000);
            return () => clearTimeout(timer);
        }
    }, [normalizedBlock?.timeout_seconds]);

    if (!normalizedBlock) return null;
    if (isDismissed) return null;

    // 处理按钮点击
    const handleButtonClick = async (action: string, payload?: Record<string, unknown>) => {
        if (onActionClick) {
            onActionClick(action, payload);
            return;
        }

        // 默认行为：发送 action 到后端
        setIsLoading(action);
        try {
            // 构造 action 消息发送到 chat
            const actionMessage = JSON.stringify({ action, payload });
            await chatService.streamMessage(
                actionMessage,
                {
                    onMessage: () => { },
                    onComplete: () => {
                        setIsLoading(null);
                    },
                    onError: (error) => {
                        console.error('Action error:', error);
                        setIsLoading(null);
                    },
                },
                currentProject?.id,
                currentEpisode?.id
            );
        } catch (error) {
            console.error('Failed to execute action:', error);
            setIsLoading(null);
        }
    };

    return (
        <div className="mt-3 p-3 bg-elevated/50 border border-border rounded-lg animate-in fade-in slide-in-from-bottom-2 duration-300 relative">
            {/* 关闭按钮 */}
            {normalizedBlock.dismissible !== false && (
                <button
                    onClick={() => setIsDismissed(true)}
                    className="absolute top-2 right-2 text-text-tertiary hover:text-text-secondary transition-colors"
                >
                    <X size={14} />
                </button>
            )}

            {/* 标题 */}
            {normalizedBlock.title && (
                <div className="text-sm font-medium text-text-primary mb-1 pr-6">
                    {normalizedBlock.title}
                </div>
            )}

            {/* 描述 */}
            {normalizedBlock.description && (
                <div className="text-xs text-text-tertiary mb-3">
                    {normalizedBlock.description}
                </div>
            )}

            {/* 按钮组 */}
            <div className="flex flex-wrap gap-2">
                {normalizedBlock.buttons.map((btn, idx) => {
                    // 动态获取图标组件
                    const IconComponent = btn.icon && (LucideIcons as any)[btn.icon]
                        ? (LucideIcons as any)[btn.icon]
                        : Zap;

                    // 按钮样式
                    let btnClasses = "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100";

                    switch (btn.style) {
                        case 'primary':
                            btnClasses += " bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm";
                            break;
                        case 'danger':
                            btnClasses += " bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/20";
                            break;
                        case 'ghost':
                            btnClasses += " bg-transparent text-text-secondary hover:text-text-primary hover:bg-elevated";
                            break;
                        case 'secondary':
                        default:
                            btnClasses += " bg-elevated text-text-secondary border border-border hover:bg-elevated/80 hover:text-text-primary";
                            break;
                    }

                    const isButtonLoading = isLoading === btn.action;

                    return (
                        <button
                            key={idx}
                            className={btnClasses}
                            onClick={() => handleButtonClick(btn.action, btn.payload)}
                            disabled={btn.disabled || isButtonLoading}
                        >
                            {isButtonLoading ? (
                                <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                            ) : (
                                IconComponent && <IconComponent size={14} />
                            )}
                            {btn.label}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
