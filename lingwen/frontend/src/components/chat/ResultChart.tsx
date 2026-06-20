import { useRef, useState, type MouseEvent } from 'react';
import {
  Box,
  Paper,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  Tooltip,
} from '@mui/material';
import BarChartIcon from '@mui/icons-material/BarChart';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import PieChartIcon from '@mui/icons-material/PieChart';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import CloseIcon from '@mui/icons-material/Close';
import type { ChartSuggestion } from '../../types';
import { useChart } from '../../hooks/useChart';

type ChartType = ChartSuggestion['type'];

interface Props {
  /** Row data. */
  data: Record<string, unknown>[];
  /** Column names. */
  columns: string[];
  /** Chart suggestion from the backend. */
  suggestion: ChartSuggestion | null;
  /** Maximum rows to render in the chart (default 50). */
  maxRows?: number;
}

/**
 * Renders a chart based on the backend's chart_suggestion.
 *
 * Features:
 * - If no suggestion or data.length <= 1, returns null (no chart).
 * - Toolbar with title, type toggle (bar/line/pie), and fullscreen button.
 * - Full-screen dialog with an independent chart instance.
 * - Shows a warning when data exceeds maxRows.
 *
 * IMPORTANT: All hooks are called unconditionally before any early return,
 * to comply with React's Rules of Hooks.
 */
export default function ResultChart({ data, columns, suggestion, maxRows = 50 }: Props) {
  const [fullscreenOpen, setFullscreenOpen] = useState(false);
  const inlineCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const { currentType, updateType } = useChart({
    canvasRef: inlineCanvasRef,
    data,
    columns,
    suggestion,
    maxRows,
  });

  const handleTypeChange = (_event: MouseEvent<HTMLElement>, newType: ChartType | null) => {
    if (newType !== null) {
      updateType(newType);
    }
  };

  // All hooks above — safe to early-return now.
  if (!suggestion || data.length <= 1) return null;

  const isTruncated = data.length > maxRows;
  const displayData = isTruncated ? data.slice(0, maxRows) : data;

  return (
    <Paper variant="outlined" sx={{ mb: 1.5 }}>
      {/* Toolbar */}
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        px={1.5}
        py={0.75}
        borderBottom="0.5px solid"
        borderColor="divider"
      >
        <Typography variant="body2" fontWeight={600}>
          {suggestion.title}
        </Typography>
        <Box display="flex" alignItems="center" gap={0.5}>
          <ToggleButtonGroup
            value={currentType}
            exclusive
            onChange={handleTypeChange}
            size="small"
          >
            <Tooltip title="柱状图" placement="top">
              <ToggleButton value="bar" sx={{ px: 1, py: 0.25 }}>
                <BarChartIcon fontSize="small" />
              </ToggleButton>
            </Tooltip>
            <Tooltip title="折线图" placement="top">
              <ToggleButton value="line" sx={{ px: 1, py: 0.25 }}>
                <ShowChartIcon fontSize="small" />
              </ToggleButton>
            </Tooltip>
            <Tooltip title="饼图" placement="top">
              <ToggleButton value="pie" sx={{ px: 1, py: 0.25 }}>
                <PieChartIcon fontSize="small" />
              </ToggleButton>
            </Tooltip>
          </ToggleButtonGroup>
          <IconButton size="small" onClick={() => setFullscreenOpen(true)} title="全屏查看">
            <FullscreenIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      {/* Chart canvas */}
      <Box sx={{ position: 'relative', height: 320, p: 1 }}>
        <canvas ref={inlineCanvasRef} style={{ width: '100%', height: '100%' }} />
      </Box>

      {/* Truncation notice */}
      {isTruncated && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', textAlign: 'center', pb: 1 }}
        >
          图表展示前 {maxRows} 行
        </Typography>
      )}

      {/* Fullscreen dialog */}
      <Dialog
        open={fullscreenOpen}
        onClose={() => setFullscreenOpen(false)}
        fullWidth
        maxWidth="lg"
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pr: 1 }}>
          <Typography variant="h6" fontWeight={600}>
            {suggestion.title}
          </Typography>
          <IconButton onClick={() => setFullscreenOpen(false)} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ height: '70vh', minHeight: 400 }}>
          <FullscreenChart
            data={displayData}
            columns={columns}
            suggestion={{ ...suggestion, type: currentType }}
            maxRows={maxRows}
          />
        </DialogContent>
      </Dialog>
    </Paper>
  );
}

/**
 * Full-screen chart with its own independent useChart instance.
 */
function FullscreenChart({
  data,
  columns,
  suggestion,
  maxRows,
}: {
  data: Record<string, unknown>[];
  columns: string[];
  suggestion: ChartSuggestion;
  maxRows: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useChart({
    canvasRef,
    data,
    columns,
    suggestion,
    maxRows,
  });

  return (
    <Box sx={{ width: '100%', height: '100%', position: 'relative' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
    </Box>
  );
}
