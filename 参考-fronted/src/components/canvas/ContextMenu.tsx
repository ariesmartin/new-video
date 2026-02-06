import { 
  Copy, 
  RefreshCw, 
  ArrowRight, 
  Link2, 
  Camera, 
  Paintbrush, 
  Expand, 
  Crop, 
  RotateCcw,
  Image as ImageIcon,
  Download,
  Trash2,
  type LucideIcon
} from 'lucide-react';
import type { Card } from '@/types';

interface ContextMenuProps {
  x: number;
  y: number;
  card: Card;
  onClose: () => void;
  onStartConnection: () => void;
  onDelete: () => void;
}

interface MenuItem {
  id: string;
  label: string;
  icon: LucideIcon;
  action: () => void;
  danger?: boolean;
  divider?: boolean;
}

export function ContextMenu({ 
  x, 
  y, 
  card, 
  onClose, 
  onStartConnection, 
  onDelete 
}: ContextMenuProps) {
  const menuItems: MenuItem[] = [
    { id: 'copy', label: '复制卡片', icon: Copy, action: () => console.log('Copy', card.id) },
    { id: 'regenerate', label: '重新生成', icon: RefreshCw, action: () => console.log('Regenerate', card.id) },
    { id: 'derive', label: '衍生下一张', icon: ArrowRight, action: () => console.log('Derive', card.id) },
    { id: 'divider1', label: '', icon: Copy, action: () => {}, divider: true },
    { id: 'connect', label: '连线', icon: Link2, action: onStartConnection },
    { id: 'camera', label: '镜头运镜', icon: Camera, action: () => console.log('Camera', card.id) },
    { id: 'divider2', label: '', icon: Copy, action: () => {}, divider: true },
    { id: 'inpaint', label: '局部重绘(Inpaint)', icon: Paintbrush, action: () => console.log('Inpaint', card.id) },
    { id: 'outpaint', label: '智能扩图(Outpaint)', icon: Expand, action: () => console.log('Outpaint', card.id) },
    { id: 'crop', label: '图片裁剪', icon: Crop, action: () => console.log('Crop', card.id) },
    { id: 'divider3', label: '', icon: Copy, action: () => {}, divider: true },
    { id: 'refresh', label: '刷新这张卡片', icon: RotateCcw, action: () => console.log('Refresh', card.id) },
    { id: 'extract', label: '提取为视觉资产', icon: ImageIcon, action: () => console.log('Extract', card.id) },
    { id: 'download', label: '下载原图', icon: Download, action: () => console.log('Download', card.id) },
    { id: 'divider4', label: '', icon: Copy, action: () => {}, divider: true },
    { id: 'delete', label: '删除卡片', icon: Trash2, action: onDelete, danger: true },
  ];

  // 确保菜单不超出视口
  const menuStyle: React.CSSProperties = {
    position: 'fixed',
    left: Math.min(x, window.innerWidth - 200),
    top: Math.min(y, window.innerHeight - 400),
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
          minWidth: '180px',
          maxWidth: '220px'
        }}
      >
        {menuItems.map((item) => {
          if (item.divider) {
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
              onClick={() => {
                item.action();
                onClose();
              }}
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-white/5 transition-colors"
              style={{ 
                color: item.danger ? 'var(--status-red)' : 'var(--text-primary)'
              }}
            >
              <Icon size={14} />
              {item.label}
            </button>
          );
        })}
      </div>
    </>
  );
}
