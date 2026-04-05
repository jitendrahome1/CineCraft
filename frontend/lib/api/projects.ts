/**
 * Projects API service.
 */
import { apiClient } from './client';
import type {
  Project,
  CreateProjectRequest,
  PaginatedResponse,
  Scene,
  Character,
} from '../types/api';

const PROJECTS_PREFIX = '/api/v1/projects';

export const projectsApi = {
  /**
   * Get all projects for current user.
   */
  async list(skip: number = 0, limit: number = 20): Promise<PaginatedResponse<Project>> {
    return apiClient.get<PaginatedResponse<Project>>(
      `${PROJECTS_PREFIX}?skip=${skip}&limit=${limit}`
    );
  },

  /**
   * Get project by ID.
   */
  async get(id: number): Promise<Project> {
    return apiClient.get<Project>(`${PROJECTS_PREFIX}/${id}`);
  },

  /**
   * Create new project.
   */
  async create(data: CreateProjectRequest): Promise<Project> {
    return apiClient.post<Project>(PROJECTS_PREFIX, data);
  },

  /**
   * Update project.
   */
  async update(id: number, data: Partial<Project>): Promise<Project> {
    return apiClient.put<Project>(`${PROJECTS_PREFIX}/${id}`, data);
  },

  /**
   * Delete project.
   */
  async delete(id: number): Promise<void> {
    return apiClient.delete(`${PROJECTS_PREFIX}/${id}`);
  },

  /**
   * Get project scenes.
   */
  async getScenes(projectId: number): Promise<Scene[]> {
    const response = await apiClient.get<{scenes: Scene[], total: number}>(`${PROJECTS_PREFIX}/${projectId}/scenes`);
    return response.scenes;
  },

  /**
   * Get project characters.
   */
  async getCharacters(projectId: number): Promise<Character[]> {
    return apiClient.get<Character[]>(`${PROJECTS_PREFIX}/${projectId}/characters`);
  },
};
