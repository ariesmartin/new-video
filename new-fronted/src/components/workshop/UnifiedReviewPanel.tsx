import { useState } from 'react';
import {
  FileText,
  Play,
  Sparkles,
  ChevronUp,
  ChevronDown,
  Brain,
  Activity,
  User,
  Zap,
  Globe,
  Anchor,
  CheckCircle,
  Lightbulb,
  AlertTriangle,
  RefreshCw,
  Eye,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { GlobalReview, ChapterReview, ReviewCategory, Issue, IssueSeverity } from '@/types/review';

// 诊断项（融合后的统一格式）
export interface DiagnosticItem {
  id: string;
  score: number;
  quote: string;
  suggestion: string;
  category: ReviewCategory;
  severity?: IssueSeverity;
  originalText?: string;
  suggestedText?: string;
  location?: {
    line?: number;
    column?: number;
  };
}

interface UnifiedReviewPanelProps {
  // 数据
  review: GlobalReview | ChapterReview | null;
  diagnostics?: DiagnosticItem[];
  chapterTitle?: string;
  
  // 状态
  isLoading?: boolean;
  
  // 回调
  onReReview?: () => void;
  onApplySuggestion?: (suggestionId: string) => void;
  onIgnoreIssue?: (issueId: string) => void;
  onViewOriginal?: (location: { line?: number; column?: number }) => void;
  onViewDetails?: (category: ReviewCategory) => void;
  
  // 样式
  className?: string;
}

// 分类配置
const categoryConfig: Record<ReviewCategory, { label: string; color: string; icon: React.ReactNode }> = {
  logic: { label: '逻辑/设定', color: '#3B82F6', icon: <Brain className="w-4 h-4" /> },
  pacing: { label: '节奏/张力', color: '#10B981', icon: <Activity className="w-4 h-4" /> },
  character: { label: '人设/角色', color: '#F59E0B', icon: <User className="w-4 h-4" /> },
  conflict: { label: '冲突/事件', color: '#EF4444', icon: <Zap className="w-4 h-4" /> },
  world: { label: '世界/规则', color: '#8B5CF6', icon: <Globe className="w-4 h-4" /> },
  hook: { label: '钩子/悬念', color: '#EC4899', icon: <Anchor className="w-4 h-4" /> },
};

// 严重级别配置
const severityConfig: Record<IssueSeverity, { label: string; color: string; bgColor: string }> = {
  low: { label: '轻微', color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
  medium: { label: '需改进', color: 'text-orange-600', bgColor: 'bg-orange-50' },
  high: { label: '严重', color: 'text-red-600', bgColor: 'bg-red-50' },
};

// 获取评分颜色
function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-500';
  if (score >= 60) return 'text-yellow-500';
  return 'text-red-500';
}

// 获取进度条颜色
function getProgressColor(score: number): string {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-yellow-500';
  return 'bg-red-500';
}

// 张力曲线组件
function TensionCurve({ data }: { data: number[] }) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  return (
    <div className="h-20 flex items-end gap-0.5 px-2">
      {data.map((value, index) => {
        const height = ((value - min) / range) * 100;
        const isPeak = value > (max + min) / 2 + range * 0.2;
        return (
          <div
            key={index}
            className={cn(
              "flex-1 rounded-t transition-all hover:opacity-80 cursor-pointer",
              isPeak ? "bg-primary" : "bg-primary/40"
            )}
            style={{ height: `${Math.max(height, 5)}%` }}
            title={`张力值: ${value.toFixed(1)}`}
          />
        );
      })}
    </div>
  );
}

// 分类评分项
function CategoryScoreItem({
  category,
  score,
  issues,
  onClick,
}: {
  category: ReviewCategory;
  score: number;
  issues: number;
  onClick?: () => void;
}) {
  const config = categoryConfig[category];

  return (
    <div
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 p-2 rounded-lg hover:bg-accent/50 cursor-pointer transition-colors",
        onClick && "cursor-pointer"
      )}
    >
      <div
        className="w-2 h-12 rounded-full"
        style={{ backgroundColor: config.color }}
      />
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">{config.label}</span>
          <span className={cn("text-sm font-bold", getScoreColor(score))}>
            {score}
          </span>
        </div>
        <div className="mt-1">
          <div className="h-1.5 w-full bg-primary/20 rounded-full overflow-hidden">
            <div
              className={cn("h-full transition-all", getProgressColor(score))}
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
        {issues > 0 && (
          <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
            <AlertTriangle className="w-3 h-3" />
            <span>{issues} 个问题</span>
          </div>
        )}
      </div>
    </div>
  );
}

// 诊断卡片组件
function DiagnosticCard({
  item,
  onApply,
  onIgnore,
  onView,
}: {
  item: DiagnosticItem;
  onApply?: () => void;
  onIgnore?: () => void;
  onView?: () => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const severity = item.severity || 'medium';
  const severityStyle = severityConfig[severity];
  const categoryStyle = categoryConfig[item.category];

  return (
    <div
      className={cn(
        "border rounded-lg overflow-hidden transition-all",
        isExpanded ? "shadow-sm" : ""
      )}
    >
      {/* 问题头部 */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "flex items-start gap-3 p-3 cursor-pointer hover:bg-accent/30 transition-colors",
          severityStyle.bgColor
        )}
      >
        {/* 分数 */}
        <div
          className={cn(
            'flex-shrink-0 w-8 h-8 rounded flex items-center justify-center font-bold text-sm',
            item.score >= 80 ? 'text-green-500 bg-green-500/10' :
            item.score >= 60 ? 'text-yellow-500 bg-yellow-500/10' : 'text-red-500 bg-red-500/10'
          )}
        >
          {item.score}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs" style={{ borderColor: categoryStyle.color, color: categoryStyle.color }}>
              {categoryStyle.label}
            </Badge>
            <Badge variant="outline" className={cn("text-xs", severityStyle.color)}>
              {severityStyle.label}
            </Badge>
            {item.location?.line && (
              <span className="text-xs text-muted-foreground">
                第{item.location.line}行
              </span>
            )}
          </div>
          <p className="text-sm mt-1 font-medium truncate">{item.suggestion}</p>
        </div>

        <ChevronDown
          className={cn(
            "w-5 h-5 text-muted-foreground transition-transform flex-shrink-0",
            isExpanded && "rotate-180"
          )}
        />
      </div>

      {/* 问题详情 */}
      {isExpanded && (
        <div className="p-3 bg-card border-t">
          {/* 引用原文 */}
          {item.quote && (
            <div className="mb-3">
              <h5 className="text-xs font-medium text-muted-foreground mb-1">引用</h5>
              <span className="text-xs text-text-tertiary bg-surface px-2 py-1 rounded block">
                "{item.quote}"
              </span>
            </div>
          )}

          {/* 详细建议 */}
          <div className="mb-3">
            <h5 className="text-xs font-medium text-muted-foreground mb-1">详细建议</h5>
            <p className="text-sm">{item.suggestion}</p>
          </div>

          {/* 原文与建议对比 */}
          {(item.originalText || item.suggestedText) && (
            <div className="grid grid-cols-2 gap-2 mb-3">
              {item.originalText && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-2">
                  <h5 className="text-xs font-medium text-red-700 mb-1">原文</h5>
                  <p className="text-sm text-red-800 line-through">{item.originalText}</p>
                </div>
              )}
              {item.suggestedText && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-2">
                  <h5 className="text-xs font-medium text-green-700 mb-1">建议</h5>
                  <p className="text-sm text-green-800">{item.suggestedText}</p>
                </div>
              )}
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center gap-2">
            {onApply && (
              <Button size="sm" onClick={onApply} className="flex-1">
                <CheckCircle className="w-4 h-4 mr-1" />
                应用修改
              </Button>
            )}
            {onView && (
              <Button size="sm" variant="outline" onClick={onView}>
                <Eye className="w-4 h-4 mr-1" />
                查看原文
              </Button>
            )}
            {onIgnore && (
              <Button size="sm" variant="ghost" onClick={onIgnore}>
                <X className="w-4 h-4 mr-1" />
                忽略
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function UnifiedReviewPanel({
  review,
  diagnostics = [],
  chapterTitle,
  isLoading,
  onReReview,
  onApplySuggestion,
  onIgnoreIssue,
  onViewOriginal,
  onViewDetails,
  className,
}: UnifiedReviewPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeView, setActiveView] = useState<'doctor' | 'tension'>('doctor');

  const overallScore = review
    ? 'overallScore' in review
      ? review.overallScore
      : review.score
    : 0;

  const totalIssues = review
    ? 'categories' in review
      ? Object.values(review.categories).reduce((sum, cat) => sum + cat.issues.length, 0)
      : (review as ChapterReview).issues?.length || 0
    : 0;

  const tensionCurve = review?.tensionCurve || [];
  const categories = review?.categories || null;
  const recommendations = (review as GlobalReview)?.recommendations || [];
  const title = chapterTitle || ('overallScore' in (review || {}) ? '全局报告' : '当前章节');

  const allDiagnostics: DiagnosticItem[] = diagnostics.length > 0
    ? diagnostics
    : review && 'issues' in review && review.issues
      ? review.issues.map((issue: Issue) => ({
          id: issue.id,
          score: issue.severity === 'high' ? 50 : issue.severity === 'medium' ? 75 : 90,
          quote: issue.originalText || '',
          suggestion: issue.suggestion,
          category: issue.category,
          severity: issue.severity,
          originalText: issue.originalText,
          suggestedText: issue.suggestedText,
          location: issue.location,
        }))
      : [];

  const handleDoctorClick = () => {
    setActiveView('doctor');
    setIsExpanded(true);
  };

  const handleTensionClick = () => {
    setActiveView('tension');
    setIsExpanded(true);
  };

  if (!review) {
    return (
      <div className={cn('border-t border-border bg-surface', className)}>
        <div className="flex items-center justify-between px-4 h-12">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <FileText size={16} className="text-primary" />
              <span>剧本医生</span>
              <span className="text-muted-foreground">--</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <Play size={16} className="text-accent" />
              <span>剧情张力曲线</span>
            </div>
          </div>
          <button
            onClick={onReReview}
            className="flex items-center gap-2 text-sm text-text-secondary hover:text-primary transition-colors"
          >
            <Sparkles size={14} />
            <span>开始诊断</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'border-t border-border bg-surface transition-all duration-300 flex flex-col',
        isExpanded ? 'h-80' : 'h-12',
        className
      )}
    >
      {/* 头部工具栏 */}
      <div className="flex items-center justify-between px-4 h-12 shrink-0">
        <div className="flex items-center gap-6">
          {/* 剧本医生评分 */}
          <button
            onClick={handleDoctorClick}
            className={cn(
              "flex items-center gap-2 text-sm transition-colors",
              activeView === 'doctor' && isExpanded
                ? "text-text-primary font-medium"
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            <FileText size={16} className="text-primary" />
            <span>剧本医生</span>
            <span
              className={cn(
                'font-bold',
                overallScore >= 80
                  ? 'text-green-500'
                  : overallScore >= 60
                  ? 'text-yellow-500'
                  : 'text-red-500'
              )}
            >
              {overallScore}
            </span>
            {totalIssues > 0 && (
              <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded-full">
                {totalIssues}
              </span>
            )}
          </button>

          {/* 张力曲线 */}
          <button
            onClick={handleTensionClick}
            className={cn(
              "flex items-center gap-2 text-sm transition-colors",
              activeView === 'tension' && isExpanded
                ? "text-text-primary font-medium"
                : "text-text-secondary hover:text-text-primary"
            )}
          >
            <Play size={16} className="text-accent" />
            <span>剧情张力曲线</span>
          </button>
        </div>

        <div className="flex items-center gap-4">
          {/* 重新诊断 */}
          <button
            onClick={onReReview}
            disabled={isLoading}
            className="flex items-center gap-2 text-sm text-text-secondary hover:text-primary transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            <span>重新诊断</span>
          </button>

          {/* 展开/收起 */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded hover:bg-elevated text-text-secondary transition-colors"
          >
            {isExpanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </button>
        </div>
      </div>

      {/* 展开内容 */}
      {isExpanded && (
        <div className="flex-1 overflow-hidden flex flex-col">
          {/* 内容区域 */}
          <ScrollArea className="flex-1">
            <div className="p-4">
              {activeView === 'doctor' ? (
                <div className="space-y-4">
                  {/* 标题和总体评价 */}
                  <div className="flex items-start gap-4">
                    <div
                      className={cn(
                        'w-16 h-16 rounded-xl flex items-center justify-center font-bold text-2xl shrink-0',
                        overallScore >= 80
                          ? 'bg-green-100 text-green-700'
                          : overallScore >= 60
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      )}
                    >
                      {overallScore}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-lg">剧本医生 - {title}</h3>
                      {(review as GlobalReview)?.summary && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {(review as GlobalReview).summary}
                        </p>
                      )}
                      {totalIssues > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          <AlertTriangle className="w-4 h-4 text-amber-500" />
                          <span className="text-sm text-amber-700">
                            发现 {totalIssues} 个问题待处理
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 分类评分 */}
                  {categories && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">分类评分</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {(Object.keys(categories) as ReviewCategory[]).map((category) => (
                          <CategoryScoreItem
                            key={category}
                            category={category}
                            score={categories[category].score}
                            issues={categories[category].issues.length}
                            onClick={() => onViewDetails?.(category)}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 改进建议 */}
                  {recommendations.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4 text-amber-500" />
                        改进建议
                      </h4>
                      <ul className="space-y-1">
                        {recommendations.map((rec, index) => (
                          <li
                            key={index}
                            className="flex items-start gap-2 text-sm text-muted-foreground"
                          >
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 问题列表 */}
                  {allDiagnostics.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        问题列表 ({allDiagnostics.length})
                      </h4>
                      <div className="space-y-2">
                        {allDiagnostics.map((item) => (
                          <DiagnosticCard
                            key={item.id}
                            item={item}
                            onApply={onApplySuggestion ? () => onApplySuggestion(item.id) : undefined}
                            onIgnore={onIgnoreIssue ? () => onIgnoreIssue(item.id) : undefined}
                            onView={onViewOriginal && item.location ? () => onViewOriginal(item.location!) : undefined}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {allDiagnostics.length === 0 && totalIssues === 0 && (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-3">
                        <CheckCircle className="w-8 h-8 text-green-600" />
                      </div>
                      <h4 className="font-medium text-green-700">审阅通过</h4>
                      <p className="text-sm text-muted-foreground mt-1">
                        没有发现明显问题
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                /* 张力曲线视图 */
                <div className="space-y-4">
                  {/* 标题 */}
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'w-12 h-12 rounded-lg flex items-center justify-center shrink-0',
                        overallScore >= 80
                          ? 'bg-green-100 text-green-700'
                          : overallScore >= 60
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      )}
                    >
                      <Play size={20} className="text-accent" />
                    </div>
                    <div>
                      <h3 className="font-medium text-lg">剧情张力曲线 - {title}</h3>
                      <p className="text-sm text-muted-foreground">
                        共 {tensionCurve.length} 个张力点
                      </p>
                    </div>
                  </div>

                  {/* 张力曲线图表 */}
                  {tensionCurve.length > 0 && (
                    <div className="bg-muted/30 rounded-lg p-3">
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Play size={14} className="text-accent" />
                        剧情张力曲线
                      </h4>
                      <TensionCurve data={tensionCurve} />
                    </div>
                  )}

                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}

export default UnifiedReviewPanel;
