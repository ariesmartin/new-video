import { useRef, useState, useEffect, useCallback } from 'react';
import ShotNodeComponent from './ShotNode';
import SceneMasterNodeComponent from './SceneMasterNode';
import { CanvasContextMenu } from './CanvasContextMenu';
import { ConnectionLines } from './ConnectionLines';
import { useCanvasStore, useEpisodeStore, useUIStore } from '@/hooks/useStore';
import { shotsService } from '@/api/services/shots';
import type { ShotNode, ShotConnection } from '@/types';

interface StoryboardCanvasProps {
  episodeId: string;
  onNodeSelect?: (node: ShotNode) => void;
  selectedNode?: ShotNode | null;
}

export function StoryboardCanvas({ episodeId, onNodeSelect }: StoryboardCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [canvasContextMenu, setCanvasContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [expandedScenes, setExpandedScenes] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  
  // Store Hooks
  const { 
    zoom, 
    offset, 
    gridVisible, 
    setZoom, 
    setOffset,
    selectedNodeIds,
    selectNode,
    deselectAll,
    isConnecting,
    connectionSource,
    endConnection,
    setMousePosition,
    isPanning,
    setIsPanning
  } = useCanvasStore();
  
  const { 
    shotNodes, 
    connections, 
    addConnection, 
    deleteConnection, 
    moveShotNode,
    loadEpisodeCanvas,
    clearEpisodeCanvas
  } = useEpisodeStore();
  
  const { addToast, openNodeEditPanel, closeRightPanel } = useUIStore();
  const mousePosition = useCanvasStore(state => state.mousePosition);

  // Load real data from API when episodeId changes
  useEffect(() => {
    if (!episodeId || episodeId === 'ep1') {
      // Clear canvas for demo/empty state
      clearEpisodeCanvas();
      return;
    }

    const loadShots = async () => {
      setIsLoading(true);
      try {
        const response = await shotsService.listShots(episodeId);
        const apiShots = response.data || [];
        
        // Convert API data to frontend ShotNode format
        const nodes: ShotNode[] = apiShots.map((shot: any) => ({
          shotId: shot.shotId,
          episodeId: shot.episodeId,
          sceneId: shot.sceneId || undefined,
          nodeType: shot.nodeType as 'shot' | 'scene_master',
          shotNumber: shot.shotNumber,
          title: shot.title,
          subtitle: shot.subtitle || undefined,
          status: shot.status as any,
          position: { x: shot.positionX || 0, y: shot.positionY || 0 },
          thumbnailUrl: shot.thumbnailUrl || undefined,
          imageUrl: shot.imageUrl || undefined,
          details: shot.details || undefined,
        }));

        // TODO: Load connections from API when available
        const shotConnections: ShotConnection[] = [];

        loadEpisodeCanvas({
          episodeId,
          viewport: { x: 0, y: 0, zoom: 1 },
          nodes,
          connections: shotConnections,
        });
        
        addToast({ type: 'success', message: `已加载 ${nodes.length} 个分镜` });
      } catch (error) {
        console.error('Failed to load shots:', error);
        addToast({ type: 'error', message: '加载分镜失败' });
      } finally {
        setIsLoading(false);
      }
    };

    loadShots();
  }, [episodeId, loadEpisodeCanvas, clearEpisodeCanvas, addToast]);

  // Local state for panning
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });

  // Handle Zoom - use native event listener with passive: false
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleWheelNative = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        setZoom(zoom * delta);
      }
    };

    canvas.addEventListener('wheel', handleWheelNative, { passive: false });
    return () => {
      canvas.removeEventListener('wheel', handleWheelNative);
    };
  }, [setZoom]);

  // Handle Panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // Middle mouse or Shift+Left for panning
    if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
      e.preventDefault();
    } else if (e.button === 0 && e.target === canvasRef.current) {
      // Click on empty space
      deselectAll();
      closeRightPanel();
      setCanvasContextMenu(null);
    }
  }, [offset, deselectAll, setIsPanning, closeRightPanel]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    // Update mouse position for connections
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      setMousePosition({
        x: (e.clientX - rect.left - offset.x) / zoom,
        y: (e.clientY - rect.top - offset.y) / zoom
      });
    }

    if (isPanning) {
      setOffset({
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y
      });
    }
  }, [isPanning, panStart, offset, zoom, setOffset, setMousePosition]);

  const handleMouseUp = useCallback(() => {
    setIsPanning(false);
  }, [setIsPanning]);

  const handleNodeSelect = (nodeId: string, multi?: boolean) => {
    if (isConnecting && connectionSource && connectionSource !== nodeId) {
      const newConnection: ShotConnection = {
        id: `conn_${Date.now()}`,
        source: connectionSource,
        target: nodeId,
        type: 'sequence'
      };
      addConnection(newConnection);
      addToast({ type: 'success', message: 'Connection created' });
      endConnection();
    } else {
      selectNode(nodeId, multi);
      const node = shotNodes.find(n => n.shotId === nodeId);
      if (node) {
        onNodeSelect?.(node);
        openNodeEditPanel(nodeId);
      }
    }
  };

  const handleNodeContextMenu = (e: React.MouseEvent, nodeId: string) => {
    e.preventDefault();
    e.stopPropagation();
    selectNode(nodeId);
    addToast({ type: 'info', message: `Context menu for node ${nodeId}` });
  };

  const handleCanvasContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setCanvasContextMenu({ x: e.clientX, y: e.clientY });
  };

  const handleNodeDragStart = (_nodeId: string) => {
    // Drag start logic if needed
  };

  const handleNodeDragEnd = (nodeId: string, position: { x: number; y: number }) => {
    moveShotNode(nodeId, position);
  };

  const handleConnectionClick = (connectionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this connection?')) {
      deleteConnection(connectionId);
      addToast({ type: 'success', message: 'Connection deleted' });
    }
  };

  // Scene Expansion
  const toggleSceneExpansion = (sceneId: string) => {
    setExpandedScenes(prev => {
      const next = new Set(prev);
      if (next.has(sceneId)) {
        next.delete(sceneId);
      } else {
        next.add(sceneId);
      }
      return next;
    });
  };

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        // Handle deletion of selected nodes
      }
      if (e.key === 'Escape') {
        if (isConnecting) {
          endConnection();
          addToast({ type: 'info', message: 'Connection cancelled' });
        }
        deselectAll();
        closeRightPanel();
        setCanvasContextMenu(null);
      }
      if (e.key === '0' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setZoom(1);
        setOffset({ x: 0, y: 0 });
        addToast({ type: 'info', message: 'View reset' });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isConnecting, deselectAll, endConnection, setZoom, setOffset, addToast]);

  if (isLoading) {
    return (
      <div className="flex-1 relative overflow-hidden bg-background flex items-center justify-center">
        <div className="text-text-secondary">加载分镜中...</div>
      </div>
    );
  }

  return (
    <div
      ref={canvasRef}
      className={`flex-1 relative overflow-hidden bg-background ${gridVisible ? 'canvas-grid' : ''}`}
      style={{
        cursor: isPanning ? 'grabbing' : isConnecting ? 'crosshair' : 'default'
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onContextMenu={handleCanvasContextMenu}
      onClick={() => setCanvasContextMenu(null)}
    >
      <div
        className="absolute inset-0"
        style={{
          transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
          transformOrigin: '0 0',
          transition: isPanning ? 'none' : 'transform 0.1s ease-out'
        }}
      >
        <ConnectionLines
          connections={connections}
          nodes={shotNodes}
          getNodePosition={(node) => node.position}
          onConnectionClick={handleConnectionClick}
          isConnecting={isConnecting}
          connectionSource={connectionSource}
          mousePosition={mousePosition}
        />

        {shotNodes.map((node) => {
          if (node.nodeType === 'scene_master') {
            const childNodes = shotNodes.filter(n => n.sceneId === node.sceneId && n.nodeType === 'shot');
            
            return (
              <SceneMasterNodeComponent
                key={node.shotId}
                masterNode={node}
                childNodes={childNodes}
                isExpanded={expandedScenes.has(node.sceneId || node.shotId)}
                isSelected={selectedNodeIds.includes(node.shotId)}
                onExpandToggle={() => toggleSceneExpansion(node.sceneId || node.shotId)}
                onSelect={handleNodeSelect}
                onChildSelect={(id) => handleNodeSelect(id)}
                onDragStart={(id) => handleNodeDragStart(id)}
                onChildReorder={() => {}}
                onContextMenu={handleNodeContextMenu}
              />
            );
          } else {
            return (
              <ShotNodeComponent
                key={node.shotId}
                node={node}
                isSelected={selectedNodeIds.includes(node.shotId)}
                onSelect={handleNodeSelect}
                onDragEnd={handleNodeDragEnd}
                onContextMenu={handleNodeContextMenu}
                onDoubleClick={(id) => {
                  addToast({ type: 'info', message: `Double clicked ${id}` });
                }}
              />
            );
          }
        })}
      </div>

      <div className="absolute bottom-20 left-4 flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg bg-surface/90 border border-border backdrop-blur-sm z-30">
        <button
          onClick={() => setZoom(zoom * 0.9)}
          className="w-6 h-6 sm:w-8 sm:h-8 flex items-center justify-center rounded hover:bg-primary/10 text-text-secondary"
        >
          -
        </button>
        <span className="text-xs sm:text-sm w-12 sm:w-16 text-center text-text-primary font-medium font-mono">
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={() => setZoom(zoom * 1.1)}
          className="w-6 h-6 sm:w-8 sm:h-8 flex items-center justify-center rounded hover:bg-primary/10 text-text-secondary"
        >
          +
        </button>
        <div className="w-px h-4 bg-border mx-1" />
        <button
          onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }}
          className="w-6 h-6 sm:w-8 sm:h-8 flex items-center justify-center rounded hover:bg-primary/10 ml-0.5 text-text-secondary"
          title="Reset View"
        >
          ⌂
        </button>
      </div>

      {isConnecting && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg flex items-center gap-2 bg-indigo-500 text-black">
          <span className="animate-pulse">●</span>
          Connection Mode: Click target node to connect, ESC to cancel
        </div>
      )}

      {shotNodes.length === 0 && !isLoading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-text-tertiary pointer-events-none z-10">
          <div className="text-4xl mb-4 opacity-20">🎬</div>
          <p className="text-lg font-medium opacity-50">暂无分镜</p>
          <p className="text-sm opacity-40 mt-2">点击顶部「剧本」开始创作，或右键创建节点</p>
        </div>
      )}

      {canvasContextMenu && (
        <CanvasContextMenu
          x={canvasContextMenu.x}
          y={canvasContextMenu.y}
          onClose={() => setCanvasContextMenu(null)}
          onCreateCard={() => addToast({ type: 'info', message: 'Create Node not implemented yet' })}
          onInsertImage={() => addToast({ type: 'info', message: 'Insert Image not implemented yet' })}
          onAutoArrange={() => addToast({ type: 'info', message: 'Auto Arrange not implemented yet' })}
          onResetView={() => {
            setZoom(1);
            setOffset({ x: 0, y: 0 });
            setCanvasContextMenu(null);
          }}
        />
      )}
    </div>
  );
}
