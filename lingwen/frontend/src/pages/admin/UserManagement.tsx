import { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, Dialog, DialogTitle, DialogContent, DialogActions, Chip, Checkbox, FormControlLabel, TextField } from '@mui/material';
import api from '../../services/api';
import type { ApiResponse } from '../../types';

export default function UserManagement() {
  const [users, setUsers] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [dialog, setDialog] = useState({ open: false, userId: 0, selected: [] as number[] });
  const [createDialog, setCreateDialog] = useState({ open: false, username: '', password: '', role: 'viewer' });

  const fetch = () => {
    api.get<ApiResponse<any[]>>('/api/users').then(r => setUsers(r.data.data || [])).catch(() => {});
    api.get<ApiResponse<any[]>>('/api/roles').then(r => setRoles(r.data.data || [])).catch(() => {});
  };
  useEffect(() => { fetch(); }, []);

  const openRoles = (u: any) => setDialog({ open: true, userId: u.id, selected: (u.roles || []).map((r: any) => r.id) });

  const saveRoles = async () => {
    await api.put(`/api/users/${dialog.userId}/roles`, null, { params: { role_ids: dialog.selected.join(',') } });
    setDialog({ ...dialog, open: false }); fetch();
  };

  const resetPassword = async (userId: number) => {
    await api.put(`/api/users/${userId}/reset-password`);
    alert('密码已重置为 123456');
  };
  const createUser = async () => {
    try {
      const resp = await api.post('/api/users', null, { params: { username: createDialog.username, password: createDialog.password, role_name: createDialog.role } });
      if (resp.data.code === 200) { setCreateDialog({ open: false, username: '', password: '', role: 'viewer' }); fetch(); }
    } catch { alert('创建失败，用户名可能已存在'); }
  };

  return (
    <Box>
      <Typography variant="h6" mb={2}>用户管理</Typography>
      <Box display="flex" gap={1} mb={2}>
        <Button variant="contained" size="small" onClick={() => setCreateDialog({ open: true, username: '', password: '', role: 'viewer' })}>新增用户</Button>
      </Box>
      <TableContainer component={Paper} variant="outlined"><Table size="small"><TableHead><TableRow>
        <TableCell>用户名</TableCell><TableCell>角色</TableCell><TableCell>状态</TableCell><TableCell>操作</TableCell>
      </TableRow></TableHead><TableBody>
        {users.map(u => (
          <TableRow key={u.id}><TableCell>{u.username}</TableCell>
            <TableCell>{(u.roles || []).map((r: any) => <Chip key={r.id} label={r.name} size="small" sx={{mr:0.5}} />)}</TableCell>
            <TableCell><Chip size="small" label={u.is_active ? '激活' : '禁用'} color={u.is_active ? 'success' : 'default'} variant="outlined" /></TableCell>
            <TableCell><Button size="small" onClick={() => openRoles(u)}>分配角色</Button><Button size="small" onClick={() => resetPassword(u.id)} sx={{ml:1}}>重置密码</Button></TableCell>
          </TableRow>
        ))}
      </TableBody></Table></TableContainer>

      <Dialog open={dialog.open} onClose={() => setDialog({...dialog,open:false})} maxWidth="xs" fullWidth>
        <DialogTitle>分配角色</DialogTitle>
        <DialogContent>
          {roles.map(r => (
            <FormControlLabel key={r.id} control={<Checkbox checked={dialog.selected.includes(r.id)} onChange={e => {
              setDialog(prev => ({ ...prev, selected: e.target.checked ? [...prev.selected,r.id] : prev.selected.filter(i=>i!==r.id) }));
            }} />} label={`${r.name} - ${r.description || ''}`} />
          ))}
        </DialogContent>
        <DialogActions><Button onClick={() => setDialog({...dialog,open:false})}>取消</Button><Button variant="contained" onClick={saveRoles}>保存</Button></DialogActions>
      </Dialog>

      <Dialog open={createDialog.open} onClose={() => setCreateDialog({...createDialog,open:false})} maxWidth="xs" fullWidth>
        <DialogTitle>新增用户</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="dense" label="用户名" value={createDialog.username} onChange={e => setCreateDialog({...createDialog,username:e.target.value})} />
          <TextField fullWidth margin="dense" label="密码" type="password" value={createDialog.password} onChange={e => setCreateDialog({...createDialog,password:e.target.value})} />
        </DialogContent>
        <DialogActions><Button onClick={() => setCreateDialog({...createDialog,open:false})}>取消</Button><Button variant="contained" onClick={createUser}>创建</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
