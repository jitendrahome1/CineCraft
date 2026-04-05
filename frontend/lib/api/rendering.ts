/**
 * Rendering API service.
 */
import { apiClient } from './client';
import type { RenderJob, RenderRequest, RenderConfig } from '../types/api';

const RENDERING_PREFIX = '/api/v1/rendering';

export const renderingApi = {
  /**
   * Start video render for project.
   */
  async startRender(request: RenderRequest): Promise<RenderJob> {
    return apiClient.post<RenderJob>(`${RENDERING_PREFIX}/render`, request);
  },

  /**
   * Get render job status.
   */
  async getJobStatus(jobId: number): Promise<RenderJob> {
    const data = await apiClient.get<RenderJob>(`${RENDERING_PREFIX}/status/${jobId}`);
    // Backend returns current_stage, frontend expects stage
    if (data.current_stage && !data.stage) {
      data.stage = data.current_stage;
    }
    // Backend status response returns job_id, map to id if needed
    if (data.job_id && !data.id) {
      data.id = data.job_id;
    }
    return data;
  },

  /**
   * Get render job result.
   */
  async getJobResult(jobId: number): Promise<RenderJob> {
    return apiClient.get<RenderJob>(`${RENDERING_PREFIX}/result/${jobId}`);
  },

  /**
   * Cancel render job.
   */
  async cancelJob(jobId: number): Promise<void> {
    return apiClient.delete(`${RENDERING_PREFIX}/${jobId}`);
  },

  /**
   * Get available render presets.
   */
  async getPresets(): Promise<Record<string, RenderConfig>> {
    return apiClient.get<Record<string, RenderConfig>>(`${RENDERING_PREFIX}/presets`);
  },

  /**
   * Get default render config.
   */
  async getDefaultConfig(): Promise<RenderConfig> {
    return apiClient.get<RenderConfig>(`${RENDERING_PREFIX}/config/default`);
  },
};
