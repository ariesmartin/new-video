import { Bell, User, Moon, Sun, Wallet, Settings } from 'lucide-react';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import { Logo } from '@/components/ui/Logo';

interface HeaderProps {
  variant?: 'home' | 'project';
  onBack?: () => void;
}

export function Header({ variant = 'home', onBack }: HeaderProps) {
  const { theme, setTheme, user } = useAppStore();
  const { openBackstageModal } = useUIStore();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header
      className={`flex items-center justify-between px-3 sm:px-6 py-2 sm:py-4 ${
        variant === 'home' ? '' : 'bg-surface border-b border-border'
      }`}
    >
      <div className="flex items-center gap-2">
        {variant === 'project' && onBack && (
          <button
            onClick={onBack}
            className="mr-2 sm:mr-4 p-1.5 sm:p-2 rounded-lg hover:bg-white/5 transition-colors text-text-secondary"
          >
            <span>←</span>
          </button>
        )}
        <Logo size={variant === 'home' ? 'lg' : 'md'} showText={true} />
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        <button
          onClick={() => openBackstageModal('settings')}
          className="p-1.5 sm:p-2 rounded-lg hover:bg-white/5 transition-colors text-text-secondary hidden sm:block"
          title="系统设置"
        >
          <Settings size={18} className="sm:w-5 sm:h-5" />
        </button>

        <button
          onClick={toggleTheme}
          className="p-1.5 sm:p-2 rounded-lg hover:bg-white/5 transition-colors text-text-secondary"
        >
          {theme === 'dark' ? <Sun size={18} className="sm:w-5 sm:h-5" /> : <Moon size={18} className="sm:w-5 sm:h-5" />}
        </button>

        <button
          className="p-1.5 sm:p-2 rounded-lg hover:bg-white/5 transition-colors relative text-text-secondary hidden sm:block"
        >
          <Bell size={18} className="sm:w-5 sm:h-5" />
          <span className="absolute top-0.5 right-0.5 sm:top-1 sm:right-1 w-2 h-2 rounded-full bg-status-red" />
        </button>

        {user && (
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10">
            <Wallet size={16} className="text-primary" />
            <span className="text-sm font-medium text-primary">
              {user.balance.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}

        <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg cursor-pointer hover:bg-white/5 transition-colors bg-surface border border-border">
          <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center bg-primary">
            <User size={12} className="sm:w-3.5 sm:h-3.5 text-primary-foreground" />
          </div>
          <span className="text-xs sm:text-sm text-text-primary hidden sm:inline">
            {user?.name || 'admin'}
          </span>
        </div>
      </div>
    </header>
  );
}
