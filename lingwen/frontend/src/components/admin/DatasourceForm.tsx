import { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import type { DataSource, DataSourceCreate, DBTypeMeta } from '../../types';
import { datasourceService } from '../../services/datasourceService';

interface Props {
  open: boolean;
  initial?: DataSource | null;
  onClose: () => void;
  onSave: (data: DataSourceCreate) => Promise<void>;
}

const DEFAULT: DataSourceCreate = {
  name: '',
  db_type: 'mysql',
  host: 'localhost',
  port: 3306,
  database: '',
  username: 'root',
  password: '',
  extra_params: {},
};

export default function DatasourceForm({ open, initial, onClose, onSave }: Props) {
  const [form, setForm] = useState<DataSourceCreate>(DEFAULT);
  const [saving, setSaving] = useState(false);
  const [dbTypes, setDbTypes] = useState<DBTypeMeta[]>([]);
  const [typesLoading, setTypesLoading] = useState(false);

  // Fetch available DB types on mount
  useEffect(() => {
    let cancelled = false;
    setTypesLoading(true);
    datasourceService
      .fetchDbTypes()
      .then((types) => { if (!cancelled) setDbTypes(types); })
      .catch(() => { /* fall back to static defaults */ })
      .finally(() => { if (!cancelled) setTypesLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (initial) {
      setForm({
        name: initial.name,
        db_type: initial.db_type,
        host: initial.host,
        port: initial.port,
        database: initial.database,
        username: initial.username,
        password: '',
        extra_params: initial.extra_params || {},
      });
    } else {
      setForm(DEFAULT);
    }
  }, [initial, open]);

  const handleChange = (field: keyof DataSourceCreate) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: field === 'port' ? Number(e.target.value) : e.target.value }));
  };

  // When db_type changes, auto-fill port to the type's default
  const handleDbTypeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newType = e.target.value;
      const meta = dbTypes.find((t) => t.db_type === newType);
      setForm((prev) => ({
        ...prev,
        db_type: newType,
        port: meta?.default_port ?? prev.port,
        extra_params: {},
      }));
    },
    [dbTypes],
  );

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await onSave(form);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{initial ? '编辑数据源' : '新增数据源'}</DialogTitle>
      <DialogContent>
        <TextField fullWidth margin="dense" label="名称" value={form.name} onChange={handleChange('name')} required />

        <TextField
          select
          fullWidth
          margin="dense"
          label="类型"
          value={form.db_type}
          onChange={handleDbTypeChange}
          InputProps={typesLoading ? { endAdornment: <CircularProgress size={20} /> } : undefined}
        >
          {dbTypes.length > 0
            ? dbTypes.map((t) => (
                <MenuItem key={t.db_type} value={t.db_type}>
                  {t.display_name}
                </MenuItem>
              ))
            : /* Fallback when API hasn't loaded yet */
              [
                <MenuItem key="mysql" value="mysql">MySQL</MenuItem>,
                <MenuItem key="postgresql" value="postgresql">PostgreSQL</MenuItem>,
              ]}
        </TextField>

        <TextField fullWidth margin="dense" label="主机" value={form.host} onChange={handleChange('host')} required />
        <TextField fullWidth margin="dense" label="端口" type="number" value={form.port} onChange={handleChange('port')} required />
        <TextField fullWidth margin="dense" label="数据库" value={form.database} onChange={handleChange('database')} required />
        <TextField fullWidth margin="dense" label="用户名" value={form.username} onChange={handleChange('username')} required />
        <TextField fullWidth margin="dense" label="密码" type="password" value={form.password} onChange={handleChange('password')} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={saving || !form.name || !form.host || !form.database || !form.username}>
          {saving ? '保存中...' : '保存'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
