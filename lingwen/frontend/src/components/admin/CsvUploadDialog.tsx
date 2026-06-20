import { useState, useRef } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Typography, Box, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, LinearProgress, Alert
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { getToken } from '../../services/api';

interface PreviewData {
  datasource_id: number;
  datasource_name: string;
  table_name: string;
  columns: { column_name: string; display_name: string; data_type: string }[];
  row_count: number;
  sheets_count: number;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CsvUploadDialog({ open, onClose, onSuccess }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<PreviewData | null>(null);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File | null) => {
    setError('');
    setResult(null);
    if (!f) return;
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (!ext || !['csv', 'xlsx', 'xls'].includes(ext)) {
      setError('仅支持 CSV 或 XLSX 文件');
      return;
    }
    if (f.size > 50 * 1024 * 1024) {
      setError('文件不能超过 50MB');
      return;
    }
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const token = getToken();
      const form = new FormData();
      form.append('file', file);
      form.append('name', file.name.replace(/\.[^.]+$/, ''));
      const resp = await fetch('/api/datasources/upload-csv', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await resp.json();
      if (resp.ok && data.code === 200) {
        setResult(data.data);
        onSuccess();
      } else {
        setError(data.detail || '上传失败');
      }
    } catch {
      setError('网络错误，上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResult(null);
    setError('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>上传 CSV / Excel 文件</DialogTitle>
      <DialogContent>
        {!result && (
          <Box
            sx={{
              border: '2px dashed',
              borderColor: file ? 'primary.main' : 'divider',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: file ? 'action.hover' : 'transparent',
            }}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              hidden
              onChange={(e) => handleFile(e.target.files?.[0] || null)}
            />
            <CloudUploadIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
            <Typography variant="body1">
              {file ? file.name : '点击选择文件或拖拽到此处'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              支持 CSV、XLSX 格式，最大 50MB，表头格式: 字段名(备注)
            </Typography>
          </Box>
        )}

        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

        {uploading && <LinearProgress sx={{ mt: 2 }} />}

        {result && (
          <Box>
            <Alert severity="success" sx={{ mb: 2 }}>
              导入成功！表名: {result.table_name}，共 {result.row_count} 行 {result.columns.length} 列
            </Alert>
            <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 300 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 500 }}>字段名</TableCell>
                    <TableCell sx={{ fontWeight: 500 }}>显示名</TableCell>
                    <TableCell sx={{ fontWeight: 500 }}>类型</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.columns.map((c) => (
                    <TableRow key={c.column_name}>
                      <TableCell>{c.column_name}</TableCell>
                      <TableCell>{c.display_name}</TableCell>
                      <TableCell>{c.data_type}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{result ? '关闭' : '取消'}</Button>
        {!result && (
          <Button variant="contained" onClick={handleUpload} disabled={!file || uploading}>
            {uploading ? '上传中...' : '上传'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
