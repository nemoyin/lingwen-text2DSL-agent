/** Unified type exports for the Lingwen frontend. */

export type { ApiResponse, PaginationParams, PaginationResponse, ErrorDetail } from './common';
export type { DataSource, DataSourceCreate, DataSourceUpdate } from './datasource';
export type { QueryRequest, QueryResponse, ChartSuggestion } from './query';
export type { ColumnInfo, TableInfo, ScanResult } from './schema';
export type {
  TableMetadata,
  ColumnMetadata,
  TableMetadataUpdate,
  ColumnMetadataUpdate,
} from './metadata';
export type { FewShotExample, FewShotCreate, FewShotUpdate } from './few-shot';
export type { SkillTemplate, SkillCreate, SkillUpdate } from './skill';
