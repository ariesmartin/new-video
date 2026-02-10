/**
 * 审阅数据结构
 */

// 审阅分类
export type ReviewCategory = 'logic' | 'pacing' | 'character' | 'conflict' | 'world' | 'hook';

// 问题严重级别
export type IssueSeverity = 'low' | 'medium' | 'high';

// 问题
export interface Issue {
  id: string;
  category: ReviewCategory;
  severity: IssueSeverity;
  location?: {
    line?: number;
    column?: number;
    start?: number;
    end?: number;
  };
  description: string;
  suggestion: string;
  originalText?: string;
  suggestedText?: string;
}

// 分类评分
export interface CategoryScore {
  score: number;
  weight: number;
  issues: Issue[];
}

// 全局审阅报告（大纲用）
export interface GlobalReview {
  generatedAt: string;
  overallScore: number;
  categories: {
    logic: CategoryScore;
    pacing: CategoryScore;
    character: CategoryScore;
    conflict: CategoryScore;
    world: CategoryScore;
    hook: CategoryScore;
  };
  tensionCurve: number[];  // 80个点的张力值
  chapterReviews: {
    [chapterId: string]: {
      score: number;
      issues: Issue[];
      status: 'passed' | 'warning' | 'error';
    };
  };
  summary: string;
  recommendations: string[];
}

// 单章审阅（小说用）
export interface ChapterReview {
  chapterId: string;
  reviewedAt: string;
  score: number;
  categories: {
    logic: CategoryScore;
    pacing: CategoryScore;
    character: CategoryScore;
    conflict: CategoryScore;
    world: CategoryScore;
    hook: CategoryScore;
  };
  issues: Issue[];
  tensionCurve: number[];
  summary: string;
}

// 修改建议
export interface Suggestion {
  id: string;
  issueId: string;
  type: 'replace' | 'delete' | 'insert';
  originalText: string;
  suggestedText: string;
  context: string;
}

// 审阅请求
export interface ReviewRequest {
  projectId: string;
  chapterId?: string;  // 不传则审阅全部（大纲模式）
  content?: string;    // 小说章节内容
}

// 审阅响应
export interface ReviewResponse {
  success: boolean;
  data?: GlobalReview | ChapterReview;
  error?: string;
}

// 应用建议请求
export interface ApplySuggestionRequest {
  projectId: string;
  chapterId: string;
  suggestionId: string;
}

// 张力曲线响应
export interface TensionCurveResponse {
  data: number[];
  labels?: string[];
}

// 分类标签映射
export const categoryLabels: Record<ReviewCategory, { label: string; icon: string; color: string }> = {
  logic: { label: '逻辑/设定', icon: 'Brain', color: '#3B82F6' },
  pacing: { label: '节奏/张力', icon: 'Activity', color: '#10B981' },
  character: { label: '人设/角色', icon: 'User', color: '#F59E0B' },
  conflict: { label: '冲突/事件', icon: 'Zap', color: '#EF4444' },
  world: { label: '世界/规则', icon: 'Globe', color: '#8B5CF6' },
  hook: { label: '钩子/悬念', icon: 'Anchor', color: '#EC4899' },
};

// 严重级别标签映射
export const severityLabels: Record<IssueSeverity, { label: string; color: string }> = {
  low: { label: '轻微', color: '#FBBF24' },
  medium: { label: '需改进', color: '#F97316' },
  high: { label: '严重', color: '#EF4444' },
};

// 状态图标映射
export const statusIcons = {
  passed: { icon: 'CheckCircle', color: '#10B981' },
  warning: { icon: 'AlertTriangle', color: '#F59E0B' },
  error: { icon: 'XCircle', color: '#EF4444' },
  pending: { icon: 'Clock', color: '#6B7280' },
};
