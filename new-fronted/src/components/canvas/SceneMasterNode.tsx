import React from 'react';
import { 
  Grid, 
  X, 
  Image as ImageIcon
} from 'lucide-react';
import type { ShotNode } from '@/types';

interface SceneMasterNodeProps {
  masterNode: ShotNode;
  childNodes: ShotNode[];
  isExpanded: boolean;
  isSelected: boolean;
  onExpandToggle: () => void;
  onSelect: (nodeId: string, multi?: boolean) => void;
  onChildSelect: (childNodeId: string) => void;
  onDragStart: (nodeId: string, e: React.DragEvent) => void;
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onChildReorder: (_sceneId: string, _newOrder: string[]) => void;
  onContextMenu: (e: React.MouseEvent, nodeId: string) => void;
}

  const statusColors = {
  pending: 'bg-status-gray',
  processing: 'bg-status-blue',
  completed: 'bg-status-green',
  approved: 'bg-status-cyan',
  revision: 'bg-status-yellow',
};



export default function SceneMasterNode({
  masterNode,
  childNodes,
  isExpanded,
  isSelected,
  onExpandToggle,
  onSelect,
  onChildSelect,
  onDragStart,
  onChildReorder: _onChildReorder,
  onContextMenu,
}: SceneMasterNodeProps) {
  // Determine position and size based on state
  const style: React.CSSProperties = {
    position: 'absolute',
    left: masterNode.position.x,
    top: masterNode.position.y,
    width: isExpanded ? 'min(650px, 90vw)' : '100px',
    height: isExpanded ? 'min(520px, 70vh)' : 'auto',
    minHeight: isExpanded ? 'auto' : '70px',
    zIndex: isExpanded ? 50 : 10,
    transition: 'width 0.3s ease, height 0.3s ease, background-color 0.3s',
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect(masterNode.shotId, e.shiftKey || e.metaKey);
  };

  // Prevent drag propagation when interacting with controls
  const handleControlMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  // Mini Shot Node Component (Internal for Grid)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const MiniShotNode = ({ shot, index: _index }: { shot: ShotNode; index: number }) => {
    return (
      <div
        className="relative flex flex-col items-center justify-center w-full h-full
                   bg-surface rounded border border-border hover:border-primary/50
                   cursor-pointer group overflow-hidden transition-colors"
        onClick={(e) => {
          e.stopPropagation();
          onChildSelect(shot.shotId);
        }}
        draggable
        onDragStart={(e) => {
          e.stopPropagation(); // Prevent moving the master node
          // Basic data transfer for reordering logic (implemented by parent usually, 
          // but we set data here)
          e.dataTransfer.setData('application/json', JSON.stringify({
            type: 'shot-reorder',
            shotId: shot.shotId,
            sceneId: masterNode.sceneId
          }));
        }}
      >
        {shot.thumbnailUrl ? (
          <img 
            src={shot.thumbnailUrl} 
            alt={shot.title} 
            className="absolute inset-0 w-full h-full object-cover opacity-50 group-hover:opacity-70 transition-opacity"
            draggable={false}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-text-tertiary">
            <ImageIcon size={24} />
          </div>
        )}

        {/* Overlay Content */}
        <div className="relative z-10 flex flex-col items-center gap-1">
          <span className="text-xs font-bold text-text-primary drop-shadow-md">
            #{shot.shotNumber}
          </span>
          <div className={`w-2 h-2 rounded-full ${statusColors[shot.status]} shadow-sm`} />
        </div>
      </div>
    );
  };

  return (
    <div
      style={style}
      className={`
        rounded-xl backdrop-blur select-none flex flex-col overflow-hidden
        ${isExpanded
          ? 'bg-surface border-2 border-primary shadow-2xl'
          : 'bg-elevated border-2 border-dashed border-primary/50 hover:border-primary'
        }
        ${isSelected && !isExpanded ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''}
      `}
      onMouseDown={handleMouseDown}
      onContextMenu={(e) => onContextMenu(e, masterNode.shotId)}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onExpandToggle();
      }}
      draggable={!isExpanded}
      onDragStart={(e) => !isExpanded && onDragStart(masterNode.shotId, e)}
    >
      {/* Header / Collapsed View */}
      <div className={`flex items-center justify-between px-2 sm:px-3 py-2 w-full min-h-[60px] sm:min-h-[70px] ${isExpanded ? 'h-auto border-b border-border' : ''}`}>

        {/* Left: Icon & Info */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-primary/10 text-primary">
            <Grid size={16} className="sm:w-5 sm:h-5" />
          </div>

          <div className="flex flex-col min-w-0">
            <span className="text-xs sm:text-sm font-bold text-text-primary truncate max-w-[60px] sm:max-w-[80px]">
               Scene {masterNode.shotNumber}
             </span>
             <span className="text-[10px] sm:text-xs text-text-secondary font-medium">
              {childNodes.length} shots
            </span>
          </div>
        </div>

        {/* Expanded View Controls */}
        {isExpanded && (
          <div className="flex items-center gap-1" onMouseDown={handleControlMouseDown}>
             <button 
              onClick={(e) => {
                e.stopPropagation();
                onExpandToggle();
              }}
               className="p-1.5 hover:bg-elevated rounded-md text-text-secondary hover:text-text-primary transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        )}
      </div>

      {/* Expanded Content: Grid */}
      {isExpanded && (
        <div 
          className="flex-1 p-4 overflow-y-auto overflow-x-hidden"
          onMouseDown={handleControlMouseDown} // Allow interaction within grid without selecting parent
        >
          <div
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2"
            style={{ minHeight: 'min(400px, 50vh)' }}
          >
            {/* Render grid slots */}
            {Array.from({ length: 25 }).map((_, index) => {
              const shot = childNodes[index];
              return (
                <div
                  key={shot ? shot.shotId : `empty-${index}`}
                  className="w-full aspect-[3/2]"
                >
                  {shot ? (
                    <MiniShotNode shot={shot} index={index} />
                  ) : (
                    // Empty Slot Placeholder
                     <div className="w-full h-full rounded border border-border/50 bg-elevated/50" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
