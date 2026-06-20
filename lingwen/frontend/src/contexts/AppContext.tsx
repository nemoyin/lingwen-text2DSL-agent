/** AppContext — global state for current datasource and datasource list. */

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';
import type { DataSource } from '../types';
import * as datasourceService from '../services/datasourceService';

interface AppState {
  currentDatasourceId: number | null;
  datasources: DataSource[];
  loading: boolean;
}

interface AppContextValue extends AppState {
  setDatasource: (id: number) => void;
  refreshDatasources: () => Promise<void>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [currentDatasourceId, setCurrentDatasourceId] = useState<
    number | null
  >(null);
  const [datasources, setDatasources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const setDatasource = useCallback((id: number) => {
    setCurrentDatasourceId(id);
  }, []);

  const refreshDatasources = useCallback(async () => {
    setLoading(true);
    try {
      const list = await datasourceService.getAll();
      setDatasources(list);
    } catch {
      // Error swallowed — callers should handle via hook state
    } finally {
      setLoading(false);
    }
  }, []);

  const value = useMemo<AppContextValue>(
    () => ({
      currentDatasourceId,
      datasources,
      loading,
      setDatasource,
      refreshDatasources,
    }),
    [currentDatasourceId, datasources, loading, setDatasource, refreshDatasources],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error('useApp must be used within AppProvider');
  }
  return ctx;
}

export default AppContext;
