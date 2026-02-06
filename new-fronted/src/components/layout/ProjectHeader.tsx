import { useState, useEffect } from 'react';
import {
  Settings,
  FileText,
  Image as ImageIcon,
  Download,
  Sun,
  Moon,
  ArrowLeft,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import { useNavigate } from 'react-router-dom';
import { Logo } from '@/components/ui/Logo';
import type { Project } from '@/types';

interface ProjectHeaderProps {
  project?: Project | null;
  onRename?: (newName: string) => Promise<void>;
  onScriptWorkshop?: () => void;
  onBatchGenerate?: () => void;
  onExport?: () => void;
  onBackstage?: () => void;
}

export function ProjectHeader({
  project,
  onRename,
  onScriptWorkshop,
  onBatchGenerate,
  onExport,
  onBackstage
}: ProjectHeaderProps) {
  const navigate = useNavigate();
  const { theme, setTheme } = useAppStore();
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);

  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  useEffect(() => {
    if (project?.name) {
      setEditName(project.name);
    }
  }, [project?.name]);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleBackstage = () => {
    if (onBackstage) {
      onBackstage();
    } else {
      addToast({ type: 'info', message: '后台管理功能开发中' });
    }
  };

  const handleBatchGenerate = () => {
    if (onBatchGenerate) {
      onBatchGenerate();
    } else {
      addToast({ type: 'info', message: '批量生图功能开发中' });
    }
  };

  const handleExport = () => {
    if (onExport) {
      onExport();
    } else {
      addToast({ type: 'info', message: '导出功能开发中' });
    }
  };

  const startRename = () => {
    if (!project) return;
    setEditName(project.name);
    setIsEditing(true);
  };

  const confirmRename = async () => {
    if (!editName.trim() || editName === project?.name) {
      setIsEditing(false);
      return;
    }

    if (onRename) {
      setIsRenaming(true);
      try {
        await onRename(editName);
        setIsEditing(false);
      } catch (error) {
        // Error handling is likely done in the parent
        console.error("Rename failed", error);
      } finally {
        setIsRenaming(false);
      }
    } else {
      setIsEditing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      confirmRename();
    } else if (e.key === 'Escape') {
      setEditName(project?.name || '');
      setIsEditing(false);
    }
  };

  return (
    <header className="flex items-center justify-between px-2 sm:px-4 py-2 sm:py-3 bg-surface border-b border-border">
      <div className="flex items-center gap-2 sm:gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleBackToHome}
          className="flex items-center gap-1.5 text-text-secondary px-2 sm:px-3"
          title="返回主页"
        >
          <ArrowLeft size={16} />
          <span className="hidden sm:inline">主页</span>
        </Button>
        <div className="w-px h-6 bg-border hidden sm:block" />
        <div className="flex items-center gap-3">
          <div className="scale-90 sm:scale-100 origin-left flex-shrink-0">
            <Logo size="md" showText={true} />
          </div>

          {project ? (
            <div className="flex items-center">
              <span className="text-border mx-2 text-lg font-light">/</span>
              {isEditing ? (
                <div className="relative">
                  <Input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onBlur={confirmRename}
                    onKeyDown={handleKeyDown}
                    autoFocus
                    className="h-7 py-1 px-2 w-48 text-sm font-medium"
                    disabled={isRenaming}
                  />
                  {isRenaming && (
                    <div className="absolute right-2 top-1.5">
                      <Loader2 size={12} className="animate-spin text-text-tertiary" />
                    </div>
                  )}
                </div>
              ) : (
                <div
                  onClick={startRename}
                  className="px-2 py-1 rounded-md hover:bg-elevated cursor-text transition-colors text-sm font-medium text-text-primary truncate max-w-[200px]"
                  title="点击重命名"
                >
                  {project.name}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>

      {/* 右侧：操作按钮 */}
      <div className="flex items-center gap-1 sm:gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleBackstage}
          className="flex items-center gap-1.5 text-text-secondary px-2 sm:px-3"
        >
          <Settings size={16} />
          <span className="hidden sm:inline">后台</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onScriptWorkshop}
          className="flex items-center gap-1.5 text-text-secondary px-2 sm:px-3"
        >
          <FileText size={16} />
          <span className="hidden sm:inline">剧本</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleBatchGenerate}
          className="flex items-center gap-1.5 text-text-secondary px-2 sm:px-3"
        >
          <ImageIcon size={16} />
          <span className="hidden sm:inline">批量</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleExport}
          className="flex items-center gap-1.5 text-text-secondary px-2 sm:px-3"
        >
          <Download size={16} />
          <span className="hidden sm:inline">导出</span>
        </Button>

        {/* 主题切换 */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="ml-1 sm:ml-2 text-text-secondary h-8 w-8 sm:h-9 sm:w-9"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </Button>

        {/* 用户头像 */}
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center ml-1 sm:ml-2 bg-primary">
          <span className="text-xs sm:text-sm font-medium text-primary-foreground">A</span>
        </div>
      </div>
    </header>
  );
}
