import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
} from '@mui/material';
import type { FewShotExample, FewShotCreate } from '../../types';

interface Props {
  open: boolean;
  initial?: FewShotExample | null;
  datasourceId: number;
  onClose: () => void;
  onSave: (data: FewShotCreate) => Promise<void>;
}

const DEFAULT = (datasourceId: number): FewShotCreate => ({
  datasource_id: datasourceId,
  question: '',
  sql: '',
  description: '',
  tags: '',
});

export default function FewShotForm({ open, initial, datasourceId, onClose, onSave }: Props) {
  const [form, setForm] = useState<FewShotCreate>(DEFAULT(datasourceId));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initial) {
      setForm({
        datasource_id: initial.datasource_id,
        question: initial.question,
        sql: initial.sql,
        description: initial.description || '',
        tags: initial.tags || '',
      });
    } else {
      setForm(DEFAULT(datasourceId));
    }
  }, [initial, datasourceId, open]);

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
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{initial ? '编辑示例' : '新增示例'}</DialogTitle>
      <DialogContent>
        <TextField fullWidth margin="dense" label="问题" value={form.question} onChange={(e) => setForm((p) => ({ ...p, question: e.target.value }))} required multiline rows={2} />
        <TextField fullWidth margin="dense" label="SQL" value={form.sql} onChange={(e) => setForm((p) => ({ ...p, sql: e.target.value }))} required multiline rows={4} />
        <TextField fullWidth margin="dense" label="描述" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} />
        <TextField fullWidth margin="dense" label="标签（逗号分隔）" value={form.tags} onChange={(e) => setForm((p) => ({ ...p, tags: e.target.value }))} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={saving || !form.question || !form.sql}>
          {saving ? '保存中...' : '保存'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
