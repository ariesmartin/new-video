import { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface ResizablePanelProps {
  children: React.ReactNode;
  minWidth?: number;
  maxWidth?: number;
  defaultWidth?: number;
  className?: string;
  side?: 'left' | 'right';
  storageKey?: string;
}

export function ResizablePanel({
  children,
  minWidth = 280,
  maxWidth = 480,
  defaultWidth = 320,
  className,
  side = 'left',
  storageKey,
}: ResizablePanelProps) {
  const [width, setWidth] = useState(() => {
    if (storageKey && typeof window !== 'undefined') {
      try {
        const saved = window.localStorage.getItem(storageKey);
        if (saved) {
          const parsed = Number(saved);
          if (!isNaN(parsed)) return Math.min(Math.max(parsed, minWidth), maxWidth);
        }
      } catch (e) {
        console.error('Failed to load panel width', e);
      }
    }
    return defaultWidth;
  });
  
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    startXRef.current = e.clientX;
    startWidthRef.current = width;
  }, [width]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    
    // For 'left' side panel (handle on right), dragging right increases width
    // For 'right' side panel (handle on left), dragging left increases width
    const delta = side === 'left' 
      ? e.clientX - startXRef.current 
      : startXRef.current - e.clientX;
      
    const newWidth = Math.max(minWidth, Math.min(maxWidth, startWidthRef.current + delta));
    setWidth(newWidth);
  }, [isResizing, minWidth, maxWidth, side]);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
    if (storageKey && typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(storageKey, String(width));
      } catch (e) {
        console.error('Failed to save panel width', e);
      }
    }
  }, [width, storageKey]);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div
      ref={panelRef}
      className={cn('relative flex-shrink-0 h-full', className)}
      style={{ width }}
    >
      <div className="h-full overflow-hidden">{children}</div>
      
      <div
        onMouseDown={handleMouseDown}
        className={cn(
          'absolute top-0 bottom-0 w-1 cursor-col-resize z-50',
          'hover:bg-primary/50 transition-colors',
          side === 'left' ? 'right-0' : 'left-0',
          isResizing && 'bg-primary'
        )}
        style={{ transform: side === 'left' ? 'translateX(50%)' : 'translateX(-50%)' }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0.5 h-8 bg-border rounded-full opacity-0 hover:opacity-100 transition-opacity" />
      </div>
    </div>
  );
}
