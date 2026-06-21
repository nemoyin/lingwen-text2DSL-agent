/** Data source API service. */

import api from './api';
import type {
  ApiResponse,
  DataSource,
  DataSourceCreate,
  DataSourceUpdate,
  DBTypeMeta,
} from '../types';

export async function getAll(): Promise<DataSource[]> {
  const resp = await api.get<ApiResponse<DataSource[]>>('/api/datasources/');
  return resp.data.data!;
}

export async function getOne(id: number): Promise<DataSource> {
  const resp = await api.get<ApiResponse<DataSource>>(`/api/datasources/${id}`);
  return resp.data.data!;
}

export async function create(data: DataSourceCreate): Promise<DataSource> {
  const resp = await api.post<ApiResponse<DataSource>>('/api/datasources/', data);
  return resp.data.data!;
}

export async function update(
  id: number,
  data: DataSourceUpdate,
): Promise<DataSource> {
  const resp = await api.put<ApiResponse<DataSource>>(
    `/api/datasources/${id}`,
    data,
  );
  return resp.data.data!;
}

export async function remove(id: number): Promise<void> {
  await api.delete(`/api/datasources/${id}`);
}

export async function testConnection(
  id: number,
): Promise<{ success: boolean; message: string }> {
  const resp = await api.post<ApiResponse<{ success: boolean; message: string }>>(
    `/api/datasources/${id}/test`,
  );
  return resp.data.data!;
}

export async function fetchDbTypes(): Promise<DBTypeMeta[]> {
  const resp = await api.get<ApiResponse<DBTypeMeta[]>>('/api/datasources/types');
  return resp.data.data!;
}

/** Default-exported service object for component convenience. */
export const datasourceService = {
  getAll,
  getOne,
  create,
  update,
  remove,
  testConnection,
  fetchDbTypes,
};
