import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Sparkles, FileEdit, ArrowRight } from 'lucide-react';

interface CreateScriptOptionsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAICreation: () => void;
  onManualCreation: () => void;
}

export function CreateScriptOptionsDialog({
  isOpen,
  onClose,
  onAICreation,
  onManualCreation,
}: CreateScriptOptionsDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg bg-surface border-border">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-text-primary">
            您想如何创建剧本？
          </DialogTitle>
          <DialogDescription className="text-text-secondary">
            选择适合您的创作方式
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <button
            onClick={onAICreation}
            className="flex items-start gap-4 p-4 rounded-lg border border-border bg-background/50 hover:bg-primary/5 hover:border-primary/30 transition-all text-left group"
          >
            <div className="p-3 rounded-full bg-primary/10 group-hover:bg-primary/20 transition-colors">
              <Sparkles className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-text-primary mb-1">
                AI协助创作
              </h3>
              <p className="text-sm text-text-secondary mb-2">
                与AI对话，共同创作小说和剧本。AI会根据您的创意生成完整的故事内容。
              </p>
              <div className="flex items-center gap-2 text-xs text-primary">
                <span>开始创作</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>
          </button>

          <button
            onClick={onManualCreation}
            className="flex items-start gap-4 p-4 rounded-lg border border-border bg-background/50 hover:bg-surface transition-all text-left group"
          >
            <div className="p-3 rounded-full bg-surface group-hover:bg-elevated transition-colors">
              <FileEdit className="w-6 h-6 text-text-secondary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-text-primary mb-1">
                手动编写
              </h3>
              <p className="text-sm text-text-secondary mb-2">
                在空白编辑器中直接输入您的剧本内容，适合已有完整剧本的场景。
              </p>
              <div className="flex items-center gap-2 text-xs text-text-tertiary">
                <span>进入编辑器</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>
          </button>
        </div>

        <div className="flex justify-end">
          <Button
            variant="outline"
            onClick={onClose}
            className="border-border text-text-secondary hover:bg-surface"
          >
            取消
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
