import { FileText, Play, Sparkles, ChevronUp, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface DiagnosticItem {
  id: string;
  score: number;
  quote: string;
  suggestion: string;
  category: 'logic' | 'dialogue' | 'pacing' | 'character';
}

interface FooterToolbarProps {
  scriptScore?: number;
  diagnostics?: DiagnosticItem[];
  onReDiagnose?: () => void;
}

export function FooterToolbar({ 
  scriptScore = 88, 
  diagnostics = [],
  onReDiagnose 
}: FooterToolbarProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={cn(
      'border-t border-border bg-surface transition-all duration-300',
      isExpanded ? 'h-64' : 'h-12'
    )}>
      <div className="flex items-center justify-between px-4 h-12">
        <div className="flex items-center gap-6">
          <button className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors">
            <FileText size={16} className="text-primary" />
            <span>剧本医生</span>
            <span className={cn(
              'font-bold',
              scriptScore >= 80 ? 'text-green-500' : 
              scriptScore >= 60 ? 'text-yellow-500' : 'text-red-500'
            )}>
              {scriptScore}
            </span>
          </button>

          <button className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors">
            <Play size={16} className="text-accent" />
            <span>剧情张力曲线</span>
          </button>
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={onReDiagnose}
            className="flex items-center gap-2 text-sm text-text-secondary hover:text-primary transition-colors"
          >
            <Sparkles size={14} />
            <span>重新诊断</span>
          </button>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded hover:bg-elevated text-text-secondary transition-colors"
          >
            {isExpanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 h-52 overflow-y-auto">
          <div className="space-y-3">
            {diagnostics.length > 0 ? (
              diagnostics.map((item) => (
                <DiagnosticCard key={item.id} item={item} />
              ))
            ) : (
              <div className="flex items-center justify-center h-full text-text-tertiary">
                点击"重新诊断"获取剧本分析建议
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DiagnosticCard({ item }: { item: DiagnosticItem }) {
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'logic': return 'text-blue-500 bg-blue-500/10';
      case 'dialogue': return 'text-purple-500 bg-purple-500/10';
      case 'pacing': return 'text-yellow-500 bg-yellow-500/10';
      case 'character': return 'text-green-500 bg-green-500/10';
      default: return 'text-text-secondary bg-surface';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'logic': return '逻辑/设定';
      case 'dialogue': return '台词打磨';
      case 'pacing': return '节奏把控';
      case 'character': return '人物塑造';
      default: return '其他';
    }
  };

  return (
    <div className="p-3 rounded-lg bg-elevated border border-border">
      <div className="flex items-start gap-3">
        <div className={cn(
          'flex-shrink-0 w-8 h-8 rounded flex items-center justify-center font-bold text-sm',
          item.score >= 80 ? 'text-green-500 bg-green-500/10' :
          item.score >= 60 ? 'text-yellow-500 bg-yellow-500/10' : 'text-red-500 bg-red-500/10'
        )}>
          {item.score}
        </div>

        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-tertiary bg-surface px-2 py-0.5 rounded">
              "{item.quote}"
            </span>
          </div>

          <p className="text-sm text-text-secondary">{item.suggestion}</p>
        </div>

        <span className={cn(
          'flex-shrink-0 text-xs px-2 py-1 rounded',
          getCategoryColor(item.category)
        )}>
          {getCategoryLabel(item.category)}
        </span>
      </div>
    </div>
  );
}
