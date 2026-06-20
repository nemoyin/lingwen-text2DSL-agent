import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { truncate } from '../../utils/formatters';
import type { FewShotExample } from '../../types';

interface Props {
  examples: FewShotExample[];
  onEdit: (example: FewShotExample) => void;
  onDelete: (id: number) => void;
}

export default function FewShotList({ examples, onEdit, onDelete }: Props) {
  if (!examples.length) return null;

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 500 }}>问题</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>SQL</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>标签</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {examples.map((ex) => (
            <TableRow key={ex.id} hover>
              <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {truncate(ex.question, 50)}
              </TableCell>
              <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {truncate(ex.sql, 60)}
              </TableCell>
              <TableCell>{ex.tags || '-'}</TableCell>
              <TableCell>
                <IconButton size="small" onClick={() => onEdit(ex)} title="编辑">
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton size="small" onClick={() => onDelete(ex.id)} title="删除" color="error">
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
