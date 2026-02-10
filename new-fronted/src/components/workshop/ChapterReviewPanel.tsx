import { useState, useCallback } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  RefreshCw, 
  CheckCircle, 
  X,
  Eye,
  Edit3,
  AlertTriangle,
  Brain,
  Activity,
  User,
  Zap,
  Globe,
  Anchor
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { ChapterReview, Issue, ReviewCategory, IssueSeverity } from '@/types/review';

interface ChapterReviewPanelProps {
  chapterId: string;
  chapterTitle?: string;
  review: ChapterReview | null;
  isLoading?: boolean;
  onReReview?: () => void;
  onApplySuggestion?: (suggestionId: string) => void;
  onIgnoreIssue?: (issueId: string) => void;
  onViewOriginal?: (location: { line?: number; column?: number }) => void;
  className?: string;
}

// 分类图标映射
const categoryIcons: Record<ReviewCategory, React.ReactNode> = {
  logic: <Brain className="w-4 h-4" />,
  pacing: <Activity className="w-4 h-4" />,
  character: <User className="w-4 h-4" />,
  conflict: <Zap className="w-4 h-4" />,
  world: <Globe className="w-4 h-4" />,
  hook: <Anchor className="w-4 h-4" />,
};

// 分类标签映射
const categoryLabels: Record<ReviewCategory, string> = {
  logic: '逻辑/设定',
  pacing: '节奏/张力',
  character: '人设/角色',
  conflict: '冲突/事件',
  world: '世界/规则',
  hook: '钩子/悬念',
};

// 严重级别映射
const severityConfig: Record<IssueSeverity, { label: string; color: string; bgColor: string }> = {
  low: { label: '轻微', color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
  medium: { label: '需改进', color: 'text-orange-600', bgColor: 'bg-orange-50' },
  high: { label: '严重', color: 'text-red-600', bgColor: 'bg-red-50' },
};

// 问题项组件
function IssueItem({
  issue,
  onApply,
  onIgnore,
  onView,
}: {
  issue: Issue;
  onApply: () => void;
  onIgnore: () => void;
  onView: () => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const severity = severityConfig[issue.severity];

  return (
    <div className={cn(
      "border rounded-lg overflow-hidden transition-all",
      isExpanded ? "shadow-sm" : ""
    )}>
      {/* 问题头部 */}
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "flex items-start gap-3 p-3 cursor-pointer hover:bg-accent/30 transition-colors",
          severity.bgColor
        )}
      >
        <div className={cn("mt-0.5", severity.color)}>
          {categoryIcons[issue.category]}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={cn("text-xs", severity.color)}>
              {categoryLabels[issue.category]}
            </Badge>
            <Badge variant="outline" className={cn("text-xs", severity.color)}>
              {severity.label}
            </Badge>
            {issue.location?.line && (
              <span className="text-xs text-muted-foreground">
                第{issue.location.line}行
              </span>
            )}
          </div>
          <p className="text-sm mt-1 font-medium truncate">{issue.description}</p>
        </div>
        <ChevronDown className={cn(
          "w-5 h-5 text-muted-foreground transition-transform",
          isExpanded && "rotate-180"
        )} />
      </div>

      {/* 问题详情 */}
      {isExpanded && (
        <div className="p-3 bg-card border-t">
          {/* 问题描述 */}
          <div className="mb-3">
            <h5 className="text-xs font-medium text-muted-foreground mb-1">问题</h5>
            <p className="text-sm">{issue.description}</p>
          </div>

          {/* 修改建议 */}
          {issue.suggestion && (
            <div className="mb-3 bg-green-50 border border-green-200 rounded-lg p-3">
              <h5 className="text-xs font-medium text-green-700 mb-1 flex items-center gap-1">
                <Edit3 className="w-3 h-3" />
                修改建议
              </h5>
              <p className="text-sm text-green-800">{issue.suggestion}</p>
            </div>
          )}

          {/* 原文与建议对比 */}
          {(issue.originalText || issue.suggestedText) && (
            <div className="grid grid-cols-2 gap-2 mb-3">
              {issue.originalText && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-2">
                  <h5 className="text-xs font-medium text-red-700 mb-1">原文</h5>
                  <p className="text-sm text-red-800 line-through">{issue.originalText}</p>
                </div>
              )}
              {issue.suggestedText && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-2">
                  <h5 className="text-xs font-medium text-green-700 mb-1">建议</h5>
                  <p className="text-sm text-green-800">{issue.suggestedText}</p>
                </div>
              )}
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={onApply} className="flex-1">
              <CheckCircle className="w-4 h-4 mr-1" />
              应用修改
            </Button>
            <Button size="sm" variant="outline" onClick={onView}>
              <Eye className="w-4 h-4 mr-1" />
              查看原文
            </Button>
            <Button size="sm" variant="ghost" onClick={onIgnore}>
              <X className="w-4 h-4 mr-1" />
              忽略
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// 张力曲线组件
function TensionCurve({ data }: { data: number[] }) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  return (
    <div className="h-20 flex items-end gap-0.5">
      {data.map((value, index) => {
        const height = ((value - min) / range) * 100;
        const isPeak = value > (max + min) / 2 + range * 0.2;
        return (
          <div
            key={index}
            className={cn(
              "flex-1 rounded-t transition-all hover:opacity-80",
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

export function ChapterReviewPanel({
  chapterTitle,
  review,
  isLoading,
  onReReview,
  onApplySuggestion,
  onIgnoreIssue,
  onViewOriginal,
  className,
}: ChapterReviewPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  const handleApply = useCallback((issueId: string) => {
    onApplySuggestion?.(issueId);
  }, [onApplySuggestion]);

  const handleIgnore = useCallback((issueId: string) => {
    onIgnoreIssue?.(issueId);
  }, [onIgnoreIssue]);

  const handleView = useCallback((location?: { line?: number; column?: number }) => {
    if (location) {
      onViewOriginal?.(location);
    }
  }, [onViewOriginal]);

  if (!review) {
    return (
      <div className={cn("p-4 border-t bg-card", className)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-muted-foreground" />
            <span className="font-medium">剧本医生</span>
          </div>
          <span className="text-sm text-muted-foreground">等待审阅</span>
        </div>
      </div>
    );
  }

  const { score, categories, issues, tensionCurve, summary } = review;
  const issueCount = issues.length;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={cn("border-t bg-card", className)}>
      {/* 头部 */}
      <CollapsibleTrigger asChild>
        <div className="flex items-center justify-between p-3 cursor-pointer hover:bg-accent/50 transition-colors">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg",
              score >= 80 ? "bg-green-100 text-green-700" :
              score >= 60 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"
            )}>
              {score}
            </div>
            <div>
              <div className="font-medium">
                剧本医生 - {chapterTitle || '当前章节'}
              </div>
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                <span>{issueCount > 0 ? `${issueCount} 个问题待处理` : '通过审阅'}</span>
                {isLoading && <RefreshCw className="w-3 h-3 animate-spin" />}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onReReview?.();
              }}
              disabled={isLoading}
            >
              <RefreshCw className={cn("w-4 h-4 mr-1", isLoading && "animate-spin")} />
              重新诊断
            </Button>
            {isOpen ? <ChevronDown className="w-5 h-5" /> : <ChevronUp className="w-5 h-5" />}
          </div>
        </div>
      </CollapsibleTrigger>

      {/* 内容 */}
      <CollapsibleContent>
        <ScrollArea className="max-h-96">
          <div className="px-4 pb-4 space-y-4">
            {/* 总体评价 */}
            {summary && (
              <div className="bg-muted/50 rounded-lg p-3">
                <p className="text-sm text-muted-foreground">{summary}</p>
              </div>
            )}

            {/* 张力曲线 */}
            {tensionCurve && tensionCurve.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">章节张力曲线</h4>
                <TensionCurve data={tensionCurve} />
              </div>
            )}

            {/* 分类评分 */}
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(categories) as ReviewCategory[]).map((category) => (
                <div key={category} className="bg-muted/50 rounded-lg p-2 text-center">
                  <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground mb-1">
                    {categoryIcons[category]}
                    <span>{categoryLabels[category]}</span>
                  </div>
                  <div className={cn(
                    "text-lg font-bold",
                    categories[category].score >= 80 ? "text-green-500" :
                    categories[category].score >= 60 ? "text-yellow-500" : "text-red-500"
                  )}>
                    {categories[category].score}
                  </div>
                </div>
              ))}
            </div>

            {/* 问题列表 */}
            {issues.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  问题列表 ({issues.length})
                </h4>
                <div className="space-y-2">
                  {issues.map((issue) => (
                    <IssueItem
                      key={issue.id}
                      issue={issue}
                      onApply={() => handleApply(issue.id)}
                      onIgnore={() => handleIgnore(issue.id)}
                      onView={() => handleView(issue.location)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* 通过状态 */}
            {issues.length === 0 && (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-3">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="font-medium text-green-700">审阅通过</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  该章节没有发现明显问题
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CollapsibleContent>
    </Collapsible>
  );
}

export default ChapterReviewPanel;
