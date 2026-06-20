import { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import CaseDialog from '../components/alerts/CaseDialog';

export default function AlertListPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [caseDialog, setCaseDialog] = useState<{ open: boolean; alertId: number; targetUnit: string; alertContent: string }>({ open: false, alertId: 0, targetUnit: '', alertContent: '' });
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/api/alerts').then(r => setAlerts(r.data.data || [])).catch(() => {});
  }, []);

  return (
    <Box maxWidth={900} mx="auto" px={2} py={3}>
      <Box sx={{ mb: 3, pb: 1, borderBottom: '3px solid', borderImage: 'linear-gradient(90deg, #2065F5, #4A88FF) 1' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h5" fontWeight={700} color="#1F2937">预警列表</Typography>
          <Button variant="contained" size="small" onClick={() => navigate('/alerts/new')}>新建预警</Button>
        </Box>
      </Box>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small"><TableHead><TableRow>
          <TableCell sx={{fontWeight:500}}>被预警单位</TableCell>
          <TableCell sx={{fontWeight:500}}>内容</TableCell>
          <TableCell sx={{fontWeight:500}}>时间</TableCell>
          <TableCell sx={{fontWeight:500}}>操作</TableCell>
        </TableRow></TableHead>
        <TableBody>
          {alerts.map(a => (
            <TableRow key={a.id} hover>
              <TableCell>{a.target_unit}</TableCell>
              <TableCell sx={{maxWidth:300,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{a.content}</TableCell>
              <TableCell>{a.created_at?.slice(0,16)}</TableCell>
              <TableCell>
                <Button size="small" onClick={() => setCaseDialog({ open: true, alertId: a.id, targetUnit: a.target_unit, alertContent: a.content })}>转线索</Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody></Table>
      </TableContainer>

      <CaseDialog
        open={caseDialog.open}
        onClose={() => setCaseDialog(c => ({ ...c, open: false }))}
        alertId={caseDialog.alertId}
        targetUnit={caseDialog.targetUnit}
        alertContent={caseDialog.alertContent}
      />
    </Box>
  );
}
