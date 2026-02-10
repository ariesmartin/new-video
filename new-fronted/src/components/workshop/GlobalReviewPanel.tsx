import { useState } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  RefreshCw, 
  CheckCircle, 
  TrendingUp,
  AlertTriangle,
  Lightbulb
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import type { GlobalReview, ReviewCategory } from '@/types/review';

interface GlobalReviewPanelProps {
  review: GlobalReview | null;
  isLoading?: boolean;
  onReReview?: () => void;
  onViewDetails?: (category: ReviewCategory) => void;
  className?: string;
}

// 分类配置
const categoryConfig: Record<ReviewCategory, { label: string; color: string; icon: string }> = {
  logic: { label: '逻辑/设定', color: '#3B82F6', icon: 'Brain' },
  pacing: { label: '节奏/张力', color: '#10B981', icon: 'Activity' },
  character: { label: '人设/角色', color: '#F59E0B', icon: 'User' },
  conflict: { label: '冲突/事件', color: '#EF4444', icon: 'Zap' },
  world: { label: '世界/规则', color: '#8B5CF6', icon: 'Globe' },
  hook: { label: '钩子/悬念', color: '#EC4899', icon: 'Anchor' },
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

// 分类评分项
function CategoryScoreItem({ 
  category, 
  score, 
  issues, 
  onClick 
}: { 
  category: ReviewCategory; 
  score: number; 
  issues: number;
  onClick: () => void;
}) {
  const config = categoryConfig[category];
  
  return (
    <div 
      onClick={onClick}
      className="flex items-center gap-3 p-2 rounded-lg hover:bg-accent/50 cursor-pointer transition-colors"
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

// 张力曲线简化展示
function TensionCurvePreview({ data }: { data: number[] }) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  return (
    <div className="h-16 flex items-end gap-0.5 px-4">
      {data.map((value, index) => {
        const height = ((value - min) / range) * 100;
        return (
          <div
            key={index}
            className="flex-1 bg-primary/60 rounded-t"
            style={{ height: `${Math.max(height, 10)}%` }}
            title={`第${index + 1}章: ${value.toFixed(1)}`}
          />
        );
      })}
    </div>
  );
}

export function GlobalReviewPanel({
  review,
  isLoading,
  onReReview,
  onViewDetails,
  className,
}: GlobalReviewPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  const handleCategoryClick = (category: ReviewCategory) => {
    onViewDetails?.(category);
  };

  if (!review) {
    return (
      <div className={cn("p-4 border-t bg-card", className)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-muted-foreground" />
            <span className="font-medium">剧本医生</span>
          </div>
          <span className="text-sm text-muted-foreground">暂无审阅数据</span>
        </div>
      </div>
    );
  }

  const { overallScore, categories, tensionCurve, summary, recommendations } = review;
  const totalIssues = Object.values(categories).reduce((sum, cat) => sum + cat.issues.length, 0);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={cn("border-t bg-card", className)}>
      {/* 头部 */}
      <CollapsibleTrigger asChild>
        <div className="flex items-center justify-between p-3 cursor-pointer hover:bg-accent/50 transition-colors">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg",
              overallScore >= 80 ? "bg-green-100 text-green-700" :
              overallScore >= 60 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"
            )}>
              {overallScore}
            </div>
            <div>
              <div className="font-medium flex items-center gap-2">
                <span>剧本医生 - 全局报告</span>
                {totalIssues > 0 && (
                  <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
                    {totalIssues} 个问题
                  </span>
                )}
              </div>
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                <span>剧情张力曲线</span>
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
        <div className="px-4 pb-4 space-y-4">
          {/* 总体评价 */}
          {summary && (
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <Lightbulb className="w-4 h-4 text-amber-500 mt-0.5" />
                <p className="text-sm text-muted-foreground">{summary}</p>
              </div>
            </div>
          )}

          {/* 张力曲线 */}
          {tensionCurve && tensionCurve.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">剧情张力曲线</h4>
              <TensionCurvePreview data={tensionCurve} />
            </div>
          )}

          {/* 分类评分 */}
          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(categories) as ReviewCategory[]).map((category) => (
              <CategoryScoreItem
                key={category}
                category={category}
                score={categories[category].score}
                issues={categories[category].issues.length}
                onClick={() => handleCategoryClick(category)}
              />
            ))}
          </div>

          {/* 改进建议 */}
          {recommendations && recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">改进建议</h4>
              <ul className="space-y-1">
                {recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export default GlobalReviewPanel;
