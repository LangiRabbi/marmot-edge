import { Camera, Clock, Activity, Zap, MapPin, Download, Edit3, Trash2, Plus, MoreHorizontal, Target, Lock, Unlock, Wifi } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { VideoPlayer } from "./VideoPlayer";
import type { CanvasZone as Zone } from "@/types";
import { ConnectionStatus } from "./ConnectionStatus";
import { useState, useEffect, useCallback } from "react";
import type { VideoSourceConfig } from "@/services/workstationService";
import { zoneService } from "@/services/zoneService";
import type { CanvasZone, ZoneStatus } from "@/types";
import { useWorkstationWebSocket } from "@/hooks/useWebSocket";
import { useDetectionData } from "@/hooks/useDetectionData";
import type { DetectionUpdateMessage, ZoneUpdateMessage, EfficiencyUpdateMessage } from "@/services/websocketService";

interface WorkstationDetailsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workstation: {
    id: number;
    name: string;
    status: 'online' | 'offline' | 'alert';
    peopleCount: number;
    efficiency: number;
    lastActivity: string;
  };
  videoConfig?: VideoSourceConfig;
}

export function WorkstationDetailsModal({ open, onOpenChange, workstation, videoConfig }: WorkstationDetailsModalProps) {
  const { toast } = useToast();
  const [zones, setZones] = useState<Zone[]>([]);
  const [editingZone, setEditingZone] = useState<number | null>(null);
  const [editingName, setEditingName] = useState('');
  const [showVideoPlayer, setShowVideoPlayer] = useState(true);
  const [showZoneOverlay, setShowZoneOverlay] = useState(true);
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [isLoadingZones, setIsLoadingZones] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);

  // Detection overlay state
  const [showDetections, setShowDetections] = useState(true);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [showCenterDots, setShowCenterDots] = useState(true);
  const [showInfoPanels, setShowInfoPanels] = useState(true);

  // WebSocket integration
  const {
    connectionState,
    isConnected,
    error: wsError,
    connect: wsConnect,
    disconnect: wsDisconnect,
    latestDetection,
    latestZoneUpdate,
    latestEfficiency,
    totalMessages,
    messagesPerSecond
  } = useWorkstationWebSocket(workstation.id.toString(), {
    autoConnect: false, // Manual connection control
    subscriptionTypes: ['all']
  });

  // Real-time data state
  const [realtimePersonCount, setRealtimePersonCount] = useState<number>(workstation.peopleCount);
  const [realtimeEfficiency, setRealtimeEfficiency] = useState<number>(workstation.efficiency);
  const [realtimeZoneData, setRealtimeZoneData] = useState<Record<string, { count: number; status: string }>>({});

  // Detection data hook - integrates with VideoCanvasOverlay
  // Dynamic video dimensions (updated from VideoPlayer loadedmetadata)
  const [videoWidth, setVideoWidth] = useState<number>(800);
  const [videoHeight, setVideoHeight] = useState<number>(450);

  const detectionData = useDetectionData(workstation.id.toString(), {
    videoWidth,
    videoHeight,
    zones,
    updateThrottleMs: 33, // ~30 FPS
    autoConnect: open, // Connect when modal is open
  });

  // Debug logging for WorkstationDetailsModal - ONLY when modal is open
  useEffect(() => {
    if (!open) return; // Skip debug logging for closed modals

    console.log('🏭 [WorkstationDetailsModal] Detection data state:', {
      workstationId: workstation.id,
      workstationName: workstation.name,
      isConnected: detectionData.isConnected,
      isLoading: detectionData.isLoading,
      error: detectionData.error,
      detectionsCount: detectionData.detections.length,
      detections: detectionData.detections,
      personCount: detectionData.personCount,
      processingFps: detectionData.processingFps,
      frameNumber: detectionData.frameNumber,
      zonesWithStatusCount: detectionData.zonesWithStatus.length,
      modalOpen: open
    });
    if (detectionData.detections.length === 0 && open) {
      console.warn('🚨 [WorkstationDetailsModal] NO DETECTIONS - This is why bounding boxes are not showing!');
    }
  }, [workstation.id, workstation.name, detectionData, open]);

  // REMOVED: startVideoProcessing() and stopVideoProcessing() functions
  // Reason: Backend runs autonomously 24/7, frontend doesn't control processing
  // Architecture: Frontend = visualization only, Backend = independent industrial monitoring

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!open) {
      setShowZoneOverlay(true);
      setIsDrawingMode(false);
      setEditingZone(null);
      setEditingName('');
      setIsEditMode(false);
      // Don't explicitly disconnect - let reference counting handle it
    } else {
      // Connect WebSocket when modal opens
      wsConnect(workstation.id.toString());
    }
  }, [open, workstation.id, wsConnect]);

  // Handle real-time detection updates
  useEffect(() => {
    if (latestDetection) {
      setRealtimePersonCount(latestDetection.person_count);

      // Show notification for significant changes
      if (Math.abs(latestDetection.person_count - workstation.peopleCount) > 1) {
        toast({
          title: "Person Count Updated",
          description: `${latestDetection.person_count} person(s) detected in real-time`,
        });
      }
    }
  }, [latestDetection, workstation.peopleCount, toast]);

  // Handle real-time zone updates
  useEffect(() => {
    if (latestZoneUpdate) {
      const zoneData: Record<string, { count: number; status: string }> = {};

      latestZoneUpdate.zones.forEach(zone => {
        zoneData[zone.zone_id] = {
          count: zone.person_count,
          status: zone.person_count > 0 ? 'work' : 'idle'
        };
      });

      setRealtimeZoneData(zoneData);

      // Update zone statuses in the zones array
      setZones(prevZones =>
        prevZones.map(zone => ({
          ...zone,
          status: (zoneData[zone.id]?.status || 'idle') as ZoneStatus
        }))
      );
    }
  }, [latestZoneUpdate]);

  // Handle real-time efficiency updates
  useEffect(() => {
    if (latestEfficiency) {
      const newEfficiency = latestEfficiency.metrics.efficiency_percentage;
      setRealtimeEfficiency(newEfficiency);

      // Show notification for significant efficiency changes
      if (Math.abs(newEfficiency - workstation.efficiency) > 10) {
        toast({
          title: "Efficiency Updated",
          description: `Efficiency: ${newEfficiency.toFixed(1)}% (${latestEfficiency.metrics.current_state})`,
        });
      }
    }
  }, [latestEfficiency, workstation.efficiency, toast]);

  // Load zones from backend when modal opens
  useEffect(() => {
    if (open && workstation.id) {
      const loadZones = async () => {
        setIsLoadingZones(true);
        try {
          const backendZones = await zoneService.getZonesByWorkstation(workstation.id);
          const canvasZones = backendZones.map(zone => zoneService.convertToCanvasZone(zone));
          setZones(canvasZones);
        } catch (error) {
          console.error('Failed to load zones:', error);
          toast({
            title: "Failed to load zones",
            description: "Using local data instead",
            variant: "destructive",
          });
          // Set some default zones as fallback
          setZones([
            { id: 1, name: 'Assembly Area', x: 20, y: 20, width: 30, height: 25, color: '#3B82F6', status: 'work' },
            { id: 2, name: 'Quality Control', x: 55, y: 20, width: 25, height: 20, color: '#10B981', status: 'idle' },
            { id: 3, name: 'Packaging Station', x: 20, y: 50, width: 28, height: 30, color: '#F59E0B', status: 'work' },
          ]);
        } finally {
          setIsLoadingZones(false);
        }
      };

      loadZones();
    }
  }, [open, workstation.id, toast]);

  // Get video source URL and type based on config
  const getVideoSource = () => {
    if (!videoConfig) {
      // Default fallback video
      return {
        src: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        sourceType: "file" as const
      };
    }

    switch (videoConfig.type) {
      case 'file': {
        // Check if blob URL is still valid, fallback to default if not
        // Prefer backend-served path if provided (e.g., backend API or static URL)
        const filePath = videoConfig.filePath || (videoConfig as VideoSourceConfig & { backendPath?: string }).backendPath;
        if (!filePath) {
          console.warn('⚠️ [WorkstationDetailsModal] videoConfig.filePath is missing - falling back to sample video');
        }
        if (filePath && filePath.startsWith('blob:')) {
          // For blob URLs, we'll let VideoPlayer handle the error and fallback
          return {
            src: filePath,
            sourceType: "file" as const,
            fallbackSrc: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
          };
        }
        return {
          src: filePath || "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
          sourceType: "file" as const
        };
      }
      case 'rtsp':
        // Use test HLS stream since RTSP URLs don't work in browser
        return {
          src: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
          sourceType: "hls" as const
        };
      case 'ip':
        // IP Camera - HLS/HTTP streams
        return {
          src: videoConfig.url || "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
          sourceType: videoConfig.url?.endsWith('.m3u8') ? "hls" as const : "file" as const
        };
      case 'usb':
        return {
          src: videoConfig.usbDeviceId || "",
          sourceType: "usb" as const
        };
      default:
        return {
          src: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
          sourceType: "file" as const
        };
    }
  };
  
  const getStatusColor = () => {
    switch (workstation.status) {
      case 'online': return 'text-success';
      case 'offline': return 'text-muted-foreground';
      case 'alert': return 'text-warning';
    }
  };

  const getZoneStatusColor = (status: string) => {
    switch (status) {
      case 'work': return 'text-success';
      case 'idle': return 'text-muted-foreground';
      case 'other': return 'text-warning';
      default: return 'text-muted-foreground';
    }
  };

  const getZoneStatusBg = (status: string) => {
    switch (status) {
      case 'work': return 'bg-success/20 border-success/30';
      case 'idle': return 'bg-muted/20 border-muted';
      case 'other': return 'bg-warning/20 border-warning/30';
      default: return 'bg-muted/20 border-muted';
    }
  };

  const handleExportData = () => {
    toast({
      title: "Data Export",
      description: "Workstation data exported successfully.",
    });
  };

  const handleAddZone = () => {
    if (zones.length >= 10) {
      toast({
        title: "Maximum zones reached",
        description: "You can only create up to 10 zones per workstation.",
        variant: "destructive",
      });
      return;
    }

    setIsDrawingMode(true);
    setShowZoneOverlay(true);

    toast({
      title: "Drawing Mode Activated",
      description: "Click and drag on the video to create a new zone.",
    });
  };

  const getZoneDisplayName = (zone: Zone) => {
    return `${workstation.name} - Zone ${zone.id}`;
  };

  const getZoneDescription = (zone: Zone) => {
    return zone.name || "New Zone";
  };

  const handleToggleZoneOverlay = () => {
    const newShowZoneOverlay = !showZoneOverlay;
    setShowZoneOverlay(newShowZoneOverlay);

    // Exit drawing and edit modes when zones are hidden
    if (!newShowZoneOverlay) {
      setIsDrawingMode(false);
      setIsEditMode(false);
    }
  };

  const handleToggleEditMode = () => {
    const newEditMode = !isEditMode;
    setIsEditMode(newEditMode);

    if (newEditMode) {
      // Entering edit mode
      setShowZoneOverlay(true); // Ensure zones are visible
    } else {
      // Exiting edit mode
      setIsDrawingMode(false); // Exit drawing mode if active
    }
  };

  const handleDeleteZone = async (zoneId: number) => {
    try {
      await zoneService.deleteZone(zoneId);
      setZones(zones.filter(zone => zone.id !== zoneId));
      toast({
        title: "Zone Deleted",
        description: `Zone has been removed successfully.`,
      });
    } catch (error) {
      console.error('Failed to delete zone:', error);
      toast({
        title: "Delete Failed",
        description: "Failed to delete zone from server.",
        variant: "destructive",
      });
    }
  };

  const handleEditZone = (zoneId: number) => {
    const zone = zones.find(z => z.id === zoneId);
    if (zone) {
      setEditingZone(zoneId);
      setEditingName(getZoneDescription(zone));
    }
  };

  const handleSaveEdit = async () => {
    if (editingZone && editingName.trim()) {
      try {
        const zone = zones.find(z => z.id === editingZone);
        if (zone) {
          const updatedZone = { ...zone, name: editingName.trim() };
          const updateRequest = zoneService.convertFromCanvasZoneUpdate(updatedZone);
          await zoneService.updateZone(editingZone, updateRequest);

          setZones(zones.map(z =>
            z.id === editingZone
              ? updatedZone
              : z
          ));
          setEditingZone(null);
          setEditingName('');
          toast({
            title: "Zone Updated",
            description: "Zone description has been updated successfully.",
          });
        }
      } catch (error) {
        console.error('Failed to update zone:', error);
        toast({
          title: "Update Failed",
          description: "Failed to update zone on server.",
          variant: "destructive",
        });
      }
    }
  };

  const handleCancelEdit = () => {
    setEditingZone(null);
    setEditingName('');
  };

  const handleConfigureZone = (zoneId: number) => {
    setShowZoneOverlay(true);
    toast({
      title: "Zone Configuration",
      description: `You can now edit zone ${zoneId} boundaries on the video feed.`,
    });
  };

  const handleZonesChange = async (newZones: Zone[]) => {
    // Check if a new zone was added (length increased)
    if (newZones.length > zones.length) {
      const newZone = newZones[newZones.length - 1];
      try {
        // Give the new zone a default description
        const zoneWithDefaultName = {
          ...newZone,
          name: "New Zone" // This will be the description, not the main name
        };

        // Create the zone in the backend
        const createRequest = zoneService.convertFromCanvasZone(zoneWithDefaultName, workstation.id);
        const createdZone = await zoneService.createZone(createRequest);
        const canvasZone = zoneService.convertToCanvasZone(createdZone);

        // Update local state with the backend-created zone (which has a real ID)
        setZones(zones.concat([canvasZone]));

        toast({
          title: "Zone Created",
          description: `${getZoneDisplayName(canvasZone)} has been created successfully.`,
        });
      } catch (error) {
        console.error('Failed to create zone:', error);
        toast({
          title: "Create Failed",
          description: "Failed to create zone on server.",
          variant: "destructive",
        });
        // Don't update the local state if backend creation failed
      }
    } else if (newZones.length < zones.length) {
      // Zone was deleted - handled by handleDeleteZone
      setZones(newZones);
    } else {
      // Zone was modified - update locally and sync to backend
      const modifiedZones = newZones.filter((newZone, index) => {
        const oldZone = zones[index];
        return oldZone && (
          newZone.x !== oldZone.x ||
          newZone.y !== oldZone.y ||
          newZone.width !== oldZone.width ||
          newZone.height !== oldZone.height
        );
      });

      if (modifiedZones.length > 0) {
        try {
          // Update all modified zones in the backend
          await Promise.all(modifiedZones.map(async (zone) => {
            const updateRequest = zoneService.convertFromCanvasZoneUpdate(zone);
            await zoneService.updateZone(zone.id, updateRequest);
          }));

          setZones(newZones);
        } catch (error) {
          console.error('Failed to update zones:', error);
          toast({
            title: "Update Failed",
            description: "Failed to save zone changes to server.",
            variant: "destructive",
          });
        }
      } else {
        // No actual changes, just update local state
        setZones(newZones);
      }
    }
  };

  const handleExportYOLOData = () => {
    const yoloData = {
      zones: zones.map(zone => ({
        id: zone.id,
        name: zone.name,
        // Convert to normalized coordinates (0-1)
        x: zone.x / 100,
        y: zone.y / 100,
        width: zone.width / 100,
        height: zone.height / 100,
        color: zone.color,
        status: zone.status
      })),
      metadata: {
        workstation: workstation.name,
        resolution: { width: 500, height: 500 },
        timestamp: new Date().toISOString(),
        version: "1.0"
      }
    };

    // In a real app, you would download this or send to backend
    console.log('YOLO Export Data:', yoloData);

    toast({
      title: "YOLO Data Exported",
      description: "Zone data has been prepared for YOLOv11 tracking.",
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-[80vw] sm:max-w-4xl max-h-[80vh] p-6 bg-background/95 backdrop-blur-md border border-border/50 rounded-lg overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <DialogHeader>
          <div className="flex items-start justify-between pr-8">
            <div className="flex flex-col gap-2">
              <DialogTitle className="text-xl font-bold text-foreground flex items-center gap-2">
                {workstation.name}
                <span className={`text-sm font-medium ${getStatusColor()}`}>
                  {workstation.status ? workstation.status.charAt(0).toUpperCase() + workstation.status.slice(1) : 'Unknown'}
                </span>
              </DialogTitle>
              <ConnectionStatus
                connectionState={connectionState}
                isConnected={isConnected}
                error={wsError}
                totalMessages={totalMessages}
                messagesPerSecond={messagesPerSecond}
                onReconnect={() => wsConnect(workstation.id.toString())}
                showDetails={true}
                className="max-w-md"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportData}
              className="border-border hover:bg-muted text-foreground"
            >
              <Download className="h-4 w-4 mr-2" />
              Export Data
            </Button>
          </div>
          <DialogDescription className="sr-only">
            Workstation details and monitoring information
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-[7fr_3fr] gap-6">
          {/* Live Camera Feed */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Camera className="h-5 w-5 text-foreground" />
                <h3 className="text-lg font-semibold text-foreground">Live Camera Feed</h3>
              </div>
              {showVideoPlayer && (
                <div className="flex items-center gap-2">
                  <Button
                    variant={showZoneOverlay ? "default" : "outline"}
                    size="sm"
                    onClick={handleToggleZoneOverlay}
                    className="text-xs"
                  >
                    <Target className="h-3 w-3 mr-1" />
                    {showZoneOverlay ? "Hide Zones" : "Show Zones"}
                  </Button>
                  <Button
                    variant={isEditMode ? "default" : "outline"}
                    size="sm"
                    onClick={handleToggleEditMode}
                    className={`text-xs ${isEditMode ? 'bg-primary text-primary-foreground border-primary shadow-lg' : ''}`}
                  >
                    {isEditMode ? (
                      <>
                        <Unlock className="h-3 w-3 mr-1" />
                        Lock Zones
                      </>
                    ) : (
                      <>
                        <Lock className="h-3 w-3 mr-1" />
                        Edit Zones
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
            
            <div className="space-y-3">
              {/* Zone Controls */}
              <div className="flex items-center justify-between">
                {isDrawingMode && !isEditMode && (
                  <div className="text-xs text-muted-foreground flex items-center gap-1">
                    <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                    Drawing Mode Active
                  </div>
                )}
              </div>

              {/* Video Player with Zone Overlay */}
              <div className={`bg-black rounded-lg border overflow-hidden ${
                isEditMode
                  ? 'border-primary border-2 shadow-lg shadow-primary/20'
                  : 'border-border'
              }`}>
                <VideoPlayer
                  src={getVideoSource().src}
                  sourceType={getVideoSource().sourceType}
                  fallbackSrc={getVideoSource().fallbackSrc}
                  width={videoWidth}
                  height={videoHeight}
                  autoPlay={true}
                  controls={true}
                  className="w-full"
                  onLoadedMetadata={(w, h) => {
                    setVideoWidth(w);
                    setVideoHeight(h);
                    console.log('WorkstationDetailsModal: video metadata received', { w, h });
                  }}
                  // Zone management props
                  zones={zones}
                  onZonesChange={handleZonesChange}
                  showZoneOverlay={showZoneOverlay}
                  isDrawingMode={isDrawingMode}
                  onDrawingModeChange={setIsDrawingMode}
                  maxZones={10}
                  isEditMode={isEditMode}
                  // Detection overlay props
                  detections={detectionData.detections}
                  zonesWithStatus={detectionData.zonesWithStatus}
                  showDetections={showDetections}
                  showBoundingBoxes={showBoundingBoxes}
                  showCenterDots={showCenterDots}
                  showInfoPanels={showInfoPanels}
                  onLoadSuccess={() => {
                    toast({
                      title: "Camera Connected",
                      description: "Live feed is now active.",
                    });
                  }}
                  onLoadError={(error) => {
                    toast({
                      title: "Connection Error",
                      description: error,
                      variant: "destructive",
                    });
                  }}
                />
              </div>

              {/* Debug Panel: shows current video dimensions and detection data for visual verification */}
              <div className="mt-2 p-3 bg-muted/10 rounded-md border border-border text-xs">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium">Video Debug</div>
                  <div className="text-muted-foreground">Open console for detailed logs</div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-muted-foreground">Dimensions</div>
                    <div className="font-mono">{videoWidth} x {videoHeight}</div>
                  </div>

                  <div>
                    <div className="text-muted-foreground">Detections</div>
                    <div className="font-mono">{detectionData.detections.length} transformed</div>
                  </div>
                </div>

                <div className="mt-3 max-h-36 overflow-auto bg-black/5 p-2 rounded">
                  <pre className="text-[10px]">
{JSON.stringify({
  raw: latestDetection?.persons?.slice(0,10) || [],
  transformed: detectionData.detections?.slice(0,10) || []
}, null, 2)}
                  </pre>
                </div>
              </div>
            </div>

            {/* Stats Grid - Real-time Data */}
            <div className="grid grid-cols-4 gap-3 mt-6">
              <div className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border">
                <Activity className="h-5 w-5 text-primary" />
                <div className="flex-1 text-center">
                  <p className="text-sm text-muted-foreground">People</p>
                  <p className="text-lg font-semibold text-foreground flex items-center justify-center gap-1">
                    {realtimePersonCount}
                    {isConnected && (
                      <span className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border">
                <Zap className="h-5 w-5 text-warning" />
                <div className="flex-1 text-center">
                  <p className="text-sm text-muted-foreground">Efficiency</p>
                  <p className="text-lg font-semibold text-foreground flex items-center justify-center gap-1">
                    {realtimeEfficiency.toFixed(1)}%
                    {isConnected && (
                      <span className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border">
                <Clock className="h-5 w-5 text-blue-500" />
                <div className="flex-1 text-center">
                  <p className="text-sm text-muted-foreground">Uptime</p>
                  <p className="text-lg font-semibold text-foreground">156h</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-muted/20 rounded-lg border border-border">
                <Wifi className="h-5 w-5 text-green-500" />
                <div className="flex-1 text-center">
                  <p className="text-sm text-muted-foreground">Data Rate</p>
                  <p className="text-lg font-semibold text-foreground">
                    {messagesPerSecond.toFixed(1)}/s
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Zone Manager */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-foreground" />
              <h3 className="text-lg font-semibold text-foreground">Zone Manager</h3>
            </div>
            
            <div className="bg-muted/30 rounded-lg p-4 border border-border">
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm font-medium text-foreground">ACTIVE ZONES</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAddZone}
                  className="border-border hover:bg-muted text-foreground"
                  disabled={isLoadingZones}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Zone
                </Button>
              </div>

              {isLoadingZones ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-muted-foreground">Loading zones...</div>
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent">
                {zones.map((zone) => (
                  <div key={zone.id} className={`flex items-center justify-between p-3 rounded-md border ${getZoneStatusBg(zone.status)}`}>
                    <div className="flex-1">
                      {editingZone === zone.id ? (
                        <div className="flex items-center gap-2">
                          <Input
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveEdit();
                              if (e.key === 'Escape') handleCancelEdit();
                            }}
                            className="text-sm h-8"
                            autoFocus
                          />
                          <div className="flex gap-1">
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
                              onClick={handleCancelEdit}
                              className="h-6 w-6 p-0 text-destructive hover:bg-destructive/20"
                            >
                              ✕
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <p className="text-sm font-medium text-foreground">{getZoneDisplayName(zone)}</p>
                          <p className="text-xs text-muted-foreground">{getZoneDescription(zone)}</p>
                        </>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <span className={`text-sm font-semibold ${getZoneStatusColor(zone.status)}`}>
                          {zone.status}
                        </span>
                        <p className="text-xs text-muted-foreground">Current Status</p>
                      </div>
                      {editingZone !== zone.id && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEditZone(zone.id)}>
                              <Edit3 className="h-4 w-4 mr-2" />
                              Edit Description
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleConfigureZone(zone.id)}>
                              <MapPin className="h-4 w-4 mr-2" />
                              Edit Boundaries
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleDeleteZone(zone.id)}
                              className="text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete Zone
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                  </div>
                ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}