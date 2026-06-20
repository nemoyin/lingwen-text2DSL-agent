import { Box, Typography, Button } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

interface Props {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({ message, onRetry }: Props) {
  return (
    <Box
      display="flex"
      alignItems="center"
      gap={1.5}
      px={2}
      py={1.5}
      bgcolor="error.main"
      color="error.contrastText"
      borderRadius={2}
      sx={{ '& .MuiButton-root': { color: 'inherit', borderColor: 'inherit' } }}
    >
      <ErrorOutlineIcon fontSize="small" />
      <Typography variant="body2" sx={{ flex: 1 }}>
        {message}
      </Typography>
      {onRetry && (
        <Button size="small" variant="outlined" onClick={onRetry}>
          重试
        </Button>
      )}
    </Box>
  );
}
