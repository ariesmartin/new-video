import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { 
  WelcomeHeader, 
  CreativeInput, 
  QuickActions, 
  ProjectList 
} from '@/components/home';
import { useAppStore, useUIStore } from '@/hooks/useStore';

export function HomePage() {
  const navigate = useNavigate();
  const { theme } = useAppStore();
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);

  useEffect(() => {
    // 应用主题
    document.body.className = theme;
  }, [theme]);

  const handleGenerate = (prompt: string, fastMode: boolean) => {
    console.log('Generate project:', prompt, 'Fast mode:', fastMode);
    addToast({ 
      type: 'success', 
      message: fastMode ? '极速模式：正在构思宏大叙事...' : '项目创建成功！' 
    });
  };

  const handleTutorial = () => {
    addToast({ type: 'info', message: '快速入门教程开发中' });
  };

  const handleScriptWorkshop = () => {
    addToast({ type: 'info', message: '剧本工坊开发中' });
  };

  const handleNavigateToProject = () => {
    navigate('/project');
  };

  return (
    <div 
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: 'var(--bg-primary)' }}
    >
      <Header variant="home" />
      
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <WelcomeHeader />
        <CreativeInput onGenerate={handleGenerate} />
        <QuickActions 
          onTutorial={handleTutorial}
          onScriptWorkshop={handleScriptWorkshop}
        />
        <ProjectList onProjectClick={handleNavigateToProject} />
      </main>

      {/* 底部水印 */}
      <div className="fixed bottom-4 right-4 pointer-events-none">
        <div className="text-right">
          <p 
            className="text-2xl font-script italic"
            style={{ color: 'var(--text-tertiary)', opacity: 0.5 }}
          >
            wuli
          </p>
          <p 
            className="text-xs"
            style={{ color: 'var(--text-tertiary)', opacity: 0.5 }}
          >
            呜哩的片子
          </p>
        </div>
      </div>
    </div>
  );
}
