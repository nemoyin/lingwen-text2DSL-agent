import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
} from '@mui/material';
import type { SkillTemplate, SkillCreate } from '../../types';

interface Props {
  open: boolean;
  initial?: SkillTemplate | null;
  onClose: () => void;
  onSave: (data: SkillCreate) => Promise<void>;
}

const DEFAULT: SkillCreate = {
  name: '',
  description: '',
  prompt_template: '',
};

export default function SkillEditor({ open, initial, onClose, onSave }: Props) {
  const [form, setForm] = useState<SkillCreate>(DEFAULT);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initial) {
      setForm({
        name: initial.name,
        description: initial.description || '',
        prompt_template: initial.prompt_template,
      });
    } else {
      setForm(DEFAULT);
    }
  }, [initial, open]);

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
      <DialogTitle>{initial ? '编辑 Skill' : '新建 Skill'}</DialogTitle>
      <DialogContent>
        <TextField fullWidth margin="dense" label="名称" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} required />
        <TextField fullWidth margin="dense" label="描述" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} />
        <TextField fullWidth margin="dense" label="Prompt 模板" value={form.prompt_template} onChange={(e) => setForm((p) => ({ ...p, prompt_template: e.target.value }))} required multiline rows={8} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={saving || !form.name || !form.prompt_template}>
          {saving ? '保存中...' : '保存'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
