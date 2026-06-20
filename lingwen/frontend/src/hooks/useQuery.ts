import { useState, useCallback, useRef } from 'react';
import * as queryService from '../services/queryService';
import type { QueryOptions, StreamProgress } from '../services/queryService';
import type { QueryResponse } from '../types';

export interface ReasoningStep {
  step: string;
  text: string;
}

interface UseQueryState {
  loading: boolean;
  result: QueryResponse | null;
  error: string | null;
  /** Pipeline progress steps emitted during streaming. */
  progressSteps: StreamProgress[];
  /** Per-step reasoning blocks (each step = one paragraph). */
  reasoningSteps: ReasoningStep[];
}

interface UseQueryReturn extends UseQueryState {
  executeQuery: (question: string, datasourceId: number, options?: QueryOptions) => Promise<void>;
  executeQueryStream: (question: string, datasourceId: number, options?: QueryOptions) => Promise<void>;
  cancelQuery: () => void;
  reset: () => void;
}

export function useQuery(): UseQueryReturn {
  const abortRef = useRef<AbortController | null>(null);

  const [state, setState] = useState<UseQueryState>({
    loading: false,
    result: null,
    error: null,
    progressSteps: [],
    reasoningSteps: [],
  });

  const executeQuery = useCallback(
    async (question: string, datasourceId: number, options?: QueryOptions) => {
      setState({ loading: true, result: null, error: null, progressSteps: [], reasoningSteps: [] });
      try {
        const result = await queryService.executeQuery(question, datasourceId, options);
        setState({ loading: false, result, error: null, progressSteps: [], reasoningSteps: [] });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : '查询失败，请稍后重试';
        setState({ loading: false, result: null, error: message, progressSteps: [], reasoningSteps: [] });
      }
    },
    [],
  );

  const executeQueryStream = useCallback(
    async (question: string, datasourceId: number, options?: QueryOptions) => {
      const steps: StreamProgress[] = [];
      const reasoningBlocks: queryService.ReasoningStep[] = [];

      const controller = new AbortController();
      abortRef.current = controller;

      setState({ loading: true, result: null, error: null, progressSteps: [], reasoningSteps: [] });
      try {
        const result = await queryService.executeQueryStream(
          question, datasourceId,
          (evt) => {
            steps.push(evt);
            if (evt.reasoning && evt.step) {
              reasoningBlocks.push({ step: evt.step, text: evt.reasoning });
            }
            setState(prev => ({
              ...prev,
              progressSteps: [...steps],
              reasoningSteps: [...reasoningBlocks],
            }));
          },
          options,
          controller.signal,
        );
        setState(prev => ({ ...prev, loading: false, result, progressSteps: [...steps] }));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : '查询失败，请稍后重试';
        if (message !== 'CANCELLED') {
          setState({ loading: false, result: null, error: message, progressSteps: [...steps], reasoningSteps: [] });
        } else {
          setState(prev => ({ ...prev, loading: false }));
        }
      } finally {
        abortRef.current = null;
      }
    },
    [],
  );

  const cancelQuery = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback(() => {
    setState({ loading: false, result: null, error: null, progressSteps: [], reasoningSteps: [] });
  }, []);

  return { ...state, executeQuery, executeQueryStream, cancelQuery, reset };
}
