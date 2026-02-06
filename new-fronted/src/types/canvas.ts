export interface CanvasViewport {
  x: number;
  y: number;
  zoom: number;
}

export interface CanvasState {
  zoom: number;
  offset: { x: number; y: number };
  gridVisible: boolean;
}

export interface Connection {
  id: string;
  source: string;
  target: string;
  type: string;
}
