import { useState, useEffect } from 'react';
import {
  Box, Typography, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip
} from '@mui/material';
import PageHeader from '../components/common/PageHeader';
import LoadingSpinner from '../components/common/LoadingSpinner';
import EmptyState from '../components/common/EmptyState';
import api from '../services/api';
import { formatDate } from '../utils/formatters';
import type { ApiResponse } from '../types';

interface HistoryItem {
  id: number;
  question: string;
  generated_sql: string;
  status: string;
  latency_ms: number;
  created_at: string;
}

interface HistoryItem {
  id: number;
  question: string;
  generated_sql: string;
  status: string;
  latency_ms: number;
  created_at: string;
  result_json?: string;
}

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [selected, setSelected] = useState<HistoryItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ApiResponse<{ items: HistoryItem[] }>>('/api/query/history')
      .then(res => setItems(res.data.data?.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <Box maxWidth={960} mx="auto" px={2} py={3} display="flex" gap={2}>
      <Box flex={1}>
        <PageHeader title="对话历史" />
        {items.length === 0 ? (
          <EmptyState message="暂无对话记录" />
        ) : (
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead><TableRow>
                <TableCell sx={{ fontWeight: 500 }}>问题</TableCell>
                <TableCell sx={{ fontWeight: 500 }}>状态</TableCell>
                <TableCell sx={{ fontWeight: 500 }}>耗时</TableCell>
                <TableCell sx={{ fontWeight: 500 }}>时间</TableCell>
              </TableRow></TableHead>
              <TableBody>
                {items.map(item => (
                  <TableRow key={item.id} hover onClick={() => setSelected(item)} sx={{ cursor: 'pointer' }}>
                    <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.question}</TableCell>
                    <TableCell><Chip size="small" label={item.status === 'success' ? '成功' : '失败'} color={item.status === 'success' ? 'success' : 'error'} variant="outlined" /></TableCell>
                    <TableCell>{item.latency_ms ? `${Math.round(item.latency_ms)}ms` : '-'}</TableCell>
                    <TableCell>{formatDate(item.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
      {selected && selected.result_json && (
        <Box width={380} flexShrink={0} border="0.5px solid" borderColor="divider" borderRadius={2} p={2} maxHeight="80vh" overflow="auto">
          <Typography variant="subtitle2" mb={1}>{selected.question}</Typography>
          <Typography variant="caption" color="text.secondary" display="block" mb={1}>SQL: {selected.generated_sql}</Typography>
          {(() => { try { const d = JSON.parse(selected.result_json); return <Box sx={{fontSize:12}}><pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(d.data?.slice(0,10),null,2)}</pre></Box>; } catch { return <Typography variant="body2">无法解析结果</Typography>; } })()}
        </Box>
      )}
    </Box>
  );
}
