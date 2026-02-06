import { Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAppStore } from '@/hooks/useStore';

interface DirectorPanelProps {
  activeTab?: 'script' | 'storyboard' | 'card';
}

export function DirectorPanel({ activeTab = 'script' }: DirectorPanelProps) {
  const { currentEpisode } = useAppStore();

  const scriptContent = currentEpisode?.script || `新巴比伦的雨总是带着一股机油味。下城区的垃圾处理厂被高耸的围墙圈禁，这里是城市不仅丢弃废料，也丢弃灵魂的地方。

巴斯特是一只甚至连名字都没有的杂种狗，它正匍匐在一堆生锈的汽车零件下。它的呼吸很轻，眼睛死死盯着前方五米处的一块发霉的面包。而在它对面，一只体型硕大的比特犬正龇着牙，那是这一带的小霸王"碎骨"。

雨水顺着巴斯特左耳那个参差不齐的缺口流下，那是它幼年时从维克多的实验室逃生时留下的烙印。`;

  const renderContent = () => {
    switch (activeTab) {
      case 'script':
        return (
          <div className="flex-1 flex flex-col p-4 pt-2">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs px-2 py-1 rounded bg-elevated text-text-secondary">
                本集故事(Story)
              </span>
              <span className="text-xs px-2 py-1 rounded cursor-pointer hover:bg-white/5 text-text-tertiary">
                场次剧本 Script
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 rounded-lg bg-elevated text-sm leading-relaxed text-text-primary">
              {scriptContent}
            </div>

            <Button className="w-full mt-3 btn-primary flex items-center justify-center gap-2 text-sm">
              <Wand2 size={16} />
              AI 扩写为场次剧本
            </Button>
          </div>
        );

      case 'storyboard':
        return (
          <div className="flex-1 flex flex-col p-4 pt-2">
            <p className="text-sm text-text-secondary">分镜列表将在这里显示</p>
          </div>
        );

      case 'card':
        return (
          <div className="flex-1 flex flex-col p-4 pt-2">
            <p className="text-sm text-text-secondary">卡片属性设置</p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full w-full">
      {renderContent()}
    </div>
  );
}
