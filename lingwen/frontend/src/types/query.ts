/** Query types — mirror backend app/schemas/query.py */

export interface QueryRequest {
  question: string;
  datasource_id: number;
  history?: { question: string; answer: string }[];
  max_context_turns?: number;
}

export interface ChartSuggestion {
  type: 'bar' | 'line' | 'pie';
  title: string;
}

export interface PipelineStep {
  step: string;
  status: string;
  detail: string;
  elapsed_ms: number;
}

export interface QueryResponse {
  question: string;
  data: Record<string, unknown>[];
  columns: string[];
  analysis: string;
  sql: string;
  chart_suggestion: ChartSuggestion | null;
  row_count: number;
  is_truncated: boolean;
  latency_ms: number;
  pipeline_steps?: PipelineStep[];
  suggested_questions?: string[];
  total_tokens?: number;
  history_id?: number;
}
