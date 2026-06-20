import { useState, useEffect, useCallback } from 'react';
import { Box, Button, Snackbar, Alert, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import FewShotList from '../../components/admin/FewShotList';
import FewShotForm from '../../components/admin/FewShotForm';
import * as fewShotService from '../../services/fewShotService';
import { useDatasources } from '../../hooks/useDatasources';
import type { FewShotExample, FewShotCreate } from '../../types';

export default function FewShotPage() {
  const { datasources } = useDatasources();
  const [currentDs, setCurrentDs] = useState<number | ''>('');
  const [examples, setExamples] = useState<FewShotExample[]>([]);
  const [loading, setLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<FewShotExample | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [snack, setSnack] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  const fetchExamples = useCallback(async (dsId: number) => {
    setLoading(true);
    try {
      const list = await fewShotService.getAll(dsId);
      setExamples(list);
    } catch {
      setSnack({ open: true, message: '加载失败', severity: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentDs) void fetchExamples(currentDs);
  }, [currentDs, fetchExamples]);

  const handleSave = async (data: FewShotCreate) => {
    if (editing) {
      await fewShotService.update(editing.id, data);
    } else {
      await fewShotService.create(data);
    }
    setEditing(null);
    if (currentDs) await fetchExamples(currentDs);
  };

  const handleDelete = async () => {
    if (deleting === null) return;
    try {
      await fewShotService.remove(deleting);
      setSnack({ open: true, message: '已删除', severity: 'success' });
      if (currentDs) await fetchExamples(currentDs);
    } catch {
      setSnack({ open: true, message: '删除失败', severity: 'error' });
    }
    setDeleting(null);
  };

  return (
    <Box>
      <PageHeader
        title="Few-shot 示例"
        actions={
          <Button
            variant="contained"
            size="small"
            startIcon={<AddIcon />}
            disabled={!currentDs}
            onClick={() => { setEditing(null); setFormOpen(true); }}
          >
            新增示例
          </Button>
        }
      />

      <FormControl size="small" sx={{ minWidth: 200, mb: 2 }}>
        <InputLabel>数据源</InputLabel>
        <Select value={currentDs} label="数据源" onChange={(e) => setCurrentDs(Number(e.target.value))}>
          {datasources.map((ds) => (
            <MenuItem key={ds.id} value={ds.id}>{ds.name}</MenuItem>
          ))}
        </Select>
      </FormControl>

      {loading ? <LoadingSpinner /> : <FewShotList examples={examples} onEdit={(ex) => { setEditing(ex); setFormOpen(true); }} onDelete={(id) => setDeleting(id)} />}

      <FewShotForm
        open={formOpen}
        initial={editing}
        datasourceId={Number(currentDs) || 0}
        onClose={() => { setFormOpen(false); setEditing(null); }}
        onSave={handleSave}
      />

      <ConfirmDialog open={deleting !== null} title="删除示例" message="确定要删除此 Few-shot 示例吗？" onConfirm={handleDelete} onCancel={() => setDeleting(null)} />

      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))}>{snack.message}</Alert>
      </Snackbar>
    </Box>
  );
}
