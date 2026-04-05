/**
 * Authentication API service.
 */
import { apiClient } from './client';
import type { AuthResponse, LoginRequest, RegisterRequest, User } from '../types/api';

const AUTH_PREFIX = '/api/v1/auth';

export const authApi = {
  /**
   * Login user.
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      `${AUTH_PREFIX}/login`,
      credentials
    );

    // Store token
    apiClient.setToken(response.access_token);

    return response;
  },

  /**
   * Register new user.
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      `${AUTH_PREFIX}/register`,
      data
    );

    // Store token
    apiClient.setToken(response.access_token);

    return response;
  },

  /**
   * Logout user.
   */
  logout(): void {
    apiClient.clearToken();
  },

  /**
   * Get current user.
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me');
  },

  /**
   * Check if user is authenticated.
   */
  isAuthenticated(): boolean {
    return apiClient.isAuthenticated();
  },
};
