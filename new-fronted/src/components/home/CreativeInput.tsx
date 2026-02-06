import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useProjectStore, useUIStore, useAppStore } from '@/hooks/useStore';
import type { Project } from '@/types';

interface CreativeInputProps {
  onGenerate?: (prompt: string, fastMode: boolean) => void;
}

export function CreativeInput({ onGenerate }: CreativeInputProps) {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [fastMode, setFastMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const addProject = useProjectStore((state) => state.addProject);
  const setCurrentProject = useAppStore((state: { setCurrentProject: (p: Project | null) => void }) => state.setCurrentProject);
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);

  const placeholderText = '灵感：悬疑恐怖风格，发生在废弃医院，3集...';

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      addToast({ type: 'warning', message: '请输入创意描述' });
      return;
    }

    setIsGenerating(true);
    
    try {
      const projectName = prompt.slice(0, 20) + (prompt.length > 20 ? '...' : '');
      const newProject = await addProject(projectName);
      
      setCurrentProject(newProject);
      addToast({ type: 'success', message: '项目创建成功！正在进入项目...' });
      setPrompt('');
      
      if (onGenerate) {
        onGenerate(prompt, fastMode);
      }
      
      navigate(`/project/${newProject.id}`);
    } catch (error) {
      addToast({ type: 'error', message: '创建项目失败' });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mb-6 sm:mb-8 px-4 sm:px-0">
      <div
        className="rounded-xl p-1 transition-all duration-200 bg-surface border border-border"
      >
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={placeholderText}
          className="w-full bg-transparent p-3 sm:p-4 resize-none outline-none text-sm sm:text-base text-text-primary"
          rows={3}
          maxLength={500}
        />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0 px-3 sm:px-4 pb-3 sm:pb-4">
          <div className="flex items-center gap-2">
            <Zap
              size={14}
              className={`sm:w-4 sm:h-4 ${fastMode ? 'text-yellow-500' : 'text-gray-500'}`}
            />
            <span
              className="text-xs sm:text-sm text-text-secondary"
            >
              极速模式
            </span>
            <Switch
              checked={fastMode}
              onCheckedChange={setFastMode}
              className="scale-90 sm:scale-100"
            />
            <span
              className={`text-[10px] sm:text-xs ml-1 ${fastMode ? 'text-[#FFD700]' : 'text-text-tertiary'}`}
            >
              {fastMode ? 'ON' : 'OFF'}
            </span>
          </div>

          <Button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="btn-primary flex items-center gap-2 w-full sm:w-auto text-sm sm:text-base"
          >
            {isGenerating ? (
              <>
                <Loader2 size={14} className="sm:w-4 sm:h-4 animate-spin" />
                生成中...
              </>
            ) : (
              '开始生成'
            )}
          </Button>
        </div>
      </div>

      {fastMode && (
        <p
          className="text-[10px] sm:text-xs mt-2 text-center text-text-tertiary px-4"
        >
          开启后将自动完成大纲、剧本、角色场景的全流程
        </p>
      )}
    </div>
  );
}
