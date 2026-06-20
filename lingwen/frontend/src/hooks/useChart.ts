import { useRef, useEffect, useCallback, useState } from 'react';
import { Chart, registerables } from 'chart.js';
import type { ChartSuggestion } from '../types';
import { buildChartConfig } from '../utils/formatters';

// Register all chart.js components once at module level.
Chart.register(...registerables);

/** Allowed chart types matching the ChartSuggestion union. */
type ChartType = ChartSuggestion['type'];

export interface UseChartOptions {
  /** Ref to the <canvas> element. */
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  /** Row data. */
  data: Record<string, unknown>[];
  /** Column names. */
  columns: string[];
  /** Chart suggestion from the backend. null → no chart is created. */
  suggestion: ChartSuggestion | null;
  /** Maximum number of rows to render in the chart (default 50). */
  maxRows?: number;
}

export interface UseChartReturn {
  /** Ref to the current Chart.js instance. */
  chartRef: React.MutableRefObject<Chart | null>;
  /** The currently active chart type. */
  currentType: ChartType;
  /** Switch to a different chart type (destroys old instance, creates new). */
  updateType: (newType: ChartType) => void;
}

/**
 * Hook that manages a Chart.js instance lifecycle.
 *
 * - Creates a new Chart when `suggestion`, `data`, or `columns` change.
 * - Exposes `updateType()` to switch chart types at runtime.
 * - Automatically destroys the chart on unmount.
 */
export function useChart(options: UseChartOptions): UseChartReturn {
  const { canvasRef, data, columns, suggestion, maxRows = 50 } = options;
  const chartRef = useRef<Chart | null>(null);
  const [currentType, setCurrentType] = useState<ChartType>(
    suggestion?.type || 'bar',
  );

  const destroyChart = useCallback(() => {
    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }
  }, []);

  const createChart = useCallback(
    (chartType: ChartType) => {
      destroyChart();
      if (!suggestion || !canvasRef.current || data.length <= 1) return;

      const config = buildChartConfig(data, columns, suggestion, maxRows);
      chartRef.current = new Chart(canvasRef.current, {
        type: chartType,
        data: config.data,
        options: config.options,
      });
    },
    [suggestion, data, columns, maxRows, canvasRef, destroyChart],
  );

  // Create chart on mount / when deps change.
  useEffect(() => {
    setCurrentType(suggestion?.type || 'bar');
    createChart(suggestion?.type || 'bar');
    return () => destroyChart();
  }, [suggestion, data, columns, maxRows, createChart, destroyChart]);

  const updateType = useCallback(
    (newType: ChartType) => {
      setCurrentType(newType);
      createChart(newType);
    },
    [createChart],
  );

  return { chartRef, currentType, updateType };
}
