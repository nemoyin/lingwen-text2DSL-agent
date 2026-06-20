/**
 * Common TypeScript types shared across the Lingwen frontend.
 * These mirror the Pydantic schemas defined in backend/app/schemas/common.py.
 */

/** Standard API success response envelope */
export interface ApiResponse<T = unknown> {
  code: number;
  data: T | null;
  message: string;
}

/** Pagination query parameters */
export interface PaginationParams {
  page: number;
  page_size: number;
}

/** Paginated list response */
export interface PaginationResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** Error detail returned by the API */
export interface ErrorDetail {
  code: number;
  message: string;
  detail?: string;
}
