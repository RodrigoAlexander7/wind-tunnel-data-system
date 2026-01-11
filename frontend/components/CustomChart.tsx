/**
 * CustomChart - Allows user to select X and Y axes for visualization
 */
'use client';

import React, { useState, useMemo } from 'react';
import { ChartModule } from './ChartModule';
import { useWindTunnelStore } from '@/lib/store';

const AXIS_OPTIONS = [
  { value: 'rpm', label: 'RPM' },
  { value: 'lift_force', label: 'Sustentación (N)' },
  { value: 'timestamp', label: 'Tiempo' },
];

export function CustomChart() {
  const { readings } = useWindTunnelStore();
  const [xAxis, setXAxis] = useState('timestamp');
  const [yAxis, setYAxis] = useState('lift_force');

  const xLabel = AXIS_OPTIONS.find(o => o.value === xAxis)?.label || xAxis;
  const yLabel = AXIS_OPTIONS.find(o => o.value === yAxis)?.label || yAxis;

  // Sort data by X axis for proper line rendering
  // Only sort when xAxis changes or when necessary (not timestamp)
  const sortedData = useMemo(() => {
    // For timestamp, data is already in chronological order
    if (xAxis === 'timestamp') {
      return readings;
    }
    // For other axes, sort only if we have data
    if (readings.length === 0) {
      return readings;
    }
    return [...readings].sort((a, b) => {
      const aVal = a[xAxis as keyof typeof a] as number;
      const bVal = b[xAxis as keyof typeof b] as number;
      return aVal - bVal;
    });
  }, [readings, xAxis]);

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Gráfica Personalizada
        </h3>

        <div className="flex items-center gap-4">
          {/* X Axis Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-zinc-600 dark:text-zinc-400">Eje X:</label>
            <select
              value={xAxis}
              onChange={(e) => setXAxis(e.target.value)}
              className="px-2 py-1 border border-zinc-300 dark:border-zinc-700 rounded 
                         bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 text-sm"
            >
              {AXIS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Y Axis Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-zinc-600 dark:text-zinc-400">Eje Y:</label>
            <select
              value={yAxis}
              onChange={(e) => setYAxis(e.target.value)}
              className="px-2 py-1 border border-zinc-300 dark:border-zinc-700 rounded 
                         bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 text-sm"
            >
              {AXIS_OPTIONS.filter((o) => o.value !== 'timestamp').map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <ChartModule
        data={sortedData}
        xKey={xAxis}
        yKey={yAxis}
        title=""
        xLabel={xLabel}
        yLabel={yLabel}
        color="#f59e0b"
        height={280}
      />
    </div>
  );
}
