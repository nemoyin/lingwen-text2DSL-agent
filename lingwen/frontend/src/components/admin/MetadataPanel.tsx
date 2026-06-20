import { Box } from '@mui/material';
import LoadingSpinner from '../common/LoadingSpinner';
import TableTree from './TableTree';
import ColumnEditor from './ColumnEditor';
import type { TableMetadata, ColumnMetadata, ColumnMetadataUpdate } from '../../types';

interface Props {
  loading: boolean;
  tables: TableMetadata[];
  columns: ColumnMetadata[];
  selectedTableId: number | null;
  onTableSelect: (tableId: number) => void;
  onColumnUpdate: (columnId: number, data: ColumnMetadataUpdate) => Promise<void>;
}

export default function MetadataPanel({
  loading,
  tables,
  columns,
  selectedTableId,
  onTableSelect,
  onColumnUpdate,
}: Props) {
  if (loading) return <LoadingSpinner message="加载元数据..." />;

  return (
    <Box display="flex" gap={2}>
      <Box width={240} flexShrink={0} border="0.5px solid" borderColor="divider" borderRadius={2} p={1}>
        <TableTree tables={tables} selectedId={selectedTableId} onSelect={onTableSelect} />
      </Box>
      <Box flex={1}>
        <ColumnEditor columns={columns} onUpdate={onColumnUpdate} />
      </Box>
    </Box>
  );
}
