import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { AIAssistantBar } from '@/components/ai/AIAssistantBar';
import { BackstageModal } from '@/components/modals/BackstageModal';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useUIStore } from '@/hooks/useStore';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import type { Toast } from '@/types';

import { HomePage } from '@/pages/HomePage';
import { ProjectPage } from '@/pages/ProjectPage';
import { ScriptWorkshopPage } from '@/pages/ScriptWorkshopPage';

function AppContent() {
  const location = useLocation();
  const toasts = useUIStore((state: { toasts: Toast[] }) => state.toasts);
  const removeToast = useUIStore((state: { removeToast: (id: string) => void }) => state.removeToast);
  const backstageModalOpen = useUIStore((state: { backstageModalOpen: boolean }) => state.backstageModalOpen);
  const closeBackstageModal = useUIStore((state: { closeBackstageModal: () => void }) => state.closeBackstageModal);

  const isScriptWorkshop = location.pathname.includes('/script-workshop');
  const isHomePage = location.pathname === '/';

  useEffect(() => {
    toasts.forEach((t: Toast) => {
      if (t.type === 'success') {
        toast.success(t.message);
      } else if (t.type === 'error') {
        toast.error(t.message);
      } else if (t.type === 'warning') {
        toast.warning(t.message);
      } else {
        toast.info(t.message);
      }
      removeToast(t.id);
    });
  }, [toasts, removeToast]);

  return (
    <>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/project/:projectId?" element={<ProjectPage />} />
        <Route path="/project/:projectId/episode/:episodeId/script-workshop" element={<ScriptWorkshopPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      {!isHomePage && !isScriptWorkshop && <AIAssistantBar />}
      
      <BackstageModal 
        isOpen={backstageModalOpen} 
        onClose={closeBackstageModal} 
      />
      
      <Toaster 
        position="top-center"
        toastOptions={{
          className: "bg-surface border border-border shadow-lg rounded-xl",
          classNames: {
            toast: "group toast group-[.toaster]:bg-surface group-[.toaster]:text-text-primary group-[.toaster]:border-border group-[.toaster]:shadow-lg group-[.toaster]:rounded-xl",
            title: "group-[.toast]:font-medium group-[.toast]:text-sm",
            description: "group-[.toast]:text-text-secondary group-[.toast]:text-xs",
            actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
            cancelButton: "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground",
          },
          style: {
            background: 'hsl(var(--surface))',
            color: 'hsl(var(--text-primary))',
            border: '1px solid hsl(var(--border))',
          },
        }}
      />
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
