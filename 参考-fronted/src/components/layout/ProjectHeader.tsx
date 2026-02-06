import { 
  Settings, 
  FileText, 
  Image as ImageIcon, 
  Download,
  Sun,
  Moon,
  ArrowLeft
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import { useNavigate } from 'react-router-dom';

interface ProjectHeaderProps {
  onScriptWorkshop?: () => void;
  onBatchGenerate?: () => void;
  onExport?: () => void;
  onBackstage?: () => void;
}

export function ProjectHeader({ 
  onScriptWorkshop, 
  onBatchGenerate, 
  onExport,
  onBackstage
}: ProjectHeaderProps) {
  const navigate = useNavigate();
  const { theme, setTheme } = useAppStore();
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);

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

  return (
    <header 
      className="flex items-center justify-between px-4 py-3"
      style={{ 
        backgroundColor: 'var(--bg-card)',
        borderBottom: '1px solid var(--border)'
      }}
    >
      {/* 左侧：返回主页 + Logo */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleBackToHome}
          className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg hover:bg-white/10 transition-colors"
          style={{ color: 'var(--text-secondary)' }}
          title="返回主页"
        >
          <ArrowLeft size={16} />
          <span className="text-sm">主页</span>
        </button>
        <div 
          className="w-px h-6"
          style={{ backgroundColor: 'var(--border)' }}
        />
        <div 
          className="w-8 h-8 rounded-lg flex items-center justify-center font-bold"
          style={{ backgroundColor: 'var(--primary)', color: '#000' }}
        >
          W
        </div>
        <span 
          className="font-semibold"
          style={{ color: 'var(--text-primary)' }}
        >
          wuli.cool 呜哩的分镜台 V8.0
        </span>
      </div>

      {/* 右侧：操作按钮 */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleBackstage}
          className="flex items-center gap-1.5"
          style={{ color: 'var(--text-secondary)' }}
        >
          <Settings size={16} />
          后台
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={onScriptWorkshop}
          className="flex items-center gap-1.5"
          style={{ color: 'var(--text-secondary)' }}
        >
          <FileText size={16} />
          剧本工坊
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={handleBatchGenerate}
          className="flex items-center gap-1.5"
          style={{ color: 'var(--text-secondary)' }}
        >
          <ImageIcon size={16} />
          批量图
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={handleExport}
          className="flex items-center gap-1.5"
          style={{ color: 'var(--text-secondary)' }}
        >
          <Download size={16} />
          导出
        </Button>

        {/* 主题切换 */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors ml-2"
          style={{ color: 'var(--text-secondary)' }}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* 用户头像 */}
        <div 
          className="w-8 h-8 rounded-full flex items-center justify-center ml-2"
          style={{ backgroundColor: 'var(--primary)' }}
        >
          <span className="text-sm font-medium text-black">A</span>
        </div>
      </div>
    </header>
  );
}
