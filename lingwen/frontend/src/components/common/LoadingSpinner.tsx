import { Box, CircularProgress, Typography } from '@mui/material';

interface Props {
  message?: string;
}

export default function LoadingSpinner({ message = '加载中...' }: Props) {
  return (
    <Box display="flex" flexDirection="column" alignItems="center" py={4}>
      <CircularProgress size={36} />
      <Typography variant="body2" color="text.secondary" mt={1.5}>
        {message}
      </Typography>
    </Box>
  );
}
