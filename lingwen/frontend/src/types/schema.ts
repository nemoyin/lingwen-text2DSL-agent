/** Schema types — mirror backend app/schemas/schema.py */

export interface ColumnInfo {
  id: number;
  column_name: string;
  data_type: string;
  display_name: string | null;
  business_description: string | null;
  is_primary_key: boolean;
  is_foreign_key: boolean;
}

export interface TableInfo {
  id: number;
  table_name: string;
  display_name: string | null;
  business_description: string | null;
  columns: ColumnInfo[];
}

export interface ScanResult {
  tables_scanned: number;
  columns_scanned: number;
}
