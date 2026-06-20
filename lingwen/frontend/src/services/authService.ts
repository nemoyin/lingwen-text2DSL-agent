/** Authentication API service. */

import api from './api';
import type { ApiResponse } from '../types';

interface LoginPayload {
  username: string;
  password: string;
}

interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export async function login(
  username: string,
  password: string,
): Promise<LoginResult> {
  const resp = await api.post<ApiResponse<LoginResult>>('/api/auth/login', {
    username,
    password,
  } as LoginPayload);
  return resp.data.data!;
}
