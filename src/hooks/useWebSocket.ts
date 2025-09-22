/**
 * React hook for WebSocket functionality.
 * Provides real-time data updates with automatic connection management.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  websocketService,
  type ConnectionState,
  type WebSocketMessage,
  type SubscriptionType,
  type DetectionUpdateMessage,
  type ZoneUpdateMessage,
  type EfficiencyUpdateMessage,
  type AlertMessage
} from '../services/websocketService';

// Hook return type
interface UseWebSocketReturn {
  // Connection state
  connectionState: ConnectionState;
  isConnected: boolean;
  error: string | null;

  // Connection management
  connect: (workstationId: string, token?: string) => void;
  disconnect: () => void;
  subscribe: (workstationIds: string[], subscriptionTypes?: SubscriptionType[]) => void;
  unsubscribe: (workstationIds?: string[], subscriptionTypes?: SubscriptionType[]) => void;

  // Latest data
  latestDetection: DetectionUpdateMessage | null;
  latestZoneUpdate: ZoneUpdateMessage | null;
  latestEfficiency: EfficiencyUpdateMessage | null;
  latestAlert: AlertMessage | null;

  // Message history
  detectionHistory: DetectionUpdateMessage[];
  zoneHistory: ZoneUpdateMessage[];
  efficiencyHistory: EfficiencyUpdateMessage[];
  alertHistory: AlertMessage[];

  // Statistics
  totalMessages: number;
  messagesPerSecond: number;
}

// Hook options
interface UseWebSocketOptions {
  workstationId?: string;
  autoConnect?: boolean;
  subscriptionTypes?: SubscriptionType[];
  maxHistorySize?: number;
  autoReconnect?: boolean;
}

/**
 * Hook for WebSocket real-time data
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    workstationId,
    autoConnect = false,
    subscriptionTypes = ['all'],
    maxHistorySize = 50,
    autoReconnect = true
  } = options;

  // Connection state
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [error, setError] = useState<string | null>(null);

  // Latest messages
  const [latestDetection, setLatestDetection] = useState<DetectionUpdateMessage | null>(null);
  const [latestZoneUpdate, setLatestZoneUpdate] = useState<ZoneUpdateMessage | null>(null);
  const [latestEfficiency, setLatestEfficiency] = useState<EfficiencyUpdateMessage | null>(null);
  const [latestAlert, setLatestAlert] = useState<AlertMessage | null>(null);

  // Message history
  const [detectionHistory, setDetectionHistory] = useState<DetectionUpdateMessage[]>([]);
  const [zoneHistory, setZoneHistory] = useState<ZoneUpdateMessage[]>([]);
  const [efficiencyHistory, setEfficiencyHistory] = useState<EfficiencyUpdateMessage[]>([]);
  const [alertHistory, setAlertHistory] = useState<AlertMessage[]>([]);

  // Statistics
  const [totalMessages, setTotalMessages] = useState(0);
  const [messagesPerSecond, setMessagesPerSecond] = useState(0);

  // Refs for tracking
  const messageCountRef = useRef(0);
  const lastStatsUpdateRef = useRef(Date.now());
  const statsIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Helper function to add to history with size limit
  const addToHistory = useCallback(
    <T>(setHistory: React.Dispatch<React.SetStateAction<T[]>>, newItem: T) => {
      setHistory(prev => {
        const updated = [newItem, ...prev];
        return updated.slice(0, maxHistorySize);
      });
    },
    [maxHistorySize]
  );

  // Message handler
  const handleMessage = useCallback((message: WebSocketMessage) => {
    messageCountRef.current++;
    setTotalMessages(prev => prev + 1);

    switch (message.type) {
      case 'detection_update':
        setLatestDetection(message);
        addToHistory(setDetectionHistory, message);
        break;

      case 'zone_update':
        setLatestZoneUpdate(message);
        addToHistory(setZoneHistory, message);
        break;

      case 'efficiency_update':
        setLatestEfficiency(message);
        addToHistory(setEfficiencyHistory, message);
        break;

      case 'alert':
        setLatestAlert(message);
        addToHistory(setAlertHistory, message);
        break;

      case 'error':
        console.error('WebSocket error message:', message.error_message);
        setError(message.error_message);
        break;

      default:
        console.log('Unknown message type:', message);
    }
  }, [addToHistory]);

  // State change handler
  const handleStateChange = useCallback((state: ConnectionState, errorMsg?: string) => {
    setConnectionState(state);
    setError(errorMsg || null);

    if (state === 'connected') {
      setError(null);
    }
  }, []);

  // Connection management functions
  const connect = useCallback(async (wsId: string, token?: string) => {
    try {
      await websocketService.connect(wsId, token);
    } catch (error) {
      console.error('Failed to connect:', error);
      setError(error instanceof Error ? error.message : 'Connection failed');
    }
  }, []);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const subscribe = useCallback((workstationIds: string[], subTypes?: SubscriptionType[]) => {
    websocketService.subscribe(workstationIds, subTypes || subscriptionTypes);
  }, [subscriptionTypes]);

  const unsubscribe = useCallback((workstationIds?: string[], subTypes?: SubscriptionType[]) => {
    websocketService.unsubscribe(workstationIds, subTypes);
  }, []);

  // Statistics calculation
  useEffect(() => {
    statsIntervalRef.current = setInterval(() => {
      const now = Date.now();
      const timeDiff = (now - lastStatsUpdateRef.current) / 1000; // seconds
      const messagesDiff = messageCountRef.current;

      if (timeDiff > 0) {
        setMessagesPerSecond(messagesDiff / timeDiff);
      }

      // Reset counters
      messageCountRef.current = 0;
      lastStatsUpdateRef.current = now;
    }, 1000);

    return () => {
      if (statsIntervalRef.current) {
        clearInterval(statsIntervalRef.current);
      }
    };
  }, []);

  // Setup event listeners
  useEffect(() => {
    const unsubscribeMessage = websocketService.onMessage(handleMessage);
    const unsubscribeState = websocketService.onStateChange(handleStateChange);

    return () => {
      unsubscribeMessage();
      unsubscribeState();
    };
  }, [handleMessage, handleStateChange]);

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && workstationId && connectionState === 'disconnected') {
      // Check if WebSocket service is already connected to the same workstation
      const connectionInfo = websocketService.getConnectionInfo();
      if (connectionInfo.currentWorkstationId === workstationId && connectionInfo.isConnected) {
        console.log(`WebSocket already connected to ${workstationId}, skipping auto-connect`);
        return;
      }

      connect(workstationId);
    }
  }, [autoConnect, workstationId, connectionState, connect]);

  // Auto-subscribe effect
  useEffect(() => {
    if (connectionState === 'connected' && workstationId) {
      subscribe([workstationId], subscriptionTypes);
    }
  }, [connectionState, workstationId, subscribe, subscriptionTypes]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Always call disconnect() to properly manage reference counting
      // The WebSocket service will only disconnect when no components need it
      disconnect();
    };
  }, [disconnect]);

  return {
    // Connection state
    connectionState,
    isConnected: connectionState === 'connected',
    error,

    // Connection management
    connect,
    disconnect,
    subscribe,
    unsubscribe,

    // Latest data
    latestDetection,
    latestZoneUpdate,
    latestEfficiency,
    latestAlert,

    // Message history
    detectionHistory,
    zoneHistory,
    efficiencyHistory,
    alertHistory,

    // Statistics
    totalMessages,
    messagesPerSecond
  };
}

/**
 * Hook for specific workstation WebSocket data
 */
export function useWorkstationWebSocket(
  workstationId: string,
  options: Omit<UseWebSocketOptions, 'workstationId'> = {}
): UseWebSocketReturn {
  return useWebSocket({
    workstationId,
    autoConnect: true,
    ...options  // Let options override defaults
  });
}

/**
 * Hook for multiple workstations WebSocket data
 */
export function useMultiWorkstationWebSocket(
  workstationIds: string[],
  options: Omit<UseWebSocketOptions, 'workstationId'> = {}
): UseWebSocketReturn & { subscribeToWorkstations: (ids: string[]) => void } {
  const webSocket = useWebSocket(options);

  const subscribeToWorkstations = useCallback((ids: string[]) => {
    if (webSocket.isConnected) {
      webSocket.subscribe(ids);
    }
  }, [webSocket]);

  // Auto-subscribe to all workstations when connected
  useEffect(() => {
    if (webSocket.isConnected && workstationIds.length > 0) {
      webSocket.subscribe(workstationIds);
    }
  }, [webSocket.isConnected, workstationIds, webSocket]);

  return {
    ...webSocket,
    subscribeToWorkstations
  };
}