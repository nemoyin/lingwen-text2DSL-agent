import { useState } from 'react';
import { Box, Typography, TextField, Button, Card, FormControlLabel, Switch, Snackbar, Alert } from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getToken } from '../services/api';

export default function CasePage() {
  const navigate = useNavigate();
  const [sp] = useSearchParams();
  const [unit, setUnit] = useState(sp.get('unit') || '');
  const [content, setContent] = useState(sp.get('content') || '');
  const [caseNumber, setCaseNumber] = useState('');
  const [handler, setHandler] = useState('');
  const [notes, setNotes] = useState('');
  const [isFiled, setIsFiled] = useState(false);
  const [snack, setSnack] = useState({ open: false, msg: '', severity: 'success' as 'success' | 'error' });

  const handleSubmit = async () => {
    const alertId = sp.get('alert_id');
    if (!alertId) return;
    try {
      const token = getToken();
      const params = new URLSearchParams({ alert_id: alertId, is_filed: isFiled ? '1' : '0', case_number: caseNumber, handler, notes });
      await fetch(`/api/alerts/${alertId}/escalate?${params}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      setSnack({ open: true, msg: '线索已创建', severity: 'success' });
      setTimeout(() => navigate('/alerts/list'), 1000);
    } catch {
      setSnack({ open: true, msg: '创建失败', severity: 'error' });
    }
  };

  return (
    <Box maxWidth={640} mx="auto" px={2} py={4}>
      <Box sx={{ mb: 3, pb: 1, borderBottom: '3px solid', borderImage: 'linear-gradient(90deg, #2065F5, #4A88FF) 1' }}>
        <Typography variant="h5" fontWeight={700} color="#1F2937">转问题线索</Typography>
      </Box>
      <Card sx={{ p: 3 }}>
        <TextField fullWidth label="被预警单位" value={unit} disabled sx={{ mb: 2 }} />
        <TextField fullWidth label="预警内容" value={content} disabled multiline rows={3} sx={{ mb: 2 }} />
        <TextField fullWidth label="线索编号" value={caseNumber} onChange={e => setCaseNumber(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="承办人" value={handler} onChange={e => setHandler(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="备注" value={notes} onChange={e => setNotes(e.target.value)} multiline rows={2} sx={{ mb: 2 }} />
        <FormControlLabel control={<Switch checked={isFiled} onChange={e => setIsFiled(e.target.checked)} />} label="立案" sx={{ mb: 2, display: 'block' }} />
        <Button variant="contained" onClick={handleSubmit}>提交线索</Button>
      </Card>
      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack(s => ({...s, open:false}))}>
        <Alert severity={snack.severity}>{snack.msg}</Alert>
      </Snackbar>
    </Box>
  );
}
