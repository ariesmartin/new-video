import { useState } from 'react';
import { Sparkles, RefreshCw, Check, ArrowRight, Image as ImageIcon, Grid3X3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface Shot {
  shotNumber: number;
  title: string;
  subtitle?: string;
  shotType?: string;
  cameraMove?: string;
  description?: string;
  dialog?: string;
}

interface StoryboardEditorProps {
  shots: Shot[];
  onShotsChange?: (shots: Shot[]) => void;
  onGenerate?: () => void;
  isGenerating?: boolean;
}

export function StoryboardEditor({ 
  shots, 
  onGenerate,
  isGenerating = false 
}: StoryboardEditorProps) {
  const [selectedShot, setSelectedShot] = useState<Shot | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const handleShotClick = (shot: Shot) => {
    setSelectedShot(shot);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface/50">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-text-primary">分镜列表</h2>
          <Badge variant="secondary">{shots.length} 个分镜</Badge>
        </div>
        <div className="flex items-center gap-2">
          <ViewToggle mode={viewMode} onModeChange={setViewMode} />
          <Button
            onClick={onGenerate}
            disabled={isGenerating}
            className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                AI 生成分镜
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex">
        <ScrollArea className="flex-1 p-4">
          {shots.length === 0 ? (
            <EmptyState onGenerate={onGenerate} isGenerating={isGenerating} />
          ) : viewMode === 'grid' ? (
            <GridView shots={shots} onShotClick={handleShotClick} selectedShot={selectedShot} />
          ) : (
            <ListView shots={shots} onShotClick={handleShotClick} selectedShot={selectedShot} />
          )}
        </ScrollArea>

        {selectedShot && (
          <ShotDetailPanel shot={selectedShot} onClose={() => setSelectedShot(null)} />
        )}
      </div>
    </div>
  );
}

function ViewToggle({ mode, onModeChange }: { mode: 'grid' | 'list'; onModeChange: (mode: 'grid' | 'list') => void }) {
  return (
    <div className="flex items-center gap-1 p-1 bg-surface rounded border border-border">
      <button
        onClick={() => onModeChange('grid')}
        className={cn(
          'p-1.5 rounded transition-all',
          mode === 'grid' ? 'bg-primary text-primary-foreground' : 'text-text-secondary hover:text-text-primary'
        )}
        title="网格视图"
      >
        <Grid3X3 size={16} />
      </button>
      <button
        onClick={() => onModeChange('list')}
        className={cn(
          'p-1.5 rounded transition-all',
          mode === 'list' ? 'bg-primary text-primary-foreground' : 'text-text-secondary hover:text-text-primary'
        )}
        title="列表视图"
      >
        <ImageIcon size={16} />
      </button>
    </div>
  );
}

function EmptyState({ onGenerate, isGenerating }: { onGenerate?: () => void; isGenerating: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-12 space-y-4">
      <div className="p-4 rounded-full bg-primary/10">
        <Sparkles className="w-8 h-8 text-primary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary">暂无分镜</h3>
      <p className="text-sm text-text-secondary text-center max-w-md">
        使用 AI 自动从剧本内容生成分镜，或手动创建分镜
      </p>
      <Button
        onClick={onGenerate}
        disabled={isGenerating}
        className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
      >
        {isGenerating ? (
          <>
            <RefreshCw className="w-4 h-4 animate-spin" />
            生成中...
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" />
            一键生成分镜
          </>
        )}
      </Button>
    </div>
  );
}

function GridView({ 
  shots, 
  onShotClick, 
  selectedShot 
}: { 
  shots: Shot[]; 
  onShotClick: (shot: Shot) => void;
  selectedShot: Shot | null;
}) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {shots.map((shot) => (
        <Card
          key={shot.shotNumber}
          onClick={() => onShotClick(shot)}
          className={cn(
            'cursor-pointer transition-all duration-200 hover:border-primary/50',
            selectedShot?.shotNumber === shot.shotNumber && 'ring-2 ring-primary border-primary'
          )}
        >
          <CardHeader className="p-3 pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">
                #{shot.shotNumber} {shot.title}
              </CardTitle>
              <ShotTypeBadge shotType={shot.shotType} />
            </div>
          </CardHeader>
          <CardContent className="p-3 pt-0 space-y-2">
            <div className="aspect-video bg-surface rounded border border-border flex items-center justify-center">
              <ImageIcon className="w-8 h-8 text-text-tertiary/30" />
            </div>
            {shot.description && (
              <p className="text-xs text-text-secondary line-clamp-2">{shot.description}</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ListView({ 
  shots, 
  onShotClick, 
  selectedShot 
}: { 
  shots: Shot[]; 
  onShotClick: (shot: Shot) => void;
  selectedShot: Shot | null;
}) {
  return (
    <div className="space-y-2">
      {shots.map((shot) => (
        <div
          key={shot.shotNumber}
          onClick={() => onShotClick(shot)}
          className={cn(
            'flex items-center gap-4 p-3 rounded-lg border cursor-pointer transition-all duration-200',
            selectedShot?.shotNumber === shot.shotNumber
              ? 'bg-primary/10 border-primary'
              : 'bg-surface border-border hover:border-primary/50'
          )}
        >
          <div className="w-12 h-12 bg-surface rounded border border-border flex items-center justify-center flex-shrink-0">
            <span className="text-lg font-bold text-text-tertiary">#{shot.shotNumber}</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-text-primary">{shot.title}</span>
              <ShotTypeBadge shotType={shot.shotType} />
            </div>            {shot.description && (
              <p className="text-sm text-text-secondary truncate">{shot.description}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function ShotTypeBadge({ shotType }: { shotType?: string }) {
  const getColor = (type?: string) => {
    switch (type) {
      case '全景': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case '中景': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case '特写': return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
      default: return 'bg-surface text-text-secondary';
    }
  };

  return (
    <Badge variant="outline" className={cn('text-xs', getColor(shotType))}>
      {shotType || '镜头'}
    </Badge>
  );
}

function ShotDetailPanel({ shot, onClose }: { shot: Shot; onClose: () => void }) {
  return (
    <div className="w-80 border-l border-border bg-surface p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-text-primary">分镜详情</h3>
        <button onClick={onClose} className="text-text-tertiary hover:text-text-primary">
          ×
        </button>
      </div>

      <div className="aspect-video bg-surface rounded-lg border border-border flex items-center justify-center">
        <ImageIcon className="w-12 h-12 text-text-tertiary/30" />
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-xs text-text-tertiary">镜头编号</label>
          <p className="text-sm font-medium">#{shot.shotNumber} {shot.title}</p>
        </div>

        {shot.shotType && (
          <div>
            <label className="text-xs text-text-tertiary">景别</label>
            <p className="text-sm">{shot.shotType}</p>
          </div>
        )}

        {shot.cameraMove && (
          <div>
            <label className="text-xs text-text-tertiary">运镜</label>
            <p className="text-sm">{shot.cameraMove}</p>
          </div>
        )}

        {shot.description && (
          <div>
            <label className="text-xs text-text-tertiary">画面描述</label>
            <p className="text-sm text-text-secondary">{shot.description}</p>
          </div>
        )}

        {shot.dialog && (
          <div>
            <label className="text-xs text-text-tertiary">对白</label>
            <p className="text-sm text-text-secondary">{shot.dialog}</p>
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-border space-y-2">
        <Button className="w-full gap-2 bg-primary text-primary-foreground">
          <Check className="w-4 h-4" />
          确认修改
        </Button>
        <Button variant="outline" className="w-full gap-2">
          前往画板
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
