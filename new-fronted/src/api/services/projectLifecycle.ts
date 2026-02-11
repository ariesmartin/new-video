import { projectsService } from './projects';
import { useAppStore, useUIStore } from '@/hooks/useStore';
import type { components } from '@/types/api';

type ProjectResponse = components['schemas']['ProjectResponse'];

interface AutoConvertResult {
  success: boolean;
  reason: 'FULL_CONVERT' | 'CONVERT_ONLY' | 'ALREADY_FORMAL' | 'ERROR';
  message: string;
}

/**
 * 项目生命周期管理服务
 * 
 * 核心职责：
 * 1. 统一管理项目转正流程
 * 2. 智能项目名称生成
 * 3. 防止重复转正验证
 * 4. 尊重用户手动命名
 */
export const projectLifecycle = {
  /**
   * 智能转正项目 - 带完整验证
   * 
   * 验证层级：
   * 1. 检查项目是否已转正
   * 2. 检查用户是否已手动命名
   * 3. 生成/保留项目名称
   * 4. 执行转正
   */
  async autoConvertToFormal(params: {
    projectId: string;
    source: 'theme_selected' | 'outline_generated' | 'script_saved';
    suggestedName?: string;
    content?: string;
  }): Promise<AutoConvertResult> {
    const { projectId, suggestedName, content } = params;
    
    try {
      // ========== 验证层1: 获取项目最新状态 ==========
      const projectRes = await projectsService.getProject(projectId);
      const project = projectRes.data as ProjectResponse;
      
      if (!project) {
        console.error(`[ProjectLifecycle] 项目不存在: ${projectId}`);
        return { 
          success: false, 
          reason: 'ERROR', 
          message: '项目不存在' 
        };
      }
      
      // ========== 验证层2: 检查是否已转正 ==========
      // 后端返回 camelCase: isTemporary
      const isTemporary = project.isTemporary ?? false;
      if (!isTemporary) {
        console.log(`[ProjectLifecycle] 项目已是正式项目，跳过转正`);
        return { 
          success: true, 
          reason: 'ALREADY_FORMAL', 
          message: '项目已是正式状态' 
        };
      }
      
      // ========== 验证层3: 检查用户是否已手动命名 ==========
      const defaultNames = ['未命名项目', '临时项目', '新项目', '新创作'];
      const currentName = project.name || '';
      const isDefaultName = defaultNames.some(
        defaultName => currentName.includes(defaultName) || currentName.trim() === ''
      );
      
      if (!isDefaultName) {
        // 用户已手动修改名称，尊重用户选择，只转正不调名
        console.log(`[ProjectLifecycle] 用户已手动命名"${currentName}"，只转正不调名`);
        await this.convertOnly(projectId);
        return { 
          success: true, 
          reason: 'CONVERT_ONLY', 
          message: `项目已保存为《${currentName}》` 
        };
      }
      
      // ========== 验证层4: 生成合适的名称 ==========
      const finalName = await this.generateProjectName({
        suggestedName,
        content,
        projectId,
        currentName
      });
      
      // ========== 执行转正 ==========
      await projectsService.saveTempProject(projectId, { name: finalName });
      
      // 更新本地状态 - 使用 setCurrentProject
      const { currentProject, setCurrentProject } = useAppStore.getState();
      if (setCurrentProject && currentProject) {
        setCurrentProject({ 
          ...currentProject,
          name: finalName,
          isTemporary: false 
        });
      }
      
      // 通知用户
      const { addToast } = useUIStore.getState();
      if (addToast) {
        addToast({ type: 'success', message: `项目已命名为《${finalName}》` });
      }
      
      console.log(`[ProjectLifecycle] 项目转正成功: ${finalName}`);
      return { 
        success: true, 
        reason: 'FULL_CONVERT', 
        message: `项目已命名为《${finalName}》` 
      };
      
    } catch (error) {
      console.error('[ProjectLifecycle] 转正失败:', error);
      return { 
        success: false, 
        reason: 'ERROR', 
        message: '项目转正失败，请重试' 
      };
    }
  },

  /**
   * 仅转正（不调名称）
   */
  async convertOnly(projectId: string): Promise<void> {
    try {
      await projectsService.saveTempProject(projectId, {});
      
      const { currentProject, setCurrentProject } = useAppStore.getState();
      if (setCurrentProject && currentProject) {
        setCurrentProject({ ...currentProject, isTemporary: false });
      }
      
      const { addToast } = useUIStore.getState();
      if (addToast) {
        addToast({ type: 'success', message: '项目已保存' });
      }
    } catch (error) {
      console.error('[ProjectLifecycle] 仅转正失败:', error);
      throw error;
    }
  },

  /**
   * 生成项目名称 - 智能优先级
   * 
   * 优先级：
   * 1. 建议名称（选题方案标题）
   * 2. 从内容提取
   * 3. 使用时间戳生成唯一名称
   */
  async generateProjectName(params: {
    suggestedName?: string;
    content?: string;
    projectId: string;
    currentName: string;
  }): Promise<string> {
    const { suggestedName, content } = params;
    
    // 优先级1: 建议名称
    if (suggestedName?.trim()) {
      return this.sanitizeName(suggestedName.trim());
    }
    
    // 优先级2: 从内容提取
    if (content) {
      const extracted = this.extractTitleFromContent(content);
      if (extracted) return extracted;
    }
    
    // 优先级3: 使用时间戳生成唯一名称
    const timestamp = new Date().toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric'
    });
    return `${timestamp}的创作`;
  },

  /**
   * 清理名称（去除非法字符）
   */
  sanitizeName(name: string): string {
    return name
      .replace(/[<>:"\\/|?*]/g, '')  // 去除文件系统非法字符
      .replace(/\s+/g, ' ')           // 合并多个空格
      .trim()
      .substring(0, 50);              // 限制长度
  },

  /**
   * 从内容中提取标题
   * 
   * 支持的格式：
   * - 剧名：《XXX》
   * - 标题：XXX
   * - 《XXX》
   */
  extractTitleFromContent(content: string): string | null {
    if (!content) return null;
    
    const lines = content.split('\n').slice(0, 20); // 只检查前20行
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      // 匹配"剧名：《XXX》"或"标题：XXX"或"名称：XXX"
      const titleMatch = trimmed.match(/^(?:剧名|标题|名称)[：:]\s*《?([^》]+)》?/);
      if (titleMatch && titleMatch[1].trim().length >= 2) {
        return this.sanitizeName(titleMatch[1].trim());
      }
      
      // 匹配书名号《XXX》（2-20个字符）
      const bookMatch = trimmed.match(/《([^》]{2,20})》/);
      if (bookMatch) {
        return this.sanitizeName(bookMatch[1].trim());
      }
    }
    
    return null;
  },

  /**
   * 检查项目是否需要转正
   */
  async checkNeedsConversion(projectId: string): Promise<{
    needsConversion: boolean;
    isTemporary: boolean;
    currentName: string;
  }> {
    try {
      const projectRes = await projectsService.getProject(projectId);
      const project = projectRes.data as ProjectResponse;
      
      // 后端返回 camelCase: isTemporary
      const isTemporary = project.isTemporary ?? false;
      const currentName = project.name || '';
      
      return {
        needsConversion: isTemporary,
        isTemporary,
        currentName
      };
    } catch (error) {
      console.error('[ProjectLifecycle] 检查转正状态失败:', error);
      return {
        needsConversion: false,
        isTemporary: false,
        currentName: ''
      };
    }
  }
};

export type { AutoConvertResult };
