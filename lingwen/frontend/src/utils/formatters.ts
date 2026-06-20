export function formatNumber(n: number): string {
  return n.toLocaleString('zh-CN');
}

export function formatDate(s: string): string {
  const d = new Date(s);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function formatPercent(n: number): string {
  const sign = n >= 0 ? '+' : '';
  return `${sign}${n.toFixed(1)}%`;
}

export function truncate(text: string, maxLen: number = 60): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + '...';
}

export function formatLatency(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/* ================================================================
 * Chart & data helpers
 * ================================================================ */

import type { ChartSuggestion } from '../types';
import type { ChartData, ChartOptions } from 'chart.js';

/**
 * Limit rows to the first `maxRows` entries.
 */
export function limitRows<T>(data: T[], maxRows: number): T[] {
  return data.slice(0, maxRows);
}

/**
 * Build a Chart.js config object from query result data.
 *
 * Rules:
 * - First column → labels
 * - bar/line: remaining columns → one dataset each
 * - pie: only the second column used as values, first column as labels
 * - Data is truncated to maxRows (default 50).
 */
export function buildChartConfig(
  data: Record<string, unknown>[],
  columns: string[],
  suggestion: ChartSuggestion,
  maxRows: number = 50,
): { data: ChartData; options: ChartOptions } {
  const truncated = limitRows(data, maxRows);
  const labels = truncated.map((row) => String(row[columns[0]] ?? ''));

  if (suggestion.type === 'pie') {
    const valueCol = columns[1] || columns[0];
    const values = truncated.map((row) => {
      const v = row[valueCol];
      return typeof v === 'number' ? v : Number(v) || 0;
    });

    return {
      data: {
        labels,
        datasets: [
          {
            label: valueCol,
            data: values,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: suggestion.title,
          },
        },
      },
    };
  }

  // bar / line: remaining columns each become a dataset
  const valueColumns = columns.slice(1);
  const datasets = valueColumns.map((col) => ({
    label: col,
    data: truncated.map((row) => {
      const v = row[col];
      return typeof v === 'number' ? v : Number(v) || 0;
    }),
  }));

  return {
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: suggestion.title,
        },
      },
    },
  };
}
