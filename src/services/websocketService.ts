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
  data?: Record<string, unknown>;
}

export interface ErrorMessage extends BaseMessage {
  type: 'error';
  error_code: string;
  error_message: string;
  details?: Record<string, unknown>;
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
    console.log(`[WebSocket] connect() called for workstation ${workstationId}. References: ${this.connectionRefs}`);

    // If already connected to the same workstation, just return
    if (this.ws && this.state === 'connected' && this.currentWorkstationId === workstationId) {
      console.log('[WebSocket] Already connected to same workstation');
      return;
    }

    // If connected to different workstation, close and reconnect
    if (this.ws && this.state === 'connected' && this.currentWorkstationId !== workstationId) {
      console.log(`[WebSocket] Switching workstation from ${this.currentWorkstationId} to ${workstationId}`);
      this.forceDisconnect();
    }

    this.currentWorkstationId = workstationId;
    this.setState('connecting');

    try {
      // Only get token if auth is required
      if (this.config.authRequired) {
        if (token) {
          this.currentToken = token;
        } else {
          // Get demo token for development
          this.currentToken = await this.getDemoToken();
        }
      } else {
        console.log('[WebSocket] Auth disabled - connecting without token');
        this.currentToken = undefined;
      }

      // Build WebSocket URL
      let wsUrl = `${this.config.baseUrl}/api/v1/ws/${workstationId}`;
      if (this.currentToken) {
        wsUrl += `?token=${this.currentToken}`;
      }

      console.log(`[WebSocket] Attempting to connect to: ${wsUrl}`);

      // Create WebSocket connection
      this.ws = new WebSocket(wsUrl);
      console.log(`[WebSocket] WebSocket instance created, readyState: ${this.ws.readyState}`);

      this.setupEventHandlers();

      // Set connection timeout
      setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN && this.state !== 'connected') {
          console.error('[WebSocket] Connection timeout - closing WebSocket');
          this.ws.close();
          this.setState('error', 'Connection timeout');
        }
      }, 10000); // 10 second timeout

    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
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
    console.log(`[WebSocket] subscribe() called for workstations: ${workstationIds}, types: ${subscriptionTypes}`);
    console.log(`[WebSocket] Current state: ${this.state}, readyState: ${this.ws?.readyState}`);

    // Enhanced connection check
    if (!this.ws) {
      console.warn('[WebSocket] Cannot subscribe: WebSocket instance not found');
      return;
    }

    if (this.ws.readyState !== WebSocket.OPEN) {
      console.warn(`[WebSocket] Cannot subscribe: WebSocket not OPEN (readyState: ${this.ws.readyState})`);
      // Queue subscription for when connection is ready
      if (this.state === 'connecting' || this.state === 'reconnecting') {
        console.log('[WebSocket] Queueing subscription for when connection is ready');
        setTimeout(() => this.subscribe(workstationIds, subscriptionTypes), 100);
      }
      return;
    }

    if (this.state !== 'connected') {
      console.warn(`[WebSocket] Cannot subscribe: Service state not connected (state: ${this.state})`);
      return;
    }

    const message: SubscribeMessage = {
      type: 'subscribe',
      workstation_ids: workstationIds,
      subscription_types: subscriptionTypes,
      timestamp: new Date().toISOString()
    };

    console.log('[WebSocket] Sending subscription message:', JSON.stringify(message));

    try {
      this.send(message);

      // Track subscriptions only after successful send
      workstationIds.forEach(id => this.subscriptions.add(id));
      console.log(`[WebSocket] Updated subscriptions:`, Array.from(this.subscriptions));
    } catch (error) {
      console.error('[WebSocket] Failed to send subscription:', error);
    }
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
      console.log(`[WebSocket] onopen event fired, readyState: ${this.ws?.readyState}`);

      // Use setTimeout to ensure readyState is properly updated
      setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          console.log('[WebSocket] Connection verified - setting state to connected');
          this.setState('connected');
          this.reconnectAttempts = 0;
          this.startHeartbeat();

          // Send immediate ping to verify bidirectional communication
          console.log('[WebSocket] Sending verification ping');
          this.ping();

          // Auto-subscribe to current workstation if we have one
          if (this.currentWorkstationId) {
            console.log(`[WebSocket] Auto-subscribing to workstation: ${this.currentWorkstationId}`);
            setTimeout(() => {
              this.subscribe([this.currentWorkstationId!], ['detections', 'zones', 'efficiency', 'alerts']);
            }, 50); // Additional delay to ensure ping is sent first
          }
        } else {
          console.error(`[WebSocket] Connection failed - readyState: ${this.ws?.readyState}, expected: ${WebSocket.OPEN}`);
          this.setState('error', 'Connection verification failed');
        }
      }, 10); // Small delay to allow readyState to update
    };

    this.ws.onmessage = (event) => {
      console.log(`[WebSocket] Received message:`, event.data);
      try {
        const message = JSON.parse(event.data) as WebSocketMessage | { type: 'pong' | 'connected' | 'subscribed' };

        // Handle system messages
        if (message.type === 'pong') {
          console.log('[WebSocket] Received pong response - connection verified');
          return;
        }

        if (message.type === 'connected') {
          console.log('[WebSocket] Server connection confirmation received');
          return;
        }

        if (message.type === 'subscribed') {
          console.log('[WebSocket] Subscription confirmed by server');
          return;
        }

        // Enhanced detection message handling
        if (message.type === 'detection_update') {
          const detectionMsg = message as DetectionUpdateMessage;
          console.log('[WebSocket] 🎯 Detection message details:', {
            workstationId: detectionMsg.workstation_id,
            personCount: detectionMsg.person_count,
            personsArray: detectionMsg.persons,
            processingFps: detectionMsg.processing_fps,
            frameNumber: detectionMsg.frame_number
          });
        }

        console.log('[WebSocket] Broadcasting message to listeners:', message.type);
        // Broadcast to listeners
        this.messageListeners.forEach(listener => {
          try {
            listener(message as WebSocketMessage);
          } catch (error) {
            console.error('Error in message listener:', error);
          }
        });

      } catch (error) {
        console.error('[WebSocket] Error parsing message:', error, 'Raw data:', event.data);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`[WebSocket] Connection closed: ${event.code} - ${event.reason}`);
      this.clearTimers();

      if (event.code !== 1000 && this.reconnectAttempts < this.config.reconnectAttempts) {
        console.log('[WebSocket] Attempting to reconnect...');
        this.setState('reconnecting');
        this.scheduleReconnect();
      } else {
        console.log('[WebSocket] Connection closed permanently');
        this.setState('disconnected');
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WebSocket] Connection error:', error);
      console.log(`[WebSocket] Error details - readyState: ${this.ws?.readyState}`);
      this.setState('error', 'Connection error');
    };
  }

  private send(message: Record<string, unknown>): void {
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