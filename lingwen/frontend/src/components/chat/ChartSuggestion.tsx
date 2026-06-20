/**
 * @deprecated 请使用 ResultChart 组件替代。保留以兼容旧引用。
 */
import { Box, Typography, Chip } from '@mui/material';
import BarChartIcon from '@mui/icons-material/BarChart';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import TableChartIcon from '@mui/icons-material/TableChart';

interface ChartSuggestionData {
  type: string;
  title: string;
}

interface Props {
  suggestion: ChartSuggestionData | null;
}

const iconMap: Record<string, React.ReactElement> = {
  bar: <BarChartIcon fontSize="small" />,
  line: <ShowChartIcon fontSize="small" />,
  table: <TableChartIcon fontSize="small" />,
};

export default function ChartSuggestion({ suggestion }: Props) {
  if (!suggestion) return null;

  return (
    <Box sx={{ mb: 1.5 }}>
      <Typography variant="subtitle2" gutterBottom>
        图表建议
      </Typography>
      <Chip
        icon={iconMap[suggestion.type] || iconMap.table}
        label={suggestion.title}
        variant="outlined"
        size="small"
      />
    </Box>
  );
}
