import { useRef, useState, useEffect, useCallback } from 'react';
import { ShotCard } from './ShotCard';
import { SceneMasterCard } from './SceneMasterCard';
import { CardContextMenu } from './CardContextMenu';
import { CanvasContextMenu } from './CanvasContextMenu';
import { ConnectionLines } from './ConnectionLines';
import { useCanvasStore, useProjectStore, useUIStore } from '@/hooks/useStore';
import type { Card } from '@/types';

interface StoryboardCanvasProps {
  onCardSelect?: (card: Card) => void;
  selectedCard?: Card | null;
}

// 示例卡片数据
const demoCards: Card[] = [
  {
    id: 'card1',
    type: 'scene_master',
    number: 1,
    title: 'Scene_Master',
    position: { x: 100, y: 100 },
    size: { width: 320, height: 400 },
    status: 'completed',
    content: {
      description: 'SCENE 1 [原创] 大',
      visualPrompt: '25-panel storyboard contact sheet'
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'chinese_3d'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
  {
    id: 'card2',
    type: 'scene_master',
    number: 2,
    title: 'Scene_Master',
    position: { x: 450, y: 100 },
    size: { width: 320, height: 400 },
    status: 'completed',
    content: {
      description: 'SCENE 2',
      visualPrompt: '25-panel storyboard'
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'chinese_3d'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
  {
    id: 'card3',
    type: 'shot',
    number: 11,
    title: '俯视镜头(High Angle)',
    subtitle: '旋转(Orbit)',
    position: { x: 800, y: 100 },
    size: { width: 280, height: 200 },
    imageUrl: 'https://picsum.photos/400/225?random=11',
    status: 'completed',
    content: {
      dialogue: '"林恩"（喘息）：呼...呼...',
      sound: '风啸声'
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'cinematic_realistic'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
  {
    id: 'card4',
    type: 'shot',
    number: 15,
    title: '微距镜头(Macro)',
    subtitle: '静态(Static)',
    position: { x: 1100, y: 100 },
    size: { width: 280, height: 200 },
    imageUrl: 'https://picsum.photos/400/225?random=15',
    status: 'completed',
    content: {
      dialogue: '',
      sound: '沉重的靴子踩碎骨骼'
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'cinematic_realistic'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
  {
    id: 'card5',
    type: 'scene_master',
    number: 3,
    title: 'Scene_Master',
    position: { x: 100, y: 520 },
    size: { width: 320, height: 400 },
    status: 'completed',
    content: {
      description: 'SCENE 3',
      visualPrompt: '25-panel storyboard'
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'chinese_3d'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
  {
    id: 'card6',
    type: 'scene_master',
    number: 4,
    title: 'Scene_Master',
    position: { x: 450, y: 520 },
    size: { width: 320, height: 400 },
    status: 'completed',
    content: {
      description: 'SCENE 4',
      visualPrompt: '25-panel storyboard'
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'chinese_3d'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
  {
    id: 'card7',
    type: 'shot',
    number: 12,
    title: '极细特写(Extreme Close-up)',
    subtitle: '焦点转换(Rack Focus)',
    position: { x: 800, y: 350 },
    size: { width: 280, height: 200 },
    imageUrl: 'https://picsum.photos/400/225?random=12',
    status: 'completed',
    content: {
      dialogue: '',
      sound: '风暴中心的奇异极光'
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'cinematic_realistic'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
  {
    id: 'card8',
    type: 'shot',
    number: 16,
    title: '过肩镜头(OTS)',
    subtitle: '极深景深(Deep Focus)',
    position: { x: 1100, y: 350 },
    size: { width: 280, height: 200 },
    imageUrl: 'https://picsum.photos/400/225?random=16',
    status: 'completed',
    content: {
      dialogue: '"林恩：伊甸园..."',
      sound: ''
    },
    params: {
      resolution: '2K',
      aspectRatio: '16:9',
      style: 'cinematic_realistic'
    },
    links: { children: [], references: [] },
    referenceImages: {}
  },
];

// 示例连线数据
const demoConnections = [
  { id: 'conn1', source: 'card1', target: 'card3' },
  { id: 'conn2', source: 'card1', target: 'card4' },
  { id: 'conn3', source: 'card2', target: 'card7' },
  { id: 'conn4', source: 'card2', target: 'card8' },
];

export function StoryboardCanvas({ onCardSelect }: StoryboardCanvasProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [cardContextMenu, setCardContextMenu] = useState<{ x: number; y: number; card: Card } | null>(null);
  const [canvasContextMenu, setCanvasContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [cardPositions, setCardPositions] = useState<Record<string, { x: number; y: number }>>(() => {
    const positions: Record<string, { x: number; y: number }> = {};
    demoCards.forEach(card => {
      positions[card.id] = { ...card.position };
    });
    return positions;
  });
  
  const { 
    zoom, 
    offset, 
    gridVisible, 
    setZoom, 
    setOffset,
    selectedCards,
    selectCard,
    deselectAll,
    isConnecting,
    connectionSource,
    startConnection,
    endConnection,
    setMousePosition
  } = useCanvasStore();
  
  const { connections, addConnection, deleteConnection, duplicateCard } = useProjectStore();
  const { openModal, addToast } = useUIStore();

  const allConnections = connections.length > 0 ? connections : demoConnections;

  // 处理滚轮缩放
  const handleWheel = useCallback((e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setZoom(zoom * delta);
    }
  }, [zoom, setZoom]);

  // 处理画布拖拽平移
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // 中键或 Space+左键 平移画布
    if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
      e.preventDefault();
    } else if (e.button === 0 && e.target === canvasRef.current) {
      // 点击空白处取消选择
      deselectAll();
    }
  }, [offset, deselectAll]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    // 更新鼠标位置（用于连线）
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
  }, []);

  // 处理卡片选择
  const handleCardClick = (card: Card, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (isConnecting && connectionSource && connectionSource !== card.id) {
      // 完成连线
      const newConnection = {
        id: `conn_${Date.now()}`,
        source: connectionSource,
        target: card.id
      };
      addConnection(newConnection);
      addToast({ type: 'success', message: '连线创建成功' });
      endConnection();
    } else {
      selectCard(card.id, e.ctrlKey || e.metaKey);
      onCardSelect?.(card);
    }
  };

  // 处理卡片右键菜单
  const handleCardContextMenu = (card: Card, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setCardContextMenu({ x: e.clientX, y: e.clientY, card });
    setCanvasContextMenu(null);
  };

  // 处理画布右键菜单
  const handleCanvasContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setCanvasContextMenu({ x: e.clientX, y: e.clientY });
    setCardContextMenu(null);
  };

  // 关闭右键菜单
  const closeContextMenus = () => {
    setCardContextMenu(null);
    setCanvasContextMenu(null);
  };

  // 处理卡片移动
  const handleCardMove = (cardId: string, newPosition: { x: number; y: number }) => {
    setCardPositions(prev => ({
      ...prev,
      [cardId]: newPosition
    }));
  };

  // 获取卡片的实际位置
  const getCardPosition = (card: Card) => {
    return cardPositions[card.id] || card.position;
  };

  // 处理连线删除
  const handleConnectionClick = (connectionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('确定要删除这条连线吗？')) {
      deleteConnection(connectionId);
      addToast({ type: 'success', message: '连线已删除' });
    }
  };

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Delete 删除选中卡片
      if (e.key === 'Delete' || e.key === 'Backspace') {
        selectedCards.forEach((_cardId: string) => {
          // deleteCard(cardId);
        });
        deselectAll();
      }
      // ESC 取消连线模式
      if (e.key === 'Escape') {
        if (isConnecting) {
          endConnection();
          addToast({ type: 'info', message: '已取消连线' });
        }
        deselectAll();
        closeContextMenus();
      }
      // Ctrl+0 重置视图
      if (e.key === '0' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setZoom(1);
        setOffset({ x: 0, y: 0 });
        addToast({ type: 'info', message: '视图已重置' });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedCards, isConnecting, deselectAll, endConnection, setZoom, setOffset, addToast]);

  // 连线相关操作
  const handleStartConnection = (cardId: string) => {
    startConnection(cardId);
    addToast({ type: 'info', message: '连线模式：点击目标卡片完成连接' });
  };

  const handleDuplicateCard = (cardId: string) => {
    duplicateCard(cardId);
    addToast({ type: 'success', message: '卡片已复制' });
  };

  const handleDeleteCard = (_cardId: string) => {
    if (confirm('确定要删除这张卡片吗？')) {
      // deleteCard(cardId);
      addToast({ type: 'success', message: '卡片已删除' });
    }
  };

  // 画布操作
  const handleAutoArrange = () => {
    addToast({ type: 'info', message: '自动整理功能开发中' });
  };

  const handleInsertImage = () => {
    addToast({ type: 'info', message: '插入图片功能开发中' });
  };

  const handleCreateCard = () => {
    addToast({ type: 'info', message: '新建卡片功能开发中' });
  };

  return (
    <div 
      ref={canvasRef}
      className={`flex-1 relative overflow-hidden ${gridVisible ? 'canvas-grid' : ''}`}
      style={{ 
        backgroundColor: 'var(--bg-night)',
        cursor: isPanning ? 'grabbing' : isConnecting ? 'crosshair' : 'default'
      }}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onContextMenu={handleCanvasContextMenu}
      onClick={closeContextMenus}
    >
      {/* 画布内容 */}
      <div
        className="absolute inset-0"
        style={{
          transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
          transformOrigin: '0 0',
          transition: isPanning ? 'none' : 'transform 0.1s ease-out'
        }}
      >
        {/* 连线层 */}
        <ConnectionLines 
          connections={allConnections}
          cards={demoCards}
          getCardPosition={getCardPosition}
          onConnectionClick={handleConnectionClick}
          isConnecting={isConnecting}
          connectionSource={connectionSource}
          mousePosition={useCanvasStore(state => state.mousePosition)}
        />

        {/* 卡片层 */}
        {demoCards.map((card: Card) => {
          const position = getCardPosition(card);
          const cardWithPosition = { ...card, position };
          
          return card.type === 'scene_master' ? (
            <SceneMasterCard
              key={card.id}
              card={cardWithPosition}
              isSelected={selectedCards.includes(card.id)}
              isConnecting={isConnecting && connectionSource === card.id}
              onClick={(e) => handleCardClick(card, e)}
              onContextMenu={(e) => handleCardContextMenu(card, e)}
              onMove={(pos) => handleCardMove(card.id, pos)}
              zoom={zoom}
            />
          ) : (
            <ShotCard
              key={card.id}
              card={cardWithPosition}
              isSelected={selectedCards.includes(card.id)}
              isConnecting={isConnecting && connectionSource === card.id}
              onClick={(e) => handleCardClick(card, e)}
              onContextMenu={(e) => handleCardContextMenu(card, e)}
              onMove={(pos) => handleCardMove(card.id, pos)}
              zoom={zoom}
            />
          );
        })}
      </div>

      {/* 缩放控制 */}
      <div 
        className="absolute bottom-4 left-4 flex items-center gap-2 px-3 py-2 rounded-lg"
        style={{ 
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border)'
        }}
      >
        <button
          onClick={() => setZoom(zoom * 0.9)}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-white/5"
          style={{ color: 'var(--text-secondary)' }}
        >
          -
        </button>
        <span 
          className="text-sm w-16 text-center"
          style={{ color: 'var(--text-primary)' }}
        >
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={() => setZoom(zoom * 1.1)}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-white/5"
          style={{ color: 'var(--text-secondary)' }}
        >
          +
        </button>
        <button
          onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-white/5 ml-2"
          style={{ color: 'var(--text-secondary)' }}
        >
          ⌂
        </button>
      </div>

      {/* 连线模式提示 */}
      {isConnecting && (
        <div 
          className="absolute top-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg flex items-center gap-2"
          style={{ 
            backgroundColor: 'var(--primary)',
            color: '#000'
          }}
        >
          <span className="animate-pulse">●</span>
          连线模式：点击目标卡片完成连接，按 ESC 取消
        </div>
      )}

      {/* 卡片右键菜单 */}
      {cardContextMenu && (
        <CardContextMenu
          x={cardContextMenu.x}
          y={cardContextMenu.y}
          card={cardContextMenu.card}
          onClose={closeContextMenus}
          onStartConnection={() => {
            handleStartConnection(cardContextMenu.card.id);
            closeContextMenus();
          }}
          onDuplicate={() => {
            handleDuplicateCard(cardContextMenu.card.id);
            closeContextMenus();
          }}
          onDelete={() => {
            handleDeleteCard(cardContextMenu.card.id);
            closeContextMenus();
          }}
          onInpaint={() => {
            openModal('inpaint', cardContextMenu.card);
            closeContextMenus();
          }}
          onOutpaint={() => {
            openModal('outpaint', cardContextMenu.card);
            closeContextMenus();
          }}
          onVirtualCamera={() => {
            openModal('virtualCamera', cardContextMenu.card);
            closeContextMenus();
          }}
          onCameraMove={() => {
            openModal('cameraMove', cardContextMenu.card);
            closeContextMenus();
          }}
        />
      )}

      {/* 画布右键菜单 */}
      {canvasContextMenu && (
        <CanvasContextMenu
          x={canvasContextMenu.x}
          y={canvasContextMenu.y}
          onClose={closeContextMenus}
          onCreateCard={handleCreateCard}
          onInsertImage={handleInsertImage}
          onAutoArrange={handleAutoArrange}
          onResetView={() => {
            setZoom(1);
            setOffset({ x: 0, y: 0 });
            closeContextMenus();
          }}
        />
      )}
    </div>
  );
}
