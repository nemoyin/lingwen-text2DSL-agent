import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  IconButton,
  Typography,
} from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import EditIcon from '@mui/icons-material/Edit';
import type { ColumnMetadata, ColumnMetadataUpdate } from '../../types';

interface Props {
  columns: ColumnMetadata[];
  onUpdate: (columnId: number, data: ColumnMetadataUpdate) => Promise<void>;
}

export default function ColumnEditor({ columns, onUpdate }: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<ColumnMetadataUpdate>({});

  if (!columns.length) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
        请选择一个表查看字段
      </Typography>
    );
  }

  const startEdit = (col: ColumnMetadata) => {
    setEditingId(col.id);
    setEditData({
      display_name: col.display_name || '',
      business_description: col.business_description || '',
    });
  };

  const saveEdit = async () => {
    if (editingId === null) return;
    await onUpdate(editingId, editData);
    setEditingId(null);
    setEditData({});
  };

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 500 }}>字段名</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>类型</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>显示名</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>业务描述</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>主键</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {columns.map((col) => (
            <TableRow key={col.id} hover>
              <TableCell sx={{ fontWeight: 500 }}>{col.column_name}</TableCell>
              <TableCell>{col.data_type}</TableCell>
              <TableCell>
                {editingId === col.id ? (
                  <TextField
                    size="small"
                    value={editData.display_name ?? ''}
                    onChange={(e) => setEditData((prev) => ({ ...prev, display_name: e.target.value }))}
                    variant="standard"
                  />
                ) : (
                  col.display_name || '-'
                )}
              </TableCell>
              <TableCell>
                {editingId === col.id ? (
                  <TextField
                    size="small"
                    value={editData.business_description ?? ''}
                    onChange={(e) => setEditData((prev) => ({ ...prev, business_description: e.target.value }))}
                    variant="standard"
                    fullWidth
                  />
                ) : (
                  col.business_description || '-'
                )}
              </TableCell>
              <TableCell>{col.is_primary_key ? 'YES' : '-'}</TableCell>
              <TableCell>
                {editingId === col.id ? (
                  <IconButton size="small" onClick={saveEdit} color="primary">
                    <CheckIcon fontSize="small" />
                  </IconButton>
                ) : (
                  <IconButton size="small" onClick={() => startEdit(col)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
