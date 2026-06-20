import { useState, useCallback } from 'react';
import { Box, Button, Snackbar, Alert } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import DatasourceList from '../../components/admin/DatasourceList';
import DatasourceForm from '../../components/admin/DatasourceForm';
import CsvUploadDialog from '../../components/admin/CsvUploadDialog';
import * as datasourceService from '../../services/datasourceService';
import * as schemaService from '../../services/schemaService';
import { useDatasources } from '../../hooks/useDatasources';
import type { DataSource, DataSourceCreate } from '../../types';

export default function DatasourcePage() {
  const { loading, datasources, refresh } = useDatasources();
  const [formOpen, setFormOpen] = useState(false);
  const [csvOpen, setCsvOpen] = useState(false);
  const [editing, setEditing] = useState<DataSource | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [snack, setSnack] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });

  const showMsg = (message: string, severity: 'success' | 'error') => setSnack({ open: true, message, severity });

  const handleEdit = (ds: DataSource) => {
    setEditing(ds);
    setFormOpen(true);
  };

  const handleSave = async (data: DataSourceCreate) => {
    if (editing) {
      await datasourceService.update(editing.id, data);
      showMsg('数据源已更新', 'success');
    } else {
      await datasourceService.create(data);
      showMsg('数据源已创建', 'success');
    }
    setEditing(null);
    await refresh();
  };

  const handleTest = async (id: number) => {
    try {
      const res = await datasourceService.testConnection(id);
      showMsg(res.success ? '连接成功' : res.message, res.success ? 'success' : 'error');
    } catch {
      showMsg('连接测试失败', 'error');
    }
  };

  const handleScan = async (id: number) => {
    try {
      const res = await schemaService.scanSchema(id);
      showMsg(`扫描完成：${res.tables_scanned} 张表，${res.columns_scanned} 个字段`, 'success');
      await refresh();
    } catch {
      showMsg('Schema 扫描失败', 'error');
    }
  };

  const handleDelete = async () => {
    if (deleting === null) return;
    try {
      await datasourceService.remove(deleting);
      showMsg('数据源已删除', 'success');
      await refresh();
    } catch {
      showMsg('删除失败', 'error');
    }
    setDeleting(null);
  };

  return (
    <Box>
      <PageHeader
        title="数据源管理"
        actions={
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<CloudUploadIcon />}
              onClick={() => setCsvOpen(true)}
            >
              上传 CSV
            </Button>
            <Button
              variant="contained"
              size="small"
              startIcon={<AddIcon />}
              onClick={() => { setEditing(null); setFormOpen(true); }}
            >
              新增数据源
            </Button>
          </Box>
        }
      />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <DatasourceList
          datasources={datasources}
          onEdit={handleEdit}
          onTest={handleTest}
          onScan={handleScan}
          onDelete={(id) => setDeleting(id)}
        />
      )}

      <DatasourceForm
        open={formOpen}
        initial={editing}
        onClose={() => { setFormOpen(false); setEditing(null); }}
        onSave={handleSave}
      />

      <ConfirmDialog
        open={deleting !== null}
        title="删除数据源"
        message="确定要删除此数据源吗？此操作不可恢复。"
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
      />

      <CsvUploadDialog
        open={csvOpen}
        onClose={() => setCsvOpen(false)}
        onSuccess={() => { setCsvOpen(false); refresh(); showMsg('CSV 导入成功', 'success'); }}
      />

      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))}>{snack.message}</Alert>
      </Snackbar>
    </Box>
  );
}
