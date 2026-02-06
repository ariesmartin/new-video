import { useState, useEffect } from 'react';
import { ProjectHeader } from '@/components/layout/ProjectHeader';
import { LeftSidebar } from '@/components/panels/LeftSidebar';
import { RightPanel } from '@/components/panels/RightPanel';
import { StoryboardCanvas } from '@/components/canvas/StoryboardCanvas';
import { ScriptWorkshopModal } from '@/components/modals/ScriptWorkshopModal';
import { BatchGenerateModal } from '@/components/modals/BatchGenerateModal';
import { BackstageModal } from '@/components/modals/BackstageModal';
import { InpaintModal } from '@/components/modals/InpaintModal';
import { OutpaintModal } from '@/components/modals/OutpaintModal';
import { VirtualCameraModal } from '@/components/modals/VirtualCameraModal';
import { CameraMoveModal } from '@/components/modals/CameraMoveModal';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import type { Card } from '@/types';

export function ProjectPage() {
  const { theme } = useAppStore();
  const { modal, closeModal } = useUIStore();
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const [isScriptWorkshopOpen, setIsScriptWorkshopOpen] = useState(false);
  const [isBatchGenerateOpen, setIsBatchGenerateOpen] = useState(false);
  const [isBackstageOpen, setIsBackstageOpen] = useState(false);
  const [isCameraMoveOpen, setIsCameraMoveOpen] = useState(false);

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  const handleCardSelect = (card: Card) => {
    setSelectedCard(card);
  };

  const handleScriptWorkshop = () => {
    setIsScriptWorkshopOpen(true);
  };

  const handleBatchGenerate = () => {
    setIsBatchGenerateOpen(true);
  };

  const handleBackstage = () => {
    setIsBackstageOpen(true);
  };

  const handleExport = () => {
    console.log('Export');
  };

  const handleImportScript = () => {
    console.log('Import script');
  };

  const handleAddEpisode = () => {
    console.log('Add episode');
  };

  const handleSmartSplit = () => {
    console.log('Smart split');
  };

  return (
    <div 
      className="h-screen flex flex-col overflow-hidden"
      style={{ backgroundColor: 'var(--bg-primary)' }}
    >
      <ProjectHeader 
        onScriptWorkshop={handleScriptWorkshop}
        onBatchGenerate={handleBatchGenerate}
        onExport={handleExport}
        onBackstage={handleBackstage}
      />
      
      <div className="flex-1 flex overflow-hidden">
        <LeftSidebar 
          onImportScript={handleImportScript}
          onAddEpisode={handleAddEpisode}
          onSmartSplit={handleSmartSplit}
        />
        
        <StoryboardCanvas 
          onCardSelect={handleCardSelect}
          selectedCard={selectedCard}
        />
        
        <RightPanel selectedCard={selectedCard} />
      </div>

      {/* 弹窗 */}
      <ScriptWorkshopModal 
        isOpen={isScriptWorkshopOpen} 
        onClose={() => setIsScriptWorkshopOpen(false)} 
      />
      
      <BatchGenerateModal 
        isOpen={isBatchGenerateOpen} 
        onClose={() => setIsBatchGenerateOpen(false)} 
      />
      
      <BackstageModal 
        isOpen={isBackstageOpen} 
        onClose={() => setIsBackstageOpen(false)} 
      />

      <CameraMoveModal
        isOpen={isCameraMoveOpen || modal.type === 'cameraMove'}
        onClose={() => {
          setIsCameraMoveOpen(false);
          closeModal();
        }}
        imageUrl={selectedCard?.imageUrl}
      />
      
      <InpaintModal 
        isOpen={modal.type === 'inpaint'}
        onClose={closeModal}
        imageUrl={selectedCard?.imageUrl}
      />
      
      <OutpaintModal 
        isOpen={modal.type === 'outpaint'}
        onClose={closeModal}
        imageUrl={selectedCard?.imageUrl}
      />
      
      <VirtualCameraModal 
        isOpen={modal.type === 'virtualCamera'}
        onClose={closeModal}
        imageUrl={selectedCard?.imageUrl}
      />
    </div>
  );
}
