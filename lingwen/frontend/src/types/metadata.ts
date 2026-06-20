/** Metadata types — mirror backend app/schemas/metadata.py */

export interface TableMetadata {
  id: number;
  datasource_id: number;
  table_name: string;
  display_name: string | null;
  business_description: string | null;
  created_at: string;
}

export interface ColumnMetadata {
  id: number;
  table_id: number;
  column_name: string;
  data_type: string;
  display_name: string | null;
  business_description: string | null;
  enum_values: Record<string, string> | null;
  is_primary_key: boolean;
  is_foreign_key: boolean;
}

export interface TableMetadataUpdate {
  display_name?: string;
  business_description?: string;
}

export interface ColumnMetadataUpdate {
  display_name?: string;
  business_description?: string;
  enum_values?: Record<string, string>;
}
