import { useState, useEffect } from 'react';
import { Box, List, ListItemButton, ListItemText, Typography } from '@mui/material';
import type { TableMetadata } from '../../types';

interface Props {
  tables: TableMetadata[];
  selectedId: number | null;
  onSelect: (tableId: number) => void;
}

export default function TableTree({ tables, selectedId, onSelect }: Props) {
  if (!tables.length) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          暂无表数据，请先扫描 Schema
        </Typography>
      </Box>
    );
  }

  return (
    <List dense disablePadding>
      {tables.map((t) => (
        <ListItemButton
          key={t.id}
          selected={t.id === selectedId}
          onClick={() => onSelect(t.id)}
          sx={{ borderRadius: 1, mb: 0.5 }}
        >
          <ListItemText
            primary={t.display_name || t.table_name}
            secondary={t.business_description || t.table_name}
            primaryTypographyProps={{ fontSize: 13, fontWeight: 500 }}
            secondaryTypographyProps={{ fontSize: 11 }}
          />
        </ListItemButton>
      ))}
    </List>
  );
}
