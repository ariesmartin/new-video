/**
 * ActionBlockRenderer - SDUI 交互块渲染器
 * 
 * 渲染 AI 返回的可交互按钮组，实现 Server-Driven UI
 */

import { useState, useEffect } from 'react';
import * as LucideIcons from 'lucide-react';
import { X, Zap } from 'lucide-react';
import type { UIInteractionBlock, FormField } from '@/types/sdui';
import { chatService } from '@/api/services/chat';
import { useAppStore } from '@/hooks/useStore';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface ActionBlockRendererProps {
    block: UIInteractionBlock;
    onActionClick?: (action: string, payload?: Record<string, unknown>) => void;
    isHistorical?: boolean;
}

export function ActionBlockRenderer({ block, onActionClick, isHistorical = false }: ActionBlockRendererProps) {
    const [isDismissed, setIsDismissed] = useState(false);
    const [isLoading, setIsLoading] = useState<string | null>(null);
    const [formValues, setFormValues] = useState<Record<string, unknown>>({});
    const { currentProject, currentEpisode } = useAppStore();

    useEffect(() => {
        if (normalizedBlock?.form_fields) {
            const defaults: Record<string, unknown> = {};
            normalizedBlock.form_fields.forEach((field: FormField) => {
                defaults[field.id] = field.default ?? '';
            });
            setFormValues(defaults);
        }
    }, [block]);

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

        // 确保 buttons 是数组（form 类型可能没有 buttons）
        let buttons = parsedBlock.buttons || [];
        if (typeof buttons === 'string') {
            try {
                buttons = JSON.parse(buttons);
            } catch {
                console.error('[ActionBlockRenderer] Failed to parse buttons string:', buttons);
                buttons = [];
            }
        }

        // 对于 form 类型，允许没有 buttons；对于其他类型，需要 buttons
        const blockType = parsedBlock.block_type;
        if (blockType !== 'form' && (!Array.isArray(buttons) || buttons.length === 0)) {
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
        <div className="mt-3 p-3 bg-elevated/50 border border-border rounded-lg animate-in fade-in slide-in-from-bottom-2 duration-300 relative w-full min-w-0">
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

            {/* 表单字段 */}
            {normalizedBlock.block_type === 'form' && normalizedBlock.form_fields && (
                <div className="space-y-3 mb-3">
                    {normalizedBlock.form_fields.map((field: FormField) => (
                        <div key={field.id} className="space-y-1">
                            <Label className="text-xs text-text-secondary">
                                {field.label}
                            </Label>
                            {field.type === 'select' && field.options ? (
                                <Select
                                    value={String(formValues[field.id] ?? '')}
                                    onValueChange={(value) => setFormValues(prev => ({ ...prev, [field.id]: value }))}
                                >
                                    <SelectTrigger className="w-full h-8 text-xs">
                                        <SelectValue placeholder={field.placeholder} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {field.options.map((opt) => (
                                            <SelectItem key={opt.value} value={String(opt.value)} className="text-xs">
                                                {opt.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            ) : field.type === 'number' ? (
                                <Input
                                    type="number"
                                    min={field.min}
                                    max={field.max}
                                    value={String(formValues[field.id] ?? '')}
                                    onChange={(e) => setFormValues(prev => ({ ...prev, [field.id]: parseInt(e.target.value) || 0 }))}
                                    placeholder={field.placeholder}
                                    className="h-8 text-xs"
                                />
                            ) : (
                                <Input
                                    type="text"
                                    value={String(formValues[field.id] ?? '')}
                                    onChange={(e) => setFormValues(prev => ({ ...prev, [field.id]: e.target.value }))}
                                    placeholder={field.placeholder}
                                    className="h-8 text-xs"
                                />
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* 按钮组 */}
            <div className="flex flex-wrap gap-2 w-full min-w-0">
                {normalizedBlock.buttons?.map((btn, idx) => {
                    const IconComponent = btn.icon && (LucideIcons as any)[btn.icon]
                        ? (LucideIcons as any)[btn.icon]
                        : Zap;

                    let btnClasses = "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100 break-all whitespace-normal text-left max-w-full overflow-hidden";

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

                    const handleClick = () => {
                        const payload = { ...btn.payload };
                        if (normalizedBlock.block_type === 'form') {
                            Object.assign(payload, formValues);
                        }
                        handleButtonClick(btn.action, payload);
                    };

                    const isButtonDisabled = btn.disabled || isButtonLoading || isHistorical;

                    return (
                        <button
                            key={idx}
                            className={btnClasses}
                            onClick={handleClick}
                            disabled={isButtonDisabled}
                            title={isHistorical ? "已完成的操作" : btn.label}
                        >
                            {isButtonLoading ? (
                                <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                            ) : (
                                IconComponent && <IconComponent size={14} />
                            )}
                            <span className="break-all whitespace-normal">{btn.label}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
