import { projectsService } from './projects';
import { episodesService } from './episodes';
import { scenesService } from './scenes';
import type { components } from '@/types/api';


type EpisodeCreate = components['schemas']['EpisodeCreate'];
type SceneCreate = components['schemas']['SceneCreate'];
type ProjectResponse = components['schemas']['ProjectResponse'];
type EpisodeResponse = components['schemas']['EpisodeResponse'];
type SceneResponse = components['schemas']['SceneResponse'];

interface CreateProjectResult {
  project: ProjectResponse;
  episode: EpisodeResponse;
  scene?: SceneResponse;
}

/**
 * 项目自动创建服务
 * 用于首页快速进入剧本工坊的场景
 */
export const projectAutoCreate = {
  /**
   * 创建临时项目并初始化第一集
   * 用于首页快速进入剧本工坊
   * 
   * @param content 可选的初始内容（AI生成的小说/剧本）
   * @returns 创建的项目和剧集
   */
  async createTemporaryProject(content?: {
    novelContent?: string;
    scriptText?: string;
  }): Promise<CreateProjectResult> {

    // 1. 调用后端接口创建真正的临时项目
    const projectRes = await projectsService.createTempProject();
    const project = projectRes.data as ProjectResponse;

    // 2. 创建第一集
    const episodeData: EpisodeCreate = {
      title: '第一集',
      summary: content?.scriptText ? content.scriptText.substring(0, 100) + '...' : '',
    };

    const episodeRes = await episodesService.createEpisode(project.id, episodeData);
    const episode = episodeRes.data as EpisodeResponse;

    // 3. 如果有内容，更新剧集内容并创建默认场景
    let scene: SceneResponse | undefined;

    if (content?.scriptText || content?.novelContent) {
      // 更新剧集内容
      await episodesService.updateEpisode(project.id, episode.episodeId, {
        scriptText: content.scriptText || content.novelContent,
      });

      // 创建默认场景
      const sceneData: SceneCreate = {
        location: '场景1',
        description: '默认场景',
        createMasterNode: true,
        masterPositionX: 100,
        masterPositionY: 100,
      };

      const sceneRes = await scenesService.createScene(episode.episodeId, sceneData);
      scene = sceneRes.data as SceneResponse;
    }

    return { project, episode, scene };
  },

  /**
   * 转正临时项目
   * 用户确认小说名后调用，立即更新项目名称
   * 
   * @param projectId 项目ID
   * @param confirmedName 用户确认的小说名
   */
  async convertToFormalProject(
    projectId: string,
    confirmedName: string
  ): Promise<void> {
    // 调用后端的 save 接口进行转正
    await projectsService.saveTempProject(projectId, {
      name: confirmedName,
    });
  },

  /**
   * 检查并恢复最近的临时项目
   * 用于用户刷新页面或重新进入时恢复状态
   * 
   * @returns 最近的临时项目，如果没有则返回 null
   */
  async recoverTemporaryProject(): Promise<CreateProjectResult | null> {
    try {
      // 获取最近的项目列表
      const projectsRes = await projectsService.listProjects(1, 10);
      const projects = (projectsRes.data || []) as any[];

      // 查找临时项目 (is_active=false 为后端临时项目标记)
      // 注意：这里需要确保后端 listProjects 能够返回 is_active 字段
      const tempProject = projects.find(p => p.is_active === false);

      if (!tempProject) return null;

      // 获取该项目的剧集
      const episodesRes = await episodesService.listEpisodes(tempProject.id);
      const episodes = episodesRes.data || [];

      if (episodes.length === 0) return null;

      return {
        project: tempProject as ProjectResponse,
        episode: episodes[0] as EpisodeResponse,
      };
    } catch (error) {
      console.error('恢复临时项目失败:', error);
      return null;
    }
  },

  /**
   * 创建空项目
   * 用于用户选择"手动编写"时的场景
   * 
   * @param projectName 项目名称
   * @returns 创建的项目和剧集
   */
  async createEmptyProject(projectName: string): Promise<CreateProjectResult> {
    // 1. 创建项目
    const projectRes = await projectsService.createProject({
      name: projectName,
    });
    const project = projectRes.data as ProjectResponse;

    // 2. 创建第一集
    const episodeRes = await episodesService.createEpisode(project.id, {
      title: '第一集',
      summary: '',
    });
    const episode = episodeRes.data as EpisodeResponse;

    // 3. 创建空白场景
    const sceneRes = await scenesService.createScene(episode.episodeId, {
      location: '场景1',
      description: '',
      createMasterNode: true,
      masterPositionX: 100,
      masterPositionY: 100,
    });
    const scene = sceneRes.data as SceneResponse;

    return { project, episode, scene };
  },

  /**
   * 检查项目是否有内容
   * 用于判断是否可以进入剧本工坊
   * 
   * @param projectId 项目ID
   * @param episodeId 剧集ID
   * @returns 是否有内容
   */
  async hasContent(
    projectId: string,
    episodeId: string
  ): Promise<boolean> {
    try {
      const episodeRes = await episodesService.getEpisode(projectId, episodeId);
      const episode = episodeRes.data as EpisodeResponse;

      return !!(
        episode.scriptText &&
        episode.scriptText.length > 0
      );
    } catch (error) {
      return false;
    }
  },
};
