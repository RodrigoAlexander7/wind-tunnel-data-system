/**
 * WebSocket hook for real-time communication with the backend
 */
'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useWindTunnelStore } from './store';
import { config } from './config';
import { SystemReading, SystemStatus } from './types';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    setConnectionStatus,
    setSystemStatus,
    addReading,
    setRecording,
    connectionStatus,
  } = useWindTunnelStore();

  const connect = useCallback(() => {
    // Don't reconnect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(config.wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');

        // Clear any pending reconnect
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          console.log('📡 WebSocket Raw Data:', event.data);
          const data = JSON.parse(event.data);

          // Handle different message types
          if (data.type === 'status') {
            setSystemStatus(data.data as SystemStatus);
          } else if (data.type === 'recording_started') {
            setRecording(true);
          } else if (data.type === 'recording_stopped') {
            setRecording(false);
          } else if (data.type === 'readings_cleared') {
            useWindTunnelStore.getState().clearReadings();
          } else if (data.timestamp) {
            // This is a reading
            addReading(data as SystemReading);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Schedule reconnection
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, config.reconnectInterval);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
    }
  }, [setConnectionStatus, setSystemStatus, addReading, setRecording]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);



  const startRecording = useCallback(() => {
    sendMessage({ type: 'command', action: 'start_recording' });
  }, [sendMessage]);

  const stopRecording = useCallback(() => {
    sendMessage({ type: 'command', action: 'stop_recording' });
  }, [sendMessage]);

  const clearReadings = useCallback(() => {
    sendMessage({ type: 'command', action: 'clear' });
  }, [sendMessage]);

  const getStatus = useCallback(() => {
    sendMessage({ type: 'command', action: 'get_status' });
  }, [sendMessage]);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    connectionStatus,
    connect,
    disconnect,

    startRecording,
    stopRecording,
    clearReadings,
    getStatus,
  };
}
