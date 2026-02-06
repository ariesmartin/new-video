import { useState } from 'react';
import { X, Image, Play, Pause, Settings, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/hooks/useStore';

interface BatchGenerateModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface GenerationTask {
  id: string;
  cardNumber: number;
  prompt: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
}

export function BatchGenerateModal({ isOpen, onClose }: BatchGenerateModalProps) {
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedStyle, setSelectedStyle] = useState('cinematic_realistic');
  const [resolution, setResolution] = useState('2K');
  const [aspectRatio, setAspectRatio] = useState('16:9');

  // 示例任务列表
  const [tasks, setTasks] = useState<GenerationTask[]>([
    { id: '1', cardNumber: 11, prompt: '俯视镜头，废土世界，主角林恩', status: 'completed', progress: 100 },
    { id: '2', cardNumber: 12, prompt: '极细特写，风暴中心，奇异极光', status: 'completed', progress: 100 },
    { id: '3', cardNumber: 15, prompt: '微距镜头，骨骼碎片，沉重氛围', status: 'processing', progress: 65 },
    { id: '4', cardNumber: 16, prompt: '过肩镜头，伊甸园远景，沙尘暴', status: 'pending', progress: 0 },
    { id: '5', cardNumber: 17, prompt: '全景镜头，废墟城市，黄昏光线', status: 'pending', progress: 0 },
  ]);

  const styles = [
    { id: 'cinematic_realistic', name: '影视写实', desc: 'Cinematic Realistic' },
    { id: 'chinese_3d', name: '国风3D', desc: 'Chinese 3D' },
    { id: 'classic_film', name: '经典胶片', desc: 'Classic Film' },
    { id: 'modern_bright', name: '现代高亮', desc: 'Modern Bright' },
    { id: 'epic_blockbuster', name: '史诗大片', desc: 'Epic Blockbuster' },
    { id: 'ink_wash', name: '水墨国风', desc: 'Ink Wash' },
  ];

  const handleStartGeneration = () => {
    setIsGenerating(true);
    addToast({ type: 'info', message: '开始批量生成图片...' });
    
    // 模拟生成过程
    let currentIndex = 0;
    const interval = setInterval(() => {
      setTasks(prev => prev.map((task, idx) => {
        if (idx === currentIndex && task.status === 'pending') {
          return { ...task, status: 'processing', progress: 0 };
        }
        if (idx === currentIndex && task.status === 'processing') {
          const newProgress = task.progress + 10;
          if (newProgress >= 100) {
            currentIndex++;
            return { ...task, status: 'completed', progress: 100 };
          }
          return { ...task, progress: newProgress };
        }
        return task;
      }));

      const allCompleted = tasks.every(t => t.status === 'completed');
      if (allCompleted || currentIndex >= tasks.length) {
        clearInterval(interval);
        setIsGenerating(false);
        addToast({ type: 'success', message: '批量生成完成！' });
      }
    }, 500);
  };

  const handlePauseGeneration = () => {
    setIsGenerating(false);
    addToast({ type: 'info', message: '已暂停生成' });
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
      onClick={onClose}
    >
      <div 
        className="w-full max-w-4xl h-[85vh] rounded-xl overflow-hidden flex flex-col"
        style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div 
          className="flex items-center justify-between px-4 py-3 border-b flex-shrink-0"
          style={{ borderColor: 'var(--border)' }}
        >
          <div className="flex items-center gap-3">
            <Image size={20} style={{ color: 'var(--primary)' }} />
            <span 
              className="font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              批量生图
            </span>
            <span 
              className="text-xs px-2 py-0.5 rounded"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                color: 'var(--text-tertiary)'
              }}
            >
              {tasks.filter(t => t.status === 'completed').length}/{tasks.length} 完成
            </span>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            style={{ color: 'var(--text-secondary)' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* 主体内容 */}
        <div className="flex-1 flex overflow-hidden">
          {/* 左侧：生成参数 */}
          <div 
            className="w-72 flex-shrink-0 border-r overflow-y-auto p-4"
            style={{ borderColor: 'var(--border)' }}
          >
            <h3 
              className="text-xs font-medium uppercase tracking-wider mb-4"
              style={{ color: 'var(--text-tertiary)' }}
            >
              生成参数
            </h3>

            {/* 画风风格 */}
            <div className="mb-4">
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                画风风格
              </label>
              <select 
                value={selectedStyle}
                onChange={(e) => setSelectedStyle(e.target.value)}
                className="w-full input text-sm"
              >
                {styles.map((style) => (
                  <option key={style.id} value={style.id}>
                    {style.name} ({style.desc})
                  </option>
                ))}
              </select>
            </div>

            {/* 分辨率 */}
            <div className="mb-4">
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                分辨率
              </label>
              <div className="flex gap-2">
                {['2K', '4K'].map((res) => (
                  <button
                    key={res}
                    onClick={() => setResolution(res)}
                    className={`flex-1 py-2 px-3 rounded-lg text-sm transition-colors ${
                      resolution === res 
                        ? 'bg-primary text-black' 
                        : 'border hover:bg-white/5'
                    }`}
                    style={{ 
                      borderColor: resolution === res ? 'transparent' : 'var(--border)',
                      color: resolution === res ? '#000' : 'var(--text-secondary)'
                    }}
                  >
                    {res}高清
                  </button>
                ))}
              </div>
            </div>

            {/* 比例 */}
            <div className="mb-4">
              <label 
                className="text-xs block mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                画面比例
              </label>
              <div className="grid grid-cols-2 gap-2">
                {['16:9', '9:16', '1:1', '4:3'].map((ratio) => (
                  <button
                    key={ratio}
                    onClick={() => setAspectRatio(ratio)}
                    className={`py-2 px-3 rounded-lg text-sm transition-colors ${
                      aspectRatio === ratio 
                        ? 'bg-primary text-black' 
                        : 'border hover:bg-white/5'
                    }`}
                    style={{ 
                      borderColor: aspectRatio === ratio ? 'transparent' : 'var(--border)',
                      color: aspectRatio === ratio ? '#000' : 'var(--text-secondary)'
                    }}
                  >
                    {ratio}
                  </button>
                ))}
              </div>
            </div>

            {/* 高级设置 */}
            <div className="mb-4">
              <button 
                className="flex items-center gap-2 text-sm"
                style={{ color: 'var(--text-tertiary)' }}
              >
                <Settings size={14} />
                高级设置
              </button>
            </div>

            {/* 操作按钮 */}
            <div className="space-y-2">
              {!isGenerating ? (
                <Button 
                  className="w-full btn-primary flex items-center justify-center gap-2"
                  onClick={handleStartGeneration}
                >
                  <Play size={16} />
                  开始生成
                </Button>
              ) : (
                <Button 
                  className="w-full flex items-center justify-center gap-2"
                  onClick={handlePauseGeneration}
                  style={{ 
                    backgroundColor: 'var(--status-yellow)',
                    color: '#000'
                  }}
                >
                  <Pause size={16} />
                  暂停生成
                </Button>
              )}
            </div>
          </div>

          {/* 右侧：任务列表 */}
          <div className="flex-1 overflow-y-auto p-4">
            <h3 
              className="text-xs font-medium uppercase tracking-wider mb-4"
              style={{ color: 'var(--text-tertiary)' }}
            >
              生成队列
            </h3>

            <div className="space-y-3">
              {tasks.map((task) => (
                <div 
                  key={task.id}
                  className="p-3 rounded-lg border"
                  style={{ 
                    backgroundColor: 'var(--bg-night)',
                    borderColor: 'var(--border)'
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span 
                        className="text-xs font-medium px-2 py-0.5 rounded"
                        style={{ 
                          backgroundColor: 'var(--bg-card)',
                          color: 'var(--text-primary)'
                        }}
                      >
                        #{task.cardNumber}
                      </span>
                      <span 
                        className="text-sm"
                        style={{ color: 'var(--text-primary)' }}
                      >
                        {task.prompt}
                      </span>
                    </div>
                    <div>
                      {task.status === 'completed' && (
                        <CheckCircle size={18} style={{ color: 'var(--status-green)' }} />
                      )}
                      {task.status === 'processing' && (
                        <Loader2 size={18} className="animate-spin" style={{ color: 'var(--status-yellow)' }} />
                      )}
                      {task.status === 'pending' && (
                        <div 
                          className="w-4 h-4 rounded-full border-2"
                          style={{ borderColor: 'var(--border)' }}
                        />
                      )}
                    </div>
                  </div>

                  {/* 进度条 */}
                  <div className="flex items-center gap-3">
                    <div 
                      className="flex-1 h-2 rounded-full overflow-hidden"
                      style={{ backgroundColor: 'var(--bg-card)' }}
                    >
                      <div 
                        className="h-full rounded-full transition-all duration-300"
                        style={{ 
                          width: `${task.progress}%`,
                          backgroundColor: task.status === 'completed' 
                            ? 'var(--status-green)' 
                            : task.status === 'processing'
                            ? 'var(--status-yellow)'
                            : 'var(--border)'
                        }}
                      />
                    </div>
                    <span 
                      className="text-xs w-10 text-right"
                      style={{ color: 'var(--text-tertiary)' }}
                    >
                      {task.progress}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
