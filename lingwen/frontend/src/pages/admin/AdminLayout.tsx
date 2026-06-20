import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import SchemaIcon from '@mui/icons-material/Schema';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import StyleIcon from '@mui/icons-material/Style';
import MenuIcon from '@mui/icons-material/Menu';
import SecurityIcon from '@mui/icons-material/Security';
import GroupIcon from '@mui/icons-material/Group';
import AssessmentIcon from '@mui/icons-material/Assessment';
import TerminalIcon from '@mui/icons-material/Terminal';
import { useAuth } from '../../contexts/AuthContext';

const DRAWER_WIDTH = 220;

const NAV_ITEMS = [
  { path: '/admin/datasources', label: '数据源管理', icon: <StorageIcon /> },
  { path: '/admin/metadata', label: '元数据管理', icon: <SchemaIcon /> },
  { path: '/admin/skills', label: 'Skill 模板', icon: <AutoAwesomeIcon /> },
  { path: '/admin/few-shot', label: 'Few-shot 示例', icon: <StyleIcon /> },
  { path: '/admin/roles', label: '角色管理', icon: <SecurityIcon /> },
  { path: '/admin/users', label: '用户管理', icon: <GroupIcon /> },
  { path: '/admin/benchmark', label: 'Agent 测评', icon: <AssessmentIcon /> },
  { path: '/admin/models', label: '模型管理', icon: <AutoAwesomeIcon /> },
  { path: '/admin/logs', label: '日志查看', icon: <TerminalIcon /> },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) navigate('/login', { replace: true });
  }, [isAuthenticated, navigate]);
  const [mobileOpen, setMobileOpen] = useState(false);

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ p: 2.5, borderBottom: '0.5px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer' }} onClick={() => navigate('/dashboard')}>
          <Box component="img" src="/lingwen-logo.png" alt="天府一网监" sx={{ width: 24, height: 24, borderRadius: 1 }} />
          <Typography variant="subtitle1" fontWeight={700} sx={{ background: 'linear-gradient(90deg, #2065F5, #3478F6, #4A88FF)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            天府一网监管理后台
          </Typography>
        </Box>
      </Box>
      <List dense sx={{ flex: 1, pt: 1 }}>
        {NAV_ITEMS.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path}
            onClick={() => { navigate(item.path); setMobileOpen(false); }}
            sx={{
              mx: 1,
              borderRadius: 1,
              mb: 0.25,
              '&.Mui-selected': {
                background: 'rgba(52,120,246,0.08)',
                borderLeft: '3px solid #3478F6',
                '& .MuiListItemIcon-root': { color: '#3478F6' },
              },
              '&:hover': { background: 'rgba(52,120,246,0.04)' },
            }}
          >
            <ListItemIcon sx={{ minWidth: 34, color: '#6B7280' }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: 13 }} />
          </ListItemButton>
        ))}
      </List>
      <Box sx={{ p: 2, borderTop: '0.5px solid', borderColor: 'divider' }}>
        <Typography variant="caption" color="#6B7280" display="block">天府一网监 v0.1.0</Typography>
      </Box>
    </Box>
  );

  return (
    <Box display="flex" minHeight="100vh">
      <AppBar position="fixed" sx={{ width: { md: `calc(100% - ${DRAWER_WIDTH}px)` }, ml: { md: `${DRAWER_WIDTH}px` } }} color="inherit" elevation={0}>
        <Toolbar variant="dense" sx={{ borderBottom: '0.5px solid', borderColor: 'divider', bgcolor: '#fff' }}>
          <IconButton edge="start" sx={{ mr: 2, display: { md: 'none' } }} onClick={() => setMobileOpen(!mobileOpen)}>
            <MenuIcon />
          </IconButton>
          <Typography variant="body2" sx={{ flexGrow: 1 }}>
            <a href="/chat" style={{ color: '#3478F6', textDecoration: 'none', fontWeight: 500 }}>← 返回对话</a>
          </Typography>
          <Typography variant="body2" color="#374151" sx={{ cursor: 'pointer' }} onClick={logout}>
            退出
          </Typography>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)}
          sx={{ display: { xs: 'block', md: 'none' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}>
          {drawer}
        </Drawer>
        <Drawer variant="permanent" sx={{ display: { xs: 'none', md: 'block' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, borderRight: '0.5px solid', borderColor: 'divider' } }} open>
          {drawer}
        </Drawer>
      </Box>

      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 6, bgcolor: '#f8f9fa', minHeight: 'calc(100vh - 48px)' }}>
        <Outlet />
      </Box>
    </Box>
  );
}
