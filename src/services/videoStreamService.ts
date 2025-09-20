import { apiClient } from './api';
import type { VideoSourceConfig } from './workstationService';

export interface VideoStream {
  id: number;
  name: string;
  workstation_id: number;
  source_type: 'rtsp' | 'usb' | 'ip' | 'file';
  source_url: string;
  status: 'active' | 'inactive' | 'error' | 'connecting';
  fps: number;
  resolution: string;
  last_frame_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateVideoStreamRequest {
  name: string;
  workstation_id: number;
  source_type: 'rtsp' | 'usb' | 'ip' | 'file';
  source_url: string;
}

export interface UpdateVideoStreamRequest {
  name?: string;
  source_type?: 'rtsp' | 'usb' | 'ip' | 'file';
  source_url?: string;
}

export interface StreamStatus {
  id: number;
  status: 'active' | 'inactive' | 'error' | 'connecting';
  fps: number;
  frames_processed: number;
  last_detection_at?: string;
  error_message?: string;
}

export interface DetectionResult {
  id: number;
  stream_id: number;
  timestamp: string;
  total_persons: number;
  zone_results: {
    zone_id: number;
    zone_name: string;
    person_count: number;
    status: 'work' | 'idle' | 'other';
    tracking_ids: number[];
  }[];
}

// Mock data for development when backend is not available
const mockVideoStreams: VideoStream[] = [
  {
    id: 1,
    name: 'Assembly Line Camera 1',
    workstation_id: 1,
    source_type: 'rtsp',
    source_url: 'rtsp://admin:password@192.168.1.100:554/stream1',
    status: 'active',
    fps: 15,
    resolution: '1920x1080',
    last_frame_at: new Date().toISOString(),
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:49:00Z'
  },
  {
    id: 2,
    name: 'QC Station Camera',
    workstation_id: 2,
    source_type: 'usb',
    source_url: '/dev/video0',
    status: 'inactive',
    fps: 0,
    resolution: '1280x720',
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:14:00Z'
  },
  {
    id: 3,
    name: 'Packaging Unit Camera',
    workstation_id: 3,
    source_type: 'ip',
    source_url: 'http://192.168.1.101:8080/video',
    status: 'active',
    fps: 20,
    resolution: '1920x1080',
    last_frame_at: new Date().toISOString(),
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:48:00Z'
  }
];

class VideoStreamService {
  async getVideoStreams(workstationId?: number): Promise<VideoStream[]> {
    try {
      const url = workstationId
        ? `/video-streams/?workstation_id=${workstationId}`
        : '/video-streams/';
      const response = await apiClient.get<VideoStream[]>(url);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      return workstationId
        ? mockVideoStreams.filter(s => s.workstation_id === workstationId)
        : mockVideoStreams;
    }
  }

  async getVideoStream(id: number): Promise<VideoStream> {
    try {
      const response = await apiClient.get<VideoStream>(`/video-streams/${id}`);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      const stream = mockVideoStreams.find(s => s.id === id);
      if (!stream) {
        throw new Error(`Video stream with id ${id} not found`);
      }
      return stream;
    }
  }

  async createVideoStream(data: CreateVideoStreamRequest): Promise<VideoStream> {
    try {
      const response = await apiClient.post<VideoStream>('/video-streams/', data);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const newStream: VideoStream = {
        id: Math.max(...mockVideoStreams.map(s => s.id)) + 1,
        name: data.name,
        workstation_id: data.workstation_id,
        source_type: data.source_type,
        source_url: data.source_url,
        status: 'inactive',
        fps: 0,
        resolution: '1920x1080',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      mockVideoStreams.push(newStream);
      return newStream;
    }
  }

  async updateVideoStream(id: number, data: UpdateVideoStreamRequest): Promise<VideoStream> {
    try {
      const response = await apiClient.put<VideoStream>(`/video-streams/${id}`, data);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const index = mockVideoStreams.findIndex(s => s.id === id);
      if (index === -1) {
        throw new Error(`Video stream with id ${id} not found`);
      }

      mockVideoStreams[index] = {
        ...mockVideoStreams[index],
        ...data,
        updated_at: new Date().toISOString()
      };
      return mockVideoStreams[index];
    }
  }

  async deleteVideoStream(id: number): Promise<void> {
    try {
      await apiClient.delete(`/video-streams/${id}`);
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const index = mockVideoStreams.findIndex(s => s.id === id);
      if (index === -1) {
        throw new Error(`Video stream with id ${id} not found`);
      }
      mockVideoStreams.splice(index, 1);
    }
  }

  async startStream(id: number): Promise<void> {
    try {
      await apiClient.post(`/video-streams/${id}/start`);
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const stream = mockVideoStreams.find(s => s.id === id);
      if (stream) {
        stream.status = 'connecting';
        setTimeout(() => {
          stream.status = 'active';
          stream.fps = 15;
          stream.last_frame_at = new Date().toISOString();
        }, 2000);
      }
    }
  }

  async stopStream(id: number): Promise<void> {
    try {
      await apiClient.post(`/video-streams/${id}/stop`);
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const stream = mockVideoStreams.find(s => s.id === id);
      if (stream) {
        stream.status = 'inactive';
        stream.fps = 0;
        stream.last_frame_at = undefined;
      }
    }
  }

  async getStreamStatus(id: number): Promise<StreamStatus> {
    try {
      const response = await apiClient.get<StreamStatus>(`/video-streams/${id}/status`);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      const stream = mockVideoStreams.find(s => s.id === id);
      if (!stream) {
        throw new Error(`Video stream with id ${id} not found`);
      }

      return {
        id: stream.id,
        status: stream.status,
        fps: stream.fps,
        frames_processed: Math.floor(Math.random() * 1000),
        last_detection_at: stream.last_frame_at,
        error_message: stream.status === 'error' ? 'Connection failed' : undefined
      };
    }
  }

  async getStreamResults(id: number): Promise<DetectionResult[]> {
    try {
      const response = await apiClient.get<DetectionResult[]>(`/video-streams/${id}/results`);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);

      // Mock detection result
      return [{
        id: 1,
        stream_id: id,
        timestamp: new Date().toISOString(),
        total_persons: 2,
        zone_results: [
          {
            zone_id: 1,
            zone_name: 'Assembly Area',
            person_count: 2,
            status: 'work',
            tracking_ids: [1, 2]
          }
        ]
      }];
    }
  }

  async getStreamsByWorkstation(workstationId: number): Promise<VideoStream[]> {
    return this.getVideoStreams(workstationId);
  }

  // Test RTSP connection
  async testRtspConnection(rtspUrl: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.post('/video-streams/test-rtsp', { rtsp_url: rtspUrl });
      return response.data;
    } catch (error) {
      console.warn('Backend not available for RTSP test:', error);
      // Mock response for development
      if (rtspUrl.startsWith('rtsp://')) {
        return { success: true, message: 'RTSP connection test successful (mocked)' };
      } else {
        return { success: false, message: 'Invalid RTSP URL format' };
      }
    }
  }

  // Generate video URL for frontend VideoPlayer
  generateVideoUrl(stream: VideoStream): string {
    switch (stream.source_type) {
      case 'rtsp':
        // RTSP streams are proxied through backend as HLS
        return `${window.location.origin}/api/v1/video-streams/${stream.id}/hls`;
      case 'usb':
        // USB cameras use getUserMedia - return deviceId for frontend
        return stream.source_url;
      case 'file':
        // File uploads - should be handled by frontend blob URL
        return stream.source_url;
      case 'ip':
        // IP cameras direct stream
        return stream.source_url;
      default:
        return '';
    }
  }

  // Convert VideoSourceConfig to CreateVideoStreamRequest
  convertFromVideoConfig(
    workstationId: number,
    workstationName: string,
    videoConfig: VideoSourceConfig
  ): CreateVideoStreamRequest {
    let sourceType: 'rtsp' | 'usb' | 'ip' | 'file' = 'file';
    let sourceUrl = '';

    switch (videoConfig.type) {
      case 'rtsp':
        sourceType = 'rtsp';
        sourceUrl = videoConfig.url || '';
        break;
      case 'usb':
        sourceType = 'usb';
        sourceUrl = videoConfig.usbDeviceId || '';
        break;
      case 'file':
        sourceType = 'file';
        sourceUrl = videoConfig.fileName || '';
        break;
      default:
        sourceType = 'file';
        sourceUrl = '';
    }

    return {
      name: `${workstationName} Camera`,
      workstation_id: workstationId,
      source_type: sourceType,
      source_url: sourceUrl
    };
  }
}

export const videoStreamService = new VideoStreamService();