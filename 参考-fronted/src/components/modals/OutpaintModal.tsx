import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface OutpaintModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl?: string;
}

export function OutpaintModal({ isOpen, onClose, imageUrl }: OutpaintModalProps) {
  const [scale, setScale] = useState(1.5);
  const [prompt, setPrompt] = useState('');

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
            智能扩图 (Outpaint)
            <button 
              onClick={onClose}
              className="p-1 rounded hover:bg-white/10 transition-colors"
            >
              <X size={20} style={{ color: 'var(--text-secondary)' }} />
            </button>
          </DialogTitle>
        </DialogHeader>

        {/* 缩放控制 */}
        <div className="flex items-center gap-4 mb-4">
          <span 
            className="text-sm"
            style={{ color: 'var(--text-secondary)' }}
          >
            画面缩放:
          </span>
          <Slider
            value={[scale]}
            onValueChange={(value) => setScale(value[0])}
            min={1}
            max={2}
            step={0.1}
            className="flex-1"
          />
          <span 
            className="text-sm w-12"
            style={{ color: 'var(--text-primary)' }}
          >
            {scale.toFixed(1)}x
          </span>
        </div>

        {/* 预览区域 */}
        <div 
          className="flex-1 overflow-auto flex items-center justify-center rounded-lg p-8"
          style={{ 
            backgroundColor: 'var(--bg-night)',
            minHeight: '400px',
            maxHeight: '500px'
          }}
        >
          {imageUrl ? (
            <div 
              className="relative"
              style={{
                width: `${scale * 100}%`,
                maxWidth: '800px',
                aspectRatio: '16/9',
                backgroundColor: 'rgba(255, 0, 0, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <img
                src={imageUrl}
                alt="Original"
                className="max-w-full max-h-full object-contain"
                style={{
                  width: `${100 / scale}%`,
                  height: `${100 / scale}%`
                }}
              />
              {/* 红色区域提示 */}
              <div 
                className="absolute inset-0 pointer-events-none"
                style={{
                  background: `
                    linear-gradient(to right, rgba(255,0,0,0.3) 0%, rgba(255,0,0,0.3) ${((scale - 1) / scale) * 50}%, transparent ${((scale - 1) / scale) * 50}%, transparent ${100 - ((scale - 1) / scale) * 50}%, rgba(255,0,0,0.3) ${100 - ((scale - 1) / scale) * 50}%, rgba(255,0,0,0.3) 100%),
                    linear-gradient(to bottom, rgba(255,0,0,0.3) 0%, rgba(255,0,0,0.3) ${((scale - 1) / scale) * 50}%, transparent ${((scale - 1) / scale) * 50}%, transparent ${100 - ((scale - 1) / scale) * 50}%, rgba(255,0,0,0.3) ${100 - ((scale - 1) / scale) * 50}%, rgba(255,0,0,0.3) 100%)
                  `
                }}
              />
              <div 
                className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs px-2 py-1 rounded"
                style={{ 
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: '#fff'
                }}
              >
                红色区域表示待填充区域
              </div>
            </div>
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
              请根据图片，填充红色区域
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
