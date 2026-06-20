import { Box, Card, Typography, Button, Divider } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const { language, setLanguage, t } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login', { replace: true }); };

  return (
    <Box maxWidth={480} mx="auto" mt={4} px={2}>
      <Box sx={{ mb: 3, pb: 1, borderBottom: '3px solid', borderImage: 'linear-gradient(90deg, #2065F5, #4A88FF) 1' }}>
        <Typography variant="h5" fontWeight={700} color="#1F2937">{t('个人中心', 'Profile')}</Typography>
      </Box>
      <Card sx={{ p: 3, mb: 2 }}>
        <Typography variant="body2" color="#6B7280" mb={0.5}>{t('用户名', 'Username')}</Typography>
        <Typography variant="body1" fontWeight={600} color="#1F2937" mb={2}>{user?.username || '-'}</Typography>
        <Divider sx={{ my: 1.5 }} />
        <Typography variant="body2" color="#6B7280" mb={0.5}>{t('角色', 'Role')}</Typography>
        <Typography variant="body1" fontWeight={600} color="#1F2937" mb={2}>{user?.username === 'admin' ? t('管理员', 'Admin') : t('普通用户', 'User')}</Typography>
      </Card>

      <Card sx={{ p: 3, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} mb={2}>{t('页面设置', 'Display Settings')}</Typography>
        <Box mt={1}>
          <Typography variant="body2" color="#6B7280" mb={0.5}>{t('语言', 'Language')}</Typography>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value as 'zh' | 'en')}
            style={{ padding: '8px 12px', borderRadius: 4, border: '1px solid #e5e7eb', fontSize: 14, minWidth: 120 }}
          >
            <option value="zh">中文</option>
            <option value="en">English</option>
          </select>
        </Box>
      </Card>

      <Button variant="outlined" color="error" fullWidth onClick={handleLogout}>
        {t('退出登录', 'Logout')}
      </Button>
    </Box>
  );
}
