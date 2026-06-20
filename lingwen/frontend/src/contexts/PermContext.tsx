import { createContext, useContext, useState, useEffect, useMemo, type ReactNode } from 'react';
import api from '../services/api';
import { useAuth } from './AuthContext';
import type { ApiResponse } from '../types';

interface PermContextValue {
  permissions: string[];
  hasPerm: (key: string) => boolean;
  loading: boolean;
}

const PermContext = createContext<PermContextValue>({ permissions: [], hasPerm: () => false, loading: true });

export function PermProvider({ children }: { children: ReactNode }) {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, user } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      setPermissions([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    api.get<ApiResponse<string[]>>('/api/my-permissions')
      .then(r => { setPermissions(r.data.data || []); })
      .catch(() => { setPermissions([]); })
      .finally(() => setLoading(false));
  }, [isAuthenticated, user?.user_id]);

  const hasPerm = (key: string) => {
    if (loading) return false;
    return permissions.includes(key);
  };
  const value = useMemo(() => ({ permissions, hasPerm, loading }), [permissions, loading]);

  return <PermContext.Provider value={value}>{children}</PermContext.Provider>;
}

export function usePerms() { return useContext(PermContext); }
