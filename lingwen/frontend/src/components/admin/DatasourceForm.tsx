import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
} from '@mui/material';
import type { DataSource, DataSourceCreate } from '../../types';

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
};

export default function DatasourceForm({ open, initial, onClose, onSave }: Props) {
  const [form, setForm] = useState<DataSourceCreate>(DEFAULT);
  const [saving, setSaving] = useState(false);

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
      });
    } else {
      setForm(DEFAULT);
    }
  }, [initial, open]);

  const handleChange = (field: keyof DataSourceCreate) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: field === 'port' ? Number(e.target.value) : e.target.value }));
  };

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
        <TextField select fullWidth margin="dense" label="类型" value={form.db_type} onChange={handleChange('db_type')}>
          <MenuItem value="mysql">MySQL</MenuItem>
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
