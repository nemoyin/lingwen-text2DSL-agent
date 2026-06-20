import { useState } from 'react';
import { Box, TextField, IconButton, FormControl, Select, MenuItem, InputLabel } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import type { DataSource } from '../../types';

interface Props {
  datasources: DataSource[];
  currentDatasourceId: number | null;
  onDatasourceChange: (id: number) => void;
  onSend: (question: string) => void;
  disabled?: boolean;
}

export default function ChatInput({
  datasources,
  currentDatasourceId,
  onDatasourceChange,
  onSend,
  disabled,
}: Props) {
  const [value, setValue] = useState('');

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <Box display="flex" alignItems="flex-end" gap={1} mt={1}>
      <FormControl size="small" sx={{ minWidth: 160 }}>
        <InputLabel>数据源</InputLabel>
        <Select
          value={currentDatasourceId ?? ''}
          label="数据源"
          onChange={(e) => onDatasourceChange(Number(e.target.value))}
        >
          {datasources.map((ds) => (
            <MenuItem key={ds.id} value={ds.id}>
              {ds.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <TextField
        fullWidth
        size="small"
        placeholder="输入您的问题..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        disabled={disabled}
        multiline
        maxRows={3}
      />
      <IconButton
        color="primary"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        sx={{ flexShrink: 0 }}
      >
        <SendIcon />
      </IconButton>
    </Box>
  );
}
