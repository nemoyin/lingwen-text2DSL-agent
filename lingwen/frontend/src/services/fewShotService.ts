/** Few-shot example API service. */

import api from './api';
import type {
  ApiResponse,
  FewShotCreate,
  FewShotExample,
  FewShotUpdate,
} from '../types';

export async function getAll(datasourceId?: number): Promise<FewShotExample[]> {
  const params: Record<string, number> = {};
  if (datasourceId !== undefined) {
    params.datasource_id = datasourceId;
  }
  const resp = await api.get<ApiResponse<FewShotExample[]>>('/api/few-shot/', {
    params,
  });
  return resp.data.data!;
}

export async function getOne(id: number): Promise<FewShotExample> {
  const resp = await api.get<ApiResponse<FewShotExample>>(
    `/api/few-shot/${id}`,
  );
  return resp.data.data!;
}

export async function create(data: FewShotCreate): Promise<FewShotExample> {
  const resp = await api.post<ApiResponse<FewShotExample>>(
    '/api/few-shot/',
    data,
  );
  return resp.data.data!;
}

export async function update(
  id: number,
  data: FewShotUpdate,
): Promise<FewShotExample> {
  const resp = await api.put<ApiResponse<FewShotExample>>(
    `/api/few-shot/${id}`,
    data,
  );
  return resp.data.data!;
}

export async function remove(id: number): Promise<void> {
  await api.delete(`/api/few-shot/${id}`);
}
