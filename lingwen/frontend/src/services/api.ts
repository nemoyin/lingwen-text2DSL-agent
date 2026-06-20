/**
 * Centralized Axios instance for all API calls.
 *
 * Features:
 * - Automatic JWT token injection via request interceptor
 * - 401 response handling → redirect to /login
 * - 120-second timeout
 * - JSON content-type by default
 */

import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiResponse } from '../types';

const TOKEN_KEY = 'lingwen_token';

/**
 * Get the stored JWT token, checking sessionStorage first then localStorage.
 *
 * Dual storage strategy:
 * - sessionStorage: token set when "Remember Me" is NOT checked (clears on tab close)
 * - localStorage: token set when "Remember Me" IS checked (persists across sessions)
 *
 * @returns The token string, or null if not found in either storage.
 */
export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
}

/**
 * Remove the token from both storage backends on logout or 401.
 */
export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor: attach JWT Bearer token via getToken().
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  },
);

/**
 * Response interceptor: handle 401 (redirect to login) and pass through errors.
 */
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiResponse>) => {
    if (error.response?.status === 401) {
      clearToken();
      // Only redirect if not already on the login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

export default api;
