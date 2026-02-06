import { useState } from 'react';
import { Upload, Image as ImageIcon, Palette, Video, Maximize2, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useEpisodeStore, useUIStore } from '@/hooks/useStore';
import type { ShotNode, NodeStatus } from '@/types';

interface ShotDetailPanelProps {
  shot: ShotNode;
}

export function ShotDetailPanel({ shot }: ShotDetailPanelProps) {
  const { closeRightPanel } = useUIStore();
  const { updateShotNode } = useEpisodeStore();
  const [referenceTab, setReferenceTab] = useState<'sketch' | 'material' | 'threeD'>('sketch');
  
  const handleStatusChange = (status: NodeStatus) => {
    updateShotNode(shot.shotId, { status });
  };

  const statusOptions = [
    { key: 'pending', color: 'bg-status-red', label: '待处理' },
    { key: 'processing', color: 'bg-status-yellow', label: '处理中' },
    { key: 'completed', color: 'bg-status-green', label: '已完成' },
    { key: 'approved', color: 'bg-status-blue', label: '已批准' },
  ];

  return (
    <div className="flex flex-col h-full bg-surface border-l border-border w-full overflow-y-auto">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between sticky top-0 bg-surface z-10">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-primary">
            镜头 #{shot.shotNumber}
          </span>
        </div>
        <button
          onClick={closeRightPanel}
          className="p-1.5 rounded-lg hover:bg-white/5 transition-colors text-text-tertiary hover:text-text-primary"
        >
          <span className="text-lg">×</span>
        </button>
      </div>

      <div className="p-4 space-y-5">
        <div>
          <h4 className="text-xs font-medium mb-2 text-text-tertiary uppercase tracking-wider">
            状态与属性
          </h4>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm"
              className="text-xs border-border text-text-secondary hover:text-text-primary"
            >
              断开
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="text-xs border-border text-text-secondary hover:text-text-primary"
            >
              分镜
            </Button>
            <div className="flex-1" />
            {statusOptions.map((status) => (
              <button
                key={status.key}
                onClick={() => handleStatusChange(status.key as NodeStatus)}
                className={`w-6 h-6 rounded-full transition-transform hover:scale-110 ${status.color} ${
                  shot.status === status.key ? 'ring-2 ring-white' : ''
                }`}
                title={status.label}
              />
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-medium mb-2 text-text-tertiary uppercase tracking-wider">
            参考图
          </h4>
          <div className="flex gap-2 mb-3">
            {[
              { key: 'sketch', label: '手绘', icon: Palette },
              { key: 'material', label: '素材', icon: ImageIcon },
              { key: 'threeD', label: '3D', icon: Video },
            ].map((type) => {
              const Icon = type.icon;
              return (
                <button
                  key={type.key}
                  onClick={() => setReferenceTab(type.key as typeof referenceTab)}
                  className={`flex-1 py-1.5 px-2 rounded text-xs flex items-center justify-center gap-1 transition-colors ${
                    referenceTab === type.key
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-elevated text-text-secondary hover:bg-white/5'
                  }`}
                >
                  <Icon size={12} />
                  {type.label}
                </button>
              );
            })}
          </div>
          <div className="flex gap-2">
            <div className="w-16 h-16 rounded-lg bg-elevated flex items-center justify-center border border-dashed border-border cursor-pointer hover:bg-white/5 transition-colors">
              <span className="text-2xl">👤</span>
            </div>
            <div className="w-16 h-16 rounded-lg bg-elevated flex flex-col items-center justify-center border border-dashed border-border cursor-pointer hover:bg-white/5 transition-colors">
              <Upload size={16} className="text-text-tertiary" />
              <span className="text-[10px] sm:text-xs text-text-tertiary mt-1">上传</span>
            </div>
            <div className="w-16 h-16 rounded-lg bg-elevated flex flex-col items-center justify-center border border-dashed border-border cursor-pointer hover:bg-white/5 transition-colors">
              <span className="text-xl">✏️</span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-medium mb-2 text-text-tertiary uppercase tracking-wider">
            分镜详情
          </h4>
          <div className="space-y-3">
            <div>
              <label className="text-xs block mb-1 text-text-secondary">
                景别
              </label>
              <select 
                className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary"
                defaultValue="extreme_long_shot"
              >
                <option value="extreme_long_shot">大远景(Extreme Long Shot)</option>
                <option value="long_shot">远景(Long Shot)</option>
                <option value="medium_shot">中景(Medium Shot)</option>
                <option value="close_up">特写(Close-up)</option>
                <option value="extreme_close_up">极特写(Extreme Close-up)</option>
              </select>
            </div>
            <div>
              <label className="text-xs block mb-1 text-text-secondary">
                画面内容
              </label>
              <textarea
                className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary resize-none"
                rows={2}
                placeholder="描述画面内容..."
                defaultValue="巨型液压门吞噬林恩"
              />
            </div>
            <div>
              <label className="text-xs block mb-1 text-text-secondary">
                角色对白
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary"
                placeholder="输入对白..."
              />
            </div>
            <div>
              <label className="text-xs block mb-1 text-text-secondary">
                环境音
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary"
                placeholder="描述环境音..."
                defaultValue="(环境音)：沉闷的液压轰鸣，金属尖啸"
              />
            </div>
          </div>
        </div>

        <div>
          <h4 className="text-xs font-medium mb-2 text-text-tertiary uppercase tracking-wider">
            生图参数
          </h4>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs block mb-1 text-text-secondary">
                  分辨率
                </label>
                <select className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary">
                  <option value="2K">2K高清</option>
                  <option value="4K">4K超清</option>
                </select>
              </div>
              <div>
                <label className="text-xs block mb-1 text-text-secondary">
                  比例
                </label>
                <select className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary">
                  <option value="16:9">16:9</option>
                  <option value="9:16">9:16</option>
                  <option value="1:1">1:1</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs block mb-1 text-text-secondary">
                画风风格
              </label>
              <select className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary">
                <option value="chinese_3d">国风3D</option>
                <option value="cinematic_realistic">影视写实</option>
                <option value="classic_film">经典胶片</option>
                <option value="modern_bright">现代高亮</option>
                <option value="epic_blockbuster">史诗大片</option>
                <option value="3d_toys">3D潮玩</option>
                <option value="ink_wash">水墨国风</option>
                <option value="hardcore_cg">硬核CG</option>
                <option value="refined_anime">精致日漫</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
              AI提示词 (VISUAL PROMPT)
            </h4>
            <div className="flex items-center gap-1">
              <button className="p-1 hover:bg-white/5 rounded text-text-tertiary">
                <Maximize2 size={14} />
              </button>
              <button className="p-1 hover:bg-white/5 rounded text-text-tertiary">
                <Trash2 size={14} />
              </button>
            </div>
          </div>
          <textarea
            className="w-full px-3 py-2 rounded-lg bg-elevated border border-border text-sm text-text-primary resize-none"
            rows={6}
            placeholder="输入AI生成图像的详细提示词..."
            defaultValue={`极低角度仰拍 (Worm's Eye View) | 缓慢推镜头 (Slow Push In)

一个巨大的、三层楼高的液压金属门正在关闭，吞噬了画面中央渺小的林恩身影。画面采用极低角度仰拍，金属门在透视下显得无比巨大，充满压迫感。门上布满了油污和划痕，周围的混凝土墙壁上嵌着工业风格的铆钉。蒸汽从门的缝隙中喷出，营造出一种闷热、压抑的氛围。林恩穿着黑色风衣的剪影在门框中显得格外渺小。画面色调偏向冷灰和锈红色，强调工业末世感。赛博朋克风格，电影级光影。`}
          />
        </div>

        <div className="flex gap-2">
          <Button className="flex-1 btn-primary text-sm">生图</Button>
          <Button variant="outline" className="flex-1 border-border text-sm">
            调色
          </Button>
        </div>
      </div>
    </div>
  );
}
