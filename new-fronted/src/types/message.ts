/**
 * 消息类型定义 - 前端
 * 
 * 明确区分系统消息、用户消息和AI消息
 */

export type MessageRole = 'system' | 'user' | 'assistant';

export type MessageType = 
  // 系统消息
  | 'system_init'           // 系统初始化消息
  | 'system_internal'       // 系统内部处理消息
  // 用户消息
  | 'user_text'             // 普通文本消息
  | 'user_init'             // 用户初始化消息（如"你好，开始创作"）
  | 'user_action'           // 用户点击按钮等操作
  // AI消息
  | 'ai_welcome'            // AI欢迎消息
  | 'ai_response'           // AI普通回复
  | 'ai_status'             // AI状态更新
  | 'ai_error';             // AI错误消息

export interface MessageMetadata {
  // 消息来源信息
  checkpointId?: string;           // 关联的checkpoint ID
  nodeId?: string;                 // 生成该消息的节点ID

  // 消息类型标记
  isSystemInit?: boolean;          // 是否是系统初始化消息
  isHidden?: boolean;              // 是否对用户隐藏
  isInternal?: boolean;
  messageType?: MessageType;       // 消息类型

  // UI关联
  hasUiInteraction?: boolean;      // 是否有关联的ui_interaction
  uiInteractionId?: string;        // 关联的ui_interaction ID

  // 其他
  action?: string;                 // 用户操作类型
  timestampMs?: number;            // 精确到毫秒的时间戳
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: MessageMetadata;
  uiInteraction?: UIInteractionBlock;
}

export interface UIInteractionBlock {
  blockType: 'action_group' | 'input_form' | 'selection_list' | 'info_card';
  title: string;
  description?: string;
  buttons?: ActionButton[];
  inputs?: InputField[];
  dismissible?: boolean;
}

export interface ActionButton {
  label: string;
  action: string;
  payload?: Record<string, any>;
  style?: 'primary' | 'secondary' | 'ghost' | 'default';
  icon?: string;
}

export interface InputField {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'number';
  placeholder?: string;
  options?: { label: string; value: string }[];
  required?: boolean;
}

// ===== 消息过滤规则 =====

/** 对用户隐藏的消息类型 */
export const HIDDEN_MESSAGE_TYPES: Set<MessageType> = new Set([
  'system_init',
  'system_internal',
  'user_init',  // "你好，开始创作"等初始化消息
]);

/** 可以显示给用户的消息类型 */
export const VISIBLE_MESSAGE_TYPES: Set<MessageType> = new Set([
  'user_text',
  'user_action',
  'ai_welcome',
  'ai_response',
  'ai_status',
  'ai_error',
]);

/**
 * 判断消息是否应该显示给用户
 */
export function shouldShowToUser(message: ChatMessage): boolean {
  // 系统消息默认隐藏
  if (message.role === 'system') {
    return false;
  }
  
  // 检查元数据中的隐藏标记
  if (message.metadata?.isHidden) {
    return false;
  }

  if (message.metadata?.isInternal) {
    return false;
  }

  // 检查消息类型
  if (message.metadata?.messageType && HIDDEN_MESSAGE_TYPES.has(message.metadata.messageType)) {
    return false;
  }
  
  // 特殊处理：用户初始化消息
  if (message.role === 'user') {
    const content = message.content.toLowerCase().trim();
    const initPhrases = ['你好，开始创作', '开始创作', '你好，开始', '你好,开始创作'];
    if (initPhrases.some(phrase => content.includes(phrase.toLowerCase()))) {
      return false;
    }
  }
  
  return true;
}

/**
 * 创建系统初始化消息
 */
export function createSystemInitMessage(content: string): ChatMessage {
  return {
    id: `sys_init_${Date.now()}`,
    role: 'system',
    content,
    timestamp: new Date(),
    metadata: {
      isSystemInit: true,
      isHidden: true,
      messageType: 'system_init',
    },
  };
}

/**
 * 创建用户初始化消息（对用户隐藏）
 */
export function createUserInitMessage(content: string = '你好，开始创作'): ChatMessage {
  return {
    id: `user_init_${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date(),
    metadata: {
      isHidden: true,
      messageType: 'user_init',
    },
  };
}

/**
 * 创建AI欢迎消息
 */
export function createAIWelcomeMessage(content: string): ChatMessage {
  return {
    id: `ai_welcome_${Date.now()}`,
    role: 'assistant',
    content,
    timestamp: new Date(),
    metadata: {
      messageType: 'ai_welcome',
    },
  };
}

/**
 * 过滤消息列表，只保留对用户可见的消息
 */
export function filterVisibleMessages(messages: ChatMessage[]): ChatMessage[] {
  return messages.filter(shouldShowToUser);
}
