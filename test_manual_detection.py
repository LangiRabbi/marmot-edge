#!/usr/bin/env python3
"""
Manual detection test - send detection message and check if it appears in frontend
"""

# Since backend is loaded, we can test by directly sending messages through browser console
print("""
=== MANUAL DETECTION TEST ===

Steps to test bounding boxes:

1. Open browser console (F12)
2. Paste this JavaScript code:

// Simulate detection message from backend
const detectionsMessage = {
  type: 'detection_update',
  timestamp: new Date().toISOString(),
  workstation_id: '7',
  frame_timestamp: new Date().toISOString(),
  person_count: 2,
  persons: [
    {
      tracking_id: 1,
      confidence: 0.89,
      bbox: [0.2, 0.3, 0.4, 0.7],  // x1, y1, x2, y2 (normalized)
      center: [0.3, 0.5],
      zones: ['zone_1']
    },
    {
      tracking_id: 2,
      confidence: 0.92,
      bbox: [0.6, 0.2, 0.8, 0.6],  // x1, y1, x2, y2 (normalized)
      center: [0.7, 0.4],
      zones: ['zone_2']
    }
  ],
  processing_fps: 15.3,
  frame_number: 12345
};

// Send message to WebSocket message handlers
window.dispatchEvent(new CustomEvent('websocket-detection', {
  detail: detectionsMessage
}));

console.log('Detection message sent:', detectionsMessage);

3. Check if bounding boxes appear on video player
4. Check if People count updates from 0 to 2

=== Expected Result ===
- Two bounding boxes should appear on the video
- People count should update to 2
- Bounding boxes should have different colors for different tracking IDs
- Console should show detection message handling logs

""")