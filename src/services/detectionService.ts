/**
 * Detection service for YOLO v11 API integration
 * Handles frame upload and detection result retrieval
 */

import api from './api';
import type { DetectionResponse, DetectionRequest } from '@/types/detection';

class DetectionService {
  /**
   * Send frame to backend for YOLO detection
   */
  async detectPersons(request: DetectionRequest): Promise<DetectionResponse> {
    try {
      const formData = new FormData();
      formData.append('file', request.frame, 'frame.jpg');
      formData.append('workstation_id', request.workstation_id.toString());
      formData.append('confidence_threshold', (request.confidence_threshold ?? 0.5).toString());
      formData.append('persist_tracking', (request.persist_tracking ?? true).toString());

      console.log('🔍 DetectionService: Sending request with FormData:');
      console.log('  - workstation_id:', request.workstation_id);
      console.log('  - confidence_threshold:', request.confidence_threshold ?? 0.5);
      console.log('  - persist_tracking:', request.persist_tracking ?? true);
      console.log('  - frame size:', request.frame.size, 'bytes');

      // DON'T set Content-Type at all - let browser set multipart/form-data with boundary automatically
      const response = await api.post<DetectionResponse>(
        `/detection/detect/image`,
        formData
        // No config - browser will set Content-Type with boundary automatically
      );

      console.log('✅ DetectionService: Got response:', {
        detection_id: response.data.detection_id,
        person_count: response.data.person_count,
        processing_time: response.data.processing_time_ms
      });

      return response.data;
    } catch (error) {
      console.error('Detection API error:', error);
      throw new Error('Failed to detect persons in frame');
    }
  }

  /**
   * Get tracking history for a specific person
   */
  async getTrackingHistory(
    trackId: number,
    workstationId: number,
    hours: number = 1
  ): Promise<any> {
    try {
      const response = await api.get(`/detection/tracking/history/${trackId}`, {
        params: {
          workstation_id: workstationId,
          hours,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get tracking history:', error);
      throw error;
    }
  }

  /**
   * Get zone analysis for efficiency metrics
   */
  async getZoneAnalysis(zoneId: number, hours: number = 1): Promise<any> {
    try {
      const response = await api.get(`/detection/zones/${zoneId}/analysis`, {
        params: { hours },
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get zone analysis:', error);
      throw error;
    }
  }

  /**
   * Start video stream detection (WebSocket - future implementation)
   */
  async startStreamDetection(
    workstationId: number,
    videoSource: string,
    confidenceThreshold: number = 0.5
  ): Promise<any> {
    try {
      const response = await api.post('/detection/detect/stream', {
        workstation_id: workstationId,
        video_source: videoSource,
        confidence_threshold: confidenceThreshold,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to start stream detection:', error);
      throw error;
    }
  }
}

export const detectionService = new DetectionService();
export default detectionService;