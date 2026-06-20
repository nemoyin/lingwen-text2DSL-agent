import { useState, useEffect, useCallback } from 'react';
import * as datasourceService from '../services/datasourceService';
import type { DataSource } from '../types';

interface UseDatasourcesReturn {
  loading: boolean;
  datasources: DataSource[];
  error: string | null;
  refresh: () => Promise<void>;
}

export function useDatasources(): UseDatasourcesReturn {
  const [loading, setLoading] = useState<boolean>(true);
  const [datasources, setDatasources] = useState<DataSource[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await datasourceService.getAll();
      setDatasources(list);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : '获取数据源列表失败';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchList();
  }, [fetchList]);

  return { loading, datasources, error, refresh: fetchList };
}
