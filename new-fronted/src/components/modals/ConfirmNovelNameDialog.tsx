import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Sparkles, BookOpen } from 'lucide-react';

interface ConfirmNovelNameDialogProps {
  isOpen: boolean;
  onClose: () => void;
  suggestedName: string;
  onConfirm: (confirmedName: string) => void;
  isLoading?: boolean;
}

/**
 * 确认小说名称对话框
 * 用于用户通过AI或临时项目进入时确认/修改项目名称
 */
export function ConfirmNovelNameDialog({
  isOpen,
  onClose,
  suggestedName,
  onConfirm,
  isLoading = false,
}: ConfirmNovelNameDialogProps) {
  const [name, setName] = useState(suggestedName);

  useEffect(() => {
    if (isOpen) {
      setName(suggestedName);
    }
  }, [isOpen, suggestedName]);

  const handleConfirm = () => {
    const trimmedName = name.trim();
    if (trimmedName) {
      onConfirm(trimmedName);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleConfirm();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-surface border-border">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 rounded-full bg-primary/10">
              <BookOpen className="w-5 h-5 text-primary" />
            </div>
            <DialogTitle className="text-lg font-semibold text-text-primary">
              确认小说名称
            </DialogTitle>
          </div>
          <DialogDescription className="text-text-secondary">
            AI已为您生成小说初稿，请确认或修改小说名称
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-primary">
              小说名称
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="请输入小说名称"
              className="bg-background border-border text-text-primary"
              autoFocus
            />
            <p className="text-xs text-text-tertiary">
              确认后将使用此名称作为项目名称
            </p>
          </div>

          <div className="flex items-start gap-2 p-3 rounded-lg bg-primary/5 border border-primary/10">
            <Sparkles className="w-4 h-4 text-primary mt-0.5 shrink-0" />
            <p className="text-sm text-text-secondary">
              项目名称将同步更新为小说名称，方便您在项目列表中识别
            </p>
          </div>
        </div>

        <div className="flex gap-3 justify-end">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
            className="border-border text-text-secondary hover:bg-surface"
          >
            稍后再说
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isLoading || !name.trim()}
            className="bg-primary text-white hover:bg-primary/90"
          >
            {isLoading ? '保存中...' : '确认并开始创作'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
