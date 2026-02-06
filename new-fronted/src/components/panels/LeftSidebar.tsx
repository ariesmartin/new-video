import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FolderOpen,
  FileText,
  Gamepad2,
  Smile,
  Image as ImageIcon,
  ChevronLeft,
  Plus,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import { episodesService } from '@/api/services/episodes';
import { assetsService } from '@/api/services/assets';
import type { Episode, Character, Scene } from '@/types';

type TabType = 'project' | 'script' | 'shots' | 'characters' | 'assets';

const tabs = [
  { id: 'project' as TabType, icon: FolderOpen, label: '项目' },
  { id: 'script' as TabType, icon: FileText, label: '剧本' },
  { id: 'shots' as TabType, icon: Gamepad2, label: '镜头' },
  { id: 'characters' as TabType, icon: Smile, label: '设定' },
  { id: 'assets' as TabType, icon: ImageIcon, label: '资产' },
];

interface LeftSidebarProps {
  episodes?: Episode[];
}

export function LeftSidebar({ episodes: externalEpisodes }: LeftSidebarProps = {}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('script');
  const { currentProject, currentEpisode, setCurrentEpisode } = useAppStore();
  const { openDirectorPanel, openNodeEditPanel, addToast } = useUIStore();

  const [episodes, setEpisodes] = useState<Episode[]>(externalEpisodes || []);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [scenes] = useState<Scene[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const panelRef = useRef<HTMLDivElement>(null);

  const handleTabClick = (tabId: TabType) => {
    setActiveTab(tabId);
    setIsExpanded(true);
    
    if (tabId === 'script') {
      openDirectorPanel();
    }
  };

  const handleEpisodeClick = (episode: Episode) => {
    setCurrentEpisode(episode);
    openDirectorPanel();
  };

  const handleShotClick = (shotId: string) => {
    openNodeEditPanel(shotId);
  };



  useEffect(() => {
    if (!currentProject?.id) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        const [episodesRes, assetsRes] = await Promise.allSettled([
          episodesService.listEpisodes(currentProject.id),
          assetsService.listAssets(currentProject.id, 'character'),
        ]);

        if (episodesRes.status === 'fulfilled') {
          const responseData = episodesRes.value.data as any;
          const apiEpisodes = responseData?.data || responseData || [];
          setEpisodes(
            apiEpisodes.map((ep: any) => ({
              id: ep.episodeId || ep.id,
              projectId: ep.projectId || currentProject.id,
              episodeNumber: ep.episodeNumber || 1,
              title: ep.title || '未命名剧集',
              summary: ep.summary,
              script: ep.scriptText || ep.script,
              novelContent: ep.novelContent,
              wordCount: ep.wordCount || 0,
              status: ep.status || 'draft',
              canvasData: ep.canvasData,
              createdAt: new Date(ep.createdAt || Date.now()),
              updatedAt: new Date(ep.updatedAt || Date.now()),
            }))
          );
        }

        if (assetsRes.status === 'fulfilled') {
          const responseData = assetsRes.value.data as any;
          const apiAssets = responseData?.data || responseData || [];
          setCharacters(
            apiAssets.map((asset: any) => ({
              id: asset.assetId || asset.id,
              projectId: asset.projectId || currentProject.id,
              name: asset.name || '未命名角色',
              gender: asset.visualTokens?.gender || asset.gender || 'other',
              description: asset.description || '',
              referenceImages: asset.referenceUrls || asset.referenceImages || [],
            }))
          );
        }
      } catch (err) {
        console.error('Failed to load sidebar data:', err);
        addToast?.({ type: 'error', message: '加载数据失败，请刷新页面重试' });
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [currentProject?.id]);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'script':
        return (
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
                大纲
              </h4>
              <button className="text-xs text-primary hover:underline">
                导入 TXT
              </button>
            </div>

            <textarea
              className="w-full h-32 p-3 rounded-lg bg-elevated border border-border text-sm text-text-primary resize-none"
              placeholder="在此输入故事大纲..."
            />

            <div className="flex items-center gap-2">
              <input
                type="number"
                defaultValue={5}
                className="w-16 px-2 py-1 rounded bg-elevated border border-border text-sm text-center"
              />
              <Button className="flex-1 btn-primary gap-1 text-sm">
                <span>✨</span>
                智能分集
              </Button>
            </div>

            <Button
              variant="outline"
              className="w-full gap-1 border-border text-text-secondary text-sm"
            >
              <Plus size={16} />
              新增一集
            </Button>

            <div>
              <h4 className="text-xs font-medium text-text-tertiary uppercase tracking-wider mb-2">
                分集列表
              </h4>
              <div className="space-y-1">
                {isLoading ? (
                  <div className="text-center py-4 text-text-tertiary text-sm">加载中...</div>
                ) : episodes.length === 0 ? (
                  <div className="text-center py-4 text-text-tertiary text-sm">暂无剧集</div>
                ) : (
                  episodes.map((ep) => (
                    <div
                      key={ep.id}
                      onClick={() => handleEpisodeClick(ep)}
                      className={`
                        group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer
                        transition-colors duration-200
                        ${currentEpisode?.id === ep.id ? 'bg-primary/10' : 'hover:bg-white/5'}
                      `}
                    >
                      <div className="flex flex-col flex-1 min-w-0">
                        <span
                          className={`text-sm truncate ${
                            currentEpisode?.id === ep.id ? 'text-primary' : 'text-text-primary'
                          }`}
                        >
                          第{ep.episodeNumber}集: {ep.title}
                        </span>
                        <span className="text-xs text-text-tertiary">{ep.wordCount}字</span>
                      </div>
                      <button
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                      >
                        <X size={14} className="text-text-tertiary" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        );

      case 'shots':
        return (
          <div className="p-4">
            <h4 className="text-xs font-medium text-text-tertiary uppercase tracking-wider mb-3">
              镜头列表
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {Array.from({ length: 6 }, (_, i) => i + 1).map((num) => (
                <div
                  key={num}
                  onClick={() => handleShotClick(`shot-${num}`)}
                  className="aspect-video bg-elevated rounded-lg flex items-center justify-center cursor-pointer hover:bg-white/5 transition-colors border border-border"
                >
                  <span className="text-xs text-text-secondary">镜头 {num}</span>
                </div>
              ))}
            </div>
          </div>
        );

      case 'characters':
        return (
          <div className="p-4 space-y-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
                  角色
                </h4>
                <button className="p-1 hover:bg-white/10 rounded transition-colors text-primary">
                  <Plus size={16} />
                </button>
              </div>
              <div className="space-y-2">
                {isLoading ? (
                  <div className="text-center py-4 text-text-tertiary text-sm">加载中...</div>
                ) : characters.length === 0 ? (
                  <div className="text-center py-4 text-text-tertiary text-sm">暂无角色</div>
                ) : (
                  characters.map((char) => (
                    <div
                      key={char.id}
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
                    >
                      <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center">
                        <span className="text-lg">👤</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-text-primary">{char.name}</p>
                        <p className="text-xs text-text-tertiary">{char.gender}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
                  场景
                </h4>
                <button className="p-1 hover:bg-white/10 rounded transition-colors text-primary">
                  <Plus size={16} />
                </button>
              </div>
              <div className="space-y-2">
                {isLoading ? (
                  <div className="text-center py-4 text-text-tertiary text-sm">加载中...</div>
                ) : scenes.length === 0 ? (
                  <div className="text-center py-4 text-text-tertiary text-sm">暂无场景</div>
                ) : (
                  scenes.map((scene) => (
                    <div
                      key={scene.id}
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
                    >
                      <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center">
                        <span className="text-lg">🏥</span>
                      </div>
                      <p className="text-sm font-medium text-text-primary">{scene.name}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        );

      case 'assets':
        return (
          <div className="p-4">
            <h4 className="text-xs font-medium text-text-tertiary uppercase tracking-wider mb-3">
              视觉资产
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {Array.from({ length: 4 }, (_, i) => i + 1).map((num) => (
                <div
                  key={num}
                  className="aspect-square bg-elevated rounded-lg flex items-center justify-center border border-border"
                >
                  <span className="text-2xl">🖼️</span>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return (
          <div className="p-4">
            <p className="text-sm text-text-secondary">项目概览</p>
          </div>
        );
    }
  };

  return (
    <>
      <AnimatePresence mode="wait">
        {!isExpanded && (
          <motion.div
            key="icon-bar"
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -100, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="fixed left-4 z-40 hidden sm:flex flex-col"
            style={{
              top: '72px',
              bottom: '80px',
              justifyContent: 'center',
            }}
          >
            <div className="flex flex-col items-center py-3 px-2 gap-2 rounded-2xl bg-surface/95 backdrop-blur-md border border-border shadow-2xl"
            >
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;

                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabClick(tab.id)}
                    className={`
                      relative w-10 h-10 flex items-center justify-center rounded-xl
                      transition-all duration-200
                      ${isActive 
                        ? 'bg-primary/20 text-primary shadow-inner' 
                        : 'text-text-secondary hover:text-text-primary hover:bg-white/5'}
                    `}
                    title={tab.label}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="leftActiveIndicator"
                        className="absolute inset-0 rounded-xl bg-primary/10"
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      />
                    )}
                    <Icon size={20} />
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            ref={panelRef}
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="fixed left-4 z-40 hidden sm:block"
              style={{
                top: '72px',
                bottom: '80px',
                width: 'min(280px, 85vw)',
              }}
          >
              <div className="h-full flex flex-col rounded-2xl bg-surface/95 backdrop-blur-md border border-border shadow-2xl overflow-hidden">
              <div className="flex items-center justify-between px-2 py-2 border-b border-border/50">
                <div className="flex items-center justify-around flex-1">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;

                    return (
                      <button
                        key={tab.id}
                        onClick={() => handleTabClick(tab.id)}
                        className={`
                          flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-lg transition-all duration-200 min-w-[44px]
                          ${isActive ? 'bg-primary/10 text-primary' : 'hover:bg-white/5 text-text-secondary'}
                        `}
                      >
                        <Icon size={18} />
                        <span className="text-[10px]">{tab.label}</span>
                      </button>
                    );
                  })}
                </div>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors text-text-tertiary hover:text-text-primary flex-shrink-0"
                >
                  <ChevronLeft size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto">{renderTabContent()}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
