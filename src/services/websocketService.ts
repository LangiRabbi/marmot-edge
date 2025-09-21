/**
 * WebSocket service for real-time communication with the backend.
 * Provides secure, authenticated connections with auto-reconnection.
 */

import { apiClient } from './api';

// WebSocket message types
export type MessageType =
  | 'subscribe' | 'unsubscribe' | 'ping'
  | 'detection_update' | 'zone_update' | 'efficiency_update' | 'alert'
  | 'pong' | 'error' | 'connected' | 'disconnected';

export type SubscriptionType = 'detections' | 'zones' | 'efficiency' | 'alerts' | 'all';

// Message interfaces
export interface BaseMessage {
  type: MessageType;
  timestamp: string;
  id?: string;
}

export interface SubscribeMessage extends BaseMessage {
  type: 'subscribe';
  workstation_ids: string[];
  subscription_types: SubscriptionType[];
}

export interface DetectionUpdateMessage extends BaseMessage {
  type: 'detection_update';
  workstation_id: string;
  frame_timestamp: string;
  person_count: number;
  persons: PersonDetection[];
  processing_fps: number;
  frame_number: number;
}

export interface PersonDetection {
  tracking_id: number;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  center: [number, number]; // [x, y]
  zones: string[];
}

export interface ZoneUpdateMessage extends BaseMessage {
  type: 'zone_update';
  workstation_id: string;
  zones: ZoneOccupancy[];
  total_persons: number;
}

export interface ZoneOccupancy {
  zone_id: string;
  person_count: number;
  person_ids: number[];
  occupancy_changed: boolean;
}

export interface EfficiencyUpdateMessage extends BaseMessage {
  type: 'efficiency_update';
  workstation_id: string;
  metrics: EfficiencyMetrics;
  period_start: string;
  period_end: string;
}

export interface EfficiencyMetrics {
  work_time_seconds: number;
  idle_time_seconds: number;
  other_time_seconds: number;
  total_time_seconds: number;
  efficiency_percentage: number;
  current_state: 'work' | 'idle' | 'other';
}

export interface AlertMessage extends BaseMessage {
  type: 'alert';
  workstation_id: string;
  alert_type: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  data?: Record<string, any>;
}

export interface ErrorMessage extends BaseMessage {
  type: 'error';
  error_code: string;
  error_message: string;
  details?: Record<string, any>;
}

export type WebSocketMessage =
  | DetectionUpdateMessage
  | ZoneUpdateMessage
  | EfficiencyUpdateMessage
  | AlertMessage
  | ErrorMessage;

// Connection state
export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

// Event listeners
export type MessageListener = (message: WebSocketMessage) => void;
export type StateListener = (state: ConnectionState, error?: string) => void;

// WebSocket service configuration
interface WebSocketConfig {
  baseUrl?: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  maxReconnectDelay?: number;
  heartbeatInterval?: number;
  authRequired?: boolean;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private state: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private currentToken: string | null = null;
  private subscriptions: Set<string> = new Set();

  // Connection reference counting
  private connectionRefs = 0;
  private currentWorkstationId: string | null = null;

  // Event listeners
  private messageListeners: Set<MessageListener> = new Set();
  private stateListeners: Set<StateListener> = new Set();

  constructor(config: WebSocketConfig = {}) {
    this.config = {
      baseUrl: config.baseUrl || 'ws://localhost:8001',
      reconnectAttempts: config.reconnectAttempts || 5,
      reconnectDelay: config.reconnectDelay || 1000,
      maxReconnectDelay: config.maxReconnectDelay || 30000,
      heartbeatInterval: config.heartbeatInterval || 30000,
      authRequired: config.authRequired ?? true
    };
  }

  /**
   * Connect to WebSocket with optional authentication
   */
  async connect(workstationId: string, token?: string): Promise<void> {
    // Increment reference count
    this.connectionRefs++;
    console.log(`WebSocket connect() called. References: ${this.connectionRefs}`);

    // If already connected to the same workstation, just return
    if (this.ws && this.state === 'connected' && this.currentWorkstationId === workstationId) {
      console.log('WebSocket already connected to same workstation');
      return;
    }

    // If connected to different workstation, close and reconnect
    if (this.ws && this.state === 'connected' && this.currentWorkstationId !== workstationId) {
      console.log(`Switching workstation from ${this.currentWorkstationId} to ${workstationId}`);
      this.forceDisconnect();
    }

    this.currentWorkstationId = workstationId;
    this.setState('connecting');

    try {
      // Get or generate token
      if (this.config.authRequired) {
        if (token) {
          this.currentToken = token;
        } else {
          // Get demo token for development
          this.currentToken = await this.getDemoToken();
        }
      }

      // Build WebSocket URL
      let wsUrl = `${this.config.baseUrl}/api/v1/ws/${workstationId}`;
      if (this.currentToken) {
        wsUrl += `?token=${this.currentToken}`;
      }

      // Create WebSocket connection
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();

    } catch (error) {
      this.setState('error', error instanceof Error ? error.message : 'Connection failed');
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect WebSocket (with reference counting)
   */
  disconnect(): void {
    // Decrement reference count
    this.connectionRefs = Math.max(0, this.connectionRefs - 1);
    console.log(`WebSocket disconnect() called. References: ${this.connectionRefs}`);

    // Only disconnect if no more references
    if (this.connectionRefs === 0) {
      console.log('No more references, closing WebSocket connection');
      this.forceDisconnect();
    }
  }

  /**
   * Force disconnect WebSocket (ignores reference counting)
   */
  forceDisconnect(): void {
    console.log('Force disconnecting WebSocket');
    this.clearTimers();
    this.reconnectAttempts = 0;
    this.connectionRefs = 0;
    this.currentWorkstationId = null;

    // Clear all subscriptions to prevent reconnect attempts with old workstation IDs
    this.subscriptions.clear();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setState('disconnected');
  }

  /**
   * Subscribe to workstation updates
   */
  subscribe(workstationIds: string[], subscriptionTypes: SubscriptionType[] = ['all']): void {
    // Check if we're connected or in the process of connecting
    if (!this.ws || (this.ws.readyState !== WebSocket.OPEN && this.state !== 'connected')) {
      console.warn('Cannot subscribe: WebSocket not connected');
      return;
    }

    // If WebSocket is opening but state is connected, wait a tiny bit
    if (this.ws.readyState === WebSocket.CONNECTING && this.state === 'connected') {
      setTimeout(() => this.subscribe(workstationIds, subscriptionTypes), 10);
      return;
    }

    const message: SubscribeMessage = {
      type: 'subscribe',
      workstation_ids: workstationIds,
      subscription_types: subscriptionTypes,
      timestamp: new Date().toISOString()
    };

    this.send(message);

    // Track subscriptions
    workstationIds.forEach(id => this.subscriptions.add(id));
  }

  /**
   * Unsubscribe from workstation updates
   */
  unsubscribe(workstationIds?: string[], subscriptionTypes?: SubscriptionType[]): void {
    if (!this.isConnected()) {
      console.warn('Cannot unsubscribe: WebSocket not connected');
      return;
    }

    const message = {
      type: 'unsubscribe' as const,
      workstation_ids: workstationIds,
      subscription_types: subscriptionTypes,
      timestamp: new Date().toISOString()
    };

    this.send(message);

    // Remove from tracking
    if (workstationIds) {
      workstationIds.forEach(id => this.subscriptions.delete(id));
    } else {
      this.subscriptions.clear();
    }
  }

  /**
   * Send ping to keep connection alive
   */
  ping(): void {
    if (!this.isConnected()) return;

    const message = {
      type: 'ping' as const,
      timestamp: new Date().toISOString()
    };

    this.send(message);
  }

  /**
   * Add message listener
   */
  onMessage(listener: MessageListener): () => void {
    this.messageListeners.add(listener);
    return () => this.messageListeners.delete(listener);
  }

  /**
   * Add state change listener
   */
  onStateChange(listener: StateListener): () => void {
    this.stateListeners.add(listener);
    return () => this.stateListeners.delete(listener);
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.state;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN && this.state === 'connected';
  }

  /**
   * Get current subscriptions
   */
  getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }

  /**
   * Get connection info (for debugging)
   */
  getConnectionInfo(): {
    connectionRefs: number;
    currentWorkstationId: string | null;
    state: ConnectionState;
    isConnected: boolean;
  } {
    return {
      connectionRefs: this.connectionRefs,
      currentWorkstationId: this.currentWorkstationId,
      state: this.state,
      isConnected: this.isConnected()
    };
  }

  // Private methods

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.setState('connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage | { type: 'pong' | 'connected' };

        if (message.type === 'pong') {
          // Handle heartbeat response
          return;
        }

        if (message.type === 'connected') {
          // Handle connection confirmation
          console.log('WebSocket connection confirmed');
          return;
        }

        // Broadcast to listeners
        this.messageListeners.forEach(listener => {
          try {
            listener(message as WebSocketMessage);
          } catch (error) {
            console.error('Error in message listener:', error);
          }
        });

      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
      this.clearTimers();

      if (event.code !== 1000 && this.reconnectAttempts < this.config.reconnectAttempts) {
        this.setState('reconnecting');
        this.scheduleReconnect();
      } else {
        this.setState('disconnected');
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.setState('error', 'Connection error');
    };
  }

  private send(message: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('Cannot send message: WebSocket not connected');
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
    }
  }

  private setState(state: ConnectionState, error?: string): void {
    if (this.state === state) return;

    this.state = state;
    this.stateListeners.forEach(listener => {
      try {
        listener(state, error);
      } catch (error) {
        console.error('Error in state listener:', error);
      }
    });
  }

  private scheduleReconnect(): void {
    this.clearTimers();

    if (this.reconnectAttempts >= this.config.reconnectAttempts) {
      this.setState('error', 'Max reconnection attempts reached');
      return;
    }

    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.config.maxReconnectDelay
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.config.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.reconnect();
    }, delay);
  }

  private async reconnect(): Promise<void> {
    // Only reconnect if we have a current workstation and subscriptions
    if (this.currentWorkstationId && this.subscriptions.size > 0) {
      console.log(`Attempting to reconnect to workstation: ${this.currentWorkstationId}`);
      await this.connect(this.currentWorkstationId, this.currentToken || undefined);

      // Re-subscribe to all workstations
      if (this.isConnected() && this.subscriptions.size > 0) {
        this.subscribe(Array.from(this.subscriptions));
      }
    } else {
      console.log('No active workstation or subscriptions, skipping reconnect');
    }
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.ping();
      }
    }, this.config.heartbeatInterval);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearTimers(): void {
    this.clearHeartbeat();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private async getDemoToken(): Promise<string> {
    try {
      const response = await apiClient.get('/websocket/demo-token');
      return response.data.token;
    } catch (error) {
      console.error('Failed to get demo token:', error);
      throw new Error('Authentication failed');
    }
  }
}

// Global WebSocket service instance
export const websocketService = new WebSocketService({
  baseUrl: 'ws://localhost:8001',
  authRequired: false // Disable auth for development
});

export default websocketService;