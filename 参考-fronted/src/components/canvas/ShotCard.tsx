import { useState, useRef, useEffect } from 'react';
import { X, Video } from 'lucide-react';
import type { Card } from '@/types';

interface ShotCardProps {
  card: Card;
  isSelected: boolean;
  isConnecting: boolean;
  onClick: (e: React.MouseEvent) => void;
  onContextMenu: (e: React.MouseEvent) => void;
  onMove: (position: { x: number; y: number }) => void;
  zoom: number;
}

export function ShotCard({ 
  card, 
  isSelected, 
  isConnecting,
  onClick, 
  onContextMenu, 
  onMove,
  zoom
}: ShotCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef({ x: 0, y: 0, cardX: 0, cardY: 0 });

  const getStatusColor = () => {
    switch (card.status) {
      case 'pending': return 'var(--status-red)';
      case 'processing': return 'var(--status-yellow)';
      case 'completed': return 'var(--status-green)';
      case 'approved': return 'var(--status-blue)';
      case 'revision': return 'var(--status-orange)';
      default: return 'var(--status-red)';
    }
  };

  // 处理鼠标按下 - 开始拖拽
  const handleMouseDown = (e: React.MouseEvent) => {
    // 只有左键且不是点击按钮时才拖拽
    if (e.button === 0 && !(e.target as HTMLElement).closest('button')) {
      e.stopPropagation();
      setIsDragging(true);
      
      dragStartRef.current = {
        x: e.clientX,
        y: e.clientY,
        cardX: card.position.x,
        cardY: card.position.y
      };
    }
  };

  // 全局鼠标移动处理
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        // 计算鼠标移动的差值（考虑缩放）
        const deltaX = (e.clientX - dragStartRef.current.x) / zoom;
        const deltaY = (e.clientY - dragStartRef.current.y) / zoom;
        
        // 更新卡片位置
        onMove({
          x: dragStartRef.current.cardX + deltaX,
          y: dragStartRef.current.cardY + deltaY
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, onMove, zoom]);

  return (
    <div
      ref={cardRef}
      className={`
        absolute rounded-lg overflow-hidden select-none
        ${isSelected ? 'ring-2 ring-[var(--primary)]' : ''}
        ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}
        ${isConnecting ? 'ring-2 ring-dashed ring-yellow-500' : ''}
      `}
      style={{
        left: card.position.x,
        top: card.position.y,
        width: card.size.width,
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border)',
        boxShadow: isSelected 
          ? '0 8px 24px rgba(0,0,0,0.3)' 
          : '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: isDragging ? 100 : isSelected ? 10 : 1
      }}
      onMouseDown={handleMouseDown}
      onClick={onClick}
      onContextMenu={onContextMenu}
    >
      {/* 卡片头部 */}
      <div 
        className="flex items-start justify-between p-2"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span 
              className="text-xs font-medium"
              style={{ color: 'var(--text-tertiary)' }}
            >
              #{card.number}
            </span>
            <span 
              className="text-sm font-medium truncate"
              style={{ color: 'var(--text-primary)' }}
            >
              {card.title}
            </span>
          </div>
          {card.subtitle && (
            <p 
              className="text-xs truncate mt-0.5"
              style={{ color: 'var(--text-secondary)' }}
            >
              {card.subtitle}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1">
          {card.id.includes('video') && (
            <Video size={14} style={{ color: 'var(--primary)' }} />
          )}
          <button 
            className="p-1 rounded hover:bg-white/10 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              console.log('Close card', card.id);
            }}
          >
            <X size={14} style={{ color: 'var(--text-tertiary)' }} />
          </button>
        </div>
      </div>

      {/* 卡片图片 */}
      <div 
        className="relative"
        style={{ aspectRatio: '16/9' }}
      >
        {card.imageUrl ? (
          <img
            src={card.imageUrl}
            alt={`Shot ${card.number}`}
            className="w-full h-full object-cover pointer-events-none"
            draggable={false}
          />
        ) : (
          <div 
            className="w-full h-full flex items-center justify-center"
            style={{ backgroundColor: 'var(--bg-night)' }}
          >
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{ 
                backgroundColor: 'rgba(255, 215, 0, 0.1)',
                border: '2px dashed var(--primary)'
              }}
            >
              <span style={{ color: 'var(--primary)' }}>+</span>
            </div>
          </div>
        )}
        
        {/* 状态指示器 */}
        <div 
          className="absolute top-2 right-2 w-3 h-3 rounded-full"
          style={{ backgroundColor: getStatusColor() }}
        />
      </div>

      {/* 卡片内容 */}
      {(card.content.dialogue || card.content.sound) && (
        <div className="p-2 space-y-1">
          {card.content.dialogue && (
            <p 
              className="text-xs truncate"
              style={{ color: 'var(--text-secondary)' }}
            >
              {card.content.dialogue}
            </p>
          )}
          {card.content.sound && (
            <p 
              className="text-xs truncate"
              style={{ color: 'var(--text-tertiary)' }}
            >
              (环境音): {card.content.sound}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
