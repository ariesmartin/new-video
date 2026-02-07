/**
 * Database TypeScript Types
 * Generated from schema.sql
 * For Supabase TypeScript client
 */

// ============================================
// Enums
// ============================================

export type ThemeStatus = 'active' | 'draft' | 'archived';
export type ElementType = 'character' | 'setting' | 'conflict' | 'trope' | 'mood' | 'twist';
export type ProjectStatus = 'planning' | 'writing' | 'editing' | 'completed' | 'archived';
export type ContentType = 
  | 'logline' 
  | 'beat_sheet' 
  | 'synopsis' 
  | 'outline' 
  | 'episode_skeleton' 
  | 'episode_script' 
  | 'scene_description';
export type ContentStatus = 'draft' | 'review' | 'approved' | 'rejected';

// ============================================
// JSONB Types
// ============================================

export interface TargetAudience {
  age_range?: string;
  gender?: 'male' | 'female' | 'all';
  interests?: string[];
  viewing_habits?: string;
}

export interface Tone {
  overall?: string;
  emotional_arc?: string;
  pacing?: 'slow' | 'moderate' | 'fast';
}

export interface ThemeConfig {
  role?: string;
  traits?: string[];
  archetype?: string;
  relationship_dynamics?: string[];
  frequency?: string;
  variation?: string;
  [key: string]: any;
}

export interface ViewingHistory {
  total_watch_time?: number;
  favorite_genres?: string[];
  average_completion_rate?: number;
}

export interface GenerationPreferences {
  default_tone?: string;
  preferred_episode_length?: number;
  auto_optimize?: boolean;
}

export interface ProjectSettings {
  target_episodes?: number;
  target_duration?: number;
  language?: string;
  style_guide?: string;
}

export interface ContentMetadata {
  word_count?: number;
  reading_time?: number;
  key_points?: string[];
  [key: string]: any;
}

export interface GenerationParams {
  model?: string;
  temperature?: number;
  max_tokens?: number;
  [key: string]: any;
}

// ============================================
// Database Tables
// ============================================

export interface Theme {
  id: string;
  name: string;
  name_en: string | null;
  slug: string;
  category: string;
  subcategories: string[] | null;
  tags: string[] | null;
  target_audience: TargetAudience | null;
  description: string | null;
  summary: string | null;
  key_themes: string[] | null;
  emotional_beats: string[] | null;
  tone: Tone | null;
  popularity_score: number;
  usage_count: number;
  success_rate: number;
  example_loglines: string[] | null;
  example_titles: string[] | null;
  status: ThemeStatus;
  is_featured: boolean;
  is_premium: boolean;
  created_at: string;
  updated_at: string;
  search_vector: unknown | null; // tsvector
  
  // Joined fields
  elements?: ThemeElement[];
}

export interface ThemeElement {
  id: string;
  theme_id: string;
  element_type: ElementType;
  name: string;
  description: string | null;
  config: ThemeConfig | null;
  weight: number;
  frequency: number;
  is_required: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ThemeTrend {
  id: string;
  theme_id: string;
  date: string;
  view_count: number;
  engagement_score: number;
  completion_rate: number;
  share_count: number;
  daily_rank: number | null;
  category_rank: number | null;
  created_at: string;
}

export interface UserPreferences {
  id: string;
  user_id: string;
  preferred_categories: string[] | null;
  preferred_themes: string[] | null;
  disliked_themes: string[] | null;
  viewing_history: ViewingHistory | null;
  generation_preferences: GenerationPreferences | null;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  user_id: string;
  title: string | null;
  description: string | null;
  status: ProjectStatus;
  theme_id: string | null;
  theme_config: Record<string, any> | null;
  settings: ProjectSettings | null;
  episode_count: number;
  total_word_count: number;
  completion_percentage: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  
  // Joined fields
  theme?: Theme | null;
}

export interface ProjectContent {
  id: string;
  project_id: string;
  content_type: ContentType;
  episode_number: number | null;
  scene_number: number | null;
  title: string | null;
  content: string;
  metadata: ContentMetadata | null;
  version: number;
  parent_version: string | null;
  ai_model: string | null;
  generation_params: GenerationParams | null;
  status: ContentStatus;
  created_at: string;
  updated_at: string;
}

// ============================================
// Views
// ============================================

export interface PopularTheme extends Theme {
  element_count: number;
}

export interface ThemeDetail extends Theme {
  elements: Array<{
    id: string;
    type: ElementType;
    name: string;
    description: string | null;
    config: ThemeConfig | null;
    weight: number;
    is_required: boolean;
  }>;
}

// ============================================
// Insert Types (omitting auto-generated fields)
// ============================================

export type ThemeInsert = Omit<Theme, 'id' | 'created_at' | 'updated_at' | 'search_vector' | 'elements'>;
export type ThemeElementInsert = Omit<ThemeElement, 'id' | 'created_at' | 'updated_at'>;
export type ThemeTrendInsert = Omit<ThemeTrend, 'id' | 'created_at'>;
export type UserPreferencesInsert = Omit<UserPreferences, 'id' | 'created_at' | 'updated_at'>;
export type ProjectInsert = Omit<Project, 'id' | 'created_at' | 'updated_at' | 'completed_at' | 'theme'>;
export type ProjectContentInsert = Omit<ProjectContent, 'id' | 'created_at' | 'updated_at'>;

// ============================================
// Update Types (partial)
// ============================================

export type ThemeUpdate = Partial<Omit<Theme, 'id' | 'created_at' | 'updated_at' | 'search_vector'>>;
export type ThemeElementUpdate = Partial<Omit<ThemeElement, 'id' | 'created_at' | 'updated_at'>>;
export type UserPreferencesUpdate = Partial<Omit<UserPreferences, 'id' | 'created_at' | 'updated_at'>>;
export type ProjectUpdate = Partial<Omit<Project, 'id' | 'created_at' | 'updated_at' | 'completed_at'>>;
export type ProjectContentUpdate = Partial<Omit<ProjectContent, 'id' | 'created_at' | 'updated_at'>>;

// ============================================
// Database Response Types
// ============================================

export interface DbResponse<T> {
  data: T | null;
  error: Error | null;
}

export interface DbListResponse<T> {
  data: T[];
  error: Error | null;
  count: number | null;
}
