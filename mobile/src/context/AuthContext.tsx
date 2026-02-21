import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import { api, clearTokens, getStoredAccessToken, setTokens } from '../api/client';
import type { User } from '../types/api';

type AuthState = {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
};

type AuthContextValue = AuthState & {
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

export interface RegisterData {
  full_name: string;
  email: string;
  phone_number: string;
  password: string;
  confirm_password: string;
  fcm_token?: string | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const refreshUser = useCallback(async () => {
    const token = await getStoredAccessToken();
    if (!token) {
      setState((s) => ({ ...s, user: null, isAuthenticated: false, isLoading: false }));
      return;
    }
    try {
      const { data } = await api.get<User>('/users/me');
      setState((s) => ({ ...s, user: data, isAuthenticated: true, isLoading: false }));
    } catch {
      setState((s) => ({ ...s, user: null, isAuthenticated: false, isLoading: false }));
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const token = await SecureStore.getItemAsync('linkup_access_token');
      if (!token || !mounted) {
        if (mounted) setState((s) => ({ ...s, isLoading: false }));
        return;
      }
      try {
        const { data } = await api.get<User>('/users/me');
        if (mounted) setState({ user: data, isAuthenticated: true, isLoading: false });
      } catch {
        await clearTokens();
        if (mounted) setState({ user: null, isAuthenticated: false, isLoading: false });
      }
    })();
    return () => { mounted = false; };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post<{ access_token: string; refresh_token: string; user: User }>(
      '/auth/login',
      { email, password }
    );
    await setTokens(data.access_token, data.refresh_token);
    setState({ user: data.user, isAuthenticated: true, isLoading: false });
  }, []);

  const register = useCallback(async (payload: RegisterData) => {
    await api.post('/auth/register', payload);
    await login(payload.email, payload.password);
  }, [login]);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // ignore
    }
    await clearTokens();
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, []);

  const value: AuthContextValue = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
