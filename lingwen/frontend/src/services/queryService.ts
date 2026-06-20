/** Query API service — execute natural-language queries with multi-turn support and SSE streaming. */

import api, { getToken } from './api';
import type { ApiResponse, QueryRequest, QueryResponse } from '../types';

export interface QueryOptions {
  history?: { question: string; answer: string }[];
  maxContextTurns?: number;
}

/** Progress event emitted during streaming query execution. */
export interface StreamProgress {
  event: 'step' | 'done' | 'error' | 'history_id';
  step?: string;
  status?: string;
  elapsed_ms?: number;
  data?: QueryResponse;
  message?: string;
  id?: number;
  /** Native LLM reasoning text (DeepSeek reasoning_content) */
  reasoning?: string;
}

export async function executeQuery(
  question: string,
  datasource_id: number,
  options?: QueryOptions,
): Promise<QueryResponse> {
  const req: QueryRequest = {
    question,
    datasource_id,
    history: options?.history,
    max_context_turns: options?.maxContextTurns ?? 6,
  };
  const resp = await api.post<ApiResponse<QueryResponse>>('/api/query', req);
  return resp.data.data!;
}

/**
 * Execute a query via SSE streaming.
 *
 * Calls ``onProgress`` with ``{event: "step", step, status, elapsed_ms}``
 * for each pipeline node and ``{event: "done", data: QueryResponse}`` on
 * completion.  Returns the final ``QueryResponse``.
 *
 * Accepts an optional ``AbortSignal`` to cancel the in-flight request.
 */
export async function executeQueryStream(
  question: string,
  datasource_id: number,
  onProgress: (evt: StreamProgress) => void,
  options?: QueryOptions,
  signal?: AbortSignal,
): Promise<QueryResponse> {
  const token = getToken();

  const response = await fetch('/api/query/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      question,
      datasource_id,
      history: options?.history,
      max_context_turns: options?.maxContextTurns ?? 6,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Query failed: ${response.status}`);
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalResult: QueryResponse | null = null;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const evt = JSON.parse(line.slice(6)) as StreamProgress;
            onProgress(evt);
            if (evt.event === 'done' && evt.data) {
              finalResult = evt.data;
            }
            if (evt.event === 'history_id' && evt.id && finalResult) {
              finalResult = { ...finalResult, history_id: evt.id };
            }
          } catch { /* skip malformed */ }
        }
      }
    }
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('CANCELLED');
    }
    throw err;
  } finally {
    reader.releaseLock();
  }

  if (!finalResult) {
    throw new Error('Stream ended without done event');
  }
  return finalResult;
}
