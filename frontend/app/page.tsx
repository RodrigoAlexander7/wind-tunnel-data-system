/**
 * Wind Tunnel Dashboard - Main page
 * Real-time monitoring and control interface
 */
'use client';

import React from 'react';
import {
  ChartModule,
  StatusPanel,
  CurrentReadings,
  CustomChart
} from '@/components';
import { useWindTunnelStore } from '@/lib/store';
import { useWebSocket } from '@/lib/useWebSocket';

export default function Dashboard() {
  const { readings } = useWindTunnelStore();

  // Initialize WebSocket connection
  useWebSocket();

  return (
    <div className="min-h-screen bg-zinc-100 dark:bg-zinc-950 p-6">
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
          🌪️ Wind Tunnel Monitor
        </h1>
        <p className="text-zinc-600 dark:text-zinc-400 mt-1">
          Sistema de adquisición y visualización de datos en tiempo real
        </p>
      </header>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Column - Controls and Status */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <StatusPanel />

          <CurrentReadings />
        </div>

        {/* Right Column - Charts */}
        <div className="col-span-12 lg:col-span-9 space-y-6">


          {/* Time Series Charts */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Lift over Time */}
            <ChartModule
              data={readings}
              xKey="timestamp"
              yKey="lift_force"
              title="📊 Sustentación en el Tiempo"
              yLabel="Fuerza (N)"
              color="#3b82f6"
            />

            {/* RPM over Time */}
            <ChartModule
              data={readings}
              xKey="timestamp"
              yKey="rpm"
              title="🔄 RPM en el Tiempo"
              yLabel="RPM"
              color="#f59e0b"
            />
          </div>

          {/* Custom Chart */}
          <CustomChart />
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-8 text-center text-sm text-zinc-500">
        Wind Tunnel Data Acquisition System | ONISAT Ground Station
      </footer>
    </div>
  );
}
