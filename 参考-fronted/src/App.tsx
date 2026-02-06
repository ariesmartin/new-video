import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { HomePage } from '@/pages/HomePage';
import { ProjectPage } from '@/pages/ProjectPage';
import { useUIStore } from '@/hooks/useStore';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import type { Toast } from '@/types';

function AppContent() {
  const toasts = useUIStore((state: { toasts: Toast[] }) => state.toasts);
  const removeToast = useUIStore((state: { removeToast: (id: string) => void }) => state.removeToast);

  // 处理 Toast 显示
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
        <Route path="/project" element={<ProjectPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster 
        position="top-center"
        toastOptions={{
          style: {
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
          },
        }}
      />
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
