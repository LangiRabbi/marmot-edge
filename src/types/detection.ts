/**
 * Detection and tracking types for YOLOv11 integration
 */

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Detection {
  bbox: BoundingBox;
  confidence: number;
  class: string;
  track_id: number | null;
}

export interface ZoneAnalysis {
  zone_id: number;
  zone_name: string;
  person_count: number;
  status: 'idle' | 'work' | 'other';
  track_ids: number[];
  timestamp: string;
  rectangle: {
    x_min: number;
    y_min: number;
    x_max: number;
    y_max: number;
  };
}

export interface DetectionResponse {
  detection_id: number;
  workstation_id: number;
  timestamp: string;
  person_count: number;
  trackings: Detection[];
  zone_analysis: {
    stream_id: string;
    analysis_timestamp: string;
    zones: Record<string, ZoneAnalysis>;
    total_persons_detected: number;
  };
  processing_time_ms: number;
  frame_width?: number;  // Original captured frame width for coordinate scaling
  frame_height?: number; // Original captured frame height for coordinate scaling
}

export interface DetectionRequest {
  workstation_id: number;
  frame: Blob;
  confidence_threshold?: number;
  persist_tracking?: boolean;
  frame_width?: number;  // For backend to include in response
  frame_height?: number; // For backend to include in response
}