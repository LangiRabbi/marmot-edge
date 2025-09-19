import React, { useState } from 'react';
import { VideoPlayer } from './VideoPlayer';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog';
import { X, AlertCircle, Camera } from 'lucide-react';

interface VideoSourceConfig {
  type: 'rtsp' | 'usb' | 'file' | 'hls';
  url?: string;
  usbDeviceId?: string;
  fileName?: string;
  filePath?: string;
}

interface VideoPlayerModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workstationName: string;
  workstationId: string;
  videoConfig?: VideoSourceConfig;
}

// Test video sources for development
const TEST_SOURCES = {
  hls: "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
  mp4: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
  rtsp: "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4" // Example RTSP (converted to HLS)
};

export function VideoPlayerModal({
  open,
  onOpenChange,
  workstationName,
  workstationId,
  videoConfig
}: VideoPlayerModalProps) {
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');

  // Determine video source and type
  const getVideoSource = (): { src: string; type: 'rtsp' | 'usb' | 'file' | 'hls' } => {
    if (!videoConfig) {
      // Default to test HLS stream
      return { src: TEST_SOURCES.hls, type: 'hls' };
    }

    switch (videoConfig.type) {
      case 'rtsp':
        // In production, this would be converted to HLS by media server
        // For now, use test HLS stream
        return { src: videoConfig.url || TEST_SOURCES.hls, type: 'hls' };

      case 'usb':
        return { src: videoConfig.usbDeviceId || '', type: 'usb' };

      case 'file':
        // Use file path from Supabase or local storage
        return { src: videoConfig.filePath || TEST_SOURCES.mp4, type: 'file' };

      case 'hls':
        return { src: videoConfig.url || TEST_SOURCES.hls, type: 'hls' };

      default:
        return { src: TEST_SOURCES.mp4, type: 'file' };
    }
  };

  const { src, type } = getVideoSource();

  const handleLoadSuccess = () => {
    setConnectionStatus('connected');
    setError(null);
  };

  const handleLoadError = (errorMsg: string) => {
    setConnectionStatus('error');
    setError(errorMsg);
  };

  const handleRetryConnection = () => {
    setConnectionStatus('connecting');
    setError(null);
    // Force re-render of VideoPlayer by changing key
    window.location.reload();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] p-0 bg-background/95 backdrop-blur-md border border-border/50">
        {/* Header */}
        <DialogHeader className="p-6 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Camera className="h-6 w-6 text-primary" />
              <div>
                <DialogTitle className="text-xl font-semibold">
                  {workstationName} - Live Feed
                </DialogTitle>
                <div className="flex items-center space-x-2 mt-1">
                  <div className={`h-2 w-2 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-green-500' :
                    connectionStatus === 'error' ? 'bg-red-500' :
                    'bg-yellow-500 animate-pulse'
                  }`} />
                  <span className="text-sm text-muted-foreground">
                    {connectionStatus === 'connected' ? 'Connected' :
                     connectionStatus === 'error' ? 'Connection Error' :
                     'Connecting...'}
                  </span>
                  {videoConfig?.type && (
                    <>
                      <span className="text-muted-foreground">•</span>
                      <span className="text-sm text-muted-foreground uppercase">
                        {videoConfig.type}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onOpenChange(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
        </DialogHeader>

        {/* Video Player Container */}
        <div className="px-6 pb-6">
          <div className="relative bg-black rounded-lg overflow-hidden">
            {error ? (
              /* Error State */
              <div className="flex flex-col items-center justify-center h-96 p-8 text-center">
                <AlertCircle className="h-12 w-12 text-red-400 mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">
                  Unable to Connect
                </h3>
                <p className="text-red-400 mb-6 max-w-md">
                  {error}
                </p>
                <Button
                  onClick={handleRetryConnection}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  Retry Connection
                </Button>
              </div>
            ) : (
              /* Video Player */
              <VideoPlayer
                src={src}
                sourceType={type}
                width={640}
                height={480}
                autoPlay={true}
                controls={true}
                className="w-full"
                onLoadSuccess={handleLoadSuccess}
                onLoadError={handleLoadError}
              />
            )}
          </div>

          {/* Video Info */}
          <div className="mt-4 p-4 bg-muted/30 rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-foreground">Source:</span>
                <span className="ml-2 text-muted-foreground">
                  {type.toUpperCase()}
                  {videoConfig?.type === 'rtsp' && videoConfig.url && (
                    <span className="block text-xs mt-1 truncate">
                      {videoConfig.url}
                    </span>
                  )}
                </span>
              </div>
              <div>
                <span className="font-medium text-foreground">Workstation:</span>
                <span className="ml-2 text-muted-foreground">{workstationName}</span>
              </div>
              <div>
                <span className="font-medium text-foreground">Status:</span>
                <span className={`ml-2 ${
                  connectionStatus === 'connected' ? 'text-green-400' :
                  connectionStatus === 'error' ? 'text-red-400' :
                  'text-yellow-400'
                }`}>
                  {connectionStatus === 'connected' ? 'Live' :
                   connectionStatus === 'error' ? 'Offline' :
                   'Connecting...'}
                </span>
              </div>
              <div>
                <span className="font-medium text-foreground">Resolution:</span>
                <span className="ml-2 text-muted-foreground">640x480</span>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}