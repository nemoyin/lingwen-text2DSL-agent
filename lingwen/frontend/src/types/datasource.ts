/** Data source types — mirror backend app/schemas/datasource.py */

export interface DataSource {
  id: number;
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  extra_params?: Record<string, unknown>;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DataSourceCreate {
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  extra_params?: Record<string, unknown>;
}

export type DataSourceUpdate = Partial<DataSourceCreate> & {
  status?: string;
};

/** Metadata about one supported DB type (from GET /api/datasources/types). */
export interface DBTypeMeta {
  db_type: string;
  display_name: string;
  default_port: number;
  extra_fields: Record<string, { type: string; default?: unknown; label?: string }>;
}
