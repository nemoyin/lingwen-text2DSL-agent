import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box, Typography, Button, List, ListItemButton, ListItemText, IconButton,
  Stack, Avatar, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  Collapse, Paper, NativeSelect, Select, Menu, MenuItem, ListItemIcon, Tooltip,
  useMediaQuery, useTheme as useMuiTheme,
  TextField, InputAdornment,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import DeleteIcon from '@mui/icons-material/Delete';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ShareIcon from '@mui/icons-material/Share';
import CachedIcon from '@mui/icons-material/Cached';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import ListAltIcon from '@mui/icons-material/ListAlt';
import StorageIcon from '@mui/icons-material/Storage';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import SmartToyIcon from '@mui/icons-material/SmartToy';

import { useQuery } from '../hooks/useQuery';
import type { ReasoningStep } from '../hooks/useQuery';
import { useApp } from '../contexts/AppContext';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import type { ApiResponse, QueryResponse } from '../types';
import { VoiceInput, SpeakButton } from '../components/chat/VoiceInput';
import ResultChart from '../components/chat/ResultChart';
import ExportButtons from '../components/chat/ExportButtons';
import DataTable from '../components/chat/DataTable';

type Message = {
  type: 'user' | 'assistant';
  content: string;
  result?: QueryResponse;
  error?: string | null;
  historyId?: number;
  /** Reasoning steps captured at the time this assistant message was completed. */
  reasoningSteps?: ReasoningStep[];
};

interface HistoryItem {
  id: number;
  question: string;
  result_json: string | null;
  created_at: string;
}

const SIDEBAR_WIDTH = 260;

/** Format milliseconds to human-readable string. */
function formatLatency(ms: number): string {
  if (!ms || ms <= 0) return '--';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/** Format ISO datetime string for history items: today → HH:mm, otherwise → MM-DD */
function _formatHistoryTime(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  if (isToday) {
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  }
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')}`;
}

/* ================================================================
 * TypewriterBox — gradually reveals text character by character.
 * When `text` changes (new content appended), animation continues.
 * ================================================================ */
function TypewriterBox({ text, speed = 12 }: { text: string; speed?: number }) {
  const len = text.length;
  const [cursor, setCursor] = useState(0);
  const prevTextRef = useRef(text);

  useEffect(() => {
    // If text was replaced (not appended), reset cursor
    if (prevTextRef.current !== text && !text.startsWith(prevTextRef.current)) {
      setCursor(0);
    }
    prevTextRef.current = text;

    if (cursor >= len) return;
    const timer = setTimeout(() => setCursor(c => Math.min(c + 1, len)), speed);
    return () => clearTimeout(timer);
  }, [cursor, text, len, speed]);

  return (
    <Box sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', lineHeight: 1.65 }}>
      {text.slice(0, cursor)}
      {cursor < len && <Box component="span" sx={{ animation: 'blink 0.8s step-end infinite', color: 'primary.main' }}>▌</Box>}
    </Box>
  );
}

export default function ChatPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const { datasources, currentDatasourceId, setDatasource, refreshDatasources } = useApp();
  const { loading, result, error, executeQueryStream, cancelQuery, reset, progressSteps, reasoningSteps } = useQuery();
  const [messages, setMessages] = useState<Message[]>([]);
  const [initializing, setInitializing] = useState(true);
  const muiTheme = useMuiTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyHasMore, setHistoryHasMore] = useState(false);
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);
  const [feedbackMap, setFeedbackMap] = useState<Record<number, number>>({});
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailTarget, setDetailTarget] = useState<QueryResponse | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const loadingStartRef = useRef<number>(0);
  const [elapsedSec, setElapsedSec] = useState<number>(0);
  const [reasoningExpanded, setReasoningExpanded] = useState(true);
  const [reasoningModalOpen, setReasoningModalOpen] = useState(false);
  const [reasoningModalTarget, setReasoningModalTarget] = useState<ReasoningStep[]>([]);
  const [searchText, setSearchText] = useState('');
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<HTMLElement | null>(null);
  const [menuTargetItem, setMenuTargetItem] = useState<HistoryItem | null>(null);

  // Snapshot of reasoning steps at the moment loading completes
  const reasoningSnapshot = useRef<ReasoningStep[]>([]);
  useEffect(() => { if (loading) reasoningSnapshot.current = reasoningSteps; }, [reasoningSteps, loading]);

  /* ---- Live elapsed timer during loading ---- */
  useEffect(() => {
    if (loading) {
      loadingStartRef.current = Date.now();
      setElapsedSec(0);
      const iv = setInterval(() => {
        setElapsedSec(Math.round((Date.now() - loadingStartRef.current) / 100) / 10);
      }, 100);
      return () => clearInterval(iv);
    }
  }, [loading]);

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login', { replace: true }); return; }
    refreshDatasources();
    const timer = setTimeout(() => setInitializing(false), 300);
    return () => clearTimeout(timer);
  }, [isAuthenticated]);

  /* ---- Auto-select default datasource ---- */
  useEffect(() => {
    if (!currentDatasourceId && datasources.length > 0) {
      const defaultDs = datasources.find(ds => ds.name === 'lingwen_testdb') || datasources[0];
      setDatasource(defaultDs.id);
    }
  }, [datasources, currentDatasourceId]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading, reasoningSteps]);

  /* ---- History ---- */
  const fetchHistory = useCallback(async (page = 1, append = false) => {
    try {
      const res = await api.get<ApiResponse<{ items: HistoryItem[]; total: number; page: number; total_pages: number }>>('/api/query/history', { params: { page, page_size: 20 } });
      const items = res.data.data?.items || [];
      const totalPages = res.data.data?.total_pages || 1;
      setHistory(prev => append ? [...prev, ...items] : items);
      setHistoryHasMore(page < totalPages);
      if (!selectedHistoryId && items.length > 0 && !append) setSelectedHistoryId(items[0].id);
    } catch { /* ignore */ }
  }, [selectedHistoryId]);
  useEffect(() => { setHistory([]); setHistoryPage(1); setSelectedHistoryId(null); fetchHistory(1); }, [user?.user_id]);

  useEffect(() => {
    if (result) {
      const snapshot = [...reasoningSnapshot.current];
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: result.analysis,
        result,
        historyId: result.history_id,
        reasoningSteps: snapshot,
      }]);
      setTimeout(() => fetchHistory(1), 800);
    }
    if (error) setMessages(prev => [...prev, { type: 'assistant', content: error, error }]);
  }, [result, error]);

  /* ---- Handlers ---- */
  const handleSend = async (question: string) => {
    if (!currentDatasourceId) return;
    reset();
    setMessages(prev => [...prev, { type: 'user', content: question }]);
    setSelectedHistoryId(null);
    const historyPairs: { question: string; answer: string }[] = [];
    for (let i = 0; i < messages.length - 1; i += 2) {
      if (messages[i]?.type === 'user' && messages[i + 1]?.type === 'assistant') {
        historyPairs.push({ question: messages[i].content, answer: messages[i + 1].result?.analysis || messages[i + 1].content });
      }
    }
    try {
      await executeQueryStream(question, currentDatasourceId, { history: historyPairs.slice(-6) });
    } catch (err) {
      console.error('Query failed:', err);
    }
  };

  const handleHistoryClick = (item: HistoryItem) => {
    if (item.result_json) {
      try {
        const parsed = JSON.parse(item.result_json);
        setSelectedHistoryId(item.id);
        // Reconstruct reasoning steps from pipeline_steps persisted in result_json
        const steps = parsed.pipeline_steps || [];
        const histReasoning: ReasoningStep[] = steps.map((s: any) => ({
          step: s.step,
          text: s.detail || '',
        }));
        setMessages([
          { type: 'user', content: item.question, historyId: item.id },
          { type: 'assistant', content: parsed.analysis || '', result: parsed, historyId: item.id, reasoningSteps: histReasoning },
        ]);
      } catch { handleReplay(item); }
    } else { handleReplay(item); }
  };

  const handleReplay = (item: HistoryItem) => {
    reset();
    setMessages([{ type: 'user', content: item.question }]);
    setSelectedHistoryId(null);
    if (currentDatasourceId) handleSend(item.question);
  };

  const handleFeedback = async (hid: number | null, rating: number) => {
    if (!hid) return;
    try {
      await api.post(`/api/query/${hid}/feedback`, null, { params: { rating: String(rating) } });
      setFeedbackMap(prev => ({ ...prev, [hid]: rating }));
    } catch { /* ignore */ }
  };

  const handleShare = (hid: number | null) => {
    if (!hid) return;
    const url = `${window.location.origin}/share/${hid}`;
    navigator.clipboard?.writeText(url);
  };

  const handleDeleteHistory = async () => {
    if (!deleteTargetId) return;
    try {
      await api.delete(`/api/query/${deleteTargetId}`);
      setDeleteConfirmOpen(false);
      setDeleteTargetId(null);
      setMenuTargetItem(null);
      fetchHistory(1);
    } catch { /* ignore */ }
  };

  const handleCopyQuestion = () => {
    if (menuTargetItem) {
      navigator.clipboard?.writeText(menuTargetItem.question);
    }
    setMenuAnchorEl(null);
    setMenuTargetItem(null);
  };

  const handleMenuDelete = () => {
    if (menuTargetItem) {
      setDeleteTargetId(menuTargetItem.id);
      setDeleteConfirmOpen(true);
    }
    setMenuAnchorEl(null);
  };

  const hasMessages = messages.length > 0;

  return (
    <Box flex={1} display="flex" flexDirection="column" overflow="hidden">
      {/* ---- Top bar ---- */}
      <Box display="flex" alignItems="center" px={1.5} py={0.5} borderBottom="0.5px solid" borderColor="divider" flexShrink={0}>
        <IconButton onClick={() => setSidebarOpen(v => !v)} size="small">{sidebarOpen ? <ChevronLeftIcon /> : <MenuIcon />}</IconButton>
        <Typography variant="body2" fontWeight={600} ml={1} flex={1}>天府一网监 · 智能问数</Typography>
      </Box>

      <Box flex={1} display="flex" overflow="hidden">
        {/* ---- Sidebar ---- */}
        <Box
          width={sidebarOpen ? SIDEBAR_WIDTH : 0} overflow="hidden" flexShrink={0}
          borderRight="0.5px solid" borderColor="divider"
          display="flex" flexDirection="column"
          sx={{ transition: 'width 0.2s', position: isMobile ? 'absolute' : 'relative', zIndex: 1200, bgcolor: 'background.paper' }}
        >
          {/* New conversation + search */}
          <Box px={1.5} py={1} borderBottom="0.5px solid" borderColor="divider">
            <Button
              fullWidth
              variant="contained"
              size="small"
              startIcon={<AddIcon sx={{ fontSize: 16 }} />}
              onClick={() => { reset(); setMessages([]); setSelectedHistoryId(null); }}
              sx={{ fontSize: 12, textTransform: 'none', mb: 1 }}
            >
              新建对话
            </Button>
            <TextField
              fullWidth
              size="small"
              placeholder="搜索历史..."
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon sx={{ fontSize: 16, color: 'text.disabled' }} /></InputAdornment> }}
              sx={{ '& .MuiInputBase-root': { fontSize: 12, height: 30 } }}
            />
          </Box>

          <List dense sx={{ flex: 1, overflow: 'auto' }}>
            {history
              .filter(h => !searchText || h.question.includes(searchText))
              .map(h => (
                <Tooltip key={h.id} title={h.question} placement="right" arrow enterDelay={500}>
                  <ListItemButton
                    selected={selectedHistoryId === h.id}
                    onClick={() => handleHistoryClick(h)}
                    sx={{ py: 0.75 }}
                  >
                    <ListItemText
                      primary={h.question.length > 22 ? h.question.slice(0, 22) + '...' : h.question}
                      secondary={_formatHistoryTime(h.created_at)}
                      primaryTypographyProps={{ fontSize: 13, noWrap: true }}
                      secondaryTypographyProps={{ fontSize: 10, color: 'text.disabled' }}
                    />
                    <IconButton
                      size="small"
                      onClick={(e) => { e.stopPropagation(); setMenuAnchorEl(e.currentTarget); setMenuTargetItem(h); }}
                      sx={{ opacity: 0, transition: 'opacity 0.15s', '.MuiListItemButton-root:hover &': { opacity: 0.6 }, '&:hover': { opacity: '1 !important' } }}
                    >
                      <MoreVertIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </ListItemButton>
                </Tooltip>
              ))}
          </List>
          {historyHasMore && (
            <Box textAlign="center" py={0.5}>
              <Button size="small" onClick={() => { const np = historyPage + 1; setHistoryPage(np); fetchHistory(np, true); }} sx={{ fontSize: 11 }}>加载更多</Button>
            </Box>
          )}
        </Box>

        {/* ---- Main chat area ---- */}
        <Box flex={1} display="flex" flexDirection="column" overflow="hidden">
          <Box flex={1} overflow="auto" px={isMobile ? 1 : 3} py={2}>
            {!hasMessages && !loading && (
              <Box textAlign="center" mt={8} color="text.secondary">
                <Typography variant="h5" fontWeight={600} mb={0.5}>天府一网监 · 智能问数</Typography>
                <Typography variant="body2" mb={3}>输入自然语言问题，AI 自动分析并回答</Typography>
                <Stack direction="column" spacing={1} alignItems="center">
                  {[
                    '各部门三公经费支出汇总',
                    '查询2024年政府采购合同总额',
                    '惠农补贴按乡镇统计发放金额',
                    '民政救助对象按救助类型分布',
                    '工程项目按地区统计投资总额',
                  ].map((q, i) => (
                    <Chip
                      key={i}
                      label={q}
                      variant="outlined"
                      onClick={() => handleSend(q)}
                      sx={{ cursor: 'pointer', maxWidth: 340, '&:hover': { bgcolor: 'primary.main', color: '#fff' } }}
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {messages.map((msg, idx) => (
              <Box
                key={idx}
                mb={2}
                display="flex"
                gap={1.5}
                alignItems="flex-start"
                flexDirection={msg.type === 'user' ? 'row-reverse' : 'row'}
              >
                <Avatar sx={{ width: 28, height: 28, fontSize: 12, bgcolor: msg.type === 'user' ? 'primary.main' : 'secondary.main', flexShrink: 0 }}>
                  {msg.type === 'user' ? '我' : <SmartToyIcon sx={{ fontSize: 18 }} />}
                </Avatar>
                <Box maxWidth={msg.type === 'user' ? '65%' : undefined} flex={msg.type === 'assistant' ? 1 : undefined} minWidth={0}>
                  {msg.type === 'user' ? (
                    <Paper variant="outlined" sx={{ p: 1.5, bgcolor: 'grey.50', borderRadius: 2 }}>
                      <Typography variant="body2">{msg.content}</Typography>
                    </Paper>
                  ) : msg.error ? (
                    <Typography variant="body2" color="error.main">{msg.content}</Typography>
                  ) : msg.result ? (
                    /* ---- Assistant result ---- */
                    <Box>
                      {/* Chart area (conditionally rendered when chart_suggestion exists) */}
                      <ResultChart
                        data={msg.result.data}
                        columns={msg.result.columns}
                        suggestion={msg.result.chart_suggestion}
                      />

                      {/* Data table */}
                      {msg.result.data && msg.result.data.length > 0 && (
                        <DataTable
                          columns={msg.result.columns}
                          data={msg.result.data}
                          isTruncated={msg.result.is_truncated}
                        />
                      )}

                      {/* Analysis */}
                      {msg.result.analysis && (
                        <Typography variant="body2" sx={{ mb: 1, lineHeight: 1.7 }}>{msg.result.analysis}</Typography>
                      )}

                      {/* Action bar: Export + Stats badges */}
                      <Stack direction="row" spacing={1} mt={1} alignItems="center" flexWrap="wrap">
                        <ExportButtons
                          data={msg.result.data}
                          columns={msg.result.columns}
                          isTruncated={msg.result.is_truncated}
                        />
                        {/* Latency badge (non-interactive) */}
                        <Box
                          sx={{
                            display: 'inline-flex', alignItems: 'center', gap: 0.5,
                            px: 1, py: 0.25, fontSize: 11, height: 28,
                            border: '1px solid', borderColor: 'divider', borderRadius: 1,
                            color: 'text.secondary',
                          }}
                        >
                          <CachedIcon sx={{ fontSize: 14 }} />
                          {formatLatency(msg.result.latency_ms || 0)}
                        </Box>
                        {/* Token badge (non-interactive) */}
                        {msg.result.total_tokens ? (
                          <Box
                            sx={{
                              display: 'inline-flex', alignItems: 'center', gap: 0.5,
                              px: 1, py: 0.25, fontSize: 11, height: 28,
                              border: '1px solid', borderColor: 'divider', borderRadius: 1,
                              color: 'text.secondary',
                            }}
                          >
                            <DataUsageIcon sx={{ fontSize: 14 }} />
                            {msg.result.total_tokens.toLocaleString()} tokens
                          </Box>
                        ) : null}
                        {msg.reasoningSteps && msg.reasoningSteps.length > 0 && (
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<PsychologyIcon sx={{ fontSize: 14 }} />}
                            sx={{ fontSize: 11, textTransform: 'none', height: 28, ml: 'auto !important' }}
                            onClick={() => { setReasoningModalTarget(msg.reasoningSteps!); setReasoningModalOpen(true); }}
                          >
                            思考过程
                          </Button>
                        )}
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<ListAltIcon sx={{ fontSize: 14 }} />}
                          sx={{ fontSize: 11, textTransform: 'none', height: 28, ml: msg.reasoningSteps?.length ? undefined : 'auto !important' }}
                          onClick={() => { setDetailTarget(msg.result!); setDetailOpen(true); }}
                        >
                          执行详情
                        </Button>
                      </Stack>

                      {/* Suggested questions */}
                      {msg.result.suggested_questions && (msg.result.suggested_questions as string[]).length > 0 && (
                        <Stack direction="row" spacing={0.5} mt={1.5} flexWrap="wrap" useFlexGap>
                          {(msg.result.suggested_questions as string[]).map((q: string, i: number) => (
                            <Chip key={i} label={q} size="small" variant="outlined" color="primary" onClick={() => handleSend(q)}
                              sx={{ cursor: 'pointer', maxWidth: 320, backgroundColor: 'rgba(52,120,246,0.04)', borderColor: 'rgba(52,120,246,0.2)', '&:hover': { backgroundColor: 'rgba(52,120,246,0.08)', fontWeight: 600 } }} />
                          ))}
                        </Stack>
                      )}

                      {/* Feedback row */}
                      {msg.historyId && (
                        <Stack direction="row" spacing={0.25} mt={1} alignItems="center">
                          <IconButton size="small" onClick={() => handleFeedback(msg.historyId!, 1)}
                            color={feedbackMap[msg.historyId!] === 1 ? 'primary' : 'default'}>
                            <ThumbUpIcon fontSize="small" />
                          </IconButton>
                          <IconButton size="small" onClick={() => handleFeedback(msg.historyId!, -1)}
                            color={feedbackMap[msg.historyId!] === -1 ? 'error' : 'default'}>
                            <ThumbDownIcon fontSize="small" />
                          </IconButton>
                          <IconButton size="small" onClick={() => handleShare(msg.historyId!)}>
                            <ShareIcon fontSize="small" />
                          </IconButton>
                          <IconButton size="small" onClick={() => handleSend(msg.result?.question || '')} title="重新生成">
                            <RefreshIcon fontSize="small" />
                          </IconButton>
                          <SpeakButton text={msg.result.analysis || msg.content} />
                        </Stack>
                      )}
                    </Box>
                  ) : null}
                </Box>
              </Box>
            ))}

            {/* Loading: streaming reasoning + stop button */}
            {loading && (
              <Box display="flex" gap={1.5} mb={2}>
                <Avatar sx={{ width: 28, height: 28, fontSize: 12, bgcolor: 'secondary.main', flexShrink: 0 }}><SmartToyIcon sx={{ fontSize: 18 }} /></Avatar>
                <Box flex={1} minWidth={0}>
                  {/* Header row */}
                  <Stack
                    direction="row"
                    spacing={0.5}
                    alignItems="center"
                    mb={reasoningSteps.length > 0 && reasoningExpanded ? 1 : 0}
                    sx={{ cursor: reasoningSteps.length > 0 ? 'pointer' : 'default' }}
                    onClick={() => reasoningSteps.length > 0 && setReasoningExpanded(v => !v)}
                  >
                    <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'warning.main', animation: 'pulse 1s infinite', flexShrink: 0 }} />
                    <Typography variant="body2" color="text.secondary" sx={{ flexShrink: 0 }}>分析中</Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, minWidth: 42, fontFamily: 'monospace', flexShrink: 0 }}>
                      {elapsedSec.toFixed(1)}s
                    </Typography>
                    {reasoningSteps.length > 0 && (
                      <IconButton size="small" sx={{ p: 0 }}>
                        {reasoningExpanded ? <KeyboardArrowUpIcon fontSize="small" /> : <KeyboardArrowDownIcon fontSize="small" />}
                      </IconButton>
                    )}
                  </Stack>

                  {/* Typewriter reasoning blocks */}
                  <Collapse in={reasoningExpanded && reasoningSteps.length > 0}>
                    <Paper variant="outlined" sx={{ p: 1.5, bgcolor: '#fafafa', fontSize: 11, maxHeight: 280, overflow: 'auto', lineHeight: 1.6, color: 'text.secondary' }}>
                      {reasoningSteps.map((rs, i) => (
                        <Box key={i} mb={i < reasoningSteps.length - 1 ? 1.25 : 0}>
                          <Typography variant="caption" fontWeight={600} color="primary.main" sx={{ display: 'block', mb: 0.25 }}>
                            {rs.step}
                          </Typography>
                          <Typography variant="caption" component="div" sx={{ fontFamily: 'monospace' }}>
                            <TypewriterBox text={rs.text} speed={8} />
                          </Typography>
                        </Box>
                      ))}
                    </Paper>
                  </Collapse>
                </Box>
              </Box>
            )}

            <div ref={chatEndRef} />
          </Box>

          {/* ---- Input bar ---- */}
          <ChatInput
            datasources={datasources}
            currentDatasourceId={currentDatasourceId}
            onDatasourceChange={setDatasource}
            onSend={handleSend}
            onCancel={cancelQuery}
            disabled={loading}
          />
        </Box>
      </Box>

      {/* ---- History item action menu ---- */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={() => { setMenuAnchorEl(null); setMenuTargetItem(null); }}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleCopyQuestion} sx={{ fontSize: 13, gap: 1 }}>
          <ContentCopyIcon sx={{ fontSize: 16 }} />
          复制问题
        </MenuItem>
        <MenuItem onClick={handleMenuDelete} sx={{ fontSize: 13, gap: 1, color: 'error.main' }}>
          <DeleteIcon sx={{ fontSize: 16 }} />
          删除
        </MenuItem>
      </Menu>

      {/* ---- Delete history confirmation dialog ---- */}
      <Dialog open={deleteConfirmOpen} onClose={() => { setDeleteConfirmOpen(false); setDeleteTargetId(null); }} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontSize: 16, fontWeight: 600 }}>确认删除</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">确定要删除这条问答记录吗？删除后无法恢复。</Typography>
        </DialogContent>
        <DialogActions>
          <Button size="small" onClick={() => { setDeleteConfirmOpen(false); setDeleteTargetId(null); setMenuTargetItem(null); }}>取消</Button>
          <Button size="small" color="error" variant="contained" onClick={handleDeleteHistory}>确认删除</Button>
        </DialogActions>
      </Dialog>

      {/* ---- Execution details modal ---- */}
      <ExecutionDetailModal open={detailOpen} result={detailTarget} onClose={() => setDetailOpen(false)} />

      {/* ---- Reasoning process modal ---- */}
      <ReasoningModal open={reasoningModalOpen} steps={reasoningModalTarget} onClose={() => setReasoningModalOpen(false)} />
    </Box>
  );
}

/* ================================================================
 * ChatInput — integrated input bar with datasource, voice, send/stop
 * ================================================================ */
function ChatInput({ datasources, currentDatasourceId, onDatasourceChange, onSend, onCancel, disabled }: {
  datasources: any[];
  currentDatasourceId: number | null;
  onDatasourceChange: (id: number) => void;
  onSend: (q: string) => void;
  onCancel: () => void;
  disabled: boolean;
}) {
  const [text, setText] = useState('');
  const textRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (disabled) { onCancel(); return; }
    const q = text.trim();
    if (!q || !currentDatasourceId) return;
    onSend(q);
    setText('');
  };

  const handleVoiceResult = (t: string) => {
    setText(t);
    setTimeout(() => {
      if (t.trim() && !disabled && currentDatasourceId) onSend(t.trim());
    }, 300);
  };

  // Auto-grow textarea
  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  }, [text]);

  return (
    <Box
      px={2} py={1.5} borderTop="0.5px solid" borderColor="divider"
      display="flex" gap={1} alignItems="flex-end"
      sx={{ bgcolor: 'background.paper' }}
    >
      {/* Datasource selector */}
      <Select
        value={currentDatasourceId || ''}
        onChange={e => onDatasourceChange(Number(e.target.value))}
        size="small"
        disabled={disabled}
        sx={{ fontSize: 12, height: 36, minWidth: 130, flexShrink: 0, '& .MuiSelect-select': { py: 0.5, display: 'flex', alignItems: 'center', gap: 0.75 } }}
      >
        {datasources.map(ds => (
          <MenuItem key={ds.id} value={ds.id} sx={{ fontSize: 12 }}>
            <ListItemIcon sx={{ minWidth: 'auto !important', mr: 0.75 }}>
              <StorageIcon sx={{ fontSize: 14 }} />
            </ListItemIcon>
            {ds.name}
          </MenuItem>
        ))}
      </Select>

      {/* Multiline textarea */}
      <textarea
        ref={textRef}
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
          }
        }}
        placeholder={!currentDatasourceId ? '请先选择数据源' : '输入您的问题，Enter 发送 · Ctrl+Enter 换行'}
        disabled={!currentDatasourceId}
        rows={1}
        style={{
          flex: 1,
          padding: '6px 10px',
          border: '1px solid #e0e0e0',
          borderRadius: 6,
          fontSize: 14,
          outline: 'none',
          resize: 'none',
          fontFamily: 'inherit',
          lineHeight: 1.5,
          maxHeight: 120,
          background: 'transparent',
        }}
      />

      {/* Voice input */}
      <VoiceInput onResult={handleVoiceResult} />

      {/* Send / Stop button */}
      <Button
        variant="contained"
        size="small"
        onClick={handleSubmit}
        disabled={!disabled && (!text.trim() || !currentDatasourceId)}
        sx={{ minWidth: 56, height: 36, flexShrink: 0, borderRadius: 2 }}
        color={disabled ? 'error' : 'primary'}
      >
        {disabled ? '停止' : '发送'}
      </Button>
    </Box>
  );
}

/* ================================================================
 * ExecutionDetailModal
 * ================================================================ */
function ExecutionDetailModal({ open, result, onClose }: { open: boolean; result: QueryResponse | null; onClose: () => void }) {
  if (!result) return null;
  const steps = result.pipeline_steps || [];
  const totalTokens = result.total_tokens || 0;
  const totalLatency = result.latency_ms || 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ fontSize: 16, fontWeight: 600 }}>执行详情</DialogTitle>
      <DialogContent dividers>
        {/* Overview stats */}
        <Box mb={2} display="flex" gap={3}>
          <Box><Typography variant="caption" color="text.secondary">总耗时</Typography>
            <Typography variant="h6" fontWeight={600}>{formatLatency(totalLatency)}</Typography></Box>
          <Box><Typography variant="caption" color="text.secondary">Token 消耗</Typography>
            <Typography variant="h6" fontWeight={600}>{totalTokens > 0 ? totalTokens.toLocaleString() : 'N/A'}</Typography></Box>
          <Box><Typography variant="caption" color="text.secondary">返回行数</Typography>
            <Typography variant="h6" fontWeight={600}>{result.row_count}</Typography></Box>
        </Box>

        {/* Pipeline steps */}
        <Typography variant="body2" fontWeight={600} mb={1}>管线执行步骤</Typography>
        {steps.length > 0 ? (
          <Stack spacing={1}>
            {steps.map((s: any, i: number) => {
              const pct = totalLatency > 0 ? Math.max(Math.round((s.elapsed_ms / totalLatency) * 100), 1) : 0;
              return (
                <Box key={i} sx={{ p: 1.5, borderRadius: 1, bgcolor: 'action.hover', fontSize: 12 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: s.status === 'error' ? 'error.main' : 'success.main' }} />
                      <Typography variant="body2" fontWeight={500}>{s.step}</Typography>
                    </Box>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <Typography variant="caption" color="text.secondary">{s.elapsed_ms > 0 ? `${s.elapsed_ms}ms (${pct}%)` : '--'}</Typography>
                      <IconButton
                        size="small"
                        onClick={() => navigator.clipboard?.writeText(`[${s.step}] ${s.detail || ''}`)}
                        sx={{ p: 0.25, opacity: 0.5, '&:hover': { opacity: 1 } }}
                        title="复制此步骤结果"
                      >
                        <ContentCopyIcon sx={{ fontSize: 13 }} />
                      </IconButton>
                    </Box>
                  </Box>
                  {s.detail && (
                    <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', display: 'block', mb: 0.5 }}>
                      {s.detail}
                    </Typography>
                  )}
                  {s.elapsed_ms > 0 && totalLatency > 0 && (
                    <Box sx={{ height: 3, borderRadius: 2, bgcolor: 'grey.200' }}>
                      <Box sx={{ height: 3, borderRadius: 2, bgcolor: s.status === 'error' ? 'error.main' : 'primary.main', width: `${Math.min(pct, 100)}%` }} />
                    </Box>
                  )}
                </Box>
              );
            })}
          </Stack>
        ) : (
          <Typography variant="caption" color="text.secondary">无管线执行详情（请通过对话问答生成）</Typography>
        )}

        {/* SQL */}
        {result.sql && (
          <Box mt={2}>
            <Typography variant="body2" fontWeight={600} mb={0.5}>生成的 SQL</Typography>
            <Paper variant="outlined" sx={{ p: 1.5, bgcolor: '#fafafa', fontFamily: 'monospace', fontSize: 11, whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 200, overflow: 'auto' }}>
              {result.sql}
            </Paper>
          </Box>
        )}
      </DialogContent>
      <DialogActions><Button onClick={onClose} size="small">关闭</Button></DialogActions>
    </Dialog>
  );
}

/* ================================================================
 * ReasoningModal — full step-by-step thinking process
 * ================================================================ */
function ReasoningModal({ open, steps, onClose }: { open: boolean; steps: ReasoningStep[]; onClose: () => void }) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ fontSize: 16, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
        <PsychologyIcon fontSize="small" color="primary" />
        思考过程
      </DialogTitle>
      <DialogContent dividers>
        {steps.length > 0 ? (
          <Stack spacing={1.5}>
            {steps.map((rs, i) => (
              <Box key={i} sx={{ p: 1.5, borderRadius: 1, bgcolor: 'action.hover', fontSize: 12 }}>
                <Typography variant="body2" fontWeight={600} color="primary.main" mb={0.5}>
                  {rs.step}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', lineHeight: 1.7 }}>
                  {rs.text}
                </Typography>
              </Box>
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary">无思考过程记录</Typography>
        )}
      </DialogContent>
      <DialogActions><Button onClick={onClose} size="small">关闭</Button></DialogActions>
    </Dialog>
  );
}
