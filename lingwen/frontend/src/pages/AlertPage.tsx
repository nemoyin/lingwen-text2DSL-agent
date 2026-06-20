import { useState } from 'react';
import { Box, Typography, TextField, Button, Card, Snackbar, Alert } from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api, { getToken } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';

export default function AlertPage() {
  const navigate = useNavigate();
  const { t } = useTheme();
  const [searchParams] = useSearchParams();
  const [targetUnit, setTargetUnit] = useState('');
  const [content, setContent] = useState(searchParams.get('content') || '');
  const [snack, setSnack] = useState({ open: false, msg: '', severity: 'success' as 'success' | 'error' });

  const handleSubmit = async () => {
    try {
      const token = getToken();
      const params = new URLSearchParams({ target_unit: targetUnit, content });
      await fetch(`/api/alerts?${params}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      setSnack({ open: true, msg: '预警已创建', severity: 'success' });
      setTimeout(() => navigate('/alerts/list'), 1000);
    } catch {
      setSnack({ open: true, msg: '创建失败', severity: 'error' });
    }
  };

  return (
    <Box maxWidth={640} mx="auto" px={2} py={4}>
      <Box sx={{ mb: 3, pb: 1, borderBottom: '3px solid', borderImage: 'linear-gradient(90deg, #2065F5, #4A88FF) 1' }}>
        <Typography variant="h5" fontWeight={700} color="#1F2937">{t('创建预警', 'Create Alert')}</Typography>
      </Box>
      <Card sx={{ p: 3 }}>
        <TextField fullWidth label={t('被预警单位', 'Target Unit')} value={targetUnit} onChange={e => setTargetUnit(e.target.value)} sx={{ mb: 2 }} required />
        <TextField fullWidth label={t('预警内容', 'Alert Content')} value={content} onChange={e => setContent(e.target.value)} multiline rows={6} sx={{ mb: 2 }} required />
        <Box display="flex" gap={2}>
          <Button variant="contained" onClick={handleSubmit} disabled={!targetUnit || !content}>{t('提交预警', 'Submit Alert')}</Button>
          <Button variant="outlined" onClick={() => navigate('/alerts/list')}>{t('查看列表', 'View List')}</Button>
        </Box>
      </Card>
      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack(s => ({...s, open:false}))}>
        <Alert severity={snack.severity}>{snack.msg}</Alert>
      </Snackbar>
    </Box>
  );
}
