/**
 * Zustand store for Wind Tunnel monitoring system state
 */
import { create } from 'zustand';
import { SystemReading, SystemStatus, ConnectionStatus } from './types';
import { config } from './config';

interface WindTunnelState {
  // Connection state
  connectionStatus: ConnectionStatus;

  // System status from backend
  systemStatus: SystemStatus | null;

  // Readings data for charts
  readings: SystemReading[];



  // Recording state
  isRecording: boolean;

  // Actions
  setConnectionStatus: (status: ConnectionStatus) => void;
  setSystemStatus: (status: SystemStatus) => void;
  addReading: (reading: SystemReading) => void;

  setRecording: (recording: boolean) => void;
  clearReadings: () => void;
}

export const useWindTunnelStore = create<WindTunnelState>((set) => ({
  // Initial state
  connectionStatus: 'disconnected',
  systemStatus: null,
  readings: [],

  isRecording: false,

  // Actions
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  setSystemStatus: (status) => set({
    systemStatus: status,
    isRecording: status.is_recording,
  }),

  addReading: (reading) => set((state) => {
    // Keep only the last N readings for performance
    const newReadings = [...state.readings, reading];
    if (newReadings.length > config.chart.maxDataPoints) {
      return { readings: newReadings.slice(-config.chart.maxDataPoints) };
    }
    return { readings: newReadings };
  }),



  setRecording: (recording) => set({ isRecording: recording }),

  clearReadings: () => set({ readings: [] }),
}));
