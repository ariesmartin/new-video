import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { OutlineData, OutlineNode } from '@/types/outline';
import type { Chapter } from '@/types/novel';
import type { GlobalReview, ChapterReview } from '@/types/review';
import { outlineService } from '@/api/services/outline';
import { novelService } from '@/api/services/novel';
import { reviewService } from '@/api/services/review';

export type WorkshopModule = 'outline' | 'novel' | 'script' | 'storyboard';

export type WorkflowStage = 
  | 'idle'
  | 'story_planning'
  | 'skeleton_building'
  | 'novel_writing'
  | 'script_adapting'
  | 'storyboard_directing'
  | 'completed';

interface WorkflowState {
  stage: WorkflowStage;
  currentAgent: string | null;
  progress: number;
  message: string;
  isRunning: boolean;
}

interface WorkshopState {
  // 当前模块
  activeModule: WorkshopModule;
  
  // 工作流状态
  workflow: WorkflowState;
  
  // 大纲数据
  outline: OutlineData | null;
  outlineNodes: OutlineNode[];
  selectedNodeId: string | null;
  
  // 全局审阅（大纲用）
  globalReview: GlobalReview | null;
  
  // 小说数据
  chapters: Chapter[];
  currentChapterId: string | null;
  currentChapterContent: string;
  
  // 章节审阅（小说用）
  chapterReviews: Map<string, ChapterReview>;
  
  // UI 状态
  isGenerating: boolean;
  isReviewing: boolean;
  isSaving: boolean;
  autoSaveEnabled: boolean;

  batchStatus: {
    currentBatch: number;
    totalBatches: number;
    needsNextBatch: boolean;
    isComplete: boolean;
  };
  
  // Actions - 模块切换
  setActiveModule: (module: WorkshopModule) => void;
  
  // Actions - 大纲
  generateOutline: (projectId: string, planId: string) => Promise<void>;
  loadOutline: (projectId: string) => Promise<void>;
  updateOutlineNode: (nodeId: string, updates: Partial<OutlineNode>) => Promise<void>;
  selectNode: (nodeId: string) => void;
  confirmOutline: (projectId: string) => Promise<{
    success: boolean;
    projectConverted?: boolean;
  }>;
  
  // Actions - 审阅
  reviewOutline: (projectId: string) => Promise<void>;
  loadGlobalReview: (projectId: string) => Promise<void>;
  reviewChapter: (projectId: string, chapterId: string) => Promise<void>;
  reReview: (projectId: string, chapterId?: string) => Promise<void>;
  applySuggestion: (projectId: string, chapterId: string, suggestionId: string) => Promise<boolean>;
  ignoreIssue: (projectId: string, chapterId: string, issueId: string) => Promise<boolean>;
  
  // Actions - 小说
  loadChapters: (projectId: string) => Promise<void>;
  selectChapter: (chapterId: string) => void;
  saveChapter: (projectId: string, chapterId: string, content: string, autoReview?: boolean) => Promise<void>;
  generateNextChapter: (projectId: string) => Promise<void>;
  updateChapterContent: (content: string) => void;
  
  // Actions - 工作流
  setWorkflowState: (state: Partial<WorkflowState>) => void;
  resetWorkflow: () => void;
  
  setIsGenerating: (value: boolean) => void;
  setIsReviewing: (value: boolean) => void;
  setAutoSaveEnabled: (value: boolean) => void;
  setBatchStatus: (status: Partial<WorkshopState['batchStatus']>) => void;
  continueOutlineGeneration: (projectId: string) => Promise<void>;
  reset: () => void;
}

const initialState = {
  activeModule: 'outline' as WorkshopModule,
  workflow: {
    stage: 'idle' as WorkflowStage,
    currentAgent: null,
    progress: 0,
    message: '',
    isRunning: false,
  },
  outline: null,
  outlineNodes: [],
  selectedNodeId: null,
  globalReview: null,
  chapters: [],
  currentChapterId: null,
  currentChapterContent: '',
  chapterReviews: new Map(),
  isGenerating: false,
  isReviewing: false,
  isSaving: false,
  autoSaveEnabled: true,
  batchStatus: {
    currentBatch: 0,
    totalBatches: 0,
    needsNextBatch: false,
    isComplete: false,
  },
};

export const useWorkshopStore = create<WorkshopState>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // 模块切换
        setActiveModule: (module) => set({ activeModule: module }),

        // 大纲操作
        generateOutline: async (projectId, planId) => {
          set({ isGenerating: true, workflow: { ...get().workflow, isRunning: true, stage: 'skeleton_building' } });
          
          try {
            const response = await outlineService.generate({ projectId, planId });
            if (response.success && response.data) {
              set({ 
                outline: response.data,
                workflow: { ...get().workflow, stage: 'skeleton_building', progress: 100 }
              });
              // 自动加载审阅
              await get().loadGlobalReview(projectId);
            }
          } finally {
            set({ isGenerating: false, workflow: { ...get().workflow, isRunning: false } });
          }
        },

        loadOutline: async (projectId) => {
          const outline = await outlineService.get(projectId);
          if (outline) {
            set({ outline });
            const nodes = convertOutlineToNodes(outline);
            set({ outlineNodes: nodes });

            const metadata = outline.metadata || {};
            const totalBatches = metadata.total_batches || 1;
            const currentBatch = metadata.current_batch || totalBatches;
            const needsNextBatch = metadata.needs_next_batch === true;

            set({
              batchStatus: {
                currentBatch: currentBatch,
                totalBatches: totalBatches,
                needsNextBatch: needsNextBatch,
                isComplete: !needsNextBatch,
              }
            });
          }
        },

        updateOutlineNode: async (nodeId, updates) => {
          const projectId = get().outline?.projectId;
          if (!projectId) return;

          const success = await outlineService.updateNode(projectId, nodeId, { nodeId, ...updates });
          if (success) {
            const nodes = get().outlineNodes.map(node => 
              node.id === nodeId ? { ...node, ...updates } : node
            );
            set({ outlineNodes: nodes });
          }
        },

        selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

        confirmOutline: async (projectId) => {
          const response = await outlineService.confirm(projectId);
          if (response.success) {
            set({ workflow: { ...get().workflow, stage: 'novel_writing' } });
            return {
              success: true,
              projectConverted: response.projectConverted,
            };
          }
          return { success: false };
        },

        // 审阅操作
        reviewOutline: async (projectId) => {
          set({ isReviewing: true });
          try {
            await outlineService.review(projectId);
            await get().loadGlobalReview(projectId);
          } finally {
            set({ isReviewing: false });
          }
        },

        loadGlobalReview: async (projectId) => {
          const review = await reviewService.getGlobalReview(projectId);
          if (review) {
            set({ globalReview: review });
            // 更新节点的审阅状态
            const nodes = get().outlineNodes.map(node => {
              const chapterReview = review.chapterReviews[node.id];
              if (chapterReview) {
                return {
                  ...node,
                  metadata: {
                    ...node.metadata,
                    reviewScore: chapterReview.score,
                    reviewStatus: chapterReview.status,
                  }
                };
              }
              return node;
            });
            set({ outlineNodes: nodes });
          }
        },

        reviewChapter: async (projectId, chapterId) => {
          set({ isReviewing: true });
          try {
            const review = await reviewService.getChapterReview(projectId, chapterId);
            if (review) {
              const reviews = new Map(get().chapterReviews);
              reviews.set(chapterId, review);
              set({ chapterReviews: reviews });
            }
          } finally {
            set({ isReviewing: false });
          }
        },

        reReview: async (projectId, chapterId) => {
          set({ isReviewing: true });
          try {
            await reviewService.reReview(projectId, chapterId);
            if (chapterId) {
              await get().reviewChapter(projectId, chapterId);
            } else {
              await get().loadGlobalReview(projectId);
            }
          } finally {
            set({ isReviewing: false });
          }
        },

        applySuggestion: async (projectId, chapterId, suggestionId) => {
          return await reviewService.applySuggestion({ projectId, chapterId, suggestionId });
        },

        ignoreIssue: async (projectId, chapterId, issueId) => {
          return await reviewService.ignoreIssue(projectId, chapterId, issueId);
        },

        // 小说操作
        loadChapters: async (projectId) => {
          const response = await novelService.listChapters(projectId);
          if (response) {
            set({ chapters: response.chapters });
          }
        },

        selectChapter: (chapterId) => {
          const chapter = get().chapters.find(c => c.chapterId === chapterId);
          set({ 
            currentChapterId: chapterId,
            currentChapterContent: chapter?.content || ''
          });
        },

        saveChapter: async (projectId, chapterId, content, autoReview = true) => {
          set({ isSaving: true });
          try {
            const response = await novelService.saveChapter(projectId, chapterId, { 
              content, 
              autoReview 
            });
            if (response.success) {
              // 更新本地章节数据
              const chapters = get().chapters.map(c => 
                c.chapterId === chapterId 
                  ? { ...c, content, updatedAt: new Date().toISOString() }
                  : c
              );
              set({ chapters });

              // 如果有审阅结果，更新
              if (response.data?.review) {
                const reviews = new Map(get().chapterReviews);
                reviews.set(chapterId, response.data.review);
                set({ chapterReviews: reviews });
              }
            }
          } finally {
            set({ isSaving: false });
          }
        },

        generateNextChapter: async (projectId) => {
          set({ isGenerating: true });
          try {
            const response = await novelService.generateNextChapter({ 
              projectId, 
              previousChapterId: get().currentChapterId || undefined 
            });
            if (response.success && response.chapterId) {
              await get().loadChapters(projectId);
              get().selectChapter(response.chapterId);
            }
          } finally {
            set({ isGenerating: false });
          }
        },

        updateChapterContent: (content) => set({ currentChapterContent: content }),

        // 工作流操作
        setWorkflowState: (state) => set({ 
          workflow: { ...get().workflow, ...state } 
        }),

        resetWorkflow: () => set({ 
          workflow: initialState.workflow 
        }),

        // UI 操作
        setIsGenerating: (value) => set({ isGenerating: value }),
        setIsReviewing: (value) => set({ isReviewing: value }),
        setAutoSaveEnabled: (value) => set({ autoSaveEnabled: value }),
        setBatchStatus: (status) => set({
          batchStatus: { ...get().batchStatus, ...status }
        }),
        continueOutlineGeneration: async (projectId) => {
          set({ isGenerating: true });
          try {
            await outlineService.continueGeneration(projectId);
            await get().loadOutline(projectId);
          } finally {
            set({ isGenerating: false });
          }
        },
        reset: () => set(initialState),
      }),
      {
        name: 'workshop-storage',
        partialize: (state) => ({
          activeModule: state.activeModule,
          autoSaveEnabled: state.autoSaveEnabled,
        }),
      }
    ),
    { name: 'workshop-store' }
  )
);

// 辅助函数：将大纲数据转换为树形节点
function convertOutlineToNodes(outline: OutlineData): OutlineNode[] {
  const nodes: OutlineNode[] = [];

  const storySettings = outline.storySettings || outline.metadata?.story_settings;
  if (storySettings) {
    const settingsNode: OutlineNode = {
      id: 'story-settings',
      type: 'episode',
      title: '📚 故事设定',
      episodeNumber: 0,
      children: [],
      metadata: {
        reviewStatus: 'pending',
        isPaidWall: false,
        content: JSON.stringify(storySettings, null, 2),
      }
    };

    if (storySettings.metadata?.markdown) {
      const metaNode: OutlineNode = {
        id: 'settings-metadata',
        type: 'scene',
        title: '📋 项目信息',
        sceneNumber: 1,
        metadata: {
          reviewStatus: 'pending',
          content: storySettings.metadata.markdown,
        }
      };
      settingsNode.children?.push(metaNode);
    }

    if (storySettings.coreSetting?.markdown) {
      const coreNode: OutlineNode = {
        id: 'settings-core',
        type: 'scene',
        title: '🌍 核心设定',
        sceneNumber: 2,
        metadata: {
          reviewStatus: 'pending',
          content: storySettings.coreSetting.markdown,
        }
      };
      settingsNode.children?.push(coreNode);
    }

    if (storySettings.characters && storySettings.characters.length > 0) {
      const charsNode: OutlineNode = {
        id: 'settings-characters',
        type: 'scene',
        title: '👥 人物体系',
        sceneNumber: 3,
        children: [],
        metadata: {
          reviewStatus: 'pending',
        }
      };

      storySettings.characters.forEach((char, idx) => {
        charsNode.children?.push({
          id: `char-${idx}`,
          type: 'shot',
          title: char.name,
          shotNumber: idx + 1,
          metadata: {
            reviewStatus: 'pending',
            content: char.description,
          }
        });
      });

      settingsNode.children?.push(charsNode);
    }

    if (storySettings.plotArchitecture?.markdown) {
      const plotNode: OutlineNode = {
        id: 'settings-plot',
        type: 'scene',
        title: '📖 情节架构',
        sceneNumber: 4,
        metadata: {
          reviewStatus: 'pending',
          content: storySettings.plotArchitecture.markdown,
        }
      };
      settingsNode.children?.push(plotNode);
    }

    if (storySettings.adaptationMapping?.markdown) {
      const adaptNode: OutlineNode = {
        id: 'settings-adaptation',
        type: 'scene',
        title: '🎬 改编映射',
        sceneNumber: 5,
        metadata: {
          reviewStatus: 'pending',
          content: storySettings.adaptationMapping.markdown,
        }
      };
      settingsNode.children?.push(adaptNode);
    }

    if (storySettings.writingGuidelines?.markdown) {
      const guideNode: OutlineNode = {
        id: 'settings-guidelines',
        type: 'scene',
        title: '✍️ 创作指导',
        sceneNumber: 6,
        metadata: {
          reviewStatus: 'pending',
          content: storySettings.writingGuidelines.markdown,
        }
      };
      settingsNode.children?.push(guideNode);
    }

    if (storySettings.paywallDesign?.markdown) {
      const paywallNode: OutlineNode = {
        id: 'settings-paywall',
        type: 'scene',
        title: '💎 付费卡点',
        sceneNumber: 7,
        metadata: {
          reviewStatus: 'pending',
          content: storySettings.paywallDesign.markdown,
        }
      };
      settingsNode.children?.push(paywallNode);
    }

    nodes.push(settingsNode);
  }

  for (const episode of outline.episodes) {
    // 剧集节点
    const episodeNode: OutlineNode = {
      id: episode.episodeId,
      type: 'episode',
      title: episode.title || `第${episode.episodeNumber}集`,
      episodeNumber: episode.episodeNumber,
      children: [],
      metadata: {
        reviewStatus: episode.reviewStatus || 'pending',
        reviewScore: episode.reviewScore,
        isPaidWall: episode.isPaidWall,
      }
    };

    // 场景节点
    if (episode.scenes) {
      for (const scene of episode.scenes) {
        const sceneNode: OutlineNode = {
          id: scene.sceneId,
          type: 'scene',
          title: scene.title || `场景${scene.sceneNumber}`,
          sceneNumber: scene.sceneNumber,
          children: [],
          metadata: {
            reviewStatus: 'pending',
          }
        };

        // 镜头节点
        if (scene.shots) {
          for (const shot of scene.shots) {
            sceneNode.children?.push({
              id: shot.shotId,
              type: 'shot',
              title: `镜头${shot.shotNumber}`,
              shotNumber: shot.shotNumber,
              metadata: {
                reviewStatus: 'pending',
              }
            });
          }
        }

        episodeNode.children?.push(sceneNode);
      }
    }

    nodes.push(episodeNode);
  }

  return nodes;
}
