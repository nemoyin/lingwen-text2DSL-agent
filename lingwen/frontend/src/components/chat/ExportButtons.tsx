import { Button, Stack, Typography } from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import TableChartIcon from '@mui/icons-material/TableChart';
import { exportCSV, exportExcel } from '../../utils/export';

interface Props {
  /** Row data. */
  data: Record<string, unknown>[];
  /** Column names. */
  columns: string[];
  /** Optional base filename (without extension). */
  filename?: string;
  /** Whether the data has been truncated (backend-side). */
  isTruncated?: boolean;
}

/**
 * Export button group for query results.
 *
 * Renders two buttons:
 * - "导出 CSV" — calls `exportCSV`
 * - "导出 Excel" — calls `exportExcel`
 *
 * When `isTruncated` is true, a caption indicates the data is partial.
 */
export default function ExportButtons({ data, columns, filename, isTruncated }: Props) {
  return (
    <Stack direction="row" spacing={0.75} alignItems="center">
      <Button
        size="small"
        variant="outlined"
        startIcon={<FileDownloadIcon fontSize="small" />}
        onClick={() => exportCSV(data, columns, filename)}
        sx={{ fontSize: 12, textTransform: 'none', height: 28, color: '#3478F6' }}
      >
        导出 CSV
      </Button>
      <Button
        size="small"
        variant="outlined"
        startIcon={<TableChartIcon fontSize="small" />}
        onClick={() => exportExcel(data, columns, filename)}
        sx={{ fontSize: 12, textTransform: 'none', height: 28, color: '#3478F6' }}
      >
        导出 Excel
      </Button>
      {isTruncated && (
        <Typography variant="caption" color="warning.main">
          导出前 1000 行
        </Typography>
      )}
    </Stack>
  );
}
