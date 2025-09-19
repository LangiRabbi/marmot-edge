import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import Hls from 'hls.js';
import { Button } from '@/components/ui/button';
import { Play, Pause, Volume2, VolumeX, Maximize } from 'lucide-react';

interface VideoPlayerProps {
  src?: string;
  sourceType: 'rtsp' | 'usb' | 'file' | 'hls';
  width?: number;
  height?: number;
  autoPlay?: boolean;
  controls?: boolean;
  className?: string;
  onLoadError?: (error: string) => void;
  onLoadSuccess?: () => void;
}

export function VideoPlayer({
  src,
  sourceType,
  width = 500,
  height = 500,
  autoPlay = false,
  controls = true,
  className = "",
  onLoadError,
  onLoadSuccess
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Cleanup HLS instance
  const cleanupHls = () => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
  };

  // Initialize video source based on type
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    setIsLoading(true);
    setError(null);

    const handleLoadSuccess = () => {
      console.log('Video loaded successfully');
      setIsLoading(false);
      if (onLoadSuccess) onLoadSuccess();
    };

    const handleLoadError = (errorMsg: string) => {
      console.error('Video load error:', errorMsg);
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

          hlsRef.current.loadSource(src);
          hlsRef.current.attachMedia(video);

          hlsRef.current.on(Hls.Events.MANIFEST_PARSED, handleLoadSuccess);
          hlsRef.current.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
              handleLoadError(`HLS Error: ${data.details}`);
            }
          });
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          // Native HLS support (Safari)
          video.src = src;
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
            deviceId: src ? { exact: src } : undefined,
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
        video.src = src;
        video.addEventListener('loadedmetadata', handleLoadSuccess);
        video.addEventListener('error', () => handleLoadError('Failed to load video file'));
        break;
      }

      default:
        handleLoadError(`Unsupported source type: ${sourceType}`);
    }

    return () => {
      console.log('Cleaning up video player');
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
  }, [src, sourceType]); // Remove callbacks from dependencies to prevent re-render loop

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

      {/* Custom Controls */}
      {controls && !error && (
        <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white p-4">
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