import { Box, Typography, Chip, Stack } from '@mui/material';

interface Props {
  onSelect: (question: string) => void;
}

const EXAMPLES = [
  '各部门三公经费实际支出汇总',
  '各供应商累计合同金额排名',
  '各乡镇惠农补贴发放总额',
  '当前在建的工程项目有哪些',
  '各救助类型发放人数和金额统计',
];

export default function ExampleQuestions({ onSelect }: Props) {
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        试试这些问题：
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {EXAMPLES.map((q) => (
          <Chip
            key={q}
            label={q}
            variant="outlined"
            size="small"
            clickable
            onClick={() => onSelect(q)}
          />
        ))}
      </Stack>
    </Box>
  );
}
