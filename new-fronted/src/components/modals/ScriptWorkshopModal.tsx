import { useState } from 'react';
import { ArrowLeft, Sparkles, Wand2, Play, FileText, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAppStore } from '@/hooks/useStore';

interface ScriptWorkshopModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ScriptWorkshopModal({ isOpen, onClose }: ScriptWorkshopModalProps) {
  const { currentProject } = useAppStore();
  const [mode, setMode] = useState<'story' | 'script'>('story');
  const [activeChapter, setActiveChapter] = useState(0);

  // 示例章节数据
  const chapters = [
    { id: 1, title: '第一集：深井的回响', wordCount: 1085, progress: 83 },
    { id: 2, title: '第二集：铁锈与猎手', wordCount: 1503, progress: 63 },
    { id: 3, title: '第三集：变异的祭坛', wordCount: 186, progress: 8 },
    { id: 4, title: '第四集：风暴将至', wordCount: 1885, progress: 83 },
  ];

  // 示例剧本内容
  const scriptContent = `【场次】: EXT. 73号深井出口 - 黄昏（或某种无法辨识的时间）

【人物】: 林恩（20岁，脸色苍白，沾满油污的防护服，呼吸急促）

【正文】:

巨大的液压门在他身后发出沉闷的轰鸣，像是一只巨兽正在缓慢合拢它的下颚。生锈的铰链互相摩擦，尖锐的金属嘶鸣声在狭窄的维修井中回荡，震得林恩耳膜生疼。

随着最后一声"咔哒"落锁声，深井内那恒定而压抑的嗡嗡声彻底消失了。取而代之的，是一片死寂。

林恩趴在粗糙的混凝土斜坡上，肺部像是有两块烧红的炭在灼烧。他颤抖着手，从防护服的侧袋里摸出那张泛黄的地图。地图的一角被烧焦了，上面用已经褪色的蓝色墨水标记着一条蜿蜒的路线，通向一个模糊的绿色圆点。

他抬起头。

第一次，没有穹顶。没有那些总是闪烁着故障红光的LED灯带，没有那些用油漆粉刷出的虚假蓝天。只有一片灰黄色的苍穹，狂风卷着沙砾，像无数把细小的锉刀，刮擦着他那已经有些破损的面罩。能见度极低，远处的废墟像是一排参差不齐的烂牙，矗立在尘暴的狂风中。

眼前的世界是一片荒芜的荒野，狂风卷着沙砾，像无数把细小的锉刀，刮擦着他那已经有些破损的面罩。能见度极低，远处的废墟像是一排参差不齐的烂牙，矗立在尘暴的狂风中。

空气中的液压门在他身后发出沉闷的轰鸣，像是一只巨兽正在缓慢合拢它的下颚。生锈的铰链互相摩擦，尖锐的金属嘶鸣声在狭窄的维修井中回荡，震得林恩耳膜生疼。

"警告：外部辐射水平超标。氧气储备剩余：85%。"面罩内的HUD显示屏跳出一行红字，冰冷地提醒着他现实的残酷。

林恩支起身体站起来，膝盖发软。他像是在两块烧红的炭在灼烧。他颤抖着手，从防护服的侧袋里摸出那张泛黄的地图。地图的一角被烧焦了，上面用已经褪色的蓝色墨水标记着一条蜿蜒的路线，通向一个模糊的绿色圆点。

一阵强风袭来，差点将他掀翻。他踉跄了两步，手掌按在了一块突出的岩石上。那是真正的石头，不像深井里那些光滑的人造聚合材料，它粗糙、冰冷、甚至有些扎手。

他低下头，看着自己的手套，那里沾满了灰尘。这是来自旧世界的灰尘，也许是某座摩天大楼的残骸，也许是某个人曾经的骨灰。

"伊甸园……"他喃喃自语，声音在面罩里显得沉闷而遥远。

远处，在那片混沌的灰黄色雾霾深处，似乎有一道极其微弱的光亮闪烁了一下。不是警示灯那种刺眼的红，也不是探照灯那种苍白的白，而是一种更柔和的、近乎幻觉的微光。

林恩握紧了手中的地图，指节因用力而发白。他回头看了一眼那扇紧闭的液压门，那是他过去二十年生命的全部，现在却成了将他拒之门外的墙。

他转过身，迎着风沙迈出了第一步。脚下的碎石发出清脆的断裂声，这声音在空旷的荒原上显得格外孤独。

风沙更大了，瞬间吞没了他单薄的身影，只留下一串歪歪扭扭的脚印，迅速被新的尘埃掩埋。`;

  const [showChapters, setShowChapters] = useState(true);
  const [showAI, setShowAI] = useState(true);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-6xl h-[90vh] rounded-xl overflow-hidden flex flex-col bg-surface border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border flex-shrink-0">
          <div className="flex items-center gap-2 sm:gap-4">
            <button 
              onClick={onClose}
              className="flex items-center gap-1 text-sm hover:opacity-80 transition-opacity text-text-secondary"
            >
              <ArrowLeft size={16} />
              <span className="hidden sm:inline">返回大厅</span>
            </button>
            <div className="w-px h-6 bg-border hidden sm:block" />
            <span className="font-medium text-text-primary text-sm sm:text-base truncate max-w-[150px] sm:max-w-none">
              {currentProject?.name || '尘埃尽头：新生代 (Dust Frontier: The New Era)'}
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-elevated text-text-tertiary hidden sm:inline-block">
              电影/短剧
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm"
              className="flex items-center gap-1 border-border hidden sm:flex"
            >
              <Sparkles size={14} />
              同步到分镜台
            </Button>
            <button 
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors ml-2 text-text-secondary"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* 主体内容 */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* 左侧章节列表 */}
          <div className={`
            w-56 flex-shrink-0 border-r overflow-y-auto border-border bg-surface
            absolute sm:relative inset-y-0 left-0 z-20 transition-transform duration-300
            ${showChapters ? 'translate-x-0' : '-translate-x-full sm:translate-x-0'}
            sm:block
          `}>
            <div className="p-4">
              <h3 className="text-xs font-medium uppercase tracking-wider mb-3 text-text-tertiary">
                CHAPTERS
              </h3>
              <div className="space-y-1">
                {chapters.map((chapter, index) => (
                  <div
                    key={chapter.id}
                    onClick={() => {
                      setActiveChapter(index);
                      if (window.innerWidth < 640) setShowChapters(false);
                    }}
                    className={`
                      p-3 rounded-lg cursor-pointer transition-colors
                      ${activeChapter === index ? 'bg-yellow-500/10' : 'hover:bg-white/5'}
                    `}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`text-xs ${activeChapter === index ? 'text-primary' : 'text-text-tertiary'}`}>
                        {chapter.id}
                      </span>
                      <span className={`text-sm font-medium truncate ${activeChapter === index ? 'text-primary' : 'text-text-primary'}`}>
                        {chapter.title}
                      </span>
                    </div>
                  </div>
                ))}
                
                <button className="w-full p-3 rounded-lg flex items-center gap-2 hover:bg-white/5 transition-colors mt-2 text-text-tertiary">
                  <span className="text-lg">+</span>
                  <span className="text-sm">新建章节</span>
                </button>
              </div>
            </div>
          </div>

          {/* Mobile Chapter Toggle (Overlay) */}
          {!showChapters && (
            <button 
              className="absolute top-1/2 left-0 z-30 p-2 bg-surface border border-border rounded-r-lg shadow-lg sm:hidden transform -translate-y-1/2"
              onClick={() => setShowChapters(true)}
            >
              <span className="text-xs">≡</span>
            </button>
          )}

          {/* 中间编辑区 */}
          <div className="flex-1 flex flex-col overflow-hidden w-full">
            {/* 工具栏 */}
            <div className="flex items-center justify-between px-4 py-2 border-b flex-shrink-0 border-border overflow-x-auto">
              <div className="flex items-center gap-2">
                <button className="p-2 rounded hover:bg-white/10 transition-colors hidden sm:block">
                  <span className="text-sm font-bold">B</span>
                </button>
                <button className="p-2 rounded hover:bg-white/10 transition-colors hidden sm:block">
                  <span className="text-sm italic">I</span>
                </button>
                <button className="p-2 rounded hover:bg-white/10 transition-colors hidden sm:block">
                  <span className="text-sm underline">U</span>
                </button>
                <div className="w-px h-6 mx-2 bg-border hidden sm:block" />
                <Tabs value={mode} onValueChange={(v) => setMode(v as 'story' | 'script')}>
                  <TabsList className="h-8 bg-elevated">
                    <TabsTrigger 
                      value="story" 
                      className="text-xs px-3 data-[state=active]:bg-primary data-[state=active]:text-black"
                    >
                      故事模式
                    </TabsTrigger>
                    <TabsTrigger 
                      value="script" 
                      className="text-xs px-3 data-[state=active]:bg-primary data-[state=active]:text-black"
                    >
                      剧本模式
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
              
              <div className="flex items-center gap-2 ml-4">
                <span className="text-xs text-text-tertiary whitespace-nowrap">
                  T {chapters[activeChapter]?.wordCount || 0} 字
                </span>
                <span className="text-xs text-text-tertiary whitespace-nowrap hidden sm:inline">
                  目标 1m ({chapters[activeChapter]?.progress || 0}%)
                </span>
              </div>
            </div>

            {/* 编辑器 */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-8 bg-elevated">
              <h2 className="text-lg sm:text-xl font-medium mb-4 sm:mb-6 text-text-primary">
                {chapters[activeChapter]?.title || '第一集：深井的回响'}
              </h2>

              <div className="prose prose-invert max-w-none text-text-primary text-sm sm:text-base" style={{ lineHeight: '1.8' }}>
                {scriptContent.split('\n\n').map((paragraph, index) => (
                  <p key={index} className="mb-4">
                    {paragraph}
                  </p>
                ))}
              </div>
            </div>

            {/* 底部诊断 */}
            <div className="px-4 py-2 border-t flex items-center justify-between flex-shrink-0 border-border bg-surface">
              <div className="flex items-center gap-4">
                <button className="text-xs flex items-center gap-1 text-text-tertiary">
                  <FileText size={12} />
                  <span className="hidden sm:inline">剧本医生</span>
                </button>
                <button className="text-xs flex items-center gap-1 text-text-tertiary">
                  <Play size={12} />
                  <span className="hidden sm:inline">剧情张力曲线</span>
                </button>
              </div>
              <button className="text-xs flex items-center gap-1 text-text-tertiary" onClick={() => setShowAI(!showAI)}>
                <Sparkles size={12} />
                <span className="sm:hidden">{showAI ? '隐藏AI' : 'AI助手'}</span>
                <span className="hidden sm:inline">重新诊断</span>
              </button>
            </div>
          </div>

          {/* 右侧AI助手 */}
          <div className={`
            w-72 flex-shrink-0 border-l overflow-y-auto border-border bg-surface
            absolute sm:relative inset-y-0 right-0 z-20 transition-transform duration-300
            ${showAI ? 'translate-x-0' : 'translate-x-full sm:translate-x-0'}
            sm:block
          `}>
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-medium uppercase tracking-wider text-text-tertiary">
                  智能体
                </h3>
                <button 
                  className="sm:hidden text-text-tertiary"
                  onClick={() => setShowAI(false)}
                >
                  <X size={16} />
                </button>
              </div>
              
              <div className="space-y-3">
                <div className="p-3 rounded-lg cursor-pointer hover:bg-white/5 transition-colors bg-elevated border border-border">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(33, 150, 243, 0.2)' }}>
                      <Sparkles size={16} style={{ color: '#2196F3' }} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        架构师
                      </p>
                      <p className="text-xs text-text-tertiary">
                        本集提纲 / 剧情梳理
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg cursor-pointer hover:bg-white/5 transition-colors" style={{ backgroundColor: 'rgba(255, 215, 0, 0.1)', border: '1px solid hsl(var(--primary))' }}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(76, 175, 80, 0.2)' }}>
                      <Wand2 size={16} style={{ color: '#4CAF50' }} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-primary">
                        AI 主笔 / 润色
                      </p>
                      <p className="text-xs text-text-tertiary">
                        续写正文 / 优化文笔
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg cursor-pointer hover:bg-white/5 transition-colors bg-elevated border border-border">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(156, 39, 176, 0.2)' }}>
                      <Sparkles size={16} style={{ color: '#9C27B0' }} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-text-primary">
                        AI 灵感助手
                      </p>
                      <p className="text-xs text-text-tertiary">
                        输入指令，如：描写一场雨夜的打斗...
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI输入区 */}
              <div className="mt-4 p-3 rounded-lg bg-elevated border border-border">
                <textarea
                  placeholder="输入指令..."
                  className="w-full bg-transparent text-sm resize-none outline-none text-text-primary"
                  style={{ minHeight: '80px' }}
                />
                <div className="flex justify-end gap-2 mt-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    className="border-border"
                  >
                    续写
                  </Button>
                  <Button size="sm" className="btn-primary">
                    执行
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
