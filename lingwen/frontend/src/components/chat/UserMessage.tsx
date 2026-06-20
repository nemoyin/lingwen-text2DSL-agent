import { Box, Typography } from '@mui/material';

interface Props {
  question: string;
}

export default function UserMessage({ question }: Props) {
  return (
    <Box display="flex" justifyContent="flex-end" mb={1.5}>
      <Box
        bgcolor="primary.main"
        color="primary.contrastText"
        px={2}
        py={1}
        borderRadius={2}
        maxWidth="70%"
      >
        <Typography variant="body2">{question}</Typography>
      </Box>
    </Box>
  );
}
