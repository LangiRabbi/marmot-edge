import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import Hls from 'hls.js';
import { Button } from '@/components/ui/button';
import { Play, Pause, Volume2, VolumeX, Maximize } from 'lucide-react';
import { VideoCanvasOverlay, Zone } from './VideoCanvasOverlay';

interface VideoPlayerProps {
  src?: string;
  sourceType: 'rtsp' | 'usb' | 'file' | 'hls';
  fallbackSrc?: string;
  width?: number;
  height?: number;
  autoPlay?: boolean;
  controls?: boolean;
  className?: string;
  onLoadError?: (error: string) => void;
  onLoadSuccess?: () => void;
  // Zone management props
  zones?: Zone[];
  onZonesChange?: (zones: Zone[]) => void;
  showZoneOverlay?: boolean;
  isDrawingMode?: boolean;
  onDrawingModeChange?: (mode: boolean) => void;
  maxZones?: number;
}

export function VideoPlayer({
  src,
  sourceType,
  fallbackSrc,
  width = 500,
  height = 500,
  autoPlay = false,
  controls = true,
  className = "",
  onLoadError,
  onLoadSuccess,
  // Zone management props
  zones = [],
  onZonesChange,
  showZoneOverlay = false,
  isDrawingMode = false,
  onDrawingModeChange,
  maxZones = 10
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [usingFallback, setUsingFallback] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(src);

  // Cleanup HLS instance
  const cleanupHls = () => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
  };

  // Memoize onLoadSuccess callback to prevent unnecessary re-renders
  const handleLoadSuccessCallback = useCallback(() => {
    if (onLoadSuccess) onLoadSuccess();
  }, [onLoadSuccess]);

  // Reset fallback state when src changes
  useEffect(() => {
    setCurrentSrc(src);
    setUsingFallback(false);
    setError(null);
  }, [src]);

  // Initialize video source based on type
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !currentSrc) return;

    setIsLoading(true);
    setError(null);

    // Create stable references to prevent cleanup errors
    let isMounted = true;

    const handleLoadSuccess = () => {
      if (!isMounted) return; // Prevent calls after cleanup
      console.log('Video loaded successfully');
      setIsLoading(false);
      handleLoadSuccessCallback();
    };

    const handleLoadError = (errorMsg: string) => {
      if (!isMounted) return; // Prevent calls after cleanup
      console.error('Video load error:', errorMsg);

      // Try fallback if we have one and haven't used it yet
      if (fallbackSrc && !usingFallback && currentSrc !== fallbackSrc) {
        console.log('Trying fallback video source:', fallbackSrc);
        setUsingFallback(true);
        setCurrentSrc(fallbackSrc);
        setError(null);
        return; // Don't set error state, let it try fallback
      }

      setError(errorMsg);
      setIsLoading(false);
      if (onLoadError) onLoadError(errorMsg);
    };

    switch (sourceType) {
      case 'hls':
      case 'rtsp': {
        // For RTSP, we assume it's been converted to HLS format
        if (Hls.isSupported()) {
          cleanupHls();
          hlsRef.current = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
            backBufferLength: 90
          });

          hlsRef.current.loadSource(currentSrc);
          hlsRef.current.attachMedia(video);

          hlsRef.current.on(Hls.Events.MANIFEST_PARSED, handleLoadSuccess);
          hlsRef.current.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
              handleLoadError(`HLS Error: ${data.details}`);
            }
          });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          // Native HLS support (Safari)
          video.src = currentSrc;
          video.addEventListener('loadedmetadata', handleLoadSuccess);
          video.addEventListener('error', () => handleLoadError('Failed to load HLS stream'));
        } else {
          handleLoadError('HLS not supported in this browser');
        }
        break;
      }

      case 'usb': {
        // USB Camera using getUserMedia
        navigator.mediaDevices.getUserMedia({
          video: {
            deviceId: currentSrc ? { exact: currentSrc } : undefined,
            width: { ideal: width },
            height: { ideal: height }
          },
          audio: false
        })
        .then(stream => {
          video.srcObject = stream;
          video.addEventListener('loadedmetadata', handleLoadSuccess);
        })
        .catch(err => {
          handleLoadError(`USB Camera Error: ${err.message}`);
        });
        break;
      }

      case 'file': {
        // Regular video file
        video.src = currentSrc || '';
        video.addEventListener('loadedmetadata', handleLoadSuccess);
        video.addEventListener('error', () => handleLoadError('Failed to load video file'));
        break;
      }

      default:
        handleLoadError(`Unsupported source type: ${sourceType}`);
    }

    return () => {
      console.log('Cleaning up video player');
      isMounted = false; // Prevent further callbacks
      cleanupHls();
      if (video) {
        // Remove event listeners
        video.removeEventListener('loadedmetadata', handleLoadSuccess);
        video.removeEventListener('error', handleLoadError);

        // Clean up media streams
        if (video.srcObject) {
          const stream = video.srcObject as MediaStream;
          stream.getTracks().forEach(track => track.stop());
          video.srcObject = null;
        }

        // Clear video source
        video.src = '';
        video.load();
      }
    };
  }, [currentSrc, sourceType, width, height, fallbackSrc, usingFallback, onLoadError, handleLoadSuccessCallback]); // React to currentSrc changes for fallback functionality

  // Handle play/pause
  const togglePlay = async () => {
    const video = videoRef.current;
    if (!video) return;

    try {
      if (isPlaying) {
        video.pause();
        setIsPlaying(false);
      } else {
        await video.play();
        setIsPlaying(true);
      }
    } catch (err) {
      setError('Failed to play video');
    }
  };

  // Handle mute/unmute
  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;

    video.muted = !video.muted;
    setIsMuted(video.muted);
  };

  // Handle fullscreen
  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      video.requestFullscreen();
    }
  };

  return (
    <div className={`relative bg-black rounded-lg overflow-hidden ${className}`}>
      {/* Video Element */}
      <video
        ref={videoRef}
        width={width}
        height={height}
        className="w-full h-full object-contain"
        autoPlay={autoPlay}
        muted={isMuted}
        playsInline
        style={{ aspectRatio: `${width}/${height}` }}
      />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <div className="text-white text-lg">Loading video...</div>
        </div>
      )}

      {/* Error Overlay */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <div className="text-red-400 text-center p-4">
            <div className="text-lg mb-2">Video Error</div>
            <div className="text-sm">{error}</div>
          </div>
        </div>
      )}

      {/* Zone Overlay */}
      {showZoneOverlay && onZonesChange && (
        <VideoCanvasOverlay
          key={`overlay-${showZoneOverlay}`}
          width={width}
          height={height}
          zones={zones}
          onZonesChange={onZonesChange}
          isDrawingMode={isDrawingMode}
          onDrawingModeChange={onDrawingModeChange || (() => {})}
          maxZones={maxZones}
        />
      )}

      {/* Custom Controls */}
      {controls && !error && (
        <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white p-4 z-20">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={togglePlay}
                className="text-white hover:text-primary"
                disabled={isLoading}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={toggleMute}
                className="text-white hover:text-primary"
                disabled={isLoading}
              >
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </Button>
            </div>

            <Button
              size="sm"
              variant="ghost"
              onClick={toggleFullscreen}
              className="text-white hover:text-primary"
              disabled={isLoading}
            >
              <Maximize className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}