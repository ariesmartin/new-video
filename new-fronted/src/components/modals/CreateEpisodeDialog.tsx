import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { FileText, Plus } from 'lucide-react';

interface CreateEpisodeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

/**
 * 创建剧集确认对话框
 * 
 * 当用户在画布点击"剧本工坊"但没有剧集时弹出
 * 询问用户是否创建第一集
 */
export function CreateEpisodeDialog({
  isOpen,
  onClose,
  onConfirm,
}: CreateEpisodeDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-surface border-border">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-text-primary">
            开始剧本创作
          </DialogTitle>
          <DialogDescription className="text-text-secondary">
            您还没有创建剧集，需要创建第一集才能进入剧本工坊
          </DialogDescription>
        </DialogHeader>

        <div className="py-6">
          <div className="flex items-start gap-4 p-4 rounded-lg border border-border bg-background/50">
            <div className="p-3 rounded-full bg-primary/10">
              <FileText className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-text-primary mb-1">
                创建第一集
              </h3>
              <p className="text-sm text-text-secondary">
                系统将为您创建空白剧集，您可以在剧本工坊中开始创作或让AI协助生成内容
              </p>
            </div>
          </div>
        </div>

        <div className="flex gap-3 justify-end">
          <Button
            variant="outline"
            onClick={onClose}
            className="border-border text-text-secondary hover:bg-surface"
          >
            取消
          </Button>
          <Button
            onClick={onConfirm}
            className="bg-primary text-white hover:bg-primary/90 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            创建并进入
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
