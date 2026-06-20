import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  IconButton,
  InputAdornment,
  Link,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ChatBubbleOutlineRoundedIcon from '@mui/icons-material/ChatBubbleOutlineRounded';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import PersonOutlineRoundedIcon from '@mui/icons-material/PersonOutlineRounded';
import SecurityRoundedIcon from '@mui/icons-material/SecurityRounded';
import ShowChartRoundedIcon from '@mui/icons-material/ShowChartRounded';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import { useAuth } from '../contexts/AuthContext';

const FEATURES = [
  {
    icon: <ChatBubbleOutlineRoundedIcon />,
    title: '自然语言对话',
    desc: '像聊天一样查数据',
  },
  {
    icon: <ShowChartRoundedIcon />,
    title: '实时流式分析',
    desc: '思考过程清晰可见',
  },
  {
    icon: <SecurityRoundedIcon />,
    title: '企业级权限管控',
    desc: '数据安全无忧',
  },
];

function HeroIllustration() {
  return (
    <Box
      sx={{
        position: 'relative',
        height: { md: 250, lg: 300 },
        mt: { md: 5, lg: 7 },
        mx: 'auto',
        width: '82%',
        maxWidth: 780,
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          inset: '42% -8% auto',
          height: 140,
          borderRadius: '50%',
          background:
            'radial-gradient(ellipse at center, rgba(99,244,255,0.55) 0%, rgba(45,142,255,0.22) 34%, transparent 68%)',
          filter: 'blur(1px)',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          left: '4%',
          right: '4%',
          bottom: 20,
          height: 120,
          background:
            'repeating-radial-gradient(ellipse at center, rgba(89,240,255,0.42) 0 1px, transparent 2px 13px)',
          transform: 'perspective(520px) rotateX(63deg)',
          opacity: 0.72,
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          left: '19%',
          right: '16%',
          bottom: 92,
          height: 104,
          background:
            'linear-gradient(to top, rgba(78,216,255,0.28), transparent), repeating-linear-gradient(90deg, transparent 0 28px, rgba(138,223,255,0.24) 29px 42px, transparent 43px 56px)',
          clipPath:
            'polygon(0 100%, 0 62%, 6% 62%, 6% 43%, 12% 43%, 12% 74%, 18% 74%, 18% 54%, 24% 54%, 24% 28%, 31% 28%, 31% 100%, 36% 100%, 36% 50%, 42% 50%, 42% 66%, 49% 66%, 49% 22%, 55% 22%, 55% 100%, 62% 100%, 62% 58%, 68% 58%, 68% 38%, 74% 38%, 74% 100%, 81% 100%, 81% 70%, 88% 70%, 88% 48%, 94% 48%, 94% 100%, 100% 100%)',
          opacity: 0.58,
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          left: '10%',
          bottom: 88,
          width: 126,
          height: 72,
          border: '1px solid rgba(106,244,255,0.48)',
          borderRadius: 2,
          background: 'rgba(39,126,255,0.18)',
          boxShadow: '0 0 24px rgba(58,219,255,0.22)',
          display: { xs: 'none', md: 'block' },
          '&::before': {
            content: '""',
            position: 'absolute',
            left: 18,
            right: 18,
            top: 24,
            height: 28,
            borderBottom: '3px solid rgba(98,245,255,0.8)',
            borderLeft: '3px solid rgba(98,245,255,0.8)',
            transform: 'skew(-22deg)',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            left: 18,
            top: 14,
            width: 42,
            height: 5,
            borderRadius: 1,
            background: 'rgba(99,244,255,0.75)',
          },
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          right: '8%',
          bottom: 112,
          width: 126,
          height: 72,
          border: '1px solid rgba(193,137,255,0.45)',
          borderRadius: 2,
          background: 'rgba(130,88,255,0.20)',
          boxShadow: '0 0 28px rgba(167,88,255,0.24)',
          display: { xs: 'none', md: 'block' },
          '&::before': {
            content: '""',
            position: 'absolute',
            left: 20,
            top: 20,
            width: 36,
            height: 36,
            borderRadius: '50%',
            background: 'conic-gradient(#6bf4ff 0 32%, #9a6cff 32% 72%, rgba(255,255,255,0.22) 72% 100%)',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            right: 20,
            top: 20,
            width: 44,
            height: 28,
            borderTop: '4px solid rgba(203,221,255,0.35)',
            borderBottom: '4px solid rgba(203,221,255,0.25)',
          },
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          left: '50%',
          top: 36,
          width: { md: 166, lg: 198 },
          height: { md: 166, lg: 198 },
          transform: 'translateX(-50%)',
          borderRadius: '42% 42% 42% 12%',
          background:
            'linear-gradient(140deg, #5ff6ff 0%, #2d89ff 46%, #754dff 100%)',
          boxShadow:
            '0 28px 62px rgba(33,63,230,0.46), inset 18px 16px 30px rgba(255,255,255,0.28)',
          '&::before': {
            content: '""',
            position: 'absolute',
            inset: '24%',
            borderRadius: '50%',
            border: '8px solid rgba(255,255,255,0.88)',
            boxShadow: 'inset 0 0 20px rgba(78,235,255,0.38)',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            width: '18%',
            height: '48%',
            right: '-4%',
            bottom: '-16%',
            borderRadius: 999,
            background: 'linear-gradient(180deg, #d8f8ff, #5cdcff 48%, #6f50ff)',
            transform: 'rotate(-38deg)',
            boxShadow: '0 12px 24px rgba(34,48,162,0.34)',
          },
        }}
      >
        <Stack
          direction="row"
          spacing={0.8}
          alignItems="flex-end"
          sx={{ position: 'absolute', left: '35%', bottom: '36%', zIndex: 1 }}
        >
          {[34, 54, 78].map((height, index) => (
            <Box
              key={height}
              sx={{
                width: 14,
                height,
                borderRadius: '8px 8px 4px 4px',
                background:
                  index === 2
                    ? 'linear-gradient(180deg, #fff, #69f3ff)'
                    : 'linear-gradient(180deg, rgba(255,255,255,0.96), rgba(124,235,255,0.72))',
                boxShadow: '0 0 12px rgba(103,245,255,0.62)',
              }}
            />
          ))}
        </Stack>
      </Box>
    </Box>
  );
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password || loading) return;

    setError('');
    setLoading(true);
    try {
      await login(username, password, rememberMe);
      navigate('/chat', { replace: true });
    } catch {
      setError('登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        flexDirection: { xs: 'column', md: 'row' },
        background: '#fff',
      }}
    >
      <Box
        sx={{
          position: 'relative',
          flex: { xs: '0 0 auto', md: '1 1 68%' },
          height: { xs: 'auto', md: '100vh' },
          px: { xs: 3, md: 5, lg: 7 },
          py: { xs: 4, md: 4.5 },
          color: '#fff',
          overflow: 'hidden',
          background:
            'radial-gradient(circle at 18% 18%, rgba(95,244,255,0.28) 0, transparent 28%), radial-gradient(circle at 78% 74%, rgba(205,83,255,0.34) 0, transparent 30%), linear-gradient(138deg, #2065F5 0%, #3478F6 45%, #4A88FF 100%)',
          '&::before': {
            content: '""',
            position: 'absolute',
            inset: 0,
            background:
              'linear-gradient(18deg, rgba(74,235,255,0.38) 0 1px, transparent 1px 54%), linear-gradient(156deg, transparent 0 56%, rgba(255,255,255,0.18) 57%, transparent 58%), linear-gradient(24deg, transparent 0 62%, rgba(107,244,255,0.34) 63%, transparent 64%)',
            opacity: 0.45,
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            left: '-10%',
            right: '-8%',
            bottom: 26,
            height: 180,
            background:
              'radial-gradient(ellipse at 50% 70%, rgba(106,244,255,0.34), transparent 56%), repeating-linear-gradient(170deg, rgba(111,245,255,0.34) 0 2px, transparent 3px 16px)',
            transform: 'skewY(-4deg)',
            opacity: 0.68,
          },
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Stack direction="row" alignItems="center" spacing={1.6}>
            <Box
              component="img"
              src="/lingwen-logo.png"
              alt="天府一网监"
              sx={{ width: 48, height: 48, borderRadius: 2, boxShadow: '0 10px 28px rgba(13,34,154,0.24)' }}
            />
            <Box>
              <Typography sx={{ fontSize: 18, fontWeight: 800, letterSpacing: 1.5 }}>
                天府一网监 · 智能问数
              </Typography>
              <Typography sx={{ fontSize: 12, letterSpacing: 6, opacity: 0.86 }}>
                让数据开口说话
              </Typography>
            </Box>
          </Stack>

          <Box sx={{ pt: { xs: 6, md: 9, lg: 10 }, textAlign: 'center' }}>
            <Typography
              component="h1"
              sx={{
                fontSize: { xs: 40, md: 50, lg: 64 },
                fontWeight: 900,
                letterSpacing: { xs: 1.5, md: 5 },
                lineHeight: 1.1,
                textShadow: '0 12px 34px rgba(22,22,116,0.26)',
              }}
            >
              <Box
                component="span"
                sx={{
                  color: '#67f5ff',
                  textShadow: '0 0 26px rgba(103,245,255,0.45)',
                }}
              >
                天府一网监
              </Box>
              <Box component="span" sx={{ mx: { xs: 1.6, md: 2.2 } }}>
                ·
              </Box>
              智能问数引擎
            </Typography>
            <Typography
              sx={{
                mt: 2.4,
                fontSize: { xs: 22, md: 30, lg: 34 },
                fontWeight: 300,
                letterSpacing: { xs: 7, md: 12 },
                opacity: 0.95,
              }}
            >
              — 让数据开口说话 —
            </Typography>

            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={{ xs: 2, md: 6, lg: 9 }}
              justifyContent="center"
              alignItems={{ xs: 'center', sm: 'flex-start' }}
              sx={{ mt: { xs: 5, md: 5.5 } }}
            >
              {FEATURES.map((feature) => (
                <Stack key={feature.title} direction="row" spacing={1.4} alignItems="flex-start">
                  <Box
                    sx={{
                      color: '#72f3ff',
                      fontSize: 31,
                      lineHeight: 1,
                      filter: 'drop-shadow(0 0 12px rgba(114,243,255,0.5))',
                      '& svg': { fontSize: 31 },
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Box sx={{ textAlign: 'left' }}>
                    <Typography sx={{ fontSize: 16, fontWeight: 800 }}>{feature.title}</Typography>
                    <Typography sx={{ mt: 0.3, fontSize: 14, color: alpha('#fff', 0.72) }}>
                      {feature.desc}
                    </Typography>
                  </Box>
                </Stack>
              ))}
            </Stack>

            {!isMobile && <HeroIllustration />}
          </Box>
        </Box>
      </Box>

      <Box
        sx={{
          position: 'relative',
          flex: { xs: '1 1 auto', md: '0 0 36%' },
          minWidth: { md: 440, lg: 500 },
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          px: { xs: 3, md: 5.5, lg: 7 },
          py: { xs: 5, md: 4 },
          ml: { md: -10, lg: -12 },
          background: '#fff',
          clipPath: { xs: 'none', md: 'polygon(15% 0, 100% 0, 100% 100%, 0 100%)' },
          boxShadow: { md: '-32px 0 70px rgba(26,33,97,0.08)' },
        }}
      >
        <Box sx={{ width: '100%', maxWidth: 372, ml: { md: 6, lg: 7 } }}>
          <Box sx={{ mb: 4.6, textAlign: 'center' }}>
            <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.7} sx={{ mb: 1.4 }}>
              <AutoAwesomeIcon sx={{ color: '#3478F6', fontSize: 22 }} />
              <Typography sx={{ fontSize: 24, fontWeight: 900, color: '#1F2937', letterSpacing: 1 }}>
                天府一网监
              </Typography>
            </Stack>
            <Typography sx={{ color: '#6B7280', fontSize: 14 }}>
              智能问数引擎 · 用对话方式探索数据
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2.2, borderRadius: 1.5 }}>
              {error}
            </Alert>
          )}

          <Stack spacing={1.6}>
            <TextField
              fullWidth
              placeholder="用户名"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && handleLogin()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonOutlineRoundedIcon sx={{ color: '#a7acb5', fontSize: 22 }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  height: 52,
                  borderRadius: 1,
                  background: '#fff',
                  '& fieldset': { borderColor: '#e5e7eb' },
                  '&:hover fieldset': { borderColor: '#bfc8d8' },
                  '&.Mui-focused fieldset': { borderColor: '#3478F6', boxShadow: '0 0 0 3px rgba(52,120,246,0.10)' },
                },
              }}
            />

            <TextField
              fullWidth
              placeholder="密码"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && handleLogin()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockOutlinedIcon sx={{ color: '#a7acb5', fontSize: 22 }} />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? '隐藏密码' : '显示密码'}
                      edge="end"
                      size="small"
                      tabIndex={-1}
                      onClick={() => setShowPassword((value) => !value)}
                      sx={{ color: '#9aa3ad' }}
                    >
                      {showPassword ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  height: 52,
                  borderRadius: 1,
                  background: '#fff',
                  '& fieldset': { borderColor: '#e5e7eb' },
                  '&:hover fieldset': { borderColor: '#bfc8d8' },
                  '&.Mui-focused fieldset': { borderColor: '#3478F6', boxShadow: '0 0 0 3px rgba(52,120,246,0.10)' },
                },
              }}
            />
          </Stack>

          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mt: 1.7, mb: 2.5 }}>
            <FormControlLabel
              control={
                <Checkbox
                  size="small"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  sx={{
                    p: 0.5,
                    color: '#d2d6df',
                    '&.Mui-checked': { color: '#3478F6' },
                  }}
                />
              }
              label={<Typography sx={{ color: '#374151', fontSize: 14 }}>记住我</Typography>}
              sx={{ m: 0 }}
            />
            <Link href="#" underline="none" sx={{ color: '#3478F6', fontSize: 14 }}>
              忘记密码?
            </Link>
          </Stack>

          <Button
            fullWidth
            variant="contained"
            size="large"
            onClick={handleLogin}
            disabled={loading || !username || !password}
            sx={{
              height: 52,
              borderRadius: 1,
              fontSize: 16,
              fontWeight: 700,
              letterSpacing: 10,
              textIndent: 10,
              color: '#fff',
              background: '#3478F6',
              boxShadow: '0 12px 24px rgba(52,120,246,0.22)',
              '&:hover': {
                background: '#4A88FF',
                boxShadow: '0 14px 28px rgba(52,120,246,0.30)',
              },
              '&.Mui-disabled': {
                color: alpha('#fff', 0.72),
                background: '#8da5f4',
              },
            }}
          >
            {loading ? '登录中' : '登录'}
          </Button>

          <Typography
            sx={{
              position: { xs: 'static', md: 'fixed' },
              right: { md: 84 },
              bottom: { md: 34 },
              mt: { xs: 8, md: 0 },
              textAlign: 'center',
              color: '#c2c6cf',
              fontSize: 13,
            }}
          >
            ✚ 数据驱动决策 · 智能创造价值
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
