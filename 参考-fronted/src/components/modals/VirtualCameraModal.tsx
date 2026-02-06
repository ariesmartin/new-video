import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface VirtualCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl?: string;
}

export function VirtualCameraModal({ isOpen, onClose, imageUrl }: VirtualCameraModalProps) {
  const [horizontalAngle, setHorizontalAngle] = useState(57);
  const [verticalAngle, setVerticalAngle] = useState(-64);
  const [zoom, setZoom] = useState(4.0);
  const [focalLength, setFocalLength] = useState('50mm');
  const [aperture, setAperture] = useState('f/2.8');

  const focalLengths = ['24mm', '35mm', '50mm', '85mm', '135mm', '200mm'];
  const apertures = ['f/1.4', 'f/1.8', 'f/2.8', 'f/4', 'f/5.6', 'f/8', 'f/11', 'f/16', 'f/22'];

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
            <span>
              虚拟摄像机(Virtual Camera)
              <span 
                className="text-xs ml-2 font-normal"
                style={{ color: 'var(--text-tertiary)' }}
              >
                ---有失败概率
              </span>
            </span>
            <button 
              onClick={onClose}
              className="p-1 rounded hover:bg-white/10 transition-colors"
            >
              <X size={20} style={{ color: 'var(--text-secondary)' }} />
            </button>
          </DialogTitle>
        </DialogHeader>

        {/* 3D预览区域 */}
        <div 
          className="flex-1 overflow-hidden flex items-center justify-center rounded-lg"
          style={{ 
            backgroundColor: 'var(--bg-night)',
            minHeight: '300px',
            maxHeight: '400px'
          }}
        >
          {imageUrl ? (
            <div className="relative w-full h-full flex items-center justify-center">
              <img
                src={imageUrl}
                alt="Preview"
                className="max-w-full max-h-full object-contain transition-transform duration-300"
                style={{
                  transform: `
                    perspective(1000px) 
                    rotateY(${horizontalAngle}deg) 
                    rotateX(${-verticalAngle}deg) 
                    scale(${zoom / 4})
                  `
                }}
              />
              <div 
                className="absolute bottom-4 left-4 text-xs px-2 py-1 rounded"
                style={{ 
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  color: '#fff'
                }}
              >
                可拖拽旋转视角
              </div>
            </div>
          ) : (
            <div 
              className="text-center"
              style={{ color: 'var(--text-tertiary)' }}
            >
              3D预览区域
            </div>
          )}
        </div>

        {/* 参数控制 */}
        <div className="space-y-4 mt-4">
          {/* 水平角度 */}
          <div className="flex items-center gap-4">
            <span 
              className="text-sm w-20"
              style={{ color: 'var(--text-secondary)' }}
            >
              水平角度:
            </span>
            <span 
              className="text-xs w-12"
              style={{ color: 'var(--text-tertiary)' }}
            >
              -180°
            </span>
            <Slider
              value={[horizontalAngle]}
              onValueChange={(value) => setHorizontalAngle(value[0])}
              min={-180}
              max={180}
              step={1}
              className="flex-1"
            />
            <span 
              className="text-xs w-12"
              style={{ color: 'var(--text-tertiary)' }}
            >
              +180°
            </span>
            <span 
              className="text-sm w-12 text-right"
              style={{ color: 'var(--text-primary)' }}
            >
              ({horizontalAngle}°)
            </span>
          </div>

          {/* 垂直角度 */}
          <div className="flex items-center gap-4">
            <span 
              className="text-sm w-20"
              style={{ color: 'var(--text-secondary)' }}
            >
              垂直角度:
            </span>
            <span 
              className="text-xs w-12"
              style={{ color: 'var(--text-tertiary)' }}
            >
              -90°
            </span>
            <Slider
              value={[verticalAngle]}
              onValueChange={(value) => setVerticalAngle(value[0])}
              min={-90}
              max={90}
              step={1}
              className="flex-1"
            />
            <span 
              className="text-xs w-12"
              style={{ color: 'var(--text-tertiary)' }}
            >
              +90°
            </span>
            <span 
              className="text-sm w-12 text-right"
              style={{ color: 'var(--text-primary)' }}
            >
              ({verticalAngle}°)
            </span>
          </div>

          {/* 推拉镜头 */}
          <div className="flex items-center gap-4">
            <span 
              className="text-sm w-20"
              style={{ color: 'var(--text-secondary)' }}
            >
              推拉镜头:
            </span>
            <span 
              className="text-xs w-12"
              style={{ color: 'var(--text-tertiary)' }}
            >
              0.5x
            </span>
            <Slider
              value={[zoom]}
              onValueChange={(value) => setZoom(value[0])}
              min={0.5}
              max={5}
              step={0.1}
              className="flex-1"
            />
            <span 
              className="text-xs w-12"
              style={{ color: 'var(--text-tertiary)' }}
            >
              5.0x
            </span>
            <span 
              className="text-sm w-12 text-right"
              style={{ color: 'var(--text-primary)' }}
            >
              ({zoom.toFixed(2)}x)
            </span>
          </div>

          {/* 焦距和光圈 */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 flex-1">
              <span 
                className="text-sm"
                style={{ color: 'var(--text-secondary)' }}
              >
                焦距:
              </span>
              <select 
                value={focalLength}
                onChange={(e) => setFocalLength(e.target.value)}
                className="input text-sm"
              >
                {focalLengths.map((fl) => (
                  <option key={fl} value={fl}>{fl}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2 flex-1">
              <span 
                className="text-sm"
                style={{ color: 'var(--text-secondary)' }}
              >
                光圈:
              </span>
              <select 
                value={aperture}
                onChange={(e) => setAperture(e.target.value)}
                className="input text-sm"
              >
                {apertures.map((ap) => (
                  <option key={ap} value={ap}>{ap}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 生成的提示词 */}
          <div>
            <label 
              className="text-xs block mb-1"
              style={{ color: 'var(--text-tertiary)' }}
            >
              生成的提示词(Prompt):
            </label>
            <div 
              className="p-3 rounded-lg text-sm"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                color: 'var(--text-secondary)'
              }}
            >
              Cinematography: Camera orbits vertically. Re-shoot from new angle. 
              Horizontal: {horizontalAngle}°, Vertical: {verticalAngle}°, 
              Zoom: {zoom.toFixed(2)}x, Focal: {focalLength}, Aperture: {aperture}
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex justify-end gap-3 mt-4">
          <Button 
            variant="outline" 
            onClick={onClose}
            style={{ borderColor: 'var(--border)' }}
          >
            取消
          </Button>
          <Button className="btn-primary">
            生成新机位(New Shot)
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
