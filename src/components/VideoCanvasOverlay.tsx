import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, Edit3, Trash2, MoreHorizontal } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';

export interface Zone {
  id: number;
  name: string;
  x: number; // percentage 0-100
  y: number; // percentage 0-100
  width: number; // percentage 0-100
  height: number; // percentage 0-100
  color: string;
  status: 'Work' | 'Idle' | 'Other';
}

interface VideoCanvasOverlayProps {
  width: number;
  height: number;
  zones: Zone[];
  onZonesChange: (zones: Zone[]) => void;
  isDrawingMode: boolean;
  onDrawingModeChange: (mode: boolean) => void;
  maxZones?: number;
}

interface DrawingState {
  isDrawing: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

interface DragState {
  isDragging: boolean;
  dragType: 'move' | 'resize';
  zoneId: number | null;
  resizeHandle: string | null; // 'nw', 'ne', 'sw', 'se', 'n', 'e', 's', 'w'
  startX: number;
  startY: number;
  originalZone: Zone | null;
}

const ZONE_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // violet
  '#06B6D4', // cyan
  '#F97316', // orange
  '#84CC16', // lime
  '#EC4899', // pink
  '#6B7280', // gray
];

const HANDLE_SIZE = 8;
const MIN_ZONE_SIZE = 20; // minimum zone size in pixels

export function VideoCanvasOverlay({
  width,
  height,
  zones,
  onZonesChange,
  isDrawingMode,
  onDrawingModeChange,
  maxZones = 10
}: VideoCanvasOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const [drawingState, setDrawingState] = useState<DrawingState>({
    isDrawing: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0
  });

  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    dragType: 'move',
    zoneId: null,
    resizeHandle: null,
    startX: 0,
    startY: 0,
    originalZone: null
  });

  const [selectedZone, setSelectedZone] = useState<number | null>(null);
  const [editingZone, setEditingZone] = useState<number | null>(null);
  const [editingName, setEditingName] = useState('');
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    zoneId: number;
  } | null>(null);

  // Convert percentage to pixel coordinates
  const percentToPixel = useCallback((x: number, y: number) => ({
    x: (x / 100) * width,
    y: (y / 100) * height
  }), [width, height]);

  // Convert pixel to percentage coordinates
  const pixelToPercent = useCallback((x: number, y: number) => ({
    x: (x / width) * 100,
    y: (y / height) * 100
  }), [width, height]);

  // Get mouse position relative to canvas
  const getMousePos = useCallback((e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }, []);

  // Check if point is inside zone
  const isPointInZone = useCallback((px: number, py: number, zone: Zone) => {
    const { x, y } = percentToPixel(zone.x, zone.y);
    const zoneWidth = (zone.width / 100) * width;
    const zoneHeight = (zone.height / 100) * height;

    return px >= x && px <= x + zoneWidth && py >= y && py <= y + zoneHeight;
  }, [percentToPixel, width, height]);

  // Get resize handle at position
  const getResizeHandle = useCallback((px: number, py: number, zone: Zone) => {
    const { x, y } = percentToPixel(zone.x, zone.y);
    const zoneWidth = (zone.width / 100) * width;
    const zoneHeight = (zone.height / 100) * height;

    const tolerance = HANDLE_SIZE / 2;

    // Corner handles
    if (Math.abs(px - x) <= tolerance && Math.abs(py - y) <= tolerance) return 'nw';
    if (Math.abs(px - (x + zoneWidth)) <= tolerance && Math.abs(py - y) <= tolerance) return 'ne';
    if (Math.abs(px - x) <= tolerance && Math.abs(py - (y + zoneHeight)) <= tolerance) return 'sw';
    if (Math.abs(px - (x + zoneWidth)) <= tolerance && Math.abs(py - (y + zoneHeight)) <= tolerance) return 'se';

    // Edge handles
    if (Math.abs(px - (x + zoneWidth / 2)) <= tolerance && Math.abs(py - y) <= tolerance) return 'n';
    if (Math.abs(px - (x + zoneWidth)) <= tolerance && Math.abs(py - (y + zoneHeight / 2)) <= tolerance) return 'e';
    if (Math.abs(px - (x + zoneWidth / 2)) <= tolerance && Math.abs(py - (y + zoneHeight)) <= tolerance) return 's';
    if (Math.abs(px - x) <= tolerance && Math.abs(py - (y + zoneHeight / 2)) <= tolerance) return 'w';

    return null;
  }, [percentToPixel, width, height]);

  // Draw canvas
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw zones
    zones.forEach(zone => {
      const { x, y } = percentToPixel(zone.x, zone.y);
      const zoneWidth = (zone.width / 100) * width;
      const zoneHeight = (zone.height / 100) * height;

      // Zone background
      ctx.fillStyle = zone.color + '40'; // 25% opacity
      ctx.fillRect(x, y, zoneWidth, zoneHeight);

      // Zone border
      ctx.strokeStyle = zone.color;
      ctx.lineWidth = selectedZone === zone.id ? 3 : 2;
      ctx.setLineDash(selectedZone === zone.id ? [5, 5] : []);
      ctx.strokeRect(x, y, zoneWidth, zoneHeight);
      ctx.setLineDash([]);

      // Zone label
      ctx.fillStyle = zone.color;
      ctx.font = '12px Inter, sans-serif';
      ctx.fontWeight = '600';
      const labelText = `Zone ${zone.id}: ${zone.name}`;
      const textMetrics = ctx.measureText(labelText);
      const labelX = x + 8;
      const labelY = y - 8;

      // Label background
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
      ctx.fillRect(labelX - 4, labelY - 14, textMetrics.width + 8, 18);

      // Label text
      ctx.fillStyle = '#ffffff';
      ctx.fillText(labelText, labelX, labelY);

      // Resize handles for selected zone
      if (selectedZone === zone.id) {
        ctx.fillStyle = zone.color;
        const handlePositions = [
          { x: x, y: y }, // nw
          { x: x + zoneWidth, y: y }, // ne
          { x: x, y: y + zoneHeight }, // sw
          { x: x + zoneWidth, y: y + zoneHeight }, // se
          { x: x + zoneWidth / 2, y: y }, // n
          { x: x + zoneWidth, y: y + zoneHeight / 2 }, // e
          { x: x + zoneWidth / 2, y: y + zoneHeight }, // s
          { x: x, y: y + zoneHeight / 2 }, // w
        ];

        handlePositions.forEach(pos => {
          ctx.fillRect(
            pos.x - HANDLE_SIZE / 2,
            pos.y - HANDLE_SIZE / 2,
            HANDLE_SIZE,
            HANDLE_SIZE
          );
        });
      }
    });

    // Draw current drawing rectangle
    if (isDrawingMode && drawingState.isDrawing) {
      const startX = Math.min(drawingState.startX, drawingState.currentX);
      const startY = Math.min(drawingState.startY, drawingState.currentY);
      const rectWidth = Math.abs(drawingState.currentX - drawingState.startX);
      const rectHeight = Math.abs(drawingState.currentY - drawingState.startY);

      ctx.strokeStyle = '#3B82F6';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(startX, startY, rectWidth, rectHeight);
      ctx.setLineDash([]);

      ctx.fillStyle = '#3B82F640';
      ctx.fillRect(startX, startY, rectWidth, rectHeight);
    }
  }, [width, height, zones, selectedZone, isDrawingMode, drawingState, percentToPixel]);

  // Mouse event handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const pos = getMousePos(e);

    if (isDrawingMode) {
      if (zones.length >= maxZones) {
        toast({
          title: "Maximum zones reached",
          description: `You can only create up to ${maxZones} zones.`,
          variant: "destructive",
        });
        return;
      }

      setDrawingState({
        isDrawing: true,
        startX: pos.x,
        startY: pos.y,
        currentX: pos.x,
        currentY: pos.y
      });
      return;
    }

    // Check for resize handles first
    for (const zone of zones) {
      const handle = getResizeHandle(pos.x, pos.y, zone);
      if (handle) {
        setDragState({
          isDragging: true,
          dragType: 'resize',
          zoneId: zone.id,
          resizeHandle: handle,
          startX: pos.x,
          startY: pos.y,
          originalZone: { ...zone }
        });
        setSelectedZone(zone.id);
        return;
      }
    }

    // Check for zone selection/dragging
    for (let i = zones.length - 1; i >= 0; i--) {
      const zone = zones[i];
      if (isPointInZone(pos.x, pos.y, zone)) {
        if (e.button === 2) { // Right click
          setContextMenu({
            x: e.clientX,
            y: e.clientY,
            zoneId: zone.id
          });
        } else {
          setDragState({
            isDragging: true,
            dragType: 'move',
            zoneId: zone.id,
            resizeHandle: null,
            startX: pos.x,
            startY: pos.y,
            originalZone: { ...zone }
          });
        }
        setSelectedZone(zone.id);
        return;
      }
    }

    // Clicked on empty area
    setSelectedZone(null);
  }, [getMousePos, isDrawingMode, zones, maxZones, toast, getResizeHandle, isPointInZone]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const pos = getMousePos(e);

    if (isDrawingMode && drawingState.isDrawing) {
      setDrawingState(prev => ({
        ...prev,
        currentX: pos.x,
        currentY: pos.y
      }));
      return;
    }

    if (dragState.isDragging && dragState.zoneId && dragState.originalZone) {
      const deltaX = pos.x - dragState.startX;
      const deltaY = pos.y - dragState.startY;
      const zone = dragState.originalZone;

      if (dragState.dragType === 'move') {
        const newPos = pixelToPercent(
          percentToPixel(zone.x, zone.y).x + deltaX,
          percentToPixel(zone.x, zone.y).y + deltaY
        );

        // Constrain to canvas bounds
        const maxX = 100 - zone.width;
        const maxY = 100 - zone.height;

        const updatedZone = {
          ...zone,
          x: Math.max(0, Math.min(maxX, newPos.x)),
          y: Math.max(0, Math.min(maxY, newPos.y))
        };

        onZonesChange(zones.map(z => z.id === dragState.zoneId ? updatedZone : z));
      } else if (dragState.dragType === 'resize' && dragState.resizeHandle) {
        // Handle resizing logic based on resize handle
        // This is a simplified version - you can expand for all handles
        const handle = dragState.resizeHandle;
        const newZone = { ...zone };

        if (handle.includes('e')) { // east handles
          const newWidth = pixelToPercent(deltaX, 0).x + zone.width;
          newZone.width = Math.max(MIN_ZONE_SIZE / width * 100, Math.min(100 - zone.x, newWidth));
        }
        if (handle.includes('s')) { // south handles
          const newHeight = pixelToPercent(0, deltaY).y + zone.height;
          newZone.height = Math.max(MIN_ZONE_SIZE / height * 100, Math.min(100 - zone.y, newHeight));
        }
        if (handle.includes('w')) { // west handles
          const deltaXPercent = pixelToPercent(deltaX, 0).x;
          const newX = zone.x + deltaXPercent;
          const newWidth = zone.width - deltaXPercent;
          if (newWidth >= MIN_ZONE_SIZE / width * 100) {
            newZone.x = Math.max(0, newX);
            newZone.width = newWidth;
          }
        }
        if (handle.includes('n')) { // north handles
          const deltaYPercent = pixelToPercent(0, deltaY).y;
          const newY = zone.y + deltaYPercent;
          const newHeight = zone.height - deltaYPercent;
          if (newHeight >= MIN_ZONE_SIZE / height * 100) {
            newZone.y = Math.max(0, newY);
            newZone.height = newHeight;
          }
        }

        onZonesChange(zones.map(z => z.id === dragState.zoneId ? newZone : z));
      }
    }

    // Update cursor based on hover state
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (isDrawingMode) {
      canvas.style.cursor = 'crosshair';
      return;
    }

    // Check for resize handles
    for (const zone of zones) {
      const handle = getResizeHandle(pos.x, pos.y, zone);
      if (handle) {
        const cursors = {
          'nw': 'nw-resize',
          'ne': 'ne-resize',
          'sw': 'sw-resize',
          'se': 'se-resize',
          'n': 'n-resize',
          'e': 'e-resize',
          's': 's-resize',
          'w': 'w-resize'
        };
        canvas.style.cursor = cursors[handle] || 'default';
        return;
      }
    }

    // Check for zones
    for (const zone of zones) {
      if (isPointInZone(pos.x, pos.y, zone)) {
        canvas.style.cursor = 'move';
        return;
      }
    }

    canvas.style.cursor = 'default';
  }, [getMousePos, isDrawingMode, drawingState, dragState, zones, onZonesChange, pixelToPercent, percentToPixel, getResizeHandle, isPointInZone, width, height]);

  const handleMouseUp = useCallback((e: React.MouseEvent) => {
    if (isDrawingMode && drawingState.isDrawing) {
      const rectWidth = Math.abs(drawingState.currentX - drawingState.startX);
      const rectHeight = Math.abs(drawingState.currentY - drawingState.startY);

      if (rectWidth >= MIN_ZONE_SIZE && rectHeight >= MIN_ZONE_SIZE) {
        const startX = Math.min(drawingState.startX, drawingState.currentX);
        const startY = Math.min(drawingState.startY, drawingState.currentY);

        const newZonePercent = pixelToPercent(startX, startY);
        const sizePercent = pixelToPercent(rectWidth, rectHeight);

        const newZone: Zone = {
          id: Math.max(0, ...zones.map(z => z.id)) + 1,
          name: `Zone ${zones.length + 1}`,
          x: newZonePercent.x,
          y: newZonePercent.y,
          width: sizePercent.x,
          height: sizePercent.y,
          color: ZONE_COLORS[zones.length % ZONE_COLORS.length],
          status: 'Idle'
        };

        onZonesChange([...zones, newZone]);
        setSelectedZone(newZone.id);
        onDrawingModeChange(false);

        toast({
          title: "Zone Created",
          description: `Zone ${newZone.id} has been created successfully.`,
        });
      }

      setDrawingState({
        isDrawing: false,
        startX: 0,
        startY: 0,
        currentX: 0,
        currentY: 0
      });
    }

    setDragState({
      isDragging: false,
      dragType: 'move',
      zoneId: null,
      resizeHandle: null,
      startX: 0,
      startY: 0,
      originalZone: null
    });
  }, [isDrawingMode, drawingState, zones, onZonesChange, onDrawingModeChange, pixelToPercent, toast]);

  // Zone management functions
  const handleDeleteZone = useCallback((zoneId: number) => {
    onZonesChange(zones.filter(z => z.id !== zoneId));
    setSelectedZone(null);
    setContextMenu(null);
    toast({
      title: "Zone Deleted",
      description: `Zone ${zoneId} has been removed.`,
    });
  }, [zones, onZonesChange, toast]);

  const handleEditZone = useCallback((zoneId: number) => {
    const zone = zones.find(z => z.id === zoneId);
    if (zone) {
      setEditingZone(zoneId);
      setEditingName(zone.name);
      setContextMenu(null);
    }
  }, [zones]);

  const handleSaveEdit = useCallback(() => {
    if (editingZone && editingName.trim()) {
      onZonesChange(zones.map(zone =>
        zone.id === editingZone
          ? { ...zone, name: editingName.trim() }
          : zone
      ));
      setEditingZone(null);
      setEditingName('');
      toast({
        title: "Zone Updated",
        description: "Zone name has been updated successfully.",
      });
    }
  }, [editingZone, editingName, zones, onZonesChange, toast]);

  // Effects
  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = width;
    canvas.height = height;

    // Force redraw after canvas is resized
    drawCanvas();
  }, [width, height, drawCanvas]);

  // Force redraw when component mounts or zones change
  useEffect(() => {
    drawCanvas();
  }, [zones, selectedZone, isDrawingMode, drawingState, dragState]);

  // Click outside to close context menu
  useEffect(() => {
    const handleClickOutside = () => setContextMenu(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 z-10"
      style={{ width, height }}
    >
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="absolute inset-0"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onContextMenu={(e) => e.preventDefault()}
      />

      {/* Zone editing input */}
      {editingZone && (
        <div className="absolute top-4 left-4 bg-background border border-border rounded-md p-2 shadow-lg z-20">
          <div className="flex items-center gap-2">
            <Input
              value={editingName}
              onChange={(e) => setEditingName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSaveEdit();
                if (e.key === 'Escape') {
                  setEditingZone(null);
                  setEditingName('');
                }
              }}
              className="text-sm h-8 w-40"
              placeholder="Zone name"
              autoFocus
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSaveEdit}
              className="h-6 w-6 p-0 text-success hover:bg-success/20"
            >
              ✓
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setEditingZone(null);
                setEditingName('');
              }}
              className="h-6 w-6 p-0 text-destructive hover:bg-destructive/20"
            >
              ✕
            </Button>
          </div>
        </div>
      )}

      {/* Context menu */}
      {contextMenu && (
        <div
          className="absolute bg-background border border-border rounded-md shadow-lg z-30 py-1"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
            transform: 'translate(-50%, -100%)'
          }}
        >
          <button
            className="w-full px-3 py-2 text-left text-sm hover:bg-muted flex items-center gap-2"
            onClick={() => handleEditZone(contextMenu.zoneId)}
          >
            <Edit3 className="h-4 w-4" />
            Rename Zone
          </button>
          <button
            className="w-full px-3 py-2 text-left text-sm hover:bg-muted text-destructive flex items-center gap-2"
            onClick={() => handleDeleteZone(contextMenu.zoneId)}
          >
            <Trash2 className="h-4 w-4" />
            Delete Zone
          </button>
        </div>
      )}
    </div>
  );
}