import { Box, Button, Stack } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import type { QueryResponse } from '../../types';
import { useClipboard } from '../../hooks/useClipboard';
import ResultChart from './ResultChart';
import ExportButtons from './ExportButtons';
import DataTable from './DataTable';

interface Props {
  result: QueryResponse;
}

export default function AssistantMessage({ result }: Props) {
  const { copied, copyToClipboard } = useClipboard();

  const handleCopyData = () => {
    const tsv = [result.columns.join('\t')]
      .concat(
        result.data.map((row) => result.columns.map((c) => String(row[c] ?? '')).join('\t')),
      )
      .join('\n');
    void copyToClipboard(tsv);
  };

  const handleCopySql = () => {
    void copyToClipboard(result.sql);
  };

  return (
    <Box
      sx={{
        border: '0.5px solid',
        borderColor: 'divider',
        borderRadius: 2,
        p: 2,
        mb: 2,
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ fontSize: 12, color: 'text.disabled', mb: 1 }}>
        已生成结果，耗时 {result.latency_ms ? `${Math.round(result.latency_ms)}ms` : '-'}
        {result.is_truncated && '（结果已截断）'}
      </Box>

      {/* Chart area */}
      <ResultChart
        data={result.data}
        columns={result.columns}
        suggestion={result.chart_suggestion}
      />

      {/* Data table */}
      {result.data.length > 0 && (
        <DataTable
          columns={result.columns}
          data={result.data}
          isTruncated={result.is_truncated}
        />
      )}

      {result.analysis && (
        <Box sx={{ mb: 1 }}>
          <Box sx={{ fontWeight: 500, fontSize: 13, mb: 0.5 }}>AI 分析</Box>
          <Box sx={{ fontSize: 13, color: 'text.secondary', lineHeight: 1.7 }}>
            {result.analysis}
          </Box>
        </Box>
      )}

      {result.sql && (
        <Box sx={{ mb: 1 }}>
          <Box
            component="details"
            sx={{ fontSize: 13, color: 'text.secondary', '& summary': { cursor: 'pointer', color: 'primary.main' } }}
          >
            <summary>查看生成的 SQL</summary>
            <Box
              component="pre"
              sx={{
                mt: 0.5,
                p: 1,
                bgcolor: 'grey.50',
                borderRadius: 1,
                fontSize: 11,
                fontFamily: 'monospace',
                overflow: 'auto',
                maxHeight: 180,
              }}
            >
              {result.sql}
            </Box>
          </Box>
        </Box>
      )}

      {/* Export + action buttons */}
      <Stack direction="row" spacing={1} mt={1} flexWrap="wrap" useFlexGap>
        <ExportButtons
          data={result.data}
          columns={result.columns}
          isTruncated={result.is_truncated}
        />
        <Button
          size="small"
          variant="outlined"
          startIcon={<ContentCopyIcon />}
          onClick={handleCopyData}
          sx={{ fontSize: 12, textTransform: 'none' }}
        >
          {copied ? '已复制' : '复制数据'}
        </Button>
        {result.sql && (
          <Button
            size="small"
            variant="outlined"
            onClick={handleCopySql}
            sx={{ fontSize: 12, textTransform: 'none' }}
          >
            复制 SQL
          </Button>
        )}
      </Stack>
    </Box>
  );
}
