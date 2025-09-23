// Database abstraction layer interfaces for different deployment scenarios
import type { VideoSourceConfig } from '@/services/workstationService';

export interface WorkstationData {
  id: number;
  name: string;
  description?: string;
  location: string;
  is_active: boolean;
  video_source_type: 'rtsp' | 'usb' | 'file';
  video_source_config: VideoSourceConfig;
  current_status: string;
  last_detection_at?: string;
  created_at: string;
  updated_at: string;
  zones?: ZoneData[];
}

export interface WorkstationCreate {
  name: string;
  description?: string;
  location: string;
  video_source_type: 'rtsp' | 'usb' | 'file';
  video_source_config: VideoSourceConfig;
}

export interface WorkstationUpdate {
  name?: string;
  description?: string;
  location?: string;
  is_active?: boolean;
  video_source_type?: 'rtsp' | 'usb' | 'file';
  video_source_config?: VideoSourceConfig;
}

export interface ZoneData {
  id: number;
  workstation_id: number;
  name: string;
  description?: string;
  zone_type: string;
  coordinates: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ZoneCreate {
  workstation_id: number;
  name: string;
  description?: string;
  zone_type: string;
  coordinates: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
}

export interface ZoneUpdate {
  name?: string;
  description?: string;
  zone_type?: string;
  coordinates?: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  };
  is_active?: boolean;
}

export interface DetectionData {
  id: number;
  workstation_id: number;
  zone_id?: number;
  person_count: number;
  timestamp: string;
  confidence: number;
  bbox_data?: Record<string, number>;
}

export interface DatabaseService {
  // Workstation operations
  getWorkstations(skip?: number, limit?: number): Promise<WorkstationData[]>;
  getWorkstation(id: number): Promise<WorkstationData | null>;
  createWorkstation(data: WorkstationCreate): Promise<WorkstationData>;
  updateWorkstation(id: number, data: WorkstationUpdate): Promise<WorkstationData | null>;
  deleteWorkstation(id: number): Promise<boolean>;
  getWorkstationStatus(id: number): Promise<Record<string, unknown>>;

  // Zone operations
  getZones(workstationId?: number, skip?: number, limit?: number): Promise<ZoneData[]>;
  getZone(id: number): Promise<ZoneData | null>;
  createZone(data: ZoneCreate): Promise<ZoneData>;
  updateZone(id: number, data: ZoneUpdate): Promise<ZoneData | null>;
  deleteZone(id: number): Promise<boolean>;

  // Detection operations
  getDetections(workstationId?: number, skip?: number, limit?: number): Promise<DetectionData[]>;

  // Health check
  healthCheck(): Promise<boolean>;
}

// Deployment configuration
export enum DeploymentType {
  OnPremise = 'onpremise',
  Cloud = 'cloud',
  Edge = 'edge'
}

export interface DatabaseConfig {
  deploymentType: DeploymentType;
  baseUrl: string;
  apiVersion?: string;
  headers?: Record<string, string>;
  timeout?: number;
}