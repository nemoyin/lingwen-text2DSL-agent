import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Button, Box, Avatar, Menu, MenuItem,
  Dialog, DialogTitle, DialogContent, Divider,
  IconButton, Drawer, List, ListItemButton, ListItemText
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { useAuth } from '../../contexts/AuthContext';
import { usePerms } from '../../contexts/PermContext';

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { hasPerm } = usePerms();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);

  const isActive = (path: string) => location.pathname.startsWith(path);

  const navItems = [
    { path: '/dashboard', label: '仪表盘', show: true },
    { path: '/chat', label: '对话问数', show: hasPerm('chat') },
    { path: '/alerts/list', label: '预警', show: hasPerm('alerts') },
    { path: '/admin/datasources', label: '管理', show: hasPerm('admin') },
  ].filter(item => item.show);

  return (
    <Box display="flex" flexDirection="column" height="100vh" overflow="hidden">
      <AppBar position="sticky" color="inherit" elevation={0} sx={{ borderBottom: '0.5px solid', borderColor: 'divider', zIndex: 1200, bgcolor: '#fff' }}>
        <Toolbar variant="dense" sx={{ gap: 0.5 }}>
          <IconButton edge="start" onClick={() => setMobileMenu(true)} sx={{ display: { md: 'none' }, mr: 0.5 }}>
            <MenuIcon fontSize="small" />
          </IconButton>
          <Box
            sx={{ cursor: 'pointer', mr: { xs: 1, md: 2 }, display: 'flex', alignItems: 'center', gap: 1 }}
            onClick={() => navigate('/dashboard')}
          >
            <Box component="img" src="/lingwen-logo.png" alt="天府一网监" sx={{ width: 26, height: 26, borderRadius: 1 }} />
            <Typography variant="h6" fontWeight={700} fontSize={{ xs: 16, md: 18 }} sx={{ background: 'linear-gradient(90deg, #2065F5, #3478F6, #4A88FF)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              天府一网监
            </Typography>
          </Box>
          <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 0.5 }}>
            {navItems.map(item => (
              <Button
                key={item.path}
                size="small"
                variant="text"
                onClick={() => navigate(item.path)}
                sx={{
                  // '&&' doubles specificity (0-2-0) to match theme's .MuiButton-root.MuiButton-text,
                  // ensuring active white text isn't overridden by theme's color: BRAND.primary
                  '&&': isActive(item.path)
                    ? {
                        color: '#fff',
                        background: 'linear-gradient(90deg, #2065F5, #3478F6, #4A88FF)',
                        boxShadow: '0 4px 12px rgba(52,120,246,0.2)',
                        '&:hover': {
                          background: 'linear-gradient(90deg, #4A88FF, #4A88FF, #4A88FF)',
                          color: '#fff',
                          boxShadow: '0 4px 14px rgba(52,120,246,0.35)',
                        },
                      }
                    : {
                        color: '#374151',
                        background: 'transparent',
                        boxShadow: 'none',
                        '&:hover': {
                          background: 'rgba(52,120,246,0.08)',
                          color: '#3478F6',
                        },
                      },
                  borderRadius: 1.5,
                  px: 2,
                  transition: 'all 0.2s ease',
                  fontWeight: 600,
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
          <Box flex={1} />
          <Box display="flex" alignItems="center" gap={1} sx={{ cursor: 'pointer' }} onClick={e => setAnchorEl(e.currentTarget)}>
            <Avatar sx={{ width: 26, height: 26, fontSize: 12, bgcolor: '#3478F6' }}>
              {(user?.username || 'U')[0].toUpperCase()}
            </Avatar>
            <Typography variant="body2" sx={{ display: { xs: 'none', sm: 'block' }, color: '#374151' }}>{user?.username || 'User'}</Typography>
          </Box>
          <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={() => setAnchorEl(null)}>
            <MenuItem onClick={() => { setAnchorEl(null); setProfileOpen(true); }}>个人中心</MenuItem>
            <MenuItem onClick={() => { setAnchorEl(null); logout(); navigate('/login'); }}>退出登录</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Drawer anchor="left" open={mobileMenu} onClose={() => setMobileMenu(false)}>
        <Box sx={{ width: 220, pt: 1 }}>
          <Typography variant="subtitle2" fontWeight={700} px={2} py={1} sx={{ background: 'linear-gradient(90deg, #2065F5, #3478F6, #4A88FF)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            天府一网监
          </Typography>
          <Divider />
          <List dense>
            {navItems.map(item => (
              <ListItemButton key={item.path} selected={isActive(item.path)} onClick={() => { navigate(item.path); setMobileMenu(false); }}
                sx={{ '&.Mui-selected': { borderLeft: '3px solid #3478F6', background: 'rgba(52,120,246,0.06)' } }}>
                <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: 13 }} />
              </ListItemButton>
            ))}
          </List>
        </Box>
      </Drawer>

      <Box flex={1} display="flex" flexDirection="column" overflow="auto">
        <Outlet />
      </Box>

      <Dialog open={profileOpen} onClose={() => setProfileOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>个人中心</DialogTitle>
        <DialogContent>
          <Box mb={2}><Typography variant="body2" color="text.secondary">用户名</Typography><Typography variant="body1" fontWeight={500}>{user?.username || '-'}</Typography></Box>
          <Divider sx={{ my: 1.5 }} />
          <Box mb={1}><Typography variant="body2" color="text.secondary">角色</Typography><Typography variant="body1">{user?.username === 'admin' ? '管理员' : '普通用户'}</Typography></Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}
