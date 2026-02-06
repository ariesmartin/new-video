import { useState } from 'react';
import { X, Camera, Move, RotateCw, ZoomIn, ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';

interface CameraMoveModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl?: string;
}

export function CameraMoveModal({ isOpen, onClose, imageUrl }: CameraMoveModalProps) {
  const [selectedMove, setSelectedMove] = useState<string>('push');
  const [intensity, setIntensity] = useState(50);
  const [speed, setSpeed] = useState(50);

  const cameraMoves = [
    { id: 'push', name: '推(Push In)', icon: ZoomIn, desc: '镜头向前推进' },
    { id: 'pull', name: '拉(Pull Out)', icon: ZoomIn, desc: '镜头向后拉出' },
    { id: 'pan_left', name: '左摇(Pan Left)', icon: ArrowLeft, desc: '镜头向左平移' },
    { id: 'pan_right', name: '右摇(Pan Right)', icon: ArrowRight, desc: '镜头向右平移' },
    { id: 'tilt_up', name: '上摇(Tilt Up)', icon: ArrowUp, desc: '镜头向上倾斜' },
    { id: 'tilt_down', name: '下摇(Tilt Down)', icon: ArrowDown, desc: '镜头向下倾斜' },
    { id: 'dolly_in', name: '前移(Dolly In)', icon: Move, desc: '摄影机前移' },
    { id: 'dolly_out', name: '后移(Dolly Out)', icon: Move, desc: '摄影机后移' },
    { id: 'truck_left', name: '左移(Truck Left)', icon: ArrowLeft, desc: '摄影机左移' },
    { id: 'truck_right', name: '右移(Truck Right)', icon: ArrowRight, desc: '摄影机右移' },
    { id: 'pedestal_up', name: '上升(Pedestal Up)', icon: ArrowUp, desc: '摄影机上升' },
    { id: 'pedestal_down', name: '下降(Pedestal Down)', icon: ArrowDown, desc: '摄影机下降' },
    { id: 'orbit', name: '环绕(Orbit)', icon: RotateCw, desc: '镜头环绕主体' },
    { id: 'rack_focus', name: '变焦(Rack Focus)', icon: Camera, desc: '焦点转换' },
  ];

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] rounded-xl overflow-y-auto flex flex-col bg-surface border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-4 py-3 border-b flex-shrink-0 border-border">
          <div className="flex items-center gap-3">
            <Camera size={20} className="text-primary" />
            <span className="font-semibold text-text-primary">
              镜头运镜 (Camera Move)
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-text-secondary"
          >
            <X size={20} />
          </button>
        </div>

        {/* 主体内容 */}
        <div className="flex-1 flex overflow-hidden flex-col sm:flex-row">
          {/* 左侧：运镜类型列表 */}
          <div className="w-full sm:w-64 flex-shrink-0 border-b sm:border-b-0 sm:border-r overflow-y-auto border-border h-40 sm:h-full">
            <div className="p-3">
              <h3 className="text-xs font-medium uppercase tracking-wider mb-3 text-text-tertiary sticky top-0 bg-surface py-1 z-10">
                运镜类型
              </h3>
              <div className="space-y-1">
                {cameraMoves.map((move) => {
                  const Icon = move.icon;
                  const isSelected = selectedMove === move.id;
                  return (
                    <button
                      key={move.id}
                      onClick={() => setSelectedMove(move.id)}
                      className={`
                        w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-sm transition-colors
                        ${isSelected ? 'bg-yellow-500/10' : 'hover:bg-white/5'}
                      `}
                    >
                      <Icon
                        size={16}
                        className={isSelected ? "text-primary" : "text-text-secondary"}
                      />
                      <div className="flex-1 min-w-0">
                        <p className={isSelected ? "text-primary" : "text-text-primary"}>
                          {move.name}
                        </p>
                        <p className="text-xs truncate text-text-tertiary">
                          {move.desc}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 中间：预览 */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 flex items-center justify-center p-4 bg-elevated">
              {imageUrl ? (
                <div className="relative">
                  <img
                    src={imageUrl}
                    alt="Preview"
                    className="max-w-full max-h-[400px] object-contain rounded-lg"
                  />
                  {/* 运镜指示器 */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-16 h-16 rounded-full border-2 flex items-center justify-center" style={{ borderColor: 'hsl(var(--primary))' }}>
                      <Camera size={24} className="text-primary" />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-text-tertiary">
                  <Camera size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
                  <p>请选择一张图片预览运镜效果</p>
                </div>
              )}
            </div>

            {/* 参数控制 */}
            <div className="p-4 border-t border-border">
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-text-secondary">
                      运镜强度
                    </span>
                    <span className="text-sm text-text-primary">
                      {intensity}%
                    </span>
                  </div>
                  <Slider
                    value={[intensity]}
                    onValueChange={(value) => setIntensity(value[0])}
                    min={0}
                    max={100}
                    step={1}
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-text-secondary">
                      运镜速度
                    </span>
                    <span className="text-sm text-text-primary">
                      {speed}%
                    </span>
                  </div>
                  <Slider
                    value={[speed]}
                    onValueChange={(value) => setSpeed(value[0])}
                    min={0}
                    max={100}
                    step={1}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 右侧：生成的提示词 */}
          <div className="w-full sm:w-72 flex-shrink-0 border-t sm:border-t-0 sm:border-l overflow-y-auto p-4 border-border h-auto sm:h-full">
            <h3 className="text-xs font-medium uppercase tracking-wider mb-3 text-text-tertiary">
              生成的提示词
            </h3>
            <div className="p-3 rounded-lg text-sm mb-4 bg-elevated text-text-secondary">
              Camera Move: {cameraMoves.find(m => m.id === selectedMove)?.name}
              <br />
              Intensity: {intensity}%
              <br />
              Speed: {speed}%
            </div>

            <div className="space-y-2">
              <Button className="w-full btn-primary">
                生成运镜视频
              </Button>
              <Button
                variant="outline"
                className="w-full border-border"
              >
                预览效果
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
