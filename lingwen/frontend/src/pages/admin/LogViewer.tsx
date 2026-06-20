import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box, Typography, Button, ToggleButtonGroup, ToggleButton,
  Paper, Stack, Switch, FormControlLabel, Chip,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import { getToken } from '../../services/api';

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: '#90a4ae',
  INFO: '#81c784',
  WARNING: '#ffb74d',
  ERROR: '#e57373',
  CRITICAL: '#d32f2f',
};

const LEVEL_ORDER = ['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

function LogLine({ entry }: { entry: { level: string; message: string; timestamp: string | null } }) {
  const color = LEVEL_COLORS[entry.level] || '#90a4ae';
  return (
    <Box
      sx={{
        fontFamily: '"Cascadia Code", "Fira Code", "JetBrains Mono", monospace',
        fontSize: 11,
        lineHeight: 1.6,
        py: 0.25,
        px: 1,
        borderBottom: '0.5px solid',
        borderColor: 'divider',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-all',
        '&:hover': { bgcolor: 'action.hover' },
      }}
    >
      {entry.timestamp && (
        <Box component="span" sx={{ color: '#78909c', mr: 1 }}>{entry.timestamp}</Box>
      )}
      <Chip
        label={entry.level}
        size="small"
        sx={{
          height: 16,
          fontSize: 9,
          fontWeight: 700,
          mr: 1,
          bgcolor: color,
          color: '#fff',
          minWidth: 52,
          '& .MuiChip-label': { px: 0.5 },
        }}
      />
      <span style={{ color: '#b0bec5' }}>{entry.message}</span>
    </Box>
  );
}

export default function LogViewer() {
  const [entries, setEntries] = useState<any[]>([]);
  const [level, setLevel] = useState<string>('ALL');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [totalLines, setTotalLines] = useState(0);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const token = getToken();
      const params = new URLSearchParams({ lines: '300' });
      if (level !== 'ALL') params.set('level', level);

      const [logRes, cntRes] = await Promise.all([
        fetch(`/api/logs?${params}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch('/api/logs/levels', { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      if (logRes.ok) {
        const data = await logRes.json();
        setEntries(data.data?.entries || []);
        setTotalLines(data.data?.total_lines || 0);
      }
      if (cntRes.ok) {
        const cntData = await cntRes.json();
        setCounts(cntData.data?.counts || {});
      }
    } catch { /* ignore */ }
  }, [level]);

  // Initial fetch
  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      timerRef.current = setInterval(fetchLogs, 3000);
    } else {
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [autoRefresh, fetchLogs]);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, gap: 1.5 }}>
      {/* Header with brand underline */}
      <Box sx={{ pb: 1, borderBottom: '3px solid', borderImage: 'linear-gradient(90deg, #2065F5, #4A88FF) 1' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
          <Typography variant="h6" fontWeight={700} color="#1F2937">日志查看</Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography variant="caption" color="text.secondary">
            {totalLines.toLocaleString()} 行
          </Typography>
          <FormControlLabel
            control={
              <Switch size="small" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
            }
            label={
              <Stack direction="row" spacing={0.5} alignItems="center">
                {autoRefresh ? <PauseIcon sx={{ fontSize: 14 }} /> : <PlayArrowIcon sx={{ fontSize: 14 }} />}
                <Typography variant="caption">{autoRefresh ? '暂停' : '自动刷新'}</Typography>
              </Stack>
            }
          />
          <Button size="small" variant="outlined" onClick={fetchLogs}>刷新</Button>
        </Stack>
      </Box>
      </Box>
      {/* ─── brand underline closes above ─── */}

      {/* Level filter + counts */}
      <Box>
        <ToggleButtonGroup
          size="small"
          value={level}
          exclusive
          onChange={(_, v) => v && setLevel(v)}
          sx={{ flexWrap: 'wrap' }}
        >
          {LEVEL_ORDER.map((lvl) => (
            <ToggleButton key={lvl} value={lvl} sx={{ px: 1.5, py: 0.25 }}>
              <Stack direction="row" spacing={0.5} alignItems="center">
                {lvl !== 'ALL' && (
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: LEVEL_COLORS[lvl] || '#78909c' }} />
                )}
                <Typography variant="caption" fontSize={11}>{lvl}</Typography>
                <Typography variant="caption" color="text.secondary" fontSize={10}>
                  {lvl === 'ALL'
                    ? Object.values(counts).reduce((a, b) => a + b, 0)
                    : counts[lvl] || 0}
                </Typography>
              </Stack>
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      {/* Log content */}
      <Paper
        ref={containerRef}
        variant="outlined"
        sx={{
          flex: 1,
          overflow: 'auto',
          bgcolor: '#1a1a2e',
          borderRadius: 1,
          minHeight: 0,
        }}
      >
        {entries.length === 0 ? (
          <Box p={4} textAlign="center">
            <Typography color="text.secondary" variant="body2">暂无日志</Typography>
          </Box>
        ) : (
          entries.map((entry, i) => <LogLine key={i} entry={entry} />)
        )}
      </Paper>
    </Box>
  );
}
