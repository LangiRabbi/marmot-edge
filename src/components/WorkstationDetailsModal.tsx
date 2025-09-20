import { Camera, Clock, Activity, Zap, MapPin, Download, Edit3, Trash2, Plus, MoreHorizontal, Target } from "lucide-react";
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
import { Zone } from "./VideoCanvasOverlay";
import { useState, useEffect } from "react";
import type { VideoSourceConfig } from "@/services/workstationService";
import { zoneService, type CanvasZone } from "@/services/zoneService";

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
  const [showVideoPlayer, setShowVideoPlayer] = useState(false);
  const [showZoneOverlay, setShowZoneOverlay] = useState(false);
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [isLoadingZones, setIsLoadingZones] = useState(false);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!open) {
      setShowVideoPlayer(false);
      setShowZoneOverlay(false);
      setIsDrawingMode(false);
      setEditingZone(null);
      setEditingName('');
    }
  }, [open]);

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
            { id: 1, name: 'Assembly Area', x: 20, y: 20, width: 30, height: 25, color: '#3B82F6', status: 'Work' },
            { id: 2, name: 'Quality Control', x: 55, y: 20, width: 25, height: 20, color: '#10B981', status: 'Idle' },
            { id: 3, name: 'Packaging Station', x: 20, y: 50, width: 28, height: 30, color: '#F59E0B', status: 'Work' },
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
        const filePath = videoConfig.filePath;
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
      case 'Work': return 'text-success';
      case 'Idle': return 'text-muted-foreground';
      case 'Other': return 'text-warning';
      default: return 'text-muted-foreground';
    }
  };

  const getZoneStatusBg = (status: string) => {
    switch (status) {
      case 'Work': return 'bg-success/20 border-success/30';
      case 'Idle': return 'bg-muted/20 border-muted';
      case 'Other': return 'bg-warning/20 border-warning/30';
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
    setShowZoneOverlay(!showZoneOverlay);
    if (isDrawingMode && !showZoneOverlay) {
      setIsDrawingMode(false);
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
      <DialogContent className="max-w-4xl bg-background border-border" onClick={(e) => e.stopPropagation()}>
        <DialogHeader>
          <div className="flex items-start justify-between pr-8">
            <DialogTitle className="text-xl font-bold text-foreground flex items-center gap-2">
              {workstation.name}
              <span className={`text-sm font-medium ${getStatusColor()}`}>
                {workstation.status ? workstation.status.charAt(0).toUpperCase() + workstation.status.slice(1) : 'Unknown'}
              </span>
            </DialogTitle>
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Live Camera Feed */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Camera className="h-5 w-5 text-foreground" />
              <h3 className="text-lg font-semibold text-foreground">Live Camera Feed</h3>
            </div>
            
            {showVideoPlayer ? (
              <div className="space-y-3">
                {/* Zone Controls */}
                <div className="flex items-center justify-between">
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
                    {showZoneOverlay && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleExportYOLOData}
                        className="text-xs"
                      >
                        <Download className="h-3 w-3 mr-1" />
                        Export YOLO
                      </Button>
                    )}
                  </div>
                  {isDrawingMode && (
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                      Drawing Mode Active
                    </div>
                  )}
                </div>

                {/* Video Player with Zone Overlay */}
                <div className="bg-black rounded-lg border border-border overflow-hidden">
                  <VideoPlayer
                    src={getVideoSource().src}
                    sourceType={getVideoSource().sourceType}
                    fallbackSrc={getVideoSource().fallbackSrc}
                    width={400}
                    height={300}
                    autoPlay={true}
                    controls={true}
                    className="w-full"
                    // Zone management props
                    zones={zones}
                    onZonesChange={handleZonesChange}
                    showZoneOverlay={showZoneOverlay}
                    isDrawingMode={isDrawingMode}
                    onDrawingModeChange={setIsDrawingMode}
                    maxZones={10}
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
              </div>
            ) : (
              <div className="bg-muted/30 rounded-lg p-8 text-center border border-border cursor-pointer hover:bg-muted/40 transition-colors"
                   onClick={() => setShowVideoPlayer(true)}>
                <div className="w-20 h-20 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
                  <Camera className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-foreground font-medium">Click to Start Camera Feed</p>
                <p className="text-sm text-muted-foreground">Resolution: 1920x1080 • 30 FPS</p>
              </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-4 mt-6">
              <div className="text-center p-4 bg-muted/20 rounded-lg border border-border">
                <Clock className="h-6 w-6 text-primary mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Uptime</p>
                <p className="text-lg font-semibold text-foreground">156h</p>
              </div>
              <div className="text-center p-4 bg-muted/20 rounded-lg border border-border">
                <Activity className="h-6 w-6 text-success mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Cycles</p>
                <p className="text-lg font-semibold text-foreground">234</p>
              </div>
              <div className="text-center p-4 bg-muted/20 rounded-lg border border-border">
                <Zap className="h-6 w-6 text-warning mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Efficiency</p>
                <p className="text-lg font-semibold text-foreground">{workstation.efficiency}%</p>
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