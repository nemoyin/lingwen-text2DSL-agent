import { useState, useEffect } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, MenuItem, Snackbar, Alert } from '@mui/material';
import { getToken } from '../../services/api';

const CITIES = [
  '成都市纪委监委', '自贡市纪委监委', '攀枝花市纪委监委', '泸州市纪委监委',
  '德阳市纪委监委', '绵阳市纪委监委', '广元市纪委监委', '遂宁市纪委监委',
  '内江市纪委监委', '乐山市纪委监委', '南充市纪委监委', '眉山市纪委监委',
  '宜宾市纪委监委', '广安市纪委监委', '达州市纪委监委', '雅安市纪委监委',
  '巴中市纪委监委', '资阳市纪委监委', '阿坝州纪委监委', '甘孜州纪委监委',
  '凉山州纪委监委',
];

interface Props {
  open: boolean;
  onClose: () => void;
  initialContent: string;
}

export default function AlertDialog({ open, onClose, initialContent }: Props) {
  const [targetUnit, setTargetUnit] = useState('');
  const [content, setContent] = useState('');
  const [snack, setSnack] = useState({ open: false, msg: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => {
    if (open) {
      setContent(initialContent);
      setTargetUnit('');
    }
  }, [open, initialContent]);

  const handleSubmit = async () => {
    try {
      const token = getToken();
      const params = new URLSearchParams({ target_unit: targetUnit, content });
      const resp = await fetch(`/api/alerts?${params}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      const data = await resp.json();
      if (data.code === 200) {
        setSnack({ open: true, msg: '预警已创建', severity: 'success' });
        setTimeout(() => onClose(), 1000);
      } else setSnack({ open: true, msg: '创建失败', severity: 'error' });
    } catch { setSnack({ open: true, msg: '网络错误', severity: 'error' }); }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>一键转预警</DialogTitle>
        <DialogContent>
          <TextField select fullWidth margin="dense" label="被预警单位（市州纪委）" value={targetUnit} onChange={e => setTargetUnit(e.target.value)} required>
            {CITIES.map(c => <MenuItem key={c} value={c}>{c}</MenuItem>)}
          </TextField>
          <TextField fullWidth margin="dense" label="预警内容" value={content} onChange={e => setContent(e.target.value)} multiline rows={6} required />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>取消</Button>
          <Button variant="contained" onClick={handleSubmit} disabled={!targetUnit}>提交预警</Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={snack.open} autoHideDuration={3000} onClose={() => setSnack(s => ({...s, open:false}))}>
        <Alert severity={snack.severity}>{snack.msg}</Alert>
      </Snackbar>
    </>
  );
}
