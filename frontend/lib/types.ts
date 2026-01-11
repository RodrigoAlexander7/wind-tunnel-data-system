/**
 * Type definitions for the Wind Tunnel Data Acquisition System
 */

export interface SystemReading {
  timestamp: string;
  rpm: number;
  lift_force: number;
  [key: string]: string | number; // Index signature for chart compatibility
}

export interface SystemStatus {
  arduino_connected: boolean;
  websocket_clients: number;
  is_recording: boolean;
  readings_count: number;
}

export interface WebSocketMessage {
  type: string;
  data?: unknown;
  value?: number;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
