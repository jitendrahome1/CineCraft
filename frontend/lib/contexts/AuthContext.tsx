/**
 * Authentication context for managing user state.
 */
'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../api';
import type { User, LoginRequest, RegisterRequest } from '../types/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch current user on mount
  useEffect(() => {
    const fetchUser = async () => {
      if (authApi.isAuthenticated()) {
        try {
          const currentUser = await authApi.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error('Failed to fetch user:', error);
          authApi.logout();
        }
      }
      setIsLoading(false);
    };

    fetchUser();
  }, []);

  const login = async (credentials: LoginRequest) => {
    await authApi.login(credentials);
    // Fetch user profile after login since login endpoint returns only tokens
    const currentUser = await authApi.getCurrentUser();
    setUser(currentUser);
  };

  const register = async (data: RegisterRequest) => {
    await authApi.register(data);
    // Fetch user profile after registration
    const currentUser = await authApi.getCurrentUser();
    setUser(currentUser);
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
  };

  const refetchUser = async () => {
    if (authApi.isAuthenticated()) {
      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error('Failed to refetch user:', error);
        logout();
      }
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refetchUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
