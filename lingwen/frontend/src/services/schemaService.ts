/** Schema API service. */

import api from './api';
import type { ApiResponse, ScanResult, TableInfo } from '../types';

export async function getSchema(datasourceId: number): Promise<TableInfo[]> {
  const resp = await api.get<ApiResponse<TableInfo[]>>('/api/schema/', {
    params: { datasource_id: datasourceId },
  });
  return resp.data.data!;
}

export async function scanSchema(datasourceId: number): Promise<ScanResult> {
  const resp = await api.post<ApiResponse<ScanResult>>('/api/schema/scan', {
    datasource_id: datasourceId,
  });
  return resp.data.data!;
}
