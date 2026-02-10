import { useState, useCallback } from 'react';
import { ChevronRight, ChevronDown, BookOpen, Film, Camera, CheckCircle, AlertTriangle, XCircle, Clock, Play, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { OutlineNode } from '@/types/outline';

interface ChapterTreeProps {
  nodes: OutlineNode[];
  selectedId: string | null;
  onSelect: (nodeId: string, node: OutlineNode) => void;
  className?: string;
  batchStatus?: {
    currentBatch: number;
    totalBatches: number;
    needsNextBatch: boolean;
    isComplete: boolean;
  };
  onContinueGeneration?: () => void;
  isGenerating?: boolean;
}

// 获取状态图标
function StatusIcon({ status, score }: { status: string; score?: number }) {
  const icons = {
    passed: <CheckCircle className="w-4 h-4 text-green-500" />,
    warning: <AlertTriangle className="w-4 h-4 text-yellow-500" />,
    error: <XCircle className="w-4 h-4 text-red-500" />,
    pending: <Clock className="w-4 h-4 text-gray-400" />,
  };

  return (
    <div className="flex items-center gap-1">
      {icons[status as keyof typeof icons] || icons.pending}
      {score !== undefined && (
        <span className={cn(
          "text-xs font-medium",
          score >= 80 ? "text-green-500" :
          score >= 60 ? "text-yellow-500" : "text-red-500"
        )}>
          {score}
        </span>
      )}
    </div>
  );
}

// 获取节点图标
function NodeIcon({ type }: { type: string }) {
  const icons = {
    episode: <BookOpen className="w-4 h-4" />,
    scene: <Film className="w-4 h-4" />,
    shot: <Camera className="w-4 h-4" />,
  };

  return icons[type as keyof typeof icons] || null;
}

// 树节点组件
function TreeNode({
  node,
  depth = 0,
  selectedId,
  onSelect,
  expandedIds,
  onToggleExpand,
}: {
  node: OutlineNode;
  depth?: number;
  selectedId: string | null;
  onSelect: (nodeId: string, node: OutlineNode) => void;
  expandedIds: Set<string>;
  onToggleExpand: (nodeId: string) => void;
}) {
  const isExpanded = expandedIds.has(node.id);
  const isSelected = selectedId === node.id;
  const hasChildren = node.children && node.children.length > 0;

  const handleClick = useCallback(() => {
    onSelect(node.id, node);
  }, [node, onSelect]);

  const handleToggle = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleExpand(node.id);
  }, [node.id, onToggleExpand]);

  // 缩进宽度
  const indentWidth = depth * 16;

  return (
    <div className="select-none">
      {/* 节点行 */}
      <div
        onClick={handleClick}
        className={cn(
          "flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors",
          "hover:bg-accent/50",
          isSelected && "bg-accent text-accent-foreground",
          "rounded-md mx-2"
        )}
        style={{ paddingLeft: `${12 + indentWidth}px` }}
      >
        {/* 展开/折叠按钮 */}
        {hasChildren ? (
          <button
            onClick={handleToggle}
            className="p-0.5 hover:bg-accent rounded transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        ) : (
          <span className="w-5" />
        )}

        {/* 节点图标 */}
        <div className={cn(
          "text-muted-foreground",
          isSelected && "text-accent-foreground"
        )}>
          <NodeIcon type={node.type} />
        </div>

        {/* 节点标题 */}
        <div className="flex-1 min-w-0">
          <span className={cn(
            "text-sm truncate block",
            isSelected ? "font-medium" : "text-foreground"
          )}>
            {node.title}
          </span>
        </div>

        {/* 付费卡点标记 */}
        {node.metadata?.isPaidWall && (
          <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded-full">
            付费
          </span>
        )}

        {/* 审阅状态 */}
        <StatusIcon 
          status={node.metadata?.reviewStatus || 'pending'} 
          score={node.metadata?.reviewScore}
        />
      </div>

      {/* 子节点 */}
      {hasChildren && isExpanded && (
        <div className="mt-0.5">
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              expandedIds={expandedIds}
              onToggleExpand={onToggleExpand}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// 主组件
export function ChapterTree({
  nodes,
  selectedId,
  onSelect,
  className,
  batchStatus,
  onContinueGeneration,
  isGenerating
}: ChapterTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    nodes.forEach(node => {
      if (node.type === 'episode') {
        initial.add(node.id);
      }
    });
    return initial;
  });

  const handleToggleExpand = useCallback((nodeId: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  const handleSelect = useCallback((nodeId: string, node: OutlineNode) => {
    onSelect(nodeId, node);
  }, [onSelect]);

  const showContinueButton = batchStatus?.needsNextBatch && !batchStatus?.isComplete;

  return (
    <div className={cn("py-2", className)}>
      {nodes.length === 0 ? (
        <div className="px-4 py-8 text-center text-muted-foreground">
          <BookOpen className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">暂无大纲数据</p>
          <p className="text-xs mt-1">请先完成故事策划</p>
        </div>
      ) : (
        <>
          {nodes.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              selectedId={selectedId}
              onSelect={handleSelect}
              expandedIds={expandedIds}
              onToggleExpand={handleToggleExpand}
            />
          ))}

          {showContinueButton && (
            <div className="px-4 py-3 mx-2 mt-2 border border-dashed border-border rounded-lg bg-muted/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">
                  生成进度: {batchStatus?.currentBatch || 0} / {batchStatus?.totalBatches || 0} 批次
                </span>
              </div>
              <button
                onClick={onContinueGeneration}
                disabled={isGenerating}
                className={cn(
                  "w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  "bg-primary text-primary-foreground hover:bg-primary/90",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    继续生成下一批
                  </>
                )}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default ChapterTree;
