/**
 * Custom hook for managing real-time person detection data
 * Integrates with WebSocket service and provides transformed detection data
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useWorkstationWebSocket } from './useWebSocket';
import {
  transformDetectionCoordinates,
  analyzeZonesWithCenterDots,
  throttle,
  type TransformedPersonDetection,
  type ZoneWithStatus,
} from '@/services/detectionService';
import type { Zone } from '@/components/VideoCanvasOverlay';
import type { DetectionUpdateMessage } from '@/services/websocketService';

export interface DetectionDataState {
  // Transformed detection data for rendering
  detections: TransformedPersonDetection[];
  // Zones with updated status based on center dots
  zonesWithStatus: ZoneWithStatus[];
  // Raw detection metrics
  personCount: number;
  processingFps: number;
  frameNumber: number;
  frameTimestamp: string | null;
  // Loading and error states
  isLoading: boolean;
  error: string | null;
  // Connection status
  isConnected: boolean;
}

export interface UseDetectionDataOptions {
  // Video dimensions for coordinate transformation
  videoWidth: number;
  videoHeight: number;
  // Zones for analysis
  zones: Zone[];
  // Performance settings
  updateThrottleMs?: number;
  // Auto-connect settings
  autoConnect?: boolean;
}

/**
 * Hook for managing real-time person detection data from WebSocket
 */
export function useDetectionData(
  workstationId: string,
  options: UseDetectionDataOptions
): DetectionDataState {
  const {
    videoWidth,
    videoHeight,
    zones,
    updateThrottleMs = 33, // ~30 FPS
    autoConnect = true,
  } = options;

  // WebSocket connection
  const {
    connectionState,
    isConnected,
    error: wsError,
    latestDetection,
    connect,
    disconnect,
  } = useWorkstationWebSocket(workstationId, {
    autoConnect,
    subscriptionTypes: ['detections'],
  });

  // Detection state
  const [detectionState, setDetectionState] = useState<DetectionDataState>({
    detections: [],
    zonesWithStatus: [],
    personCount: 0,
    processingFps: 0,
    frameNumber: 0,
    frameTimestamp: null,
    isLoading: true,
    error: null,
    isConnected: false,
  });

  // Throttled update function for smooth performance
  const throttledUpdateDetections = useMemo(
    () =>
      throttle((detectionMessage: DetectionUpdateMessage) => {
        try {
          console.log('🔧 [throttledUpdate] Processing detection:', {
            personsRaw: detectionMessage.persons,
            personCount: detectionMessage.person_count,
            videoWidth,
            videoHeight,
            zonesLength: zones.length
          });

          // Transform raw detection data to pixel coordinates
          const transformedDetections = transformDetectionCoordinates(
            detectionMessage.persons,
            videoWidth,
            videoHeight
          );

          console.log('✨ [throttledUpdate] Transformed detections:', transformedDetections);

          // Analyze zones with center dot positions
          const zonesWithStatus = analyzeZonesWithCenterDots(
            zones,
            transformedDetections,
            videoWidth,
            videoHeight
          );

          console.log('🎯 [throttledUpdate] Zones with status:', zonesWithStatus);

          // Update state with new detection data
          setDetectionState(prev => ({
            ...prev,
            detections: transformedDetections,
            zonesWithStatus,
            personCount: detectionMessage.person_count,
            processingFps: detectionMessage.processing_fps,
            frameNumber: detectionMessage.frame_number,
            frameTimestamp: detectionMessage.frame_timestamp,
            isLoading: false,
            error: null,
          }));
        } catch (error) {
          console.error('Error processing detection data:', error);
          setDetectionState(prev => ({
            ...prev,
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false,
          }));
        }
      }, updateThrottleMs),
    [videoWidth, videoHeight, zones, updateThrottleMs]
  );

  // Handle new detection messages
  useEffect(() => {
    if (latestDetection) {
      console.log('🔍 [useDetectionData] New detection received:', {
        workstationId,
        personCount: latestDetection.person_count,
        personsLength: latestDetection.persons?.length || 0,
        frameNumber: latestDetection.frame_number,
        videoWidth,
        videoHeight
      });
      throttledUpdateDetections(latestDetection);
    }
  }, [latestDetection, throttledUpdateDetections, workstationId, videoWidth, videoHeight]);

  // Update connection status
  useEffect(() => {
    setDetectionState(prev => ({
      ...prev,
      isConnected,
      error: wsError || prev.error,
      isLoading: connectionState === 'connecting',
    }));
  }, [isConnected, wsError, connectionState]);

  // Update zones when they change
  useEffect(() => {
    if (detectionState.detections.length > 0) {
      const zonesWithStatus = analyzeZonesWithCenterDots(
        zones,
        detectionState.detections,
        videoWidth,
        videoHeight
      );

      setDetectionState(prev => ({
        ...prev,
        zonesWithStatus,
      }));
    }
  }, [zones, videoWidth, videoHeight, detectionState.detections]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect, disconnect]);

  return detectionState;
}

/**
 * Hook for simplified detection data without zone analysis
 * Useful for components that only need basic detection info
 */
export function useSimpleDetectionData(
  workstationId: string,
  videoWidth: number,
  videoHeight: number,
  options: { autoConnect?: boolean; updateThrottleMs?: number } = {}
) {
  const { autoConnect = true, updateThrottleMs = 33 } = options;

  const {
    isConnected,
    error: wsError,
    latestDetection,
  } = useWorkstationWebSocket(workstationId, {
    autoConnect,
    subscriptionTypes: ['detections'],
  });

  const [simpleState, setSimpleState] = useState({
    detections: [] as TransformedPersonDetection[],
    personCount: 0,
    processingFps: 0,
    isConnected: false,
    error: null as string | null,
  });

  const throttledUpdate = useMemo(
    () =>
      throttle((detectionMessage: DetectionUpdateMessage) => {
        const transformedDetections = transformDetectionCoordinates(
          detectionMessage.persons,
          videoWidth,
          videoHeight
        );

        setSimpleState(prev => ({
          ...prev,
          detections: transformedDetections,
          personCount: detectionMessage.person_count,
          processingFps: detectionMessage.processing_fps,
          error: null,
        }));
      }, updateThrottleMs),
    [videoWidth, videoHeight, updateThrottleMs]
  );

  useEffect(() => {
    if (latestDetection) {
      throttledUpdate(latestDetection);
    }
  }, [latestDetection, throttledUpdate]);

  useEffect(() => {
    setSimpleState(prev => ({
      ...prev,
      isConnected,
      error: wsError || prev.error,
    }));
  }, [isConnected, wsError]);

  return simpleState;
}

/**
 * Hook for getting detection statistics
 */
export function useDetectionStats(detections: TransformedPersonDetection[]) {
  return useMemo(() => {
    const totalPersons = detections.length;
    const avgConfidence = totalPersons > 0
      ? detections.reduce((sum, d) => sum + d.confidence, 0) / totalPersons
      : 0;

    const confidenceDistribution = {
      high: detections.filter(d => d.confidence >= 0.8).length,
      medium: detections.filter(d => d.confidence >= 0.5 && d.confidence < 0.8).length,
      low: detections.filter(d => d.confidence < 0.5).length,
    };

    const zoneDistribution = detections.reduce((acc, detection) => {
      detection.zone_ids.forEach(zoneId => {
        acc[zoneId] = (acc[zoneId] || 0) + 1;
      });
      return acc;
    }, {} as Record<string, number>);

    return {
      totalPersons,
      avgConfidence,
      confidenceDistribution,
      zoneDistribution,
    };
  }, [detections]);
}