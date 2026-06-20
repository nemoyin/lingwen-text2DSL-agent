import { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Select, MenuItem, Chip, IconButton, Alert
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import api from '../../services/api';
import type { ApiResponse } from '../../types';

const PROVIDERS = ['deepseek', 'openai', 'kimi', 'glm', 'minimax'] as const;
const PROVIDER_LABELS: Record<string, string> = {
  deepseek: 'DeepSeek', openai: 'OpenAI 兼容', kimi: 'Kimi (Moonshot)',
  glm: 'GLM (智谱)', minimax: 'MiniMax',
};

export default function ModelManagement() {
  const [models, setModels] = useState<any[]>([]);
  const [dialog, setDialog] = useState({ open: false, id: 0, name: '', provider: 'deepseek', model_name: '', api_base: '', api_key: '' });
  const [testResult, setTestResult] = useState('');

  const fetch = () => api.get('/api/models').then(r => setModels(r.data.data || [])).catch(() => {});
  useEffect(() => { fetch(); }, []);

  const openDialog = (m?: any) => {
    if (m) {
      setDialog({ open: true, id: m.id, name: m.name, provider: m.provider, model_name: m.model_name, api_base: m.api_base, api_key: m.api_key || '' });
    } else {
      setDialog({ open: true, id: 0, name: '', provider: 'deepseek', model_name: '', api_base: '', api_key: '' });
    }
  };

  const save = async () => {
    const p = { name: dialog.name, provider: dialog.provider, model_name: dialog.model_name, api_base: dialog.api_base, api_key: dialog.api_key };
    if (dialog.id) {
      await api.put(`/api/models/${dialog.id}`, null, { params: p });
    } else {
      await api.post('/api/models', null, { params: p });
    }
    setDialog({ ...dialog, open: false }); fetch();
  };

  const del = async (id: number) => { await api.delete(`/api/models/${id}`); fetch(); };

  const setDefault = async (id: number) => { await api.post(`/api/models/${id}/set-default`); fetch(); };

  const test = async (id: number) => {
    setTestResult('测试中...');
    const r = await api.post(`/api/models/${id}/test`);
    const d = r.data.data;
    setTestResult(d.status === 'ok' ? `连接成功: ${d.response}` : `连接失败: ${d.error}`);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">模型管理</Typography>
        <Button size="small" variant="contained" onClick={() => openDialog()}>新增模型</Button>
      </Box>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small"><TableHead><TableRow>
          <TableCell>名称</TableCell><TableCell>供应商</TableCell><TableCell>模型</TableCell><TableCell>API Base</TableCell><TableCell>状态</TableCell><TableCell>操作</TableCell>
        </TableRow></TableHead><TableBody>
          {models.map(m => (
            <TableRow key={m.id}>
              <TableCell>{m.name} {m.is_default ? <Chip size="small" label="默认" color="primary" sx={{ ml: 0.5 }} /> : null}</TableCell>
              <TableCell><Chip size="small" label={PROVIDER_LABELS[m.provider] || m.provider} variant="outlined" /></TableCell>
              <TableCell>{m.model_name}</TableCell>
              <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 11 }}>{m.api_base}</TableCell>
              <TableCell><Chip size="small" label={m.is_active ? '启用' : '禁用'} color={m.is_active ? 'success' : 'default'} variant="outlined" /></TableCell>
              <TableCell>
                <IconButton size="small" onClick={() => test(m.id)} title="测试连接"><PlayArrowIcon fontSize="inherit" /></IconButton>
                <IconButton size="small" onClick={() => setDefault(m.id)} title="设为默认">
                  {m.is_default ? <StarIcon fontSize="inherit" /> : <StarBorderIcon fontSize="inherit" />}
                </IconButton>
                <IconButton size="small" onClick={() => openDialog(m)} title="编辑">✎</IconButton>
                <IconButton size="small" onClick={() => del(m.id)} title="删除" color="error"><DeleteIcon fontSize="inherit" /></IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody></Table>
      </TableContainer>

      {testResult && <Alert severity={testResult.includes('成功') ? 'success' : 'error'} sx={{ mt: 1 }} onClose={() => setTestResult('')}>{testResult}</Alert>}

      <Dialog open={dialog.open} onClose={() => setDialog({ ...dialog, open: false })} maxWidth="sm" fullWidth>
        <DialogTitle>{dialog.id ? '编辑模型' : '新增模型'}</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="dense" label="名称" value={dialog.name} onChange={e => setDialog({ ...dialog, name: e.target.value })} />
          <Select fullWidth value={dialog.provider} onChange={e => setDialog({ ...dialog, provider: e.target.value, api_base: '' })} sx={{ mt: 1 }}>
            {PROVIDERS.map(p => <MenuItem key={p} value={p}>{PROVIDER_LABELS[p]}</MenuItem>)}
          </Select>
          <TextField fullWidth margin="dense" label="模型名称" value={dialog.model_name} onChange={e => setDialog({ ...dialog, model_name: e.target.value })} helperText="例如: deepseek-chat, gpt-4o-mini, glm-4" />
          <TextField fullWidth margin="dense" label="API Base URL" value={dialog.api_base} onChange={e => setDialog({ ...dialog, api_base: e.target.value })} helperText="例如: https://api.deepseek.com/v1" />
          <TextField fullWidth margin="dense" label="API Key" type="password" value={dialog.api_key} onChange={e => setDialog({ ...dialog, api_key: e.target.value })} />
        </DialogContent>
        <DialogActions><Button onClick={() => setDialog({ ...dialog, open: false })}>取消</Button><Button variant="contained" onClick={save}>保存</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
