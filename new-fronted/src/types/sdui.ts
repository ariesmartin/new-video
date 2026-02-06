/**
 * Server-Driven UI (SDUI) 类型定义
 * 
 * 用于 AI 返回的可交互按钮和交互块
 */

// 操作按钮类型
export interface ActionButton {
    label: string;
    action: string; // 命令 ID, 如 "rewrite_scene"
    payload?: Record<string, unknown>; // 命令参数
    style?: 'primary' | 'secondary' | 'danger' | 'ghost';
    icon?: string; // Lucide 图标名称
    disabled?: boolean;
    disabled_reason?: string;
}

// UI 交互块类型
export interface UIInteractionBlock {
    block_type: 'action_group' | 'selection' | 'confirmation' | 'input';
    title?: string;
    description?: string;
    buttons: ActionButton[];
    data?: Record<string, unknown>;
    dismissible?: boolean;
    timeout_seconds?: number;
}
