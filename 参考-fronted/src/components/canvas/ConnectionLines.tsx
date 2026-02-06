import { useRef } from 'react';
import type { Card, Connection } from '@/types';

interface ConnectionLinesProps {
  connections: Connection[];
  cards: Card[];
  getCardPosition: (card: Card) => { x: number; y: number };
  onConnectionClick?: (connectionId: string, e: React.MouseEvent) => void;
  isConnecting?: boolean;
  connectionSource?: string | null;
  mousePosition?: { x: number; y: number };
}

export function ConnectionLines({ 
  connections, 
  cards,
  getCardPosition,
  onConnectionClick,
  isConnecting,
  connectionSource,
  mousePosition
}: ConnectionLinesProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  // 获取源卡片位置（用于连线模式提示）
  const getSourcePosition = () => {
    if (!connectionSource) return null;
    const sourceCard = cards.find(c => c.id === connectionSource);
    if (!sourceCard) return null;
    const pos = getCardPosition(sourceCard);
    return {
      x: pos.x + sourceCard.size.width / 2,
      y: pos.y + sourceCard.size.height / 2
    };
  };

  const sourcePos = getSourcePosition();

  // 计算连线路径（使用贝塞尔曲线）
  const calculatePath = (from: { x: number; y: number }, to: { x: number; y: number }) => {
    const dx = to.x - from.x;
    const controlOffset = Math.min(Math.abs(dx) * 0.5, 100);
    
    return `M ${from.x} ${from.y} 
            C ${from.x + controlOffset} ${from.y},
              ${to.x - controlOffset} ${to.y},
              ${to.x} ${to.y}`;
  };

  // 获取连接点位置
  const getConnectionPoints = (connection: Connection) => {
    const sourceCard = cards.find(c => c.id === connection.source);
    const targetCard = cards.find(c => c.id === connection.target);
    
    if (!sourceCard || !targetCard) return null;
    
    const sourcePos = getCardPosition(sourceCard);
    const targetPos = getCardPosition(targetCard);
    
    // 从源卡片右侧中心出发，到目标卡片左侧中心
    const from = {
      x: sourcePos.x + sourceCard.size.width,
      y: sourcePos.y + sourceCard.size.height / 2
    };
    
    const to = {
      x: targetPos.x,
      y: targetPos.y + targetCard.size.height / 2
    };
    
    return { from, to };
  };

  return (
    <svg 
      ref={svgRef}
      className="absolute inset-0 pointer-events-none"
      style={{ 
        width: '100%', 
        height: '100%',
        overflow: 'visible'
      }}
    >
      <defs>
        {/* 箭头标记 */}
        <marker
          id="arrowhead"
          markerWidth="12"
          markerHeight="8"
          refX="10"
          refY="4"
          orient="auto"
        >
          <polygon
            points="0 0, 12 4, 0 8"
            fill="var(--primary)"
          />
        </marker>
        
        {/* 流动动画渐变 */}
        <linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.3" />
          <stop offset="50%" stopColor="var(--primary)" stopOpacity="1" />
          <stop offset="100%" stopColor="var(--primary)" stopOpacity="0.3" />
        </linearGradient>
        
        {/* 流动动画 */}
        <style>{`
          @keyframes flow {
            0% { stroke-dashoffset: 20; }
            100% { stroke-dashoffset: 0; }
          }
          .flow-line {
            stroke-dasharray: 5 5;
            animation: flow 0.5s linear infinite;
          }
        `}</style>
      </defs>

      {/* 渲染所有连线 */}
      {connections.map((connection) => {
        const points = getConnectionPoints(connection);
        if (!points) return null;
        
        const path = calculatePath(points.from, points.to);
        
        return (
          <g key={connection.id} className="pointer-events-auto">
            {/* 点击区域（更宽的透明线） */}
            <path
              d={path}
              stroke="transparent"
              strokeWidth="20"
              fill="none"
              className="cursor-pointer"
              onClick={(e) => onConnectionClick?.(connection.id, e)}
            />
            {/* 主连线 */}
            <path
              d={path}
              stroke="var(--primary)"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrowhead)"
              className="flow-line"
            />
            {/* 连线发光效果 */}
            <path
              d={path}
              stroke="var(--primary)"
              strokeWidth="6"
              fill="none"
              opacity="0.2"
              pointerEvents="none"
            />
          </g>
        );
      })}

      {/* 连线模式下的动态连线 */}
      {isConnecting && sourcePos && mousePosition && (
        <g pointerEvents="none">
          {/* 虚线连接 */}
          <path
            d={calculatePath(sourcePos, mousePosition)}
            stroke="var(--primary)"
            strokeWidth="2"
            fill="none"
            strokeDasharray="5 5"
            opacity="0.8"
          />
          {/* 源点脉冲 */}
          <circle
            cx={sourcePos.x}
            cy={sourcePos.y}
            r="8"
            fill="var(--primary)"
            opacity="0.5"
          >
            <animate
              attributeName="r"
              values="8;14;8"
              dur="1s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values="0.5;0.2;0.5"
              dur="1s"
              repeatCount="indefinite"
            />
          </circle>
          {/* 源点 */}
          <circle
            cx={sourcePos.x}
            cy={sourcePos.y}
            r="5"
            fill="var(--primary)"
          />
          {/* 鼠标跟随点 */}
          <circle
            cx={mousePosition.x}
            cy={mousePosition.y}
            r="4"
            fill="var(--primary)"
            opacity="0.8"
          />
        </g>
      )}
    </svg>
  );
}
