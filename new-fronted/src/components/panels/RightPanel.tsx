import { motion, AnimatePresence } from 'framer-motion';
import { X, BookOpen, Grid3X3, LayoutGrid } from 'lucide-react';
import { DirectorPanel } from './DirectorPanel';
import { ShotDetailPanel } from './ShotDetailPanel';
import { useUIStore, useEpisodeStore } from '@/hooks/useStore';
import { useState } from 'react';

type RightPanelTab = 'script' | 'storyboard' | 'card';

export function RightPanel() {
  const { rightPanelVisible, rightPanelMode, selectedNodeId, closeRightPanel } = useUIStore();
  const { shotNodes } = useEpisodeStore();
  const [activeTab, setActiveTab] = useState<RightPanelTab>('script');

  const selectedShot = selectedNodeId 
    ? shotNodes.find((n) => n.shotId === selectedNodeId)
    : null;

  const tabs = [
    { id: 'script' as RightPanelTab, label: '剧本', icon: BookOpen },
    { id: 'storyboard' as RightPanelTab, label: '分镜', icon: Grid3X3 },
    { id: 'card' as RightPanelTab, label: '卡片', icon: LayoutGrid },
  ];

  return (
    <AnimatePresence>
      {rightPanelVisible && (
        <motion.div
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 100, opacity: 0 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="fixed right-4 z-40 w-[340px] max-w-[calc(100vw-32px)] hidden sm:block"
          style={{
            top: '72px',
            bottom: '80px',
          }}
        >
          <div className="h-full flex flex-col rounded-2xl bg-surface/95 backdrop-blur-md border border-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary"></span>
                <h3 className="font-medium text-text-primary text-sm">
                  {rightPanelMode === 'director' 
                    ? 'Ep.1 导演台' 
                    : selectedShot 
                      ? `镜头 #${selectedShot.shotNumber}` 
                      : '节点编辑'}
                </h3>
              </div>
              <button
                onClick={closeRightPanel}
                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-text-tertiary hover:text-text-primary"
              >
                <X size={16} />
              </button>
            </div>

            {rightPanelMode === 'director' && (
              <div className="flex border-b border-border/50">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`
                        flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium
                        transition-all duration-200
                        ${isActive 
                          ? 'bg-primary text-primary-foreground' 
                          : 'text-text-secondary hover:text-text-primary hover:bg-white/5'}
                      `}
                    >
                      <Icon size={14} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            )}

            <div className="flex-1 overflow-hidden">
              {rightPanelMode === 'director' && <DirectorPanel activeTab={activeTab} />}
              {rightPanelMode === 'node-edit' && selectedShot && <ShotDetailPanel shot={selectedShot} />}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
