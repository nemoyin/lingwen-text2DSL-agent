import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="60vh">
      <Box
        component="img"
        src="/lingwen-logo.png"
        alt="天府一网监"
        sx={{ width: 80, height: 80, mb: 2, borderRadius: 2, opacity: 0.4 }}
      />
      <Typography variant="h2" fontWeight={800} sx={{ background: 'linear-gradient(90deg, #2065F5, #4A88FF)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
        404
      </Typography>
      <Typography variant="body1" color="#6B7280" mb={3}>页面未找到</Typography>
      <Button variant="contained" onClick={() => navigate('/chat')}>返回首页</Button>
    </Box>
  );
}
