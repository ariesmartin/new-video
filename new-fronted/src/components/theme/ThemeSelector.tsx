import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, TrendingUp, Users, Sparkles, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useProjectStore, useUIStore, useAppStore } from '@/hooks/useStore';
import type { Project } from '@/types';

// Theme data structure
interface Theme {
  id: string;
  slug: string;
  name: string;
  nameEn: string;
  description: string;
  category: string;
  marketScore: number;
  successRate: number;
  trendDirection: 'hot' | 'up' | 'stable' | 'down' | 'cold';
  keywords: string[];
  color: string;
}

const themes: Theme[] = [
  {
    id: '1',
    slug: 'revenge',
    name: '复仇逆袭',
    nameEn: 'Revenge & Comeback',
    description: '精准击中观众的"共情痛感"与"理智爽感"双重需求，通过压抑-释放的情绪曲线实现强用户粘性',
    category: 'drama',
    marketScore: 95,
    successRate: 88,
    trendDirection: 'hot',
    keywords: ['隐忍', '爆发', '身份揭露', '打脸', '清算'],
    color: 'from-red-500 to-orange-600',
  },
  {
    id: '2',
    slug: 'romance',
    name: '甜宠恋爱',
    nameEn: 'Sweet Romance',
    description: '高颜值CP+高糖互动，满足女性观众的情感投射与恋爱幻想',
    category: 'romance',
    marketScore: 92,
    successRate: 85,
    trendDirection: 'up',
    keywords: ['反差萌', '契约婚姻', '甜宠', '治愈', '双向奔赴'],
    color: 'from-pink-500 to-rose-600',
  },
  {
    id: '3',
    slug: 'suspense',
    name: '悬疑推理',
    nameEn: 'Suspense & Mystery',
    description: '强悬疑钩子+逻辑严密的推理过程，打造高粘性追剧体验',
    category: 'thriller',
    marketScore: 88,
    successRate: 82,
    trendDirection: 'up',
    keywords: ['密室', '反转', '线索', '真相', '心理博弈'],
    color: 'from-purple-500 to-indigo-600',
  },
  {
    id: '4',
    slug: 'transmigration',
    name: '穿越重生',
    nameEn: 'Transmigration',
    description: '现代人穿越古代/重生逆袭，利用信息差和认知优势改变命运',
    category: 'fantasy',
    marketScore: 85,
    successRate: 78,
    trendDirection: 'stable',
    keywords: ['穿越', '重生', '金手指', '逆袭', '改变历史'],
    color: 'from-blue-500 to-cyan-600',
  },
  {
    id: '5',
    slug: 'family_urban',
    name: '家庭伦理',
    nameEn: 'Family Drama',
    description: '聚焦现代都市家庭矛盾，婆媳关系、婚姻危机、职场平衡等现实议题',
    category: 'drama',
    marketScore: 82,
    successRate: 75,
    trendDirection: 'stable',
    keywords: ['婆媳', '婚姻', '职场', '亲子', '现实'],
    color: 'from-emerald-500 to-teal-600',
  },
];

const trendIcons = {
  hot: '🔥',
  up: '📈',
  stable: '➡️',
  down: '📉',
  cold: '❄️',
};

const trendLabels = {
  hot: '热门',
  up: '上升',
  stable: '稳定',
  down: '下降',
  cold: '冷门',
};

interface ThemeSelectorProps {
  onThemeSelect?: (theme: Theme) => void;
  showMarketData?: boolean;
}

export function ThemeSelector({ onThemeSelect, showMarketData = true }: ThemeSelectorProps) {
  const navigate = useNavigate();
  const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const addProject = useProjectStore((state) => state.addProject);
  const setCurrentProject = useAppStore((state: { setCurrentProject: (p: Project | null) => void }) => state.setCurrentProject);
  const addToast = useUIStore((state: { addToast: (t: { type: 'success' | 'warning' | 'error' | 'info'; message: string }) => void }) => state.addToast);

  const handleThemeSelect = (theme: Theme) => {
    setSelectedTheme(theme);
    if (onThemeSelect) {
      onThemeSelect(theme);
    }
  };

  const handleCreateProject = async () => {
    if (!selectedTheme) {
      addToast({ type: 'warning', message: '请先选择一个题材' });
      return;
    }

    setIsCreating(true);
    
    try {
      const newProject = await addProject(`${selectedTheme.name}短剧`);
      
      // Store theme selection in project metadata
      const projectWithTheme = {
        ...newProject,
        genre: selectedTheme.name,
        setting: selectedTheme.category === 'fantasy' ? 'ancient' : 'modern',
      };
      
      setCurrentProject(projectWithTheme);
      addToast({ 
        type: 'success', 
        message: `已选择「${selectedTheme.name}」题材，正在进入项目...` 
      });
      
      navigate(`/project/${newProject.id}`);
    } catch (error) {
      addToast({ type: 'error', message: '创建项目失败' });
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4">
      <div className="mb-8 text-center">
        <h2 className="text-3xl font-bold text-text-primary mb-3">
          选择题材
        </h2>
        <p className="text-text-secondary max-w-2xl mx-auto">
          基于市场数据分析，我们为您推荐了当前最热门的短剧题材。
          每个题材都包含完整的创作指导、爆款元素和市场趋势。
        </p>
      </div>

      {/* Theme Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {themes.map((theme) => (
          <Card
            key={theme.id}
            className={`cursor-pointer transition-all duration-200 hover:scale-[1.02] ${
              selectedTheme?.id === theme.id
                ? 'ring-2 ring-primary border-primary'
                : 'hover:border-border-hover'
            }`}
            onClick={() => handleThemeSelect(theme)}
          >
            <CardHeader className={`bg-gradient-to-r ${theme.color} text-white rounded-t-lg`}>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-xl font-bold">{theme.name}</CardTitle>
                  <CardDescription className="text-white/80 text-sm mt-1">
                    {theme.nameEn}
                  </CardDescription>
                </div>
                {showMarketData && (
                  <Badge variant="secondary" className="bg-white/20 text-white border-0">
                    {trendIcons[theme.trendDirection]} {trendLabels[theme.trendDirection]}
                  </Badge>
                )}
              </div>
            </CardHeader>
            
            <CardContent className="pt-4">
              <p className="text-text-secondary text-sm mb-4 line-clamp-2">
                {theme.description}
              </p>

              {/* Keywords */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                {theme.keywords.slice(0, 3).map((keyword) => (
                  <Badge key={keyword} variant="outline" className="text-xs">
                    {keyword}
                  </Badge>
                ))}
                {theme.keywords.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{theme.keywords.length - 3}
                  </Badge>
                )}
              </div>

              {/* Market Data */}
              {showMarketData && (
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border">
                  <div className="flex items-center gap-2">
                    <TrendingUp size={14} className="text-success" />
                    <span className="text-xs text-text-secondary">市场评分</span>
                    <span className="text-sm font-semibold text-text-primary">
                      {theme.marketScore}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users size={14} className="text-info" />
                    <span className="text-xs text-text-secondary">成功率</span>
                    <span className="text-sm font-semibold text-text-primary">
                      {theme.successRate}%
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Selected Theme Details */}
      {selectedTheme && (
        <Card className="mb-6 border-primary/30 bg-primary/5">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                  <Sparkles size={18} className="text-primary" />
                  已选择：{selectedTheme.name}
                </h3>
                <p className="text-text-secondary text-sm mt-1">
                  系统将自动注入该题材的完整创作指导，包括核心公式、爆款元素、钩子模板等
                </p>
              </div>
              
              <Button
                onClick={handleCreateProject}
                disabled={isCreating}
                className="btn-primary flex items-center gap-2 min-w-[140px]"
              >
                {isCreating ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    创建中...
                  </>
                ) : (
                  <>
                    开始创作
                    <ChevronRight size={16} />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tips */}
      <div className="text-center text-text-tertiary text-sm">
        <p className="flex items-center justify-center gap-2">
          <BookOpen size={14} />
          每个题材都包含详细的创作指南，帮助您快速产出爆款短剧
        </p>
      </div>
    </div>
  );
}

// Export theme data for use in other components
export { themes };
export type { Theme };
