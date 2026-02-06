import { useState } from 'react';
import { Wand2, Upload, Image as ImageIcon, Palette, Video } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { useAppStore } from '@/hooks/useStore';
import type { Card } from '@/types';

interface RightPanelProps {
  selectedCard?: Card | null;
}

export function RightPanel({ selectedCard }: RightPanelProps) {
  const { currentEpisode } = useAppStore();
  const [activeTab, setActiveTab] = useState('script');
  const [cardStatus, setCardStatus] = useState(selectedCard?.status || 'pending');
  const [referenceTab, setReferenceTab] = useState<'sketch' | 'material' | 'threeD'>('sketch');

  // 更新卡片状态
  const handleStatusChange = (status: typeof cardStatus) => {
    setCardStatus(status);
    // TODO: 更新卡片状态到 store
  };

  // 示例剧本内容
  const scriptContent = currentEpisode?.story || `新巴比伦的雨总是带着一股机油味。下城区的垃圾处理厂被高耸的围墙圈禁，这里是城市不仅丢弃废料，也丢弃灵魂的地方。

巴斯特是一只甚至连名字都没有的杂种狗，它正匍匐在一堆生锈的汽车零件下。它的呼吸很轻，眼睛死死盯着前方五米处的一块发霉的面包。而在它对面，一只体型硕大的比特犬正龇着牙，那是这一带的小霸王"碎骨"。

雨水顺着巴斯特左耳那个参差不齐的缺口流下，那是它幼年时从维克多的实验室逃生时留下的烙印。它记得那个男人穿着白大褂，手里拿着针管，冷漠地看着它的母亲在笼子里哀嚎。那段记忆像火炭一样灼烧着它的背。`;

  return (
    <aside 
      className="w-80 flex-shrink-0 flex flex-col"
      style={{ 
        backgroundColor: 'var(--bg-card)',
        borderLeft: '1px solid var(--border)'
      }}
    >
      {/* 导演台标题 */}
      <div 
        className="px-4 py-3"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <h3 
          className="font-medium"
          style={{ color: 'var(--text-primary)' }}
        >
          Ep.1 导演台
        </h3>
      </div>

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList 
          className="w-full grid grid-cols-3 p-1 m-4 mb-0"
          style={{ backgroundColor: 'var(--bg-night)' }}
        >
          <TabsTrigger 
            value="script"
            className="data-[state=active]:bg-primary data-[state=active]:text-black"
          >
            1.剧本
          </TabsTrigger>
          <TabsTrigger 
            value="storyboard"
            className="data-[state=active]:bg-primary data-[state=active]:text-black"
          >
            2.分镜
          </TabsTrigger>
          <TabsTrigger 
            value="card"
            className="data-[state=active]:bg-primary data-[state=active]:text-black"
          >
            3.卡片
          </TabsTrigger>
        </TabsList>

        {/* 剧本标签 */}
        <TabsContent value="script" className="flex-1 flex flex-col m-0 p-4 pt-2">
          <div className="flex items-center gap-2 mb-3">
            <span 
              className="text-xs px-2 py-1 rounded"
              style={{ 
                backgroundColor: 'var(--bg-night)',
                color: 'var(--text-secondary)'
              }}
            >
              本集故事(Story)
            </span>
            <span 
              className="text-xs px-2 py-1 rounded cursor-pointer hover:bg-white/5"
              style={{ 
                backgroundColor: 'transparent',
                color: 'var(--text-tertiary)'
              }}
            >
              场次剧本 Script
            </span>
          </div>

          <div 
            className="flex-1 overflow-y-auto p-3 rounded-lg text-sm leading-relaxed"
            style={{ 
              backgroundColor: 'var(--bg-night)',
              color: 'var(--text-primary)'
            }}
          >
            {scriptContent}
          </div>

          <Button className="w-full mt-3 btn-primary flex items-center justify-center gap-2">
            <Wand2 size={16} />
            AI 扩写为场次剧本
          </Button>
        </TabsContent>

        {/* 分镜标签 */}
        <TabsContent value="storyboard" className="flex-1 flex flex-col m-0 p-4 pt-2 overflow-y-auto">
          {selectedCard ? (
            <div className="space-y-4">
              {/* 状态与属性 */}
              <div>
                <h4 
                  className="text-xs font-medium mb-2"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  状态与属性
                </h4>
                <div className="flex items-center gap-1">
                  {[
                    { key: 'pending', color: 'var(--status-red)', label: '待处理' },
                    { key: 'processing', color: 'var(--status-yellow)', label: '处理中' },
                    { key: 'completed', color: 'var(--status-green)', label: '已完成' },
                    { key: 'approved', color: 'var(--status-blue)', label: '已批准' },
                    { key: 'revision', color: 'var(--status-orange)', label: '需修改' },
                  ].map((status) => (
                    <button
                      key={status.key}
                      onClick={() => handleStatusChange(status.key as typeof cardStatus)}
                      className={`w-6 h-6 rounded-full transition-transform hover:scale-110 ${
                        cardStatus === status.key ? 'ring-2 ring-white' : ''
                      }`}
                      style={{ backgroundColor: status.color }}
                      title={status.label}
                    />
                  ))}
                  <button 
                    className="ml-auto text-xs px-2 py-1 rounded hover:bg-white/5"
                    style={{ color: 'var(--text-tertiary)' }}
                    onClick={() => handleStatusChange('pending')}
                  >
                    [重开]
                  </button>
                </div>
              </div>

              {/* 参考图 */}
              <div>
                <h4 
                  className="text-xs font-medium mb-2"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  参考图
                </h4>
                {/* 参考图类型切换 */}
                <div className="flex gap-1 mb-2">
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
                            ? 'bg-primary text-black' 
                            : 'hover:bg-white/5'
                        }`}
                        style={{ 
                          backgroundColor: referenceTab === type.key ? 'var(--primary)' : 'var(--bg-night)',
                          color: referenceTab === type.key ? '#000' : 'var(--text-secondary)'
                        }}
                      >
                        <Icon size={12} />
                        {type.label}
                      </button>
                    );
                  })}
                </div>
                {/* 参考图上传区 */}
                <div 
                  className="flex gap-2"
                >
                  <div 
                    className="w-16 h-16 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:bg-white/5 transition-colors border border-dashed"
                    style={{ 
                      backgroundColor: 'var(--bg-night)',
                      borderColor: 'var(--border)'
                    }}
                  >
                    <Upload size={16} style={{ color: 'var(--text-tertiary)' }} />
                    <span className="text-[10px] mt-1" style={{ color: 'var(--text-tertiary)' }}>上传</span>
                  </div>
                  <div 
                    className="w-16 h-16 rounded-lg flex items-center justify-center cursor-pointer hover:bg-white/5 transition-colors"
                    style={{ backgroundColor: 'var(--bg-night)' }}
                  >
                    <span className="text-lg">✏️</span>
                  </div>
                  <div 
                    className="w-16 h-16 rounded-lg flex items-center justify-center cursor-pointer hover:bg-white/5 transition-colors"
                    style={{ backgroundColor: 'var(--bg-night)' }}
                  >
                    <span className="text-lg">🖼️</span>
                  </div>
                </div>
              </div>

              {/* 分镜详情 */}
              <div>
                <h4 
                  className="text-xs font-medium mb-2"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  分镜详情
                </h4>
                <div className="space-y-2">
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      景别
                    </label>
                    <select 
                      className="w-full input text-sm"
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
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      画面内容
                    </label>
                    <input 
                      type="text"
                      className="w-full input text-sm"
                      placeholder="描述画面内容..."
                    />
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      角色对白
                    </label>
                    <input 
                      type="text"
                      className="w-full input text-sm"
                      placeholder="输入对白..."
                    />
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      环境音
                    </label>
                    <input 
                      type="text"
                      className="w-full input text-sm"
                      placeholder="描述环境音..."
                    />
                  </div>
                </div>
              </div>

              {/* 生图参数 */}
              <div>
                <h4 
                  className="text-xs font-medium mb-2"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  生图参数
                </h4>
                <div className="space-y-2">
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      分辨率
                    </label>
                    <select className="w-full input text-sm" defaultValue="2K">
                      <option value="2K">2K高清</option>
                      <option value="4K">4K超清</option>
                    </select>
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      比例
                    </label>
                    <select className="w-full input text-sm" defaultValue="16:9">
                      <option value="16:9">16:9</option>
                      <option value="9:16">9:16</option>
                      <option value="1:1">1:1</option>
                      <option value="4:3">4:3</option>
                    </select>
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      AI提示词
                    </label>
                    <textarea 
                      className="w-full input text-sm resize-none"
                      rows={3}
                      placeholder="输入AI提示词..."
                    />
                  </div>
                  <div>
                    <label 
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      画风风格
                    </label>
                    <select className="w-full input text-sm" defaultValue="chinese_3d">
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

              {/* 操作按钮 */}
              <div className="flex gap-2">
                <Button className="flex-1 btn-primary">
                  生图
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  style={{ borderColor: 'var(--border)' }}
                >
                  调色
                </Button>
              </div>
              <Button 
                variant="outline" 
                className="w-full"
                style={{ borderColor: 'var(--border)' }}
              >
                生成动态视频
              </Button>
            </div>
          ) : (
            <div 
              className="flex-1 flex items-center justify-center text-sm"
              style={{ color: 'var(--text-tertiary)' }}
            >
              请选择一个镜头卡片
            </div>
          )}
        </TabsContent>

        {/* 卡片标签 */}
        <TabsContent value="card" className="flex-1 flex flex-col m-0 p-4 pt-2">
          <div 
            className="flex-1 flex items-center justify-center text-sm"
            style={{ color: 'var(--text-tertiary)' }}
          >
            卡片属性设置
          </div>
        </TabsContent>
      </Tabs>
    </aside>
  );
}
