import { Box, Typography, Button } from '@mui/material';
import InboxIcon from '@mui/icons-material/Inbox';

interface Props {
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({
  message = '暂无数据',
  actionLabel,
  onAction,
}: Props) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      py={6}
      color="text.secondary"
    >
      <InboxIcon sx={{ fontSize: 48, mb: 1.5 }} />
      <Typography variant="body2">{message}</Typography>
      {actionLabel && onAction && (
        <Button variant="outlined" size="small" sx={{ mt: 2 }} onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </Box>
  );
}
