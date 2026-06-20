/** Data source types — mirror backend app/schemas/datasource.py */

export interface DataSource {
  id: number;
  name: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
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
}

export type DataSourceUpdate = Partial<DataSourceCreate> & {
  status?: string;
};
