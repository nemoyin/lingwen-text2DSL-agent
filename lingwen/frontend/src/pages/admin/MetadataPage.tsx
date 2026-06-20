import { useState, useEffect, useCallback } from 'react';
import { Box, FormControl, InputLabel, Select, MenuItem, Snackbar, Alert } from '@mui/material';
import PageHeader from '../../components/common/PageHeader';
import MetadataPanel from '../../components/admin/MetadataPanel';
import * as metadataService from '../../services/metadataService';
import { useDatasources } from '../../hooks/useDatasources';
import type { TableMetadata, ColumnMetadata, ColumnMetadataUpdate } from '../../types';

export default function MetadataPage() {
  const { datasources } = useDatasources();
  const [currentDs, setCurrentDs] = useState<number | ''>('');
  const [tables, setTables] = useState<TableMetadata[]>([]);
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  const [selectedTable, setSelectedTable] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [snack, setSnack] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  const loadTables = useCallback(async (dsId: number) => {
    setLoading(true);
    try {
      const t = await metadataService.getTables(dsId);
      setTables(t);
      setSelectedTable(null);
      setColumns([]);
    } catch {
      setSnack({ open: true, message: '加载表失败', severity: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentDs) {
      void loadTables(currentDs);
    }
  }, [currentDs, loadTables]);

  const handleTableSelect = async (tableId: number) => {
    setSelectedTable(tableId);
    setLoading(true);
    try {
      const cols = await metadataService.getColumns(tableId);
      setColumns(cols);
    } catch {
      setSnack({ open: true, message: '加载字段失败', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleColumnUpdate = async (columnId: number, data: ColumnMetadataUpdate) => {
    try {
      await metadataService.updateColumn(columnId, data);
      setSnack({ open: true, message: '字段已更新', severity: 'success' });
      if (selectedTable) await handleTableSelect(selectedTable);
    } catch {
      setSnack({ open: true, message: '更新失败', severity: 'error' });
    }
  };

  return (
    <Box>
      <PageHeader title="元数据管理" />
      <FormControl size="small" sx={{ minWidth: 200, mb: 2 }}>
        <InputLabel>数据源</InputLabel>
        <Select value={currentDs} label="数据源" onChange={(e) => setCurrentDs(Number(e.target.value))}>
          {datasources.map((ds) => (
            <MenuItem key={ds.id} value={ds.id}>{ds.name}</MenuItem>
          ))}
        </Select>
      </FormControl>

      <MetadataPanel
        loading={loading}
        tables={tables}
        columns={columns}
        selectedTableId={selectedTable}
        onTableSelect={handleTableSelect}
        onColumnUpdate={handleColumnUpdate}
      />

      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))}>{snack.message}</Alert>
      </Snackbar>
    </Box>
  );
}
