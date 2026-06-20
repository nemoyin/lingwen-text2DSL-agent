import {
  Chip,
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
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import type { DataSource } from '../../types';

interface Props {
  datasources: DataSource[];
  onEdit: (ds: DataSource) => void;
  onTest: (id: number) => void;
  onScan: (id: number) => void;
  onDelete: (id: number) => void;
}

export default function DatasourceList({
  datasources,
  onEdit,
  onTest,
  onScan,
  onDelete,
}: Props) {
  if (!datasources.length) {
    return null;
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 500 }}>名称</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>类型</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>连接信息</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>数据库</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>状态</TableCell>
            <TableCell sx={{ fontWeight: 500 }}>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {datasources.map((ds) => (
            <TableRow key={ds.id} hover>
              <TableCell sx={{ fontWeight: 500 }}>{ds.name}</TableCell>
              <TableCell>{ds.db_type === 'csv_temp' ? 'CSV 上传' : ds.db_type}</TableCell>
              <TableCell>
                {ds.host}:{ds.port}
              </TableCell>
              <TableCell>{ds.database}</TableCell>
              <TableCell>
                <Chip
                  size="small"
                  label={ds.status === 'active' ? '已连接' : '未连接'}
                  color={ds.status === 'active' ? 'success' : 'warning'}
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                <IconButton size="small" onClick={() => onEdit(ds)} title="编辑">
                  <EditIcon fontSize="small" />
                </IconButton>
                {ds.status === 'active' ? (
                  <IconButton size="small" onClick={() => onScan(ds.id)} title="扫描Schema">
                    <TravelExploreIcon fontSize="small" />
                  </IconButton>
                ) : (
                  <IconButton size="small" onClick={() => onTest(ds.id)} title="测试连接">
                    <PlayArrowIcon fontSize="small" />
                  </IconButton>
                )}
                <IconButton
                  size="small"
                  onClick={() => onDelete(ds.id)}
                  title="删除"
                  color="error"
                >
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
