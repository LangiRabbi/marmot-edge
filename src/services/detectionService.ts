/**
 * Detection service for processing YOLOv11 person detection data
 * Handles coordinate transformation and zone analysis
 */

import type { PersonDetection } from './websocketService';
import type { Zone } from '@/components/VideoCanvasOverlay';

// Transformed person detection for rendering
export interface TransformedPersonDetection {
  tracking_id: number;
  confidence: number;
  // Pixel coordinates for rendering
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    width: number;
    height: number;
  };
  // Center point for zone analysis
  center: {
    x: number;
    y: number;
  };
  // Zone status determined by center point position
  zone_status: 'Work' | 'Idle' | 'Other' | 'None';
  zone_ids: string[];
}

// Zone with updated status based on center dot analysis
export interface ZoneWithStatus extends Zone {
  center_dots_count: number;
  dynamic_status: 'Idle' | 'Work' | 'Other';
  dynamic_color: string;
}

/**
 * Transform normalized YOLO coordinates to pixel coordinates
 */
export function transformDetectionCoordinates(
  persons: PersonDetection[],
  videoWidth: number,
  videoHeight: number
): TransformedPersonDetection[] {
  return persons.map(person => {
    // Transform normalized bbox [x1, y1, x2, y2] to pixels
    const x1 = person.bbox[0] * videoWidth;
    const y1 = person.bbox[1] * videoHeight;
    const x2 = person.bbox[2] * videoWidth;
    const y2 = person.bbox[3] * videoHeight;

    // Calculate center point for zone analysis
    const centerX = (x1 + x2) / 2;
    const centerY = (y1 + y2) / 2;

    return {
      tracking_id: person.tracking_id,
      confidence: person.confidence,
      bbox: {
        x1,
        y1,
        x2,
        y2,
        width: x2 - x1,
        height: y2 - y1,
      },
      center: {
        x: centerX,
        y: centerY,
      },
      zone_status: 'None', // Will be calculated by zone analysis
      zone_ids: [...person.zones], // Copy zones from backend
    };
  });
}

/**
 * Check if a point (center dot) is inside a zone rectangle
 */
export function isPointInZone(
  centerX: number,
  centerY: number,
  zone: Zone,
  videoWidth: number,
  videoHeight: number
): boolean {
  // Convert zone percentage coordinates to pixels
  const zoneX = (zone.x / 100) * videoWidth;
  const zoneY = (zone.y / 100) * videoHeight;
  const zoneWidth = (zone.width / 100) * videoWidth;
  const zoneHeight = (zone.height / 100) * videoHeight;

  // Check if center point is inside zone rectangle
  return (
    centerX >= zoneX &&
    centerX <= zoneX + zoneWidth &&
    centerY >= zoneY &&
    centerY <= zoneY + zoneHeight
  );
}

/**
 * Analyze zones and update their status based on center dot positions
 */
export function analyzeZonesWithCenterDots(
  zones: Zone[],
  detections: TransformedPersonDetection[],
  videoWidth: number,
  videoHeight: number
): ZoneWithStatus[] {
  return zones.map(zone => {
    // Count center dots in this zone
    const centerDotsInZone = detections.filter(detection =>
      isPointInZone(detection.center.x, detection.center.y, zone, videoWidth, videoHeight)
    );

    const centerDotsCount = centerDotsInZone.length;

    // Determine zone status based on center dot count
    let dynamicStatus: 'Idle' | 'Work' | 'Other';
    let dynamicColor: string;

    if (centerDotsCount === 0) {
      dynamicStatus = 'Idle';
      dynamicColor = 'rgba(255, 255, 0, 0.3)'; // Yellow
    } else if (centerDotsCount === 1) {
      dynamicStatus = 'Work';
      dynamicColor = 'rgba(0, 255, 0, 0.3)'; // Green
    } else {
      dynamicStatus = 'Other';
      dynamicColor = 'rgba(255, 165, 0, 0.3)'; // Orange
    }

    // Update detection zone status based on their position
    centerDotsInZone.forEach(detection => {
      detection.zone_status = dynamicStatus;
      if (!detection.zone_ids.includes(zone.id.toString())) {
        detection.zone_ids.push(zone.id.toString());
      }
    });

    return {
      ...zone,
      center_dots_count: centerDotsCount,
      dynamic_status: dynamicStatus,
      dynamic_color: dynamicColor,
    };
  });
}

/**
 * Format confidence percentage for display
 */
export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

/**
 * Get zone name by ID for display in person info
 */
export function getZoneNamesForPerson(
  zoneIds: string[],
  zones: Zone[]
): string {
  if (zoneIds.length === 0) return 'None';

  const zoneNames = zoneIds
    .map(id => zones.find(zone => zone.id.toString() === id)?.name)
    .filter(Boolean);

  return zoneNames.length > 0 ? zoneNames.join(', ') : 'None';
}

/**
 * Throttle function for smooth animation updates
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;
  let lastExecTime = 0;

  return (...args: Parameters<T>) => {
    const currentTime = Date.now();

    if (currentTime - lastExecTime > delay) {
      func(...args);
      lastExecTime = currentTime;
    } else {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutId = setTimeout(() => {
        func(...args);
        lastExecTime = Date.now();
      }, delay - (currentTime - lastExecTime));
    }
  };
}

/**
 * Calculate video dimensions maintaining aspect ratio
 */
export function calculateVideoDimensions(
  containerWidth: number,
  containerHeight: number,
  videoAspectRatio: number = 16/9
): { width: number; height: number } {
  const containerAspectRatio = containerWidth / containerHeight;

  if (containerAspectRatio > videoAspectRatio) {
    // Container is wider than video - fit to height
    return {
      width: containerHeight * videoAspectRatio,
      height: containerHeight,
    };
  } else {
    // Container is taller than video - fit to width
    return {
      width: containerWidth,
      height: containerWidth / videoAspectRatio,
    };
  }
}