/**
 * Master Type Definitions for Marmot Edge Industrial Monitoring System
 * This file consolidates all shared types to prevent TypeScript inconsistencies
 */

// ============================================================================
// CORE STATUS TYPES
// ============================================================================

/** Union type for zone/workstation status - lowercase only */
export type ZoneStatus = 'work' | 'idle' | 'other';

/** Capitalized status type for UI display - to be phased out */
export type DisplayStatus = 'Work' | 'Idle' | 'Other';

// ============================================================================
// ZONE INTERFACES
// ============================================================================

/** Main Zone interface matching backend schema */
export interface Zone {
  id: number;
  name: string;
  workstation_id: number;
  coordinates: {
    points?: number[][];
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
  is_active: boolean;
  color: string;
  person_count: number;
  status: ZoneStatus;
  created_at: string;
  updated_at?: string;
}

/** Frontend-specific zone interface for canvas overlay */
export interface CanvasZone {
  id: number;
  name: string;
  x: number; // percentage 0-100
  y: number; // percentage 0-100
  width: number; // percentage 0-100
  height: number; // percentage 0-100
  color: string;
  status: ZoneStatus; // FIXED: Now uses lowercase only
}

/** Zone creation request */
export interface CreateZoneRequest {
  name: string;
  workstation_id: number;
  coordinates: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  is_active?: boolean;
  color: string;
}

/** Zone update request */
export interface UpdateZoneRequest {
  name?: string;
  coordinates?: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
  is_active?: boolean;
  color?: string;
}

// ============================================================================
// WORKSTATION INTERFACES
// ============================================================================

export interface Workstation {
  id: number;
  name: string;
  location: string;
  description: string;
  is_active: boolean;
  video_source?: VideoSourceConfig;
  efficiency: number;
  status: ZoneStatus;
  created_at: string;
  updated_at?: string;
}

// ============================================================================
// VIDEO SOURCE INTERFACES
// ============================================================================

export type VideoSourceType = 'rtsp' | 'usb' | 'file';

export interface VideoSourceConfig {
  type: VideoSourceType;
  source: string;
  settings?: {
    width?: number;
    height?: number;
    fps?: number;
  };
}

// ============================================================================
// DETECTION INTERFACES
// ============================================================================

export interface Detection {
  id: number;
  workstation_id: number;
  frame_timestamp: string;
  person_count: number;
  bounding_boxes: {
    boxes: number[][];
  };
  track_ids?: {
    track_ids: number[];
  };
  confidence_scores?: {
    detections: number[];
  };
  processing_time_ms: number;
  created_at: string;
}

/** Person tracking result from YOLOv11 */
export interface PersonTracking {
  track_id: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  confidence: number;
  class_id: number;
  class_name: string;
}

/** Video processing result */
export interface ProcessingResult {
  frame_number: number;
  timestamp: string;
  person_count: number;
  trackings: PersonTracking[];
  processing_time_ms: number;
  fps: number;
  queue_size: number;
}

// ============================================================================
// WEBSOCKET MESSAGE INTERFACES
// ============================================================================

export interface WebSocketMessage {
  type: 'detection' | 'zone_update' | 'efficiency' | 'alert' | 'heartbeat';
  workstation_id: number;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface DetectionMessage extends WebSocketMessage {
  type: 'detection';
  data: {
    person_count: number;
    bounding_boxes: number[][];
    track_ids: number[];
    confidence_scores: number[];
    processing_time_ms: number;
    frame_timestamp: string;
  };
}

export interface ZoneUpdateMessage extends WebSocketMessage {
  type: 'zone_update';
  data: {
    zone_id: number;
    status: ZoneStatus;
    person_count: number;
    updated_at: string;
  };
}

export interface EfficiencyMessage extends WebSocketMessage {
  type: 'efficiency';
  data: {
    efficiency_percentage: number;
    current_state: ZoneStatus;
    work_time_minutes: number;
    idle_time_minutes: number;
    other_time_minutes: number;
    total_time_minutes: number;
  };
}

// ============================================================================
// UTILITY TYPE HELPERS
// ============================================================================

/** Convert Display status to Zone status */
export function displayToZoneStatus(status: DisplayStatus): ZoneStatus {
  switch (status) {
    case 'Work': return 'work';
    case 'Idle': return 'idle';
    case 'Other': return 'other';
    default: return 'idle';
  }
}

/** Convert Zone status to Display status */
export function zoneToDisplayStatus(status: ZoneStatus): DisplayStatus {
  switch (status) {
    case 'work': return 'Work';
    case 'idle': return 'Idle';
    case 'other': return 'Other';
    default: return 'Idle';
  }
}

/** Validate zone status */
export function isValidZoneStatus(status: string): status is ZoneStatus {
  return ['work', 'idle', 'other'].includes(status);
}

// ============================================================================
// TEST INTERFACES (for Python test compatibility)
// ============================================================================

/** Mock processing result for tests - matches ProcessingResult exactly */
export interface MockProcessingResult extends ProcessingResult {
  /** Flag to indicate this is a mock for testing */
  is_mock?: boolean;
}

/** Mock WebSocket for tests */
export interface MockWebSocket {
  send: (data: string) => void;
  close: () => void;
  readyState: number;
  CONNECTING: number;
  OPEN: number;
  CLOSING: number;
  CLOSED: number;
}