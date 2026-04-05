/**
 * AI Generation API service.
 */
import { apiClient } from './client';
import type { StoryGenerationRequest, StoryGenerationResponse } from '../types/api';

const AI_PREFIX = '/api/v1/ai';

export const aiApi = {
  /**
   * Generate story from title.
   */
  async generateStory(request: StoryGenerationRequest): Promise<StoryGenerationResponse> {
    return apiClient.post<StoryGenerationResponse>(
      `${AI_PREFIX}/generate-story`,
      request
    );
  },

  /**
   * Generate scenes for existing story.
   */
  async generateScenes(projectId: number, story: string): Promise<StoryGenerationResponse> {
    return apiClient.post<StoryGenerationResponse>(
      `${AI_PREFIX}/generate-scenes`,
      { project_id: projectId, story }
    );
  },

  /**
   * Generate image for scene.
   */
  async generateImage(sceneId: number): Promise<{ image_url: string }> {
    return apiClient.post<{ image_url: string }>(
      `${AI_PREFIX}/generate-image`,
      { scene_id: sceneId }
    );
  },

  /**
   * Generate voice narration for scene.
   */
  async generateVoice(sceneId: number): Promise<{ voice_url: string }> {
    return apiClient.post<{ voice_url: string }>(
      `${AI_PREFIX}/generate-voice`,
      { scene_id: sceneId }
    );
  },

  /**
   * Generate background music for project.
   */
  async generateMusic(projectId: number, mood?: string): Promise<{ music_url: string }> {
    return apiClient.post<{ music_url: string }>(
      `${AI_PREFIX}/generate-music`,
      { project_id: projectId, mood }
    );
  },
};
