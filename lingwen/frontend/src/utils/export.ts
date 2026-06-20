import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';

/**
 * Escape a CSV field value: wrap in double quotes if it contains comma,
 * double quote, or newline, and escape internal double quotes.
 */
function escapeCsvField(value: string): string {
  const needsQuoting = value.includes(',') || value.includes('"') || value.includes('\n') || value.includes('\r');
  if (needsQuoting) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

/**
 * Export query result data as a UTF-8 CSV file with BOM.
 *
 * @param data    - Row data array (key-value objects).
 * @param columns - Ordered list of column names.
 * @param filename - Output filename; defaults to `query_result_{timestamp}.csv`.
 */
export function exportCSV(
  data: Record<string, unknown>[],
  columns: string[],
  filename?: string,
): void {
  const headerRow = columns.map(escapeCsvField).join(',');
  const bodyRows = data.map((row) =>
    columns.map((col) => {
      const value = row[col];
      const text = value === null || value === undefined ? '' : String(value);
      return escapeCsvField(text);
    }).join(','),
  );
  const csvContent = '\uFEFF' + [headerRow, ...bodyRows].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const outputName = filename || `query_result_${Date.now()}.csv`;
  saveAs(blob, outputName);
}

/**
 * Export query result data as an Excel (.xlsx) file with bold header row.
 *
 * @param data    - Row data array (key-value objects).
 * @param columns - Ordered list of column names.
 * @param filename - Output filename; defaults to `query_result_{timestamp}.xlsx`.
 */
export function exportExcel(
  data: Record<string, unknown>[],
  columns: string[],
  filename?: string,
): void {
  const rows: unknown[][] = [];

  // Header row
  rows.push(columns);

  // Data rows
  for (const row of data) {
    rows.push(columns.map((col) => row[col] ?? ''));
  }

  const worksheet = XLSX.utils.aoa_to_sheet(rows);

  // Bold the header row
  const headerRange = XLSX.utils.decode_range(worksheet['!ref'] || 'A1');
  for (let colIdx = headerRange.s.c; colIdx <= headerRange.e.c; colIdx++) {
    const cellAddress = XLSX.utils.encode_cell({ r: 0, c: colIdx });
    const cell = worksheet[cellAddress];
    if (cell) {
      cell.s = cell.s || {};
      cell.s.font = { bold: true };
    }
  }

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, '查询结果');
  const outputName = filename || `query_result_${Date.now()}.xlsx`;
  XLSX.writeFile(workbook, outputName);
}
