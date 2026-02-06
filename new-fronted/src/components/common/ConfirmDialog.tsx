import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  variant?: 'default' | 'destructive' | 'info';
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = "确认",
  cancelText = "取消",
  onConfirm,
  variant = 'default'
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px] p-6 gap-6 bg-surface border-border shadow-xl rounded-2xl">
        <div className="flex flex-col gap-4">
          <div className="flex items-start gap-4">
            {variant === 'destructive' && (
              <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
            )}
            <div className="flex flex-col gap-2 pt-1">
              <DialogTitle className="text-lg font-semibold leading-none tracking-tight">
                {title}
              </DialogTitle>
              {description && (
                <DialogDescription className="text-sm text-text-secondary leading-relaxed">
                  {description}
                </DialogDescription>
              )}
            </div>
          </div>
        </div>
        
        <DialogFooter className="flex-row gap-3 sm:justify-end">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="flex-1 sm:flex-none h-9 rounded-lg"
          >
            {cancelText}
          </Button>
          <Button
            variant={variant === 'destructive' ? "destructive" : "default"}
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
            className="flex-1 sm:flex-none h-9 rounded-lg"
          >
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
