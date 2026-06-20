/**
 * Application-wide constants for the Lingwen frontend.
 */

/** Base URL for the Lingwen API backend */
export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/** Pagination defaults (matches backend default page_size = 20) */
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

/** Maximum rows the backend will return per query (safety limit) */
export const MAX_RESULT_ROWS: number = 1000;

/** localStorage key for the JWT access token */
export const TOKEN_KEY: string = 'lingwen_token';

/** Application display title */
export const APP_TITLE: string = '天府一网监 · 智能问数引擎';

/** Query request timeout (ms) */
export const QUERY_TIMEOUT_MS: number = 30000;
