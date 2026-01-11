/**
 * CurrentReadings - Shows the latest sensor readings in real-time
 */
'use client';

import React from 'react';
import { useWindTunnelStore } from '@/lib/store';

export function CurrentReadings() {
  const { readings } = useWindTunnelStore();

  // Get the latest reading
  const latestReading = readings[readings.length - 1];

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 p-4">
      <h3 className="text-lg font-semibold mb-4 text-zinc-900 dark:text-zinc-100">
        Lecturas Actuales
      </h3>

      <div className="grid grid-cols-2 gap-4">

        {/* RPM */}
        <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div className="text-sm text-green-600 dark:text-green-400 mb-1">
            RPM
          </div>
          <div className="text-3xl font-bold text-green-700 dark:text-green-300">
            {latestReading ? latestReading.rpm.toFixed(0) : '---'}
          </div>
          <div className="text-xs text-green-500">rev/min</div>
        </div>

        {/* Lift Force */}
        <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
          <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">
            Sustentación
          </div>
          <div className="text-3xl font-bold text-purple-700 dark:text-purple-300">
            {latestReading ? latestReading.lift_force.toFixed(2) : '---'}
          </div>
          <div className="text-xs text-purple-500">N</div>
        </div>
      </div>

      {/* Timestamp */}
      {latestReading && (
        <div className="mt-4 text-center text-xs text-zinc-500">
          Última lectura: {new Date(latestReading.timestamp).toLocaleString('es-ES')}
        </div>
      )}
    </div>
  );
}
