/**
 * Server-Driven UI (SDUI) 类型定义
 *
 * 用于 AI 返回的可交互按钮和交互块
 */

// 操作按钮类型
export interface ActionButton {
    label: string;
    action: string;
    payload?: Record<string, unknown>;
    style?: 'primary' | 'secondary' | 'danger' | 'ghost';
    icon?: string;
    disabled?: boolean;
    disabled_reason?: string;
}

// 表单字段类型
export interface FormField {
    id: string;
    label: string;
    type: 'number' | 'text' | 'select' | 'textarea';
    placeholder?: string;
    default?: unknown;
    min?: number;
    max?: number;
    options?: { value: string | number; label: string }[];
}

// UI 交互块类型
export interface UIInteractionBlock {
    block_type: 'action_group' | 'selection' | 'confirmation' | 'input' | 'form';
    title?: string;
    description?: string;
    buttons?: ActionButton[];
    form_fields?: FormField[];
    data?: Record<string, unknown>;
    dismissible?: boolean;
    timeout_seconds?: number;
}
