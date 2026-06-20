/** Metadata API service. */

import api from './api';
import type {
  ApiResponse,
  ColumnMetadata,
  ColumnMetadataUpdate,
  TableMetadata,
  TableMetadataUpdate,
} from '../types';

export async function getTables(
  datasourceId: number,
): Promise<TableMetadata[]> {
  const resp = await api.get<ApiResponse<TableMetadata[]>>(
    '/api/metadata/tables',
    { params: { datasource_id: datasourceId } },
  );
  return resp.data.data!;
}

export async function updateTable(
  id: number,
  data: TableMetadataUpdate,
): Promise<TableMetadata> {
  const resp = await api.put<ApiResponse<TableMetadata>>(
    `/api/metadata/tables/${id}`,
    data,
  );
  return resp.data.data!;
}

export async function getColumns(
  tableId: number,
): Promise<ColumnMetadata[]> {
  const resp = await api.get<ApiResponse<ColumnMetadata[]>>(
    '/api/metadata/columns',
    { params: { table_id: tableId } },
  );
  return resp.data.data!;
}

export async function updateColumn(
  id: number,
  data: ColumnMetadataUpdate,
): Promise<ColumnMetadata> {
  const resp = await api.put<ApiResponse<ColumnMetadata>>(
    `/api/metadata/columns/${id}`,
    data,
  );
  return resp.data.data!;
}
