import { Box, Typography } from '@mui/material';

interface Props {
  analysis: string;
}

export default function AnalysisBlock({ analysis }: Props) {
  if (!analysis) return null;

  return (
    <Box sx={{ mb: 1.5 }}>
      <Typography variant="subtitle2" gutterBottom>
        AI 分析
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
        {analysis}
      </Typography>
    </Box>
  );
}
