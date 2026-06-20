import { useState } from 'react';
import { Box, Typography, Button, Collapse } from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';

interface Props {
  sql: string;
}

export default function SqlBlock({ sql }: Props) {
  const [open, setOpen] = useState(false);

  if (!sql) return null;

  return (
    <Box sx={{ mb: 1 }}>
      <Button
        size="small"
        startIcon={<CodeIcon />}
        onClick={() => setOpen(!open)}
        sx={{ textTransform: 'none', fontSize: 12 }}
      >
        {open ? '隐藏 SQL' : '查看生成的 SQL'}
      </Button>
      <Collapse in={open}>
        <Box
          component="pre"
          sx={{
            mt: 0.5,
            p: 1.5,
            bgcolor: 'grey.100',
            borderRadius: 1,
            fontSize: 12,
            fontFamily: 'monospace',
            overflow: 'auto',
            maxHeight: 200,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {sql}
        </Box>
      </Collapse>
    </Box>
  );
}
