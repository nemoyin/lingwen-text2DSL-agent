import { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Checkbox, FormControlLabel, Snackbar, Alert } from '@mui/material';
import api from '../../services/api';
import type { ApiResponse } from '../../types';

const ALL_PERMS = [
  { key: 'dashboard', label: '仪表盘' }, { key: 'chat', label: '对话问数' },
  { key: 'alerts', label: '预警列表' }, { key: 'alert_create', label: '创建预警' },
  { key: 'case_manage', label: '问题线索' }, { key: 'history', label: '对话历史' },
  { key: 'profile', label: '个人中心' }, { key: 'admin', label: '管理后台' },
  { key: 'admin_datasources', label: '数据源管理' }, { key: 'admin_metadata', label: '元数据管理' },
  { key: 'admin_skills', label: 'Skill模板' }, { key: 'admin_fewshot', label: 'Few-shot' },
  { key: 'admin_roles', label: '角色管理' }, { key: 'admin_users', label: '用户管理' },
];

export default function RoleManagement() {
  const [roles, setRoles] = useState<any[]>([]);
  const [dialog, setDialog] = useState({ open: false, name: '', desc: '' });
  const [permDialog, setPermDialog] = useState({ open: false, roleId: 0, selected: [] as string[] });
  const [snack, setSnack] = useState({ open: false, msg: '', severity: 'success' as 'success' | 'error' });

  const fetch = () => api.get('/api/roles').then(r => setRoles(r.data.data || [])).catch(() => {});
  useEffect(() => { fetch(); }, []);

  const createRole = async () => {
    await api.post('/api/roles', null, { params: { name: dialog.name, description: dialog.desc } });
    fetch(); setDialog({ open: false, name: '', desc: '' });
  };

  const openPerms = (role: any) => setPermDialog({ open: true, roleId: role.id, selected: role.permissions || [] });

  const savePerms = async () => {
    await api.put(`/api/roles/${permDialog.roleId}/permissions`, null, { params: { permissions: permDialog.selected.join(',') } });
    setPermDialog({ ...permDialog, open: false }); fetch();
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={2}>
        <Typography variant="h6">角色管理</Typography>
        <Button variant="contained" size="small" onClick={() => setDialog({ open: true, name: '', desc: '' })}>新增角色</Button>
      </Box>
      <TableContainer component={Paper} variant="outlined"><Table size="small"><TableHead><TableRow>
        <TableCell>名称</TableCell><TableCell>描述</TableCell><TableCell>权限数</TableCell><TableCell>用户数</TableCell><TableCell>操作</TableCell>
      </TableRow></TableHead><TableBody>
        {roles.map(r => (
          <TableRow key={r.id}><TableCell>{r.name}</TableCell><TableCell>{r.description}</TableCell>
            <TableCell>{r.permissions?.length || 0}</TableCell><TableCell>{r.user_ids?.length || 0}</TableCell>
            <TableCell><Button size="small" onClick={() => openPerms(r)}>配置权限</Button></TableCell>
          </TableRow>
        ))}
      </TableBody></Table></TableContainer>

      <Dialog open={dialog.open} onClose={() => setDialog({...dialog,open:false})} maxWidth="xs" fullWidth>
        <DialogTitle>新增角色</DialogTitle>
        <DialogContent>
          <TextField fullWidth margin="dense" label="角色名" value={dialog.name} onChange={e => setDialog({...dialog,name:e.target.value})} />
          <TextField fullWidth margin="dense" label="描述" value={dialog.desc} onChange={e => setDialog({...dialog,desc:e.target.value})} />
        </DialogContent>
        <DialogActions><Button onClick={() => setDialog({...dialog,open:false})}>取消</Button><Button variant="contained" onClick={createRole}>创建</Button></DialogActions>
      </Dialog>

      <Dialog open={permDialog.open} onClose={() => setPermDialog({...permDialog,open:false})} maxWidth="sm" fullWidth>
        <DialogTitle>配置权限</DialogTitle>
        <DialogContent>
          {ALL_PERMS.map(p => (
            <FormControlLabel key={p.key} control={<Checkbox checked={permDialog.selected.includes(p.key)} onChange={e => {
              setPermDialog(prev => ({ ...prev, selected: e.target.checked ? [...prev.selected,p.key] : prev.selected.filter(k=>k!==p.key) }));
            }} />} label={p.label} />
          ))}
        </DialogContent>
        <DialogActions><Button onClick={() => setPermDialog({...permDialog,open:false})}>取消</Button><Button variant="contained" onClick={savePerms}>保存</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
