import { useState } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useProjectStore, useUIStore } from '@/hooks/useStore';
import { createProject, ApiError } from '@/api';
import type { Project } from '@/types';

interface CreativeInputProps {
  onGenerate?: (prompt: string, fastMode: boolean) => void;
}

export function CreativeInput({ onGenerate }: CreativeInputProps) {
  const [prompt, setPrompt] = useState('');
  const [fastMode, setFastMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const addProject = useProjectStore((state: { addProject: (p: Project) => void }) => state.addProject);
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);

  const placeholderText = '灵感：悬疑恐怖风格，发生在废弃医院，3集...';

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      addToast({ type: 'warning', message: '请输入创意描述' });
      return;
    }

    setIsGenerating(true);
    
    try {
      // ✅ 调用真实后端 API 创建项目
      const newProject = await createProject(prompt, fastMode);
      
      // 添加到前端状态
      addProject(newProject);
      
      addToast({ type: 'success', message: '项目创建成功！' });
      
      setPrompt('');
      
      if (onGenerate) {
        onGenerate(prompt, fastMode);
      }
    } catch (error) {
      console.error('创建项目失败:', error);
      
      if (error instanceof ApiError) {
        // 根据错误类型显示不同提示
        if (error.code === 'NETWORK_ERROR') {
          addToast({ 
            type: 'error', 
            message: '无法连接到后端服务，请确保后端服务已启动 (python backend/main.py)' 
          });
        } else if (error.code === 'TIMEOUT_ERROR') {
          addToast({ type: 'error', message: '请求超时，请稍后重试' });
        } else {
          addToast({ type: 'error', message: error.message || '创建项目失败' });
        }
      } else {
        addToast({ type: 'error', message: '创建项目时发生未知错误' });
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mb-8">
      <div 
        className="rounded-xl p-1 transition-all duration-200"
        style={{ 
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border)'
        }}
      >
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={placeholderText}
          className="w-full bg-transparent p-4 resize-none outline-none text-base"
          style={{ color: 'var(--text-primary)' }}
          rows={3}
          maxLength={500}
          disabled={isGenerating}
        />
        
        <div className="flex items-center justify-between px-4 pb-4">
          <div className="flex items-center gap-2">
            <Zap 
              size={16} 
              className={fastMode ? 'text-yellow-500' : 'text-gray-500'}
            />
            <span 
              className="text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              极速模式
            </span>
            <Switch
              checked={fastMode}
              onCheckedChange={setFastMode}
              disabled={isGenerating}
            />
            <span 
              className="text-xs ml-1"
              style={{ color: fastMode ? '#FFD700' : 'var(--text-tertiary)' }}
            >
              {fastMode ? 'ON' : 'OFF'}
            </span>
          </div>
          
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
            className="btn-primary flex items-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                创建中...
              </>
            ) : (
              '开始生成'
            )}
          </Button>
        </div>
      </div>
      
      {fastMode && (
        <p 
          className="text-xs mt-2 text-center"
          style={{ color: 'var(--text-tertiary)' }}
        >
          极速模式功能开发中
        </p>
      )}
    </div>
  );
}
