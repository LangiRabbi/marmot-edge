/**
 * PersonDetectionOverlay component for rendering YOLOv11 detection results
 * Displays bounding boxes with info panels and center analysis dots
 */

import React, { memo } from 'react';
import {
  type TransformedPersonDetection,
  formatConfidence,
  getZoneNamesForPerson,
} from '@/services/detectionService';
import type { CanvasZone as Zone } from '@/types';

interface PersonDetectionOverlayProps {
  // Detection data to render
  detections: TransformedPersonDetection[];
  // Zone data for name lookup
  zones: Zone[];
  // Container dimensions
  width: number;
  height: number;
  // Visibility controls
  showBoundingBoxes?: boolean;
  showCenterDots?: boolean;
  showInfoPanels?: boolean;
  // Style options
  className?: string;
}

/**
 * Individual person bounding box component
 */
const PersonBoundingBox = memo(({
  detection,
  zones,
  showInfoPanel = true,
}: {
  detection: TransformedPersonDetection;
  zones: Zone[];
  showInfoPanel?: boolean;
}) => {
  const { bbox, tracking_id, confidence, zone_status } = detection;

  // Calculate info panel content
  const confidenceText = formatConfidence(confidence);
  const zoneNames = getZoneNamesForPerson(detection.zone_ids, zones);
  const infoText = `P${tracking_id} | ${confidenceText} | ${zoneNames}`;

  // Bounding box styles
  const boxStyle: React.CSSProperties = {
    position: 'absolute',
    left: `${bbox.x1}px`,
    top: `${bbox.y1}px`,
    width: `${bbox.width}px`,
    height: `${bbox.height}px`,
    border: '2px solid lime',
    borderRadius: '2px',
    background: 'transparent',
    pointerEvents: 'none',
    zIndex: 20,
  };

  // Info panel styles
  const infoPanelStyle: React.CSSProperties = {
    position: 'absolute',
    left: `${bbox.x1}px`,
    top: `${bbox.y1 - 30}px`, // 30px above bounding box
    background: 'rgba(0, 0, 0, 0.7)',
    color: 'white',
    fontSize: '12px',
    fontWeight: 'bold',
    padding: '4px 8px',
    borderRadius: '4px',
    whiteSpace: 'nowrap',
    pointerEvents: 'none',
    zIndex: 21,
    // Ensure panel doesn't go above container
    transform: bbox.y1 < 35 ? 'translateY(35px)' : 'none',
  };

  return (
    <>
      {/* Bounding Box */}
      <div style={boxStyle} />

      {/* Info Panel */}
      {showInfoPanel && (
        <div style={infoPanelStyle}>
          {infoText}
        </div>
      )}
    </>
  );
});

PersonBoundingBox.displayName = 'PersonBoundingBox';

/**
 * Center analysis dot component
 */
const CenterAnalysisDot = memo(({
  detection,
}: {
  detection: TransformedPersonDetection;
}) => {
  const { center } = detection;

  const dotStyle: React.CSSProperties = {
    position: 'absolute',
    left: `${center.x - 3}px`, // Center the 6px dot
    top: `${center.y - 3}px`,
    width: '6px',
    height: '6px',
    background: 'white',
    border: '1px solid black',
    borderRadius: '50%',
    pointerEvents: 'none',
    zIndex: 22,
  };

  return <div style={dotStyle} />;
});

CenterAnalysisDot.displayName = 'CenterAnalysisDot';

/**
 * Detection statistics overlay (optional)
 */
const DetectionStats = memo(({
  detections,
  processingFps,
}: {
  detections: TransformedPersonDetection[];
  processingFps?: number;
}) => {
  const statsStyle: React.CSSProperties = {
    position: 'absolute',
    top: '10px',
    right: '10px',
    background: 'rgba(0, 0, 0, 0.7)',
    color: 'white',
    fontSize: '12px',
    padding: '8px',
    borderRadius: '4px',
    pointerEvents: 'none',
    zIndex: 25,
  };

  return (
    <div style={statsStyle}>
      <div>Persons: {detections.length}</div>
      {processingFps && (
        <div>FPS: {processingFps.toFixed(1)}</div>
      )}
    </div>
  );
});

DetectionStats.displayName = 'DetectionStats';

/**
 * Main PersonDetectionOverlay component
 */
export const PersonDetectionOverlay = memo<PersonDetectionOverlayProps>(({
  detections,
  zones,
  width,
  height,
  showBoundingBoxes = true,
  showCenterDots = true,
  showInfoPanels = true,
  className = '',
}) => {
  console.log('🎨 [PersonDetectionOverlay] Rendering with:', {
    detectionsCount: detections.length,
    zonesCount: zones.length,
    width,
    height,
    showBoundingBoxes,
    showCenterDots,
    showInfoPanels,
    detections: detections.slice(0, 2) // Show first 2 detections for debugging
  });

  // Container styles
  const containerStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: `${width}px`,
    height: `${height}px`,
    pointerEvents: 'none',
    overflow: 'hidden',
  };

  return (
    <div
      className={`person-detection-overlay ${className}`}
      style={containerStyle}
    >
      {/* Render bounding boxes and info panels */}
      {showBoundingBoxes &&
        detections.map((detection) => (
          <PersonBoundingBox
            key={`bbox-${detection.tracking_id}`}
            detection={detection}
            zones={zones}
            showInfoPanel={showInfoPanels}
          />
        ))}

      {/* Render center analysis dots */}
      {showCenterDots &&
        detections.map((detection) => (
          <CenterAnalysisDot
            key={`dot-${detection.tracking_id}`}
            detection={detection}
          />
        ))}
    </div>
  );
});

PersonDetectionOverlay.displayName = 'PersonDetectionOverlay';

/**
 * Compact detection overlay for minimal UI
 */
export const CompactPersonDetectionOverlay = memo<{
  detections: TransformedPersonDetection[];
  width: number;
  height: number;
  showStats?: boolean;
  processingFps?: number;
}>(({
  detections,
  width,
  height,
  showStats = false,
  processingFps,
}) => {
  const containerStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: `${width}px`,
    height: `${height}px`,
    pointerEvents: 'none',
    overflow: 'hidden',
  };

  return (
    <div style={containerStyle}>
      {/* Only center dots for minimal UI */}
      {detections.map((detection) => (
        <CenterAnalysisDot
          key={`compact-dot-${detection.tracking_id}`}
          detection={detection}
        />
      ))}

      {/* Optional stats */}
      {showStats && (
        <DetectionStats
          detections={detections}
          processingFps={processingFps}
        />
      )}
    </div>
  );
});

CompactPersonDetectionOverlay.displayName = 'CompactPersonDetectionOverlay';

export default PersonDetectionOverlay;