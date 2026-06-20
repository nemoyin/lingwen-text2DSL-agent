/** AuthContext — manages user authentication state across the app. */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import * as authService from '../services/authService';
import { getToken, clearToken } from '../services/api';

interface AuthState {
  user: { user_id: number; username: string } | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  /** Login with optional "Remember Me" persistence flag. */
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_KEY = 'lingwen_token';

function parseJwt(token: string): { user_id: number; username: string } | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join(''),
    );
    const payload = JSON.parse(jsonPayload);
    if (payload.sub && payload.username) {
      return { user_id: parseInt(payload.sub, 10), username: payload.username };
    }
    return null;
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  // Initialize from either sessionStorage or localStorage (via getToken)
  const [token, setToken] = useState<string | null>(() => getToken());
  const [user, setUser] = useState<{
    user_id: number;
    username: string;
  } | null>(() => {
    const stored = getToken();
    return stored ? parseJwt(stored) : null;
  });
  const [loading, setLoading] = useState<boolean>(false);

  // Track the "Remember Me" preference so we know where to persist
  const rememberMeRef = useRef<boolean>(false);

  useEffect(() => {
    if (token) {
      if (rememberMeRef.current) {
        localStorage.setItem(TOKEN_KEY, token);
        sessionStorage.removeItem(TOKEN_KEY);
      } else {
        sessionStorage.setItem(TOKEN_KEY, token);
        localStorage.removeItem(TOKEN_KEY);
      }
    } else {
      clearToken();
    }
  }, [token]);

  const login = useCallback(
    async (username: string, password: string, rememberMe: boolean = false) => {
      setLoading(true);
      try {
        const result = await authService.login(username, password);
        rememberMeRef.current = rememberMe;
        setToken(result.access_token);
        const parsed = parseJwt(result.access_token);
        setUser(parsed);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    rememberMeRef.current = false;
    clearToken();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: !!token && !!user,
      loading,
      login,
      logout,
    }),
    [user, token, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}

export default AuthContext;
