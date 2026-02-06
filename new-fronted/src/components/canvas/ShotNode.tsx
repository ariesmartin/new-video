import React, { memo } from 'react';
import { statusColors, type ShotNode as IShotNode } from '@/types/shotNode';

interface ShotNodeProps {
  node: IShotNode;
  isSelected: boolean;
  onSelect: (nodeId: string, multi?: boolean) => void;
  // onDragStart: (nodeId: string) => void;
  onDragEnd: (nodeId: string, position: { x: number; y: number }) => void;
  onContextMenu: (e: React.MouseEvent, nodeId: string) => void;
  onDoubleClick?: (nodeId: string) => void; // Added to support the double-click requirement
}

const ShotNode: React.FC<ShotNodeProps> = ({
  node,
  isSelected,
  onSelect,
  // onDragStart,
  onDragEnd,
  onContextMenu,
  onDoubleClick,
}) => {
  // Memoize status color to avoid lookup on every render
  const statusColor = statusColors[node.status] || statusColors.pending;

  const handleMouseDown = (e: React.MouseEvent) => {
    // Stop propagation to prevent canvas panning if applicable
    e.stopPropagation();
    
    // Handle selection
    // CMD/CTRL/SHIFT for multi-select
    const isMulti = e.ctrlKey || e.metaKey || e.shiftKey;
    onSelect(node.shotId, isMulti);
    
    // Notify drag start
    // onDragStart(node.shotId);
  };

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDoubleClick?.(node.shotId);
  };

  return (
    <div
      className={`
        absolute flex flex-col
        w-[100px] sm:w-[120px] h-[70px] sm:h-[80px] p-1 sm:p-1.5
        bg-surface backdrop-blur-sm
        rounded-lg shadow-lg
        transition-transform duration-200
        hover:scale-[1.02] hover:shadow-xl
        cursor-pointer
        group
        ${isSelected
          ? 'border-2 border-primary z-50'
          : 'border border-border hover:border-primary/50 z-10'
        }
      `}
      style={{
        left: node.position.x,
        top: node.position.y,
      }}
      onMouseDown={handleMouseDown}
      onContextMenu={(e) => onContextMenu(e, node.shotId)}
      onDoubleClick={handleDoubleClick}
      onMouseUp={() => {
        // Simple drag end simulation if needed or rely on parent
        onDragEnd(node.shotId, { x: node.position.x, y: node.position.y });
      }}
      role="button"
      aria-label={`Shot ${node.shotNumber}: ${node.title}`}
      tabIndex={0}
    >
      {/* Top Bar: Shot Number */}
      <div className="flex items-center justify-between px-0.5 sm:px-1 mb-0.5">
        <span className="text-xs sm:text-sm font-bold text-text-primary leading-none">
          {node.shotNumber}
        </span>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col items-center min-h-0 relative">

        <div className="w-full text-[10px] sm:text-xs leading-tight text-text-secondary line-clamp-2 text-center select-none mb-0.5 sm:mb-1">
          {node.title}
        </div>

        {(node.thumbnailUrl || node.imageUrl) && (
          <div className="w-[50px] sm:w-[60px] h-[32px] sm:h-[40px] flex-shrink-0 rounded-sm overflow-hidden bg-elevated">
             <img
              src={node.thumbnailUrl || node.imageUrl}
              alt={node.title}
              className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
              draggable={false}
            />
          </div>
        )}
      </div>

      <div 
        className="absolute bottom-0 left-0 right-0 h-1 rounded-b-lg overflow-hidden z-0"
      >
          <div className="w-full h-full opacity-80" style={{ backgroundColor: statusColor }} />
      </div>
    </div>
  );
};

export default memo(ShotNode);
