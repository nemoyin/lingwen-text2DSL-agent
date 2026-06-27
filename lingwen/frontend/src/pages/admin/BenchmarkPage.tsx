import { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  Dialog, DialogTitle, DialogContent, DialogActions, Select, MenuItem, LinearProgress, Chip, TextField
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import api from '../../services/api';
import type { ApiResponse } from '../../types';

export default function BenchmarkPage() {
  const [sets, setSets] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [datasources, setDatasources] = useState<any[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedSet, setSelectedSet] = useState(0);
  const [selectedDs, setSelectedDs] = useState(0);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState('');
  const [detailRun, setDetailRun] = useState<any>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  const fetchAll = () => {
    api.get('/api/benchmark/sets').then(r => setSets(r.data.data || [])).catch(() => {});
    api.get('/api/benchmark/runs').then(r => setRuns(r.data.data || [])).catch(() => {});
    api.get('/api/datasources').then(r => setDatasources(r.data.data || [])).catch(() => {});
  };
  useEffect(() => { fetchAll(); }, []);

  const handleUpload = async () => {
    if (!uploadFile) return;
    const fd = new FormData();
    fd.append('file', uploadFile);
    const res = await api.post('/api/benchmark/sets', fd, { params: { name: uploadName }, headers: { 'Content-Type': 'multipart/form-data' } });
    if (res.data.code === 200) { setUploadOpen(false); fetchAll(); }
  };

  const handleCreate = async () => {
    await api.post('/api/benchmark/runs', null, { params: { set_id: selectedSet, datasource_id: selectedDs } });
    setCreateOpen(false); fetchAll();
  };

  const handleExecute = async (runId: number) => {
    await api.post(`/api/benchmark/runs/${runId}/execute`);
    fetchAll();
  };

  const handleDetail = async (runId: number) => {
    const r = await api.get(`/api/benchmark/runs/${runId}`);
    setDetailRun(r.data.data);
  };

  return (
    <Box>
      <Box sx={{ mb: 3, pb: 1, borderBottom: '3px solid', borderImage: 'linear-gradient(90deg, #2065F5, #4A88FF) 1' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6" fontWeight={700} color="#1F2937">Agent 性能测评</Typography>
        <Box gap={1} display="flex">
          <Button size="small" variant="outlined" onClick={() => setUploadOpen(true)}>上传测试集</Button>
          <Button size="small" variant="contained" onClick={() => setCreateOpen(true)}>新建任务</Button>
        </Box>
      </Box>
      </Box>

      <Typography variant="subtitle2" gutterBottom>评测任务</Typography>
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
        <Table size="small"><TableHead><TableRow>
          <TableCell>测试集</TableCell><TableCell>数据源</TableCell><TableCell>得分</TableCell><TableCell>通过/总数</TableCell><TableCell>状态</TableCell><TableCell>操作</TableCell>
        </TableRow></TableHead><TableBody>
          {runs.map(r => (
            <TableRow key={r.id}>
              <TableCell>{r.set_name}</TableCell>
              <TableCell>{datasources.find((d: any) => d.id === r.datasource_id)?.name || `ID:${r.datasource_id}`}</TableCell>
              <TableCell><Chip size="small" label={`${r.score}%`} color={(r.score ?? 0) > 60 ? 'success' : 'warning'} /></TableCell>
              <TableCell>{r.passed_count}/{r.total_count}</TableCell>
              <TableCell><Chip size="small" label={r.status} color={r.status === 'done' ? 'success' : r.status === 'running' ? 'info' : 'default'} variant="outlined" /></TableCell>
              <TableCell>
                {r.status === 'pending' || r.status === 'running' ? (
                  <Button size="small" onClick={() => handleExecute(r.id)} startIcon={<PlayArrowIcon />}>{r.status === 'running' ? '执行中...' : '执行'}</Button>
                ) : null}
                <Button size="small" onClick={() => handleDetail(r.id)}>详情</Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody></Table>
      </TableContainer>

      <Dialog open={uploadOpen} onClose={() => setUploadOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>上传测试集</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="dense" label="名称" value={uploadName} onChange={e => setUploadName(e.target.value)} />
          <Button variant="outlined" component="label" fullWidth sx={{ mt: 1 }}>
            选择 CSV 文件
            <input type="file" accept=".csv" hidden onChange={e => setUploadFile(e.target.files?.[0] || null)} />
          </Button>
          {uploadFile && <Typography variant="caption" sx={{ mt: 0.5 }}>{uploadFile.name}</Typography>}
        </DialogContent>
        <DialogActions><Button onClick={() => setUploadOpen(false)}>取消</Button><Button variant="contained" onClick={handleUpload}>上传</Button></DialogActions>
      </Dialog>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>新建评测任务</DialogTitle>
        <DialogContent>
          <Select fullWidth value={selectedSet} onChange={e => setSelectedSet(e.target.value as number)} sx={{ mt: 1 }}>
            <MenuItem value={0} disabled>选择测试集</MenuItem>
            {sets.map(s => <MenuItem key={s.id} value={s.id}>{s.name} ({s.row_count}题)</MenuItem>)}
          </Select>
          <Select fullWidth value={selectedDs} onChange={e => setSelectedDs(e.target.value as number)} sx={{ mt: 1 }}>
            <MenuItem value={0} disabled>选择数据源</MenuItem>
            {datasources.map((d: any) => <MenuItem key={d.id} value={d.id}>{d.name}</MenuItem>)}
          </Select>
        </DialogContent>
        <DialogActions><Button onClick={() => setCreateOpen(false)}>取消</Button><Button variant="contained" onClick={handleCreate}>创建</Button></DialogActions>
      </Dialog>

      <Dialog open={!!detailRun} onClose={() => setDetailRun(null)} maxWidth="md" fullWidth>
        <DialogTitle>评测详情 — 得分 {detailRun?.score}%</DialogTitle>
        <DialogContent>
          {detailRun?.results?.map((r: any, i: number) => (
            <Box key={i} sx={{ mb: 2, p: 1.5, border: '0.5px solid', borderColor: r.passed ? 'success.main' : 'error.main', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight={500}>{r.question}</Typography>
              <Box display="flex" gap={2} mt={0.5}>
                <Box flex={1}><Typography variant="caption" color="text.secondary">期望答案</Typography><Typography variant="body2" fontSize={12}>{r.expected_answer || '——'}</Typography></Box>
                <Box flex={1}><Typography variant="caption" color="text.secondary">系统答案</Typography><Typography variant="body2" fontSize={12}>{r.actual_answer?.slice(0, 200)}</Typography></Box>
              </Box>
              <Box display="flex" gap={2} mt={0.5}>
                <Chip size="small" label={`相似度 ${r.similarity_score?.toFixed(2)}`} />
                <Chip size="small" label={`${r.latency_ms}ms`} />
                <Chip size="small" label={r.passed ? '通过' : '未通过'} color={r.passed ? 'success' : 'error'} variant="outlined" />
              </Box>
              {r.actual_sql && (
                <Box mt={0.5}>
                  <Typography variant="caption" color="text.secondary">生成 SQL</Typography>
                  <Typography variant="body2" fontSize={11} fontFamily="monospace" sx={{ whiteSpace: 'pre-wrap', bgcolor: '#fafafa', p: 0.5, borderRadius: 0.5, maxHeight: 80, overflow: 'auto' }}>
                    {r.actual_sql?.slice(0, 300)}
                  </Typography>
                </Box>
              )}
              {r.pipeline_json && (
                <Box mt={0.5}>
                  <Typography variant="caption" color="text.secondary">管线步骤 ({(() => { try { return JSON.parse(r.pipeline_json || '[]').length } catch { return 0 } })()}步)</Typography>
                </Box>
              )}
            </Box>
          ))}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
