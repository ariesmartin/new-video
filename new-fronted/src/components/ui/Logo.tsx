import { Film, Sparkles } from 'lucide-react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  variant?: 'light' | 'dark';
}

export function Logo({ size = 'md', showText = true, variant = 'dark' }: LogoProps) {
  const sizeMap = {
    sm: { container: 28, icon: 14, fontSize: 'text-sm' },
    md: { container: 32, icon: 16, fontSize: 'text-base' },
    lg: { container: 40, icon: 20, fontSize: 'text-lg' },
  };

  const { container, icon, fontSize } = sizeMap[size];
  const isDark = variant === 'dark';

  return (
    <div className="flex items-center gap-2 select-none">
      <div
        className="relative rounded-xl flex items-center justify-center overflow-hidden flex-shrink-0"
        style={{
          width: container,
          height: container,
          background: isDark
            ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF6B35 100%)'
            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          boxShadow: '0 2px 8px rgba(255, 107, 53, 0.3)',
        }}
      >
        <Film size={icon} className="text-white relative z-10" />
        <Sparkles
          size={icon * 0.5}
          className="absolute top-1 right-1 text-white/80"
        />
      </div>

      {showText && (
        <div className="flex flex-col">
          <span
            className={`font-bold ${fontSize} tracking-tight`}
            style={{
              background: isDark
                ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF6B35 100%)'
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            幕境 Studio
          </span>
          <span className={`text-xs text-text-tertiary -mt-0.5`}>
            AI短剧创作台
          </span>
        </div>
      )}
    </div>
  );
}
