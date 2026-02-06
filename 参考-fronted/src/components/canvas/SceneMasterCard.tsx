import { useState, useRef, useEffect } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Card } from '@/types';

interface SceneMasterCardProps {
  card: Card;
  isSelected: boolean;
  isConnecting: boolean;
  onClick: (e: React.MouseEvent) => void;
  onContextMenu: (e: React.MouseEvent) => void;
  onMove: (position: { x: number; y: number }) => void;
  zoom: number;
}

export function SceneMasterCard({ 
  card, 
  isSelected, 
  isConnecting,
  onClick, 
  onContextMenu, 
  onMove,
  zoom
}: SceneMasterCardProps) {
  const [isDragging, setIsDragging] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef({ x: 0, y: 0, cardX: 0, cardY: 0 });

  // 生成25格缩略图
  const generateThumbnails = () => {
    return Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      image: `https://picsum.photos/60/40?random=${card.number * 100 + i}`
    }));
  };

  const thumbnails = generateThumbnails();

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
        className="flex items-center justify-between p-2"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2">
          <span 
            className="text-xs font-medium"
            style={{ color: 'var(--text-tertiary)' }}
          >
            #{card.number}
          </span>
          <span 
            className="text-sm font-medium"
            style={{ color: 'var(--text-primary)' }}
          >
            Scene_Master
          </span>
        </div>
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

      {/* 25格网格 */}
      <div className="p-3">
        <div 
          className="grid grid-cols-5 gap-1"
          style={{ 
            backgroundColor: 'var(--bg-night)',
            padding: '4px',
            borderRadius: '4px'
          }}
        >
          {thumbnails.map((thumb) => (
            <div
              key={thumb.id}
              className="relative aspect-video overflow-hidden rounded cursor-pointer hover:opacity-80 transition-opacity"
            >
              <img
                src={thumb.image}
                alt={`Shot ${thumb.id}`}
                className="w-full h-full object-cover pointer-events-none"
                draggable={false}
              />
              <span 
                className="absolute top-0.5 left-0.5 text-[8px] font-medium px-1 rounded"
                style={{ 
                  backgroundColor: 'rgba(0,0,0,0.6)',
                  color: '#fff'
                }}
              >
                {thumb.id}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 场景信息 */}
      <div className="px-3 pb-2">
        <p 
          className="text-xs mb-2"
          style={{ color: 'var(--text-secondary)' }}
        >
          Scene: {card.content.description || `SCENE ${card.number} [原创] 大`}
        </p>
        <Button 
          className="w-full btn-primary text-xs py-1"
          onClick={(e) => {
            e.stopPropagation();
            console.log('Generate 25 shots for', card.id);
          }}
        >
          生成 25格 分镜
        </Button>
        <p 
          className="text-xs text-center mt-2"
          style={{ color: 'var(--text-tertiary)' }}
        >
          25 shots
        </p>
      </div>
    </div>
  );
}
