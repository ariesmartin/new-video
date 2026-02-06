import { 
  Plus, 
  Image as ImageIcon, 
  LayoutGrid, 
  Maximize
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface CanvasContextMenuProps {
  x: number;
  y: number;
  onClose: () => void;
  onCreateCard: () => void;
  onInsertImage: () => void;
  onAutoArrange: () => void;
  onResetView: () => void;
}

interface MenuItem {
  id: string;
  label: string;
  icon: LucideIcon;
  action: () => void;
  shortcut?: string;
}

export function CanvasContextMenu({ 
  x, 
  y, 
  onClose, 
  onCreateCard,
  onInsertImage,
  onAutoArrange,
  onResetView
}: CanvasContextMenuProps) {
  const menuItems: MenuItem[] = [
    { id: 'newCard', label: '新建卡片', icon: Plus, action: onCreateCard, shortcut: 'N' },
    { id: 'insertImage', label: '插入本地图片', icon: ImageIcon, action: onInsertImage },
    { id: 'divider1', label: '', icon: Plus, action: () => {} },
    { id: 'autoArrange', label: '自动整理', icon: LayoutGrid, action: onAutoArrange },
    { id: 'resetView', label: '视角复位', icon: Maximize, action: onResetView, shortcut: '0' },
  ];

  // 确保菜单不超出视口
  const menuStyle: React.CSSProperties = {
    position: 'fixed',
    left: Math.min(x, window.innerWidth - 200),
    top: Math.min(y, window.innerHeight - 200),
    zIndex: 1000,
  };

  return (
    <>
      <div 
        className="fixed inset-0 z-[999]"
        onClick={onClose}
      />
      <div
        className="rounded-lg py-1 shadow-xl overflow-hidden"
        style={{ 
          ...menuStyle,
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border)',
          minWidth: '180px'
        }}
      >
        {menuItems.map((item) => {
          if (item.id.startsWith('divider')) {
            return (
              <div 
                key={item.id}
                className="my-1"
                style={{ borderTop: '1px solid var(--border)' }}
              />
            );
          }

          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={(e) => {
                e.stopPropagation();
                item.action();
              }}
              className="w-full px-3 py-2 text-left text-sm flex items-center justify-between hover:bg-white/5 transition-colors"
              style={{ color: 'var(--text-primary)' }}
            >
              <div className="flex items-center gap-2">
                <Icon size={14} />
                {item.label}
              </div>
              {item.shortcut && (
                <span 
                  className="text-xs px-1.5 py-0.5 rounded"
                  style={{ 
                    backgroundColor: 'var(--bg-night)',
                    color: 'var(--text-tertiary)'
                  }}
                >
                  {item.shortcut}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </>
  );
}
