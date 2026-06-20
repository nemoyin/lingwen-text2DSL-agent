import { Box, CircularProgress, Typography } from '@mui/material';

export default function ThinkingIndicator() {
  return (
    <Box
      display="flex"
      alignItems="center"
      gap={1.5}
      px={2}
      py={1.5}
      bgcolor="grey.50"
      borderRadius={2}
      border="0.5px solid"
      borderColor="divider"
    >
      <CircularProgress size={18} />
      <Typography variant="body2" color="text.secondary">
        正在分析您的问题...
      </Typography>
    </Box>
  );
}
