import { useRef } from 'react';
import type { ShotConnection, ShotNode } from '@/types';

interface ConnectionLinesProps {
  connections: ShotConnection[];
  nodes: ShotNode[];
  getNodePosition: (node: ShotNode) => { x: number; y: number };
  onConnectionClick?: (connectionId: string, e: React.MouseEvent) => void;
  isConnecting?: boolean;
  connectionSource?: string | null;
  mousePosition?: { x: number; y: number };
}

export function ConnectionLines({
  connections,
  nodes,
  getNodePosition,
  onConnectionClick,
  isConnecting,
  connectionSource,
  mousePosition,
}: ConnectionLinesProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const getSourcePosition = () => {
    if (!connectionSource) return null;
    const sourceNode = nodes.find((n) => n.shotId === connectionSource);
    if (!sourceNode) return null;
    const pos = getNodePosition(sourceNode);
    return {
      x: pos.x + 60,
      y: pos.y + 40,
    };
  };

  const sourcePos = getSourcePosition();

  const calculatePath = (
    from: { x: number; y: number },
    to: { x: number; y: number }
  ) => {
    const dx = to.x - from.x;
    const controlOffset = Math.min(Math.abs(dx) * 0.5, 100);

    return `M ${from.x} ${from.y} 
            C ${from.x + controlOffset} ${from.y},
              ${to.x - controlOffset} ${to.y},
              ${to.x} ${to.y}`;
  };

  const getConnectionPoints = (connection: ShotConnection) => {
    const sourceNode = nodes.find((n) => n.shotId === connection.source);
    const targetNode = nodes.find((n) => n.shotId === connection.target);

    if (!sourceNode || !targetNode) return null;

    const sourcePos = getNodePosition(sourceNode);
    const targetPos = getNodePosition(targetNode);

    const from = {
      x: sourcePos.x + 120,
      y: sourcePos.y + 40,
    };

    const to = {
      x: targetPos.x,
      y: targetPos.y + 40,
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
        overflow: 'visible',
      }}
    >
      <defs>
        <marker
          id="arrowhead"
          markerWidth="12"
          markerHeight="8"
          refX="10"
          refY="4"
          orient="auto"
        >
          <polygon points="0 0, 12 4, 0 8" fill="hsl(var(--primary))" />
        </marker>

        <linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.3" />
          <stop offset="50%" stopColor="hsl(var(--primary))" stopOpacity="1" />
          <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.3" />
        </linearGradient>

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

      {connections.map((connection) => {
        const points = getConnectionPoints(connection);
        if (!points) return null;

        const path = calculatePath(points.from, points.to);

        return (
          <g key={connection.id} className="pointer-events-auto">
            <path
              d={path}
              stroke="transparent"
              strokeWidth="20"
              fill="none"
              className="cursor-pointer"
              onClick={(e) => onConnectionClick?.(connection.id, e)}
            />
            <path
              d={path}
              stroke="hsl(var(--primary))"
              strokeWidth="2"
              fill="none"
              markerEnd="url(#arrowhead)"
              className="flow-line"
            />
            <path
              d={path}
              stroke="hsl(var(--primary))"
              strokeWidth="6"
              fill="none"
              opacity="0.2"
              pointerEvents="none"
            />
          </g>
        );
      })}

      {isConnecting && sourcePos && mousePosition && (
        <g pointerEvents="none">
          <path
            d={calculatePath(sourcePos, mousePosition)}
            stroke="hsl(var(--primary))"
            strokeWidth="2"
            fill="none"
            strokeDasharray="5 5"
            opacity="0.8"
          />
          <circle
            cx={sourcePos.x}
            cy={sourcePos.y}
            r="8"
            fill="hsl(var(--primary))"
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
          <circle
            cx={sourcePos.x}
            cy={sourcePos.y}
            r="5"
            fill="hsl(var(--primary))"
          />
          <circle
            cx={mousePosition.x}
            cy={mousePosition.y}
            r="4"
            fill="hsl(var(--primary))"
            opacity="0.8"
          />
        </g>
      )}
    </svg>
  );
}
