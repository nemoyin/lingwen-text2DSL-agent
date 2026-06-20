import { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, FormControlLabel, Switch, Snackbar, Alert } from '@mui/material';
import { getToken } from '../../services/api';

interface Props {
  open: boolean;
  onClose: () => void;
  alertId: number;
  targetUnit: string;
  alertContent: string;
}

export default function CaseDialog({ open, onClose, alertId, targetUnit, alertContent }: Props) {
  const [caseNumber, setCaseNumber] = useState('');
  const [handler, setHandler] = useState('');
  const [notes, setNotes] = useState('');
  const [isFiled, setIsFiled] = useState(false);
  const [snack, setSnack] = useState({ open: false, msg: '', severity: 'success' as 'success' | 'error' });

  const handleSubmit = async () => {
    try {
      const token = getToken();
      const params = new URLSearchParams({ is_filed: isFiled ? '1' : '0', case_number: caseNumber, handler, notes });
      const resp = await fetch(`/api/alerts/${alertId}/escalate?${params}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      const data = await resp.json();
      if (data.code === 200) {
        setSnack({ open: true, msg: '线索已创建', severity: 'success' });
        setTimeout(() => onClose(), 1000);
      } else {
        setSnack({ open: true, msg: '创建失败', severity: 'error' });
      }
    } catch {
      setSnack({ open: true, msg: '网络错误', severity: 'error' });
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>转问题线索</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="dense" label="被预警单位" value={targetUnit} disabled />
          <TextField fullWidth margin="dense" label="预警内容" value={alertContent} disabled multiline rows={3} />
          <TextField fullWidth margin="dense" label="线索编号" value={caseNumber} onChange={e => setCaseNumber(e.target.value)} />
          <TextField fullWidth margin="dense" label="承办人" value={handler} onChange={e => setHandler(e.target.value)} />
          <TextField fullWidth margin="dense" label="备注" value={notes} onChange={e => setNotes(e.target.value)} multiline rows={2} />
          <FormControlLabel control={<Switch checked={isFiled} onChange={e => setIsFiled(e.target.checked)} />} label="立案" sx={{ mt: 1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>取消</Button>
          <Button variant="contained" onClick={handleSubmit}>提交线索</Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack(s => ({...s, open:false}))}>
        <Alert severity={snack.severity}>{snack.msg}</Alert>
      </Snackbar>
    </>
  );
}
