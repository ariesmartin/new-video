import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sparkles, Check, RefreshCw, ArrowRight, Image as ImageIcon } from 'lucide-react';
import { shotsService } from '@/api/services/shots';
import { chatService } from '@/api/services/chat';
import { useUIStore } from '@/hooks/useStore';

interface ShotPreview {
  shotNumber: number;
  title: string;
  subtitle?: string;
  shotType?: string;
  cameraMove?: string;
  description?: string;
  dialog?: string;
}

interface StoryboardGeneratorProps {
  episodeId: string;
  scriptText: string;
  projectId?: string;
  onConfirm?: () => void;
  onNavigateToCanvas?: () => void;
}

export function StoryboardGenerator({
  episodeId,
  scriptText,
  projectId,
  onConfirm,
  onNavigateToCanvas,
}: StoryboardGeneratorProps) {
  const { addToast } = useUIStore();
  const [previewShots, setPreviewShots] = useState<ShotPreview[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);

  const handleGenerate = () => {
    if (!scriptText.trim()) {
      addToast?.({ type: 'warning', message: '请先输入剧本内容' });
      return;
    }
    
    setIsGenerating(true);
    
    // 使用chatService通过Master Router调用Storyboard Director Agent
    const cancelStream = chatService.streamMessage(
      `请为以下剧本生成分镜列表：\n\n${scriptText}\n\n请生成详细的分镜列表，包含镜头编号、场景标题、景别、运镜方式、画面描述和对白。以JSON格式返回shots数组。`,
      {
        onMessage: (message) => {
          // 尝试从AI响应中解析JSON
          try {
            const content = message.content;
            // 查找JSON代码块
            const jsonMatch = content.match(/```json\s*([\s\S]*?)\s*```/) || 
                              content.match(/\{[\s\S]*"shots"[\s\S]*\}/);
            
            if (jsonMatch) {
              const jsonStr = jsonMatch[1] || jsonMatch[0];
              const parsed = JSON.parse(jsonStr);
              
              if (parsed.shots && parsed.shots.length > 0) {
                setPreviewShots(parsed.shots.map((shot: any) => ({
                  shotNumber: shot.shotNumber || shot.shot_number,
                  title: shot.title,
                  subtitle: shot.subtitle,
                  shotType: shot.shotType || shot.shot_type,
                  cameraMove: shot.cameraMove || shot.camera_move,
                  description: shot.description,
                  dialog: shot.dialog,
                })));
              }
            }
          } catch (e) {
            // 如果解析失败，继续等待更多内容
            console.log('Waiting for complete JSON...');
          }
        },
        onThinking: (thinking) => {
          console.log('AI思考中:', thinking);
        },
        onError: (error) => {
          console.error('生成失败:', error);
          addToast?.({ type: 'error', message: 'AI解析剧本失败: ' + error });
          setIsGenerating(false);
        },
        onComplete: () => {
          setHasGenerated(true);
          setIsGenerating(false);
          addToast?.({ type: 'success', message: '分镜生成完成' });
        },
      },
      projectId,
      episodeId
    );
    
    // 返回取消函数以便需要时取消
    return cancelStream;
  };

  const handleConfirm = async () => {
    if (!episodeId || previewShots.length === 0) return;
    
    setIsSaving(true);
    
    try {
      // 批量保存分镜到数据库
      const shotsToCreate = previewShots.map((shot, index) => ({
        title: shot.title,
        subtitle: shot.subtitle || '',
        nodeType: 'shot' as const,
        shotNumber: shot.shotNumber,
        positionX: 100 + (index % 5) * 200,
        positionY: 100 + Math.floor(index / 5) * 150,
        details: {
          shotType: shot.shotType || '中景',
          cameraMove: shot.cameraMove || '静止',
          description: shot.description || '',
          dialog: shot.dialog || '',
        },
      }));
      
      await shotsService.batchCreateShots(episodeId, { shots: shotsToCreate });
      
      onConfirm?.();
    } catch (error) {
      console.error('保存分镜失败:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerate = () => {
    setHasGenerated(false);
    setPreviewShots([]);
    handleGenerate();
  };



  const getShotTypeColor = (shotType?: string) => {
    switch (shotType) {
      case '全景':
        return 'bg-blue-500/10 text-blue-500';
      case '中景':
        return 'bg-green-500/10 text-green-500';
      case '特写':
        return 'bg-purple-500/10 text-purple-500';
      default:
        return 'bg-gray-500/10 text-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      {/* 生成按钮 */}
      {!hasGenerated && (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="p-4 rounded-full bg-primary/10">
            <Sparkles className="w-8 h-8 text-primary" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary">生成分镜预览</h3>
          <p className="text-sm text-text-secondary text-center max-w-md">
            AI将自动解析剧本内容，为您生成对应的分镜头预览
          </p>
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !scriptText.trim()}
            className="gap-2 bg-primary text-white hover:bg-primary/90"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                解析中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                一键生成分镜
              </>
            )}
          </Button>
        </div>
      )}

      {/* 预览区域 */}
      {hasGenerated && previewShots.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-text-primary">分镜预览</h3>
              <p className="text-sm text-text-secondary">
                共生成 {previewShots.length} 个分镜，请确认后保存到画板
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleRegenerate}
                disabled={isGenerating}
                className="gap-2 border-border text-text-secondary hover:bg-surface"
              >
                <RefreshCw className="w-4 h-4" />
                重新生成
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={isSaving}
                className="gap-2 bg-primary text-white hover:bg-primary/90"
              >
                {isSaving ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    确认并同步
                  </>
                )}
              </Button>
            </div>
          </div>

          <ScrollArea className="h-[500px] pr-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {previewShots.map((shot) => (
                <Card key={shot.shotNumber} className="bg-surface border-border">
                  <CardHeader className="p-4 pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium text-text-primary">
                        #{shot.shotNumber} {shot.title}
                      </CardTitle>
                      <Badge className={getShotTypeColor(shot.shotType)}>
                        {shot.shotType || '镜头'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 pt-0 space-y-2">
                    {/* 占位图 */}
                    <div className="aspect-video bg-background rounded border border-border flex items-center justify-center">
                      <ImageIcon className="w-8 h-8 text-text-tertiary/30" />
                    </div>
                    
                    {/* 分镜信息 */}
                    <div className="space-y-1 text-sm">
                      <p className="text-text-secondary">
                        <span className="text-text-tertiary">运镜:</span> {shot.cameraMove || '静止'}
                      </p>
                      {shot.description && (
                        <p className="text-text-secondary line-clamp-2">
                          <span className="text-text-tertiary">画面:</span> {shot.description}
                        </p>
                      )}
                      {shot.dialog && (
                        <p className="text-text-secondary line-clamp-2">
                          <span className="text-text-tertiary">对白:</span> {shot.dialog}
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>

          {/* 操作栏 */}
          <div className="flex items-center justify-between pt-4 border-t border-border">
            <p className="text-sm text-text-tertiary">
              确认后将创建分镜节点并同步到画板页面
            </p>
            <Button
              onClick={onNavigateToCanvas}
              variant="outline"
              className="gap-2 border-primary text-primary hover:bg-primary/5"
            >
              前往画板查看
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* 空状态 */}
      {hasGenerated && previewShots.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <p className="text-text-secondary">未能从剧本中解析出分镜内容</p>
          <Button
            variant="outline"
            onClick={handleRegenerate}
            className="gap-2 border-border text-text-secondary hover:bg-surface"
          >
            <RefreshCw className="w-4 h-4" />
            重新解析
          </Button>
        </div>
      )}
    </div>
  );
}
