import { useState, useRef, useEffect } from 'react';
import { X, Undo, Redo, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface InpaintModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl?: string;
}

export function InpaintModal({ isOpen, onClose, imageUrl }: InpaintModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [brushColor, setBrushColor] = useState<'red' | 'blue' | 'yellow'>('red');
  const [brushSize, setBrushSize] = useState(20);
  const [isDrawing, setIsDrawing] = useState(false);
  const [prompt, setPrompt] = useState('');

  useEffect(() => {
    if (isOpen && canvasRef.current && imageUrl) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        const img = new Image();
        img.onload = () => {
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
        };
        img.src = imageUrl;
      }
    }
  }, [isOpen, imageUrl]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDrawing(true);
    draw(e);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDrawing) {
      draw(e);
    }
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);

    ctx.beginPath();
    ctx.arc(x, y, brushSize, 0, Math.PI * 2);
    ctx.fillStyle = brushColor === 'red' ? 'rgba(255, 0, 0, 0.5)' : 
                    brushColor === 'blue' ? 'rgba(0, 0, 255, 0.5)' : 
                    'rgba(255, 255, 0, 0.5)';
    ctx.fill();
  };

  const clearCanvas = () => {
    if (canvasRef.current && imageUrl) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        const img = new Image();
        img.onload = () => {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0);
        };
        img.src = imageUrl;
      }
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent 
        className="max-w-4xl max-h-[90vh] overflow-y-auto"
        style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}
      >
        <DialogHeader>
          <DialogTitle 
            className="flex items-center justify-between"
            style={{ color: 'var(--text-primary)' }}
          >
            局部重绘 (Inpaint)
            <button 
              onClick={onClose}
              className="p-1 rounded hover:bg-white/10 transition-colors"
            >
              <X size={20} style={{ color: 'var(--text-secondary)' }} />
            </button>
          </DialogTitle>
        </DialogHeader>

        {/* 工具栏 */}
        <div 
          className="flex items-center gap-2 p-2 rounded-lg mb-4"
          style={{ backgroundColor: 'var(--bg-night)' }}
        >
          <button
            onClick={() => setBrushColor('red')}
            className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
              brushColor === 'red' ? 'ring-2 ring-white' : ''
            }`}
            style={{ backgroundColor: '#ff4444' }}
            title="红色画笔 - 标记重绘区域"
          />
          <button
            onClick={() => setBrushColor('blue')}
            className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
              brushColor === 'blue' ? 'ring-2 ring-white' : ''
            }`}
            style={{ backgroundColor: '#4444ff' }}
            title="蓝色画笔 - 标记保护区域"
          />
          <button
            onClick={() => setBrushColor('yellow')}
            className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
              brushColor === 'yellow' ? 'ring-2 ring-white' : ''
            }`}
            style={{ backgroundColor: '#ffff44' }}
            title="黄色画笔 - 标记参考区域"
          />
          <div 
            className="w-px h-6 mx-2"
            style={{ backgroundColor: 'var(--border)' }}
          />
          <button
            onClick={clearCanvas}
            className="p-2 rounded hover:bg-white/10 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
            title="清空"
          >
            <Trash2 size={18} />
          </button>
          <button
            className="p-2 rounded hover:bg-white/10 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
            title="撤销"
          >
            <Undo size={18} />
          </button>
          <button
            className="p-2 rounded hover:bg-white/10 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
            title="重做"
          >
            <Redo size={18} />
          </button>
          <div className="flex items-center gap-2 ml-auto">
            <span 
              className="text-xs"
              style={{ color: 'var(--text-tertiary)' }}
            >
              画笔大小:
            </span>
            <input
              type="range"
              min="5"
              max="50"
              value={brushSize}
              onChange={(e) => setBrushSize(Number(e.target.value))}
              className="w-24"
            />
            <span 
              className="text-xs w-6"
              style={{ color: 'var(--text-secondary)' }}
            >
              {brushSize}
            </span>
          </div>
        </div>

        {/* 画布区域 */}
        <div 
          className="flex-1 overflow-auto flex items-center justify-center rounded-lg"
          style={{ 
            backgroundColor: 'var(--bg-night)',
            minHeight: '400px',
            maxHeight: '500px'
          }}
        >
          {imageUrl ? (
            <canvas
              ref={canvasRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="max-w-full max-h-full cursor-crosshair"
              style={{ objectFit: 'contain' }}
            />
          ) : (
            <div 
              className="text-center"
              style={{ color: 'var(--text-tertiary)' }}
            >
              请先选择一张图片
            </div>
          )}
        </div>

        {/* 提示词和操作 */}
        <div className="mt-4 flex items-end gap-4">
          <div className="flex-1">
            <label 
              className="text-xs block mb-1"
              style={{ color: 'var(--text-tertiary)' }}
            >
              提示词参考: 将红色区域修改XXX
            </label>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="输入提示词..."
              className="w-full input"
            />
          </div>
          <Button className="btn-primary px-6">
            开始生成
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
