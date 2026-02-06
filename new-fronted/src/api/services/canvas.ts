import { client } from '../client';
import type { CanvasData, CanvasSaveRequest, CanvasViewport, ShotNode } from '@/types';

// Helper to map Shot from API to Frontend
const mapShotFromApi = (s: any): ShotNode => ({
  shotId: s.shot_id,
  episodeId: s.episode_id,
  sceneId: s.scene_id,
  nodeType: s.node_type as any,
  shotNumber: s.shot_number,
  title: s.title,
  subtitle: s.subtitle,
  thumbnailUrl: s.thumbnail_url,
  imageUrl: s.image_url,
  status: s.status as any,
  position: { x: s.position_x, y: s.position_y },
  details: s.details,
});

export const canvasService = {
  async getCanvas(episodeId: string): Promise<CanvasData> {
    const { data, error } = await client.GET('/api/episodes/{episode_id}/canvas', {
      params: { path: { episode_id: episodeId }, query: {} as any },
    });

    if (error) throw new Error((error as any).message || 'Failed to get canvas');
    const c = (data as any).data;

    return {
      episodeId: c.episode_id,
      viewport: c.viewport || { x: 0, y: 0, zoom: 1 },
      nodes: (c.nodes || []).map(mapShotFromApi),
      connections: c.connections || [],
    };
  },

  async saveCanvas(episodeId: string, data: CanvasSaveRequest): Promise<CanvasData> {
    const { data: resData, error } = await client.PUT('/api/episodes/{episode_id}/canvas', {
      params: { path: { episode_id: episodeId }, query: {} as any },
      body: {
        viewport: data.viewport,
        connections: data.connections,
        nodes: data.nodes.map(n => ({
          shot_id: n.shotId,
          episode_id: n.episodeId,
          scene_id: n.sceneId,
          node_type: n.nodeType,
          shot_number: n.shotNumber,
          title: n.title,
          subtitle: n.subtitle,
          status: n.status,
          position_x: n.position.x,
          position_y: n.position.y,
          details: n.details,
        })),
      } as any,
    });

    if (error) throw new Error((error as any).message || 'Failed to save canvas');
    const c = (resData as any).data;

    return {
      episodeId: c.episode_id,
      viewport: c.viewport,
      nodes: (c.nodes || []).map(mapShotFromApi),
      connections: c.connections || [],
    };
  },

  async updateViewport(episodeId: string, viewport: CanvasViewport): Promise<CanvasViewport> {
    const { data, error } = await client.PATCH('/api/episodes/{episode_id}/canvas/viewport', {
      params: { path: { episode_id: episodeId }, query: {} as any },
      body: viewport,
    });

    if (error) throw new Error((error as any).message || 'Failed to update viewport');
    return (data as any).data;
  }
};
