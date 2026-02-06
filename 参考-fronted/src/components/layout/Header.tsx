import { Bell, User, Moon, Sun, Wallet } from 'lucide-react';
import { useAppStore } from '@/hooks/useStore';

interface HeaderProps {
  variant?: 'home' | 'project';
  onBack?: () => void;
}

export function Header({ variant = 'home', onBack }: HeaderProps) {
  const { theme, setTheme, user } = useAppStore();

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header 
      className="flex items-center justify-between px-6 py-4"
      style={{ 
        backgroundColor: variant === 'home' ? 'transparent' : 'var(--bg-card)',
        borderBottom: variant === 'project' ? '1px solid var(--border)' : 'none'
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2">
        {variant === 'project' && onBack && (
          <button 
            onClick={onBack}
            className="mr-4 p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <span style={{ color: 'var(--text-secondary)' }}>←</span>
          </button>
        )}
        <div 
          className="w-8 h-8 rounded-lg flex items-center justify-center font-bold"
          style={{ backgroundColor: 'var(--primary)', color: '#000' }}
        >
          W
        </div>
        <span 
          className="font-semibold text-lg"
          style={{ color: 'var(--text-primary)' }}
        >
          {variant === 'home' ? '分镜台' : 'wuli.cool 呜哩的分镜台 V8.0'}
        </span>
      </div>

      {/* 右侧操作区 */}
      <div className="flex items-center gap-4">
        {/* 主题切换 */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          style={{ color: 'var(--text-secondary)' }}
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        {/* 通知 */}
        <button
          className="p-2 rounded-lg hover:bg-white/5 transition-colors relative"
          style={{ color: 'var(--text-secondary)' }}
        >
          <Bell size={20} />
          <span 
            className="absolute top-1 right-1 w-2 h-2 rounded-full"
            style={{ backgroundColor: 'var(--status-red)' }}
          />
        </button>

        {/* 用户余额 */}
        {user && (
          <div 
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
            style={{ backgroundColor: 'rgba(255, 215, 0, 0.1)' }}
          >
            <Wallet size={16} style={{ color: 'var(--primary)' }} />
            <span 
              className="text-sm font-medium"
              style={{ color: 'var(--primary)' }}
            >
              {user.balance.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
            </span>
          </div>
        )}

        {/* 用户头像 */}
        <div 
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer hover:bg-white/5 transition-colors"
          style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          <div 
            className="w-7 h-7 rounded-full flex items-center justify-center"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            <User size={14} className="text-black" />
          </div>
          <span 
            className="text-sm"
            style={{ color: 'var(--text-primary)' }}
          >
            {user?.name || 'admin'}
          </span>
        </div>
      </div>
    </header>
  );
}
