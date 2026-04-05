/**
 * TypeScript types for CineCraft API.
 * Corresponds to backend Pydantic schemas.
 */

// User types
export interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Subscription types
export interface Plan {
  id: number;
  name: string;
  description?: string;
  price_cents: number;
  stripe_price_id: string;
  features: Record<string, any>;
  limits: Record<string, number>;
  is_active: boolean;
}

export interface Subscription {
  id: number;
  user_id: number;
  plan_id: number;
  stripe_subscription_id?: string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  plan: Plan;
}

// Project types
export interface Project {
  id: number;
  title: string;
  description?: string;
  user_id: number;
  status: 'draft' | 'generating' | 'ready' | 'rendering' | 'completed' | 'failed';
  story?: string;
  metadata?: Record<string, any>;
  language?: string;
  video_length?: string;
  video_url?: string;
  thumbnail_url?: string;
  video_duration?: number;
  created_at: string;
  updated_at: string;
  scenes?: Scene[];
}

export interface CreateProjectRequest {
  title: string;
  description?: string;
  language?: string;
  video_length?: string;
}

// Scene types
export interface Scene {
  id: number;
  project_id: number;
  sequence_number: number;  // Backend uses sequence_number, not scene_number
  title?: string;
  narration?: string;
  visual_description?: string;
  video_prompt?: string;
  emotion?: string;
  duration_seconds: number;
  image_url?: string;
  voice_url?: string;
  audio_url?: string;  // Backend also returns audio_url
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Character types
export interface Character {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  role?: string;
  metadata?: Record<string, any>;
}

// Media Asset types
export interface MediaAsset {
  id: number;
  project_id: number;
  scene_id?: number;
  asset_type: 'image' | 'voice' | 'music' | 'video';
  file_path: string;
  file_url: string;
  file_size_bytes: number;
  duration_seconds?: number;
  metadata?: Record<string, any>;
  created_at: string;
}

// Render Job types
export interface RenderJob {
  id: number;
  job_id?: number;
  project_id: number;
  user_id: number;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  stage?: string;
  current_stage?: string;
  output_url?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface RenderRequest {
  project_id: number;
  width?: number;
  height?: number;
  fps?: number;
  enable_ken_burns?: boolean;
  music_volume?: number;
  enable_ducking?: boolean;
  enable_subtitles?: boolean;
}

export interface RenderConfig {
  resolution?: '1080p' | '720p' | '480p';
  fps?: number;
  format?: 'mp4' | 'webm';
  quality?: 'high' | 'medium' | 'low';
  enable_ken_burns?: boolean;
  enable_transitions?: boolean;
  enable_audio_ducking?: boolean;
}

// AI Generation types
export interface StoryGenerationRequest {
  title: string;
  description?: string;
  genre?: string;
  tone?: string;
}

export interface StoryGenerationResponse {
  story: string;
  scenes: Scene[];
  characters: Character[];
}

// Analytics types
export interface UserStats {
  user_id: number;
  event_counts: Record<string, number>;
  total_events: number;
  api_calls: number;
  total_cost_cents: number;
  avg_response_time_ms: number;
}

export interface SystemStats {
  event_counts: Record<string, number>;
  total_events: number;
  unique_users: number;
  api_calls: number;
  error_rate: number;
  avg_response_time_ms: number;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'progress' | 'completion' | 'error' | 'status';
  job_id: number;
  data?: any;
}

export interface ProgressMessage extends WebSocketMessage {
  type: 'progress';
  data: {
    progress: number;
    stage: string;
    status: string;
  };
}

export interface CompletionMessage extends WebSocketMessage {
  type: 'completion';
  data: {
    output_url: string;
    duration_seconds: number;
    file_size_bytes: number;
  };
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  data: {
    error: string;
    message: string;
  };
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// API Error
export interface ApiError {
  error: string;
  message: string;
  details?: any;
}
