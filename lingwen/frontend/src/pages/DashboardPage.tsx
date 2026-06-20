import { useState, useEffect, useRef } from 'react';
import { Box, Card, Typography, Grid2, ToggleButtonGroup, ToggleButton } from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import PeopleIcon from '@mui/icons-material/People';
import WarningIcon from '@mui/icons-material/Warning';
import GavelIcon from '@mui/icons-material/Gavel';
import TodayIcon from '@mui/icons-material/Today';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import TimerIcon from '@mui/icons-material/Timer';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ShareIcon from '@mui/icons-material/Share';
import api from '../services/api';
import type { ApiResponse } from '../types';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

/* ---- Types ---- */

interface StatsData {
  users: number; datasources: number; queries: number; tables: number;
  fewshots: number; today_queries: number; alerts: number; cases: number; filed_cases: number;
}

interface TokenInfo {
  total: number; avg_per_query: number; max_per_query: number; total_queries: number;
}
interface TokenTrend { date: string; tokens: number; queries: number; avg_tokens: number; }
interface LatencyInfo { min_ms: number; max_ms: number; avg_ms: number; }
interface LatencyTrend { date: string; min_ms: number; max_ms: number; avg_ms: number; }
interface PipelineInfo { avg_step_ms: number; avg_step_count: number; }
interface InteractionInfo { likes: number; dislikes: number; shares: number; }
interface PerformanceData {
  tokens: TokenInfo;
  token_trend: TokenTrend[];
  latency: LatencyInfo;
  latency_trend: LatencyTrend[];
  pipeline: PipelineInfo;
  interactions: InteractionInfo;
}

/* ---- Helpers ---- */

function formatMs(ms: number): string {
  if (ms <= 0) return '--';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

/* ================================================================
 * DashboardPage
 * ================================================================ */
export default function DashboardPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [trends, setTrends] = useState<{ date: string; count: number }[]>([]);
  const [perf, setPerf] = useState<PerformanceData | null>(null);
  const [range, setRange] = useState(30);

  /* ---- Refs for canvas-based charts ---- */
  const lineRef = useRef<HTMLCanvasElement>(null);
  const pieRef = useRef<HTMLCanvasElement>(null);
  const tokenTrendRef = useRef<HTMLCanvasElement>(null);
  const latencyTrendRef = useRef<HTMLCanvasElement>(null);
  const lineChart = useRef<Chart | null>(null);
  const pieChart = useRef<Chart | null>(null);
  const tokenTrackChart = useRef<Chart | null>(null);
  const latencyTrackChart = useRef<Chart | null>(null);

  /* ---- Fetch data ---- */
  useEffect(() => {
    api.get<ApiResponse<StatsData>>('/api/stats').then(r => setStats(r.data.data || null)).catch(() => { });
    api.get<ApiResponse<{ date: string; count: number }[]>>('/api/stats/trends').then(r => setTrends(r.data.data || [])).catch(() => { });
    api.get<ApiResponse<PerformanceData>>('/api/stats/performance').then(r => setPerf(r.data.data || null)).catch(() => { });
  }, []);

  /* ---- Query trend chart ---- */
  useEffect(() => {
    if (!lineRef.current || trends.length === 0) return;
    if (lineChart.current) lineChart.current.destroy();
    lineChart.current = new Chart(lineRef.current, {
      type: 'line',
      data: {
        labels: trends.map(t => t.date.slice(5)),
        datasets: [{
          label: '对话次数', data: trends.map(t => t.count),
          borderColor: '#3478F6', backgroundColor: 'rgba(52,120,246,0.1)',
          fill: true, tension: 0.3, pointRadius: 2, borderWidth: 2,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { ticks: { maxTicksLimit: 10 } }, y: { beginAtZero: true, ticks: { stepSize: 1 } } },
      },
    });
    return () => { lineChart.current?.destroy(); };
  }, [trends]);

  /* ---- Pie chart ---- */
  useEffect(() => {
    if (!pieRef.current) return;
    if (pieChart.current) pieChart.current.destroy();
    const s = stats || { alerts: 0, cases: 0, filed_cases: 0, queries: 0 };
    pieChart.current = new Chart(pieRef.current, {
      type: 'doughnut',
      data: {
        labels: ['预警', '线索', '已立案'],
        datasets: [{
          data: [s.alerts, s.cases, s.filed_cases],
          backgroundColor: ['#3478F6', '#4A88FF', '#2065F5'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12, font: { size: 11 } } } },
      },
    });
    return () => { pieChart.current?.destroy(); };
  }, [stats]);

  /* ---- Token daily trend chart ---- */
  useEffect(() => {
    if (!tokenTrendRef.current || !perf?.token_trend?.length) return;
    if (tokenTrackChart.current) tokenTrackChart.current.destroy();
    const tt = perf.token_trend;
    tokenTrackChart.current = new Chart(tokenTrendRef.current, {
      type: 'line',
      data: {
        labels: tt.map(t => t.date.slice(5)),
        datasets: [
          {
            label: '日均 Token', data: tt.map(t => t.avg_tokens),
            borderColor: '#22C55E', backgroundColor: 'rgba(34,197,94,0.08)',
            fill: true, tension: 0.3, pointRadius: 2, borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { ticks: { maxTicksLimit: 10 } }, y: { beginAtZero: true } },
      },
    });
    return () => { tokenTrackChart.current?.destroy(); };
  }, [perf]);

  /* ---- Latency daily trend chart ---- */
  useEffect(() => {
    if (!latencyTrendRef.current || !perf?.latency_trend?.length) return;
    if (latencyTrackChart.current) latencyTrackChart.current.destroy();
    const lt = perf.latency_trend;
    latencyTrackChart.current = new Chart(latencyTrendRef.current, {
      type: 'bar',
      data: {
        labels: lt.map(t => t.date.slice(5)),
        datasets: [
          {
            label: '平均耗时(ms)', data: lt.map(t => t.avg_ms),
            backgroundColor: 'rgba(52,120,246,0.6)', borderColor: '#3478F6', borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { ticks: { maxTicksLimit: 14 } }, y: { beginAtZero: true } },
      },
    });
    return () => { latencyTrackChart.current?.destroy(); };
  }, [perf]);

  /* ---- KPI card definitions ---- */
  const cards1 = [
    { label: '数据源', value: stats?.datasources || 0, icon: <StorageIcon />, color: '#3478F6' },
    { label: '总对话数', value: stats?.queries || 0, icon: <QuestionAnswerIcon />, color: '#3478F6' },
    { label: '今日对话', value: stats?.today_queries || 0, icon: <TodayIcon />, color: '#4A88FF' },
    { label: '用户数', value: stats?.users || 0, icon: <PeopleIcon />, color: '#2065F5' },
  ];
  const cards2 = [
    { label: '预警数', value: stats?.alerts || 0, icon: <WarningIcon />, color: '#ef5350' },
    { label: '线索数', value: stats?.cases || 0, icon: <GavelIcon />, color: '#ed6c02' },
    { label: '已立案', value: stats?.filed_cases || 0, icon: <GavelIcon />, color: '#1b5e20' },
  ];

  return (
    <Box sx={{ width: '100%', px: 3, py: 2, height: '100%', overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      {/* ---- Row 1: 7 KPI cards ---- */}
      <Grid2 container spacing={1.5}>
        {[...cards1, ...cards2].map(card => (
          <Grid2 size={{ xs: 6, sm: 4, md: 12/7 }} key={card.label}>
            <KpiCard {...card} />
          </Grid2>
        ))}
      </Grid2>

      {/* ---- Row 3: 对话趋势 + 预警分布 ---- */}
      <Grid2 container spacing={1.5} flex={1}>
        <Grid2 size={{ xs: 12, md: 8 }}>
          <Card sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" fontWeight={600} color="#1F2937">对话趋势</Typography>
              <ToggleButtonGroup size="small" value={range} exclusive onChange={(_, v) => v && setRange(v)}>
                <ToggleButton value={7} sx={{ fontSize: 11, px: 1 }}>7天</ToggleButton>
                <ToggleButton value={30} sx={{ fontSize: 11, px: 1 }}>30天</ToggleButton>
              </ToggleButtonGroup>
            </Box>
            <Box flex={1} minHeight={0}><canvas ref={lineRef} /></Box>
          </Card>
        </Grid2>
        <Grid2 size={{ xs: 12, md: 4 }}>
          <Card sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="body2" fontWeight={600} color="#1F2937" mb={1}>预警分布</Typography>
            <Box flex={1} minHeight={0}><canvas ref={pieRef} /></Box>
          </Card>
        </Grid2>
      </Grid2>

      {/* ---- Row 4: 性能指标 ---- */}
      {perf && (
        <>
          <Typography variant="body1" fontWeight={600} color="#1F2937" sx={{ mt: 0 }}>
            系统性能
          </Typography>

          {/* Token + Latency stats side by side */}
          <Grid2 container spacing={1.5}>
            <Grid2 size={{ xs: 12, md: 6 }}>
              <Card sx={{ p: 1.5 }}>
                <Typography variant="body2" fontWeight={600} color="#1F2937" mb={1}>Token 消耗</Typography>
                <Box display="flex" justifyContent="space-around">
                  <Box textAlign="center">
                    <DataUsageIcon sx={{ color: '#22C55E', fontSize: 20 }} />
                    <Typography variant="body2" fontWeight={700}>{formatTokens(perf.tokens.total)}</Typography>
                    <Typography variant="caption" color="#6B7280">总消耗</Typography>
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="body2" fontWeight={700}>{formatTokens(perf.tokens.avg_per_query)}</Typography>
                    <Typography variant="caption" color="#6B7280">均/问题</Typography>
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="body2" fontWeight={700}>{formatTokens(perf.tokens.max_per_query)}</Typography>
                    <Typography variant="caption" color="#6B7280">单次最大</Typography>
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="body2" fontWeight={700}>{perf.tokens.total_queries}</Typography>
                    <Typography variant="caption" color="#6B7280">完成查询</Typography>
                  </Box>
                </Box>
              </Card>
            </Grid2>

            <Grid2 size={{ xs: 12, md: 6 }}>
              <Card sx={{ p: 1.5 }}>
                <Typography variant="body2" fontWeight={600} color="#1F2937" mb={1}>响应耗时 / 管线</Typography>
                <Box display="flex" justifyContent="space-around">
                  <Box textAlign="center">
                    <TimerIcon sx={{ color: '#22C55E', fontSize: 20 }} />
                    <Typography variant="body2" fontWeight={700}>{formatMs(perf.latency.min_ms)}</Typography>
                    <Typography variant="caption" color="#6B7280">最快</Typography>
                  </Box>
                  <Box textAlign="center">
                    <TimerIcon sx={{ color: '#FF9F43', fontSize: 20 }} />
                    <Typography variant="body2" fontWeight={700}>{formatMs(perf.latency.avg_ms)}</Typography>
                    <Typography variant="caption" color="#6B7280">平均</Typography>
                  </Box>
                  <Box textAlign="center">
                    <TimerIcon sx={{ color: '#EF4444', fontSize: 20 }} />
                    <Typography variant="body2" fontWeight={700} color="#EF4444">{formatMs(perf.latency.max_ms)}</Typography>
                    <Typography variant="caption" color="#6B7280">最慢</Typography>
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="body2" fontWeight={700}>{perf.pipeline.avg_step_count}</Typography>
                    <Typography variant="caption" color="#6B7280">管线步骤</Typography>
                  </Box>
                  <Box textAlign="center">
                    <Typography variant="body2" fontWeight={700}>{formatMs(perf.pipeline.avg_step_ms)}</Typography>
                    <Typography variant="caption" color="#6B7280">步骤耗时</Typography>
                  </Box>
                </Box>
              </Card>
            </Grid2>
          </Grid2>

          {/* Trend charts side by side */}
          <Grid2 container spacing={1.5} flex={1}>
            {perf.token_trend.length > 0 && (
              <Grid2 size={{ xs: 12, md: 6 }}>
                <Card sx={{ p: 1.5, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="caption" fontWeight={600} color="#1F2937" mb={0.5}>
                    Token 消耗趋势（日均每问题）
                  </Typography>
                  <Box flex={1} minHeight={0}><canvas ref={tokenTrendRef} /></Box>
                </Card>
              </Grid2>
            )}
            {perf.latency_trend.length > 0 && (
              <Grid2 size={{ xs: 12, md: 6 }}>
                <Card sx={{ p: 1.5, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="caption" fontWeight={600} color="#1F2937" mb={0.5}>
                    响应时间趋势（日均）
                  </Typography>
                  <Box flex={1} minHeight={0}><canvas ref={latencyTrendRef} /></Box>
                </Card>
              </Grid2>
            )}
          </Grid2>

          {/* Interaction + System overview side by side */}
          <Grid2 container spacing={1.5}>
            <Grid2 size={{ xs: 12, md: 6 }}>
              <Card sx={{ p: 1.5 }}>
                <Typography variant="body2" fontWeight={600} color="#1F2937" mb={1}>用户互动</Typography>
                <Box display="flex" justifyContent="space-around">
                  <Box textAlign="center">
                    <ThumbUpIcon sx={{ color: '#22C55E', fontSize: 22 }} />
                    <Typography variant="body2" fontWeight={700}>{perf.interactions.likes}</Typography>
                    <Typography variant="caption" color="#6B7280">点赞</Typography>
                  </Box>
                  <Box textAlign="center">
                    <ThumbDownIcon sx={{ color: '#EF4444', fontSize: 22 }} />
                    <Typography variant="body2" fontWeight={700}>{perf.interactions.dislikes}</Typography>
                    <Typography variant="caption" color="#6B7280">点踩</Typography>
                  </Box>
                  <Box textAlign="center">
                    <ShareIcon sx={{ color: '#3478F6', fontSize: 22 }} />
                    <Typography variant="body2" fontWeight={700}>{perf.interactions.shares}</Typography>
                    <Typography variant="caption" color="#6B7280">分享</Typography>
                  </Box>
                </Box>
              </Card>
            </Grid2>
            <Grid2 size={{ xs: 12, md: 6 }}>
              <Card sx={{ p: 1.5 }}>
                <Typography variant="body2" fontWeight={600} color="#1F2937" mb={1}>系统概览</Typography>
                <Box display="flex" justifyContent="space-around">
                  {[
                    ['数据库表', stats?.tables || 0],
                    ['Few-shot', stats?.fewshots || 0],
                    ['CSV数据源', stats?.datasources ? stats.datasources - 1 : 0],
                    ['待处理预警', (stats?.alerts || 0) - (stats?.cases || 0)],
                    ['立案率', stats?.alerts ? Math.round((stats.filed_cases || 0) / stats.alerts * 100) + '%' : '0%'],
                  ].map(([label, value]) => (
                    <Box textAlign="center" key={label as string}>
                      <Typography variant="body2" fontWeight={700} color="#1F2937">{value}</Typography>
                      <Typography variant="caption" color="#6B7280">{label}</Typography>
                    </Box>
                  ))}
                </Box>
              </Card>
            </Grid2>
          </Grid2>
        </>
      )}
      {/* Fallback when no performance data yet */}
      {!perf && (
        <Card sx={{ p: 1.5 }}>
          <Typography variant="body2" fontWeight={600} color="#1F2937" mb={1}>系统概览</Typography>
          <Box display="flex" justifyContent="space-around">
            {[
              ['数据库表', stats?.tables || 0],
              ['Few-shot', stats?.fewshots || 0],
              ['CSV数据源', stats?.datasources ? stats.datasources - 1 : 0],
              ['待处理预警', (stats?.alerts || 0) - (stats?.cases || 0)],
              ['立案率', stats?.alerts ? Math.round((stats.filed_cases || 0) / stats.alerts * 100) + '%' : '0%'],
            ].map(([label, value]) => (
              <Box textAlign="center" key={label as string}>
                <Typography variant="body2" fontWeight={700} color="#1F2937">{value}</Typography>
                <Typography variant="caption" color="#6B7280">{label}</Typography>
              </Box>
            ))}
          </Box>
        </Card>
      )}
      </Box>
    </Box>
  );
}

/* ================================================================
 * KpiCard — reusable KPI metric card
 * ================================================================ */
function KpiCard({ label, value, icon, color }: {
  label: string; value: number; icon: React.ReactNode; color: string;
}) {
  return (
    <Card sx={{
      p: 2, display: 'flex', alignItems: 'center', gap: 1.5,
      position: 'relative', overflow: 'visible', height: '100%',
    }}>
      <Box sx={{
        width: 4, height: 48, borderRadius: 2,
        background: `linear-gradient(180deg, ${color}, ${color}88)`,
        position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)',
        flexShrink: 0,
      }} />
      <Box sx={{ pl: 1.5, minWidth: 0 }}>
        <Box sx={{ color, display: 'flex', mb: 0.5 }}>{icon}</Box>
        <Typography variant="h4" fontWeight={700} fontSize={28} color="#1F2937" sx={{ lineHeight: 1.2 }} noWrap>
          {value}
        </Typography>
        <Typography variant="caption" color="#6B7280" noWrap>{label}</Typography>
      </Box>
    </Card>
  );
}
