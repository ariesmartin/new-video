import { useState } from 'react';
import { 
  FileText, 
  Camera, 
  Settings, 
  Image as ImageIcon,
  Plus,
  X,
  Upload
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAppStore, useUIStore } from '@/hooks/useStore';

interface LeftSidebarProps {
  onImportScript?: () => void;
  onAddEpisode?: () => void;
  onSmartSplit?: () => void;
}

type TabType = 'script' | 'shots' | 'settings' | 'assets';

export function LeftSidebar({ 
  onImportScript, 
  onAddEpisode, 
  onSmartSplit 
}: LeftSidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>('script');
  const { currentProject, currentEpisode, setCurrentEpisode } = useAppStore();
  const { addToast } = useUIStore();

  const tabs = [
    { id: 'script' as TabType, label: '剧本', icon: FileText },
    { id: 'shots' as TabType, label: '镜头', icon: Camera },
    { id: 'settings' as TabType, label: '设定', icon: Settings },
    { id: 'assets' as TabType, label: '资产', icon: ImageIcon },
  ];

  // 示例分集数据
  const episodes = currentProject?.episodes || [
    { id: '1', title: '第一集：深井的回响', order: 1 },
    { id: '2', title: '第二集：铁锈与猎手', order: 2 },
    { id: '3', title: '第三集：变异的祭坛', order: 3 },
    { id: '4', title: '第四集：风暴将至', order: 4 },
  ];

  const handleEpisodeClick = (episode: any) => {
    setCurrentEpisode(episode);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'script':
        return (
          <div className="p-4">
            {/* 导入按钮 */}
            <Button
              variant="outline"
              onClick={onImportScript}
              className="w-full mb-4 flex items-center justify-center gap-2"
              style={{ 
                borderColor: 'var(--border)',
                color: 'var(--text-secondary)'
              }}
            >
              <Upload size={16} />
              导入TXT
            </Button>

            {/* 智能分镜 */}
            <div className="mb-4">
              <Button
                onClick={onSmartSplit}
                className="w-full btn-primary mb-2"
              >
                智能分镜
              </Button>
              <Button
                variant="outline"
                onClick={onAddEpisode}
                className="w-full flex items-center justify-center gap-2"
                style={{ 
                  borderColor: 'var(--border)',
                  color: 'var(--text-secondary)'
                }}
              >
                <Plus size={16} />
                新增一集
              </Button>
            </div>

            {/* 分集列表 */}
            <div>
              <h4 
                className="text-xs font-medium mb-2 uppercase tracking-wider"
                style={{ color: 'var(--text-tertiary)' }}
              >
                分集列表
              </h4>
              <div className="space-y-1">
                {episodes.map((episode) => (
                  <div
                    key={episode.id}
                    onClick={() => handleEpisodeClick(episode)}
                    className={`
                      flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer
                      transition-colors duration-200
                      ${currentEpisode?.id === episode.id ? 'bg-yellow-500/10' : 'hover:bg-white/5'}
                    `}
                  >
                    <span 
                      className="text-sm truncate flex-1"
                      style={{ 
                        color: currentEpisode?.id === episode.id ? 'var(--primary)' : 'var(--text-primary)'
                      }}
                    >
                      {episode.title}
                    </span>
                    <button 
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded"
                      onClick={(e) => {
                        e.stopPropagation();
                        addToast({ type: 'info', message: '删除功能开发中' });
                      }}
                    >
                      <X size={14} style={{ color: 'var(--text-tertiary)' }} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'shots':
        return (
          <div className="p-4">
            <p 
              className="text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              镜头列表将在这里显示
            </p>
          </div>
        );

      case 'settings':
        return (
          <div className="p-4">
            {/* 角色列表 */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h4 
                  className="text-xs font-medium uppercase tracking-wider"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  角色 (2)
                </h4>
                <button 
                  className="p-1 hover:bg-white/10 rounded transition-colors"
                  style={{ color: 'var(--primary)' }}
                >
                  <Plus size={16} />
                </button>
              </div>
              <div className="space-y-2">
                {[
                  { name: '哑奴', gender: '男', avatar: '👤' },
                  { name: '叶孤鸿', gender: '男', avatar: '👤' },
                ].map((char, i) => (
                  <div 
                    key={i}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
                  >
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: 'var(--bg-night)' }}
                    >
                      <span className="text-lg">{char.avatar}</span>
                    </div>
                    <div>
                      <p 
                        className="text-sm font-medium"
                        style={{ color: 'var(--text-primary)' }}
                      >
                        {char.name}
                      </p>
                      <p 
                        className="text-xs"
                        style={{ color: 'var(--text-tertiary)' }}
                      >
                        {char.gender}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 场景列表 */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 
                  className="text-xs font-medium uppercase tracking-wider"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  场景 (2)
                </h4>
                <button 
                  className="p-1 hover:bg-white/10 rounded transition-colors"
                  style={{ color: 'var(--primary)' }}
                >
                  <Plus size={16} />
                </button>
              </div>
              <div className="space-y-2">
                {[
                  { name: '万剑冢', image: '🏞️' },
                  { name: '弑神剑觉醒', image: '🏞️' },
                ].map((scene, i) => (
                  <div 
                    key={i}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
                  >
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: 'var(--bg-night)' }}
                    >
                      <span className="text-lg">{scene.image}</span>
                    </div>
                    <p 
                      className="text-sm font-medium"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {scene.name}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'assets':
        return (
          <div className="p-4">
            <p 
              className="text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              视觉资产将在这里显示
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <aside 
      className="w-60 flex-shrink-0 flex flex-col"
      style={{ 
        backgroundColor: 'var(--bg-card)',
        borderRight: '1px solid var(--border)'
      }}
    >
      {/* 标签导航 */}
      <div 
        className="flex items-center justify-around p-2"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex flex-col items-center gap-1 p-2 rounded-lg transition-all duration-200
                ${isActive ? 'bg-yellow-500/10' : 'hover:bg-white/5'}
              `}
            >
              <Icon 
                size={20} 
                style={{ color: isActive ? 'var(--primary)' : 'var(--text-secondary)' }}
              />
              <span 
                className="text-xs"
                style={{ color: isActive ? 'var(--primary)' : 'var(--text-secondary)' }}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* 标签内容 */}
      <div className="flex-1 overflow-y-auto">
        {renderTabContent()}
      </div>
    </aside>
  );
}
