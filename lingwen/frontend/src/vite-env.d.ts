/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL for the Lingwen API backend */
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
