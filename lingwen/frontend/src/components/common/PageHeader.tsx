import { Box, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface Props {
  title: string;
  actions?: ReactNode;
}

export default function PageHeader({ title, actions }: Props) {
  return (
    <Box mb={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h5" fontWeight={700} color="#1F2937">
          {title}
        </Typography>
        {actions && <Box display="flex" gap={1}>{actions}</Box>}
      </Box>
      <Box sx={{ mt: 1, height: 3, borderRadius: 2, background: 'linear-gradient(90deg, #2065F5, #4A88FF)', width: 80 }} />
    </Box>
  );
}
