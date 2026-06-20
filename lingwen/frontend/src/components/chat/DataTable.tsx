import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
} from '@mui/material';
import { formatNumber } from '../../utils/formatters';

interface Props {
  columns: string[];
  data: Record<string, unknown>[];
  /** Whether the result has been truncated server-side. */
  isTruncated?: boolean;
}

function cellValue(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'number') return formatNumber(value);
  return String(value);
}

export default function DataTable({ columns, data, isTruncated }: Props) {
  if (!data.length) {
    return <Typography variant="body2" color="text.secondary">查询结果为空</Typography>;
  }

  return (
    <TableContainer
      component={Paper}
      variant="outlined"
      sx={{ mb: 1.5, maxHeight: 420 }}
    >
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            {columns.map((col) => (
              <TableCell key={col} sx={{ fontWeight: 500, whiteSpace: 'nowrap' }}>
                {col}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((row, idx) => (
            <TableRow key={idx} hover sx={{ '&:nth-of-type(even)': { bgcolor: '#FAFAFA' } }}>
              {columns.map((col) => (
                <TableCell key={col} sx={{ whiteSpace: 'nowrap' }}>
                  {cellValue(row[col])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {isTruncated && (
        <Typography variant="caption" color="warning.main" sx={{ display: 'block', textAlign: 'center', py: 0.75 }}>
          结果已截断，仅显示前 1000 行
        </Typography>
      )}
    </TableContainer>
  );
}
