/**
 * Frame capture service using requestVideoFrameCallback API
 * Based on MDN Web Docs best practices (2024)
 */

export interface FrameCaptureOptions {
  targetFPS?: number; // Default: 1-2 FPS for detection
  quality?: number; // JPEG quality 0-1, default: 0.9
  maxWidth?: number;
  maxHeight?: number;
}

export interface CapturedFrame {
  blob: Blob;
  timestamp: number;
  frameNumber: number;
  metadata: {
    mediaTime: number;
    width: number;
    height: number;
  };
}

export class FrameCaptureService {
  private video: HTMLVideoElement | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private ctx: CanvasRenderingContext2D | null = null;
  private isCapturing = false;
  private frameNumber = 0;
  private lastCaptureTime = 0;
  private options: Required<FrameCaptureOptions>;
  private callbackHandle: number | null = null;

  constructor(options: FrameCaptureOptions = {}) {
    this.options = {
      targetFPS: options.targetFPS ?? 1,
      quality: options.quality ?? 0.9,
      maxWidth: options.maxWidth ?? 1920,
      maxHeight: options.maxHeight ?? 1080,
    };
  }

  /**
   * Initialize frame capture for a video element
   */
  initialize(video: HTMLVideoElement): void {
    this.video = video;

    // Create off-screen canvas for frame capture
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d', {
      alpha: false, // No transparency needed
      willReadFrequently: false, // Optimize for drawing
    });

    if (!this.ctx) {
      throw new Error('Failed to get canvas 2D context');
    }

    // Set canvas size based on video dimensions
    const width = Math.min(video.videoWidth, this.options.maxWidth);
    const height = Math.min(video.videoHeight, this.options.maxHeight);
    this.canvas.width = width;
    this.canvas.height = height;
  }

  /**
   * Start capturing frames using requestVideoFrameCallback
   */
  async startCapture(
    onFrame: (frame: CapturedFrame) => void | Promise<void>
  ): Promise<void> {
    if (!this.video || !this.canvas || !this.ctx) {
      throw new Error('Frame capture not initialized. Call initialize() first.');
    }

    if (this.isCapturing) {
      console.warn('Frame capture already running');
      return;
    }

    this.isCapturing = true;
    this.frameNumber = 0;
    this.lastCaptureTime = 0;

    const captureLoop = async (now: DOMHighResTimeStamp, metadata: VideoFrameCallbackMetadata) => {
      if (!this.isCapturing || !this.video || !this.canvas || !this.ctx) {
        return;
      }

      // Throttle to target FPS
      const minInterval = 1000 / this.options.targetFPS;
      const timeSinceLastCapture = now - this.lastCaptureTime;

      if (timeSinceLastCapture >= minInterval) {
        try {
          // Draw current video frame to canvas
          this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

          // Convert canvas to blob
          const blob = await new Promise<Blob>((resolve, reject) => {
            this.canvas!.toBlob(
              (blob) => {
                if (blob) {
                  resolve(blob);
                } else {
                  reject(new Error('Failed to create blob from canvas'));
                }
              },
              'image/jpeg',
              this.options.quality
            );
          });

          // Create captured frame object
          const capturedFrame: CapturedFrame = {
            blob,
            timestamp: now,
            frameNumber: this.frameNumber++,
            metadata: {
              mediaTime: metadata.mediaTime,
              width: this.canvas.width,
              height: this.canvas.height,
            },
          };

          // Call user callback
          await onFrame(capturedFrame);

          this.lastCaptureTime = now;
        } catch (error) {
          console.error('Frame capture error:', error);
        }
      }

      // Request next frame
      if (this.isCapturing && this.video) {
        this.callbackHandle = this.video.requestVideoFrameCallback(captureLoop);
      }
    };

    // Start the capture loop
    this.callbackHandle = this.video.requestVideoFrameCallback(captureLoop);
  }

  /**
   * Stop capturing frames
   */
  stopCapture(): void {
    this.isCapturing = false;

    if (this.callbackHandle !== null && this.video) {
      // Cancel pending callback
      this.video.cancelVideoFrameCallback(this.callbackHandle);
      this.callbackHandle = null;
    }
  }

  /**
   * Capture a single frame manually
   */
  async captureFrame(): Promise<CapturedFrame> {
    if (!this.video || !this.canvas || !this.ctx) {
      throw new Error('Frame capture not initialized');
    }

    if (!this.video.paused && !this.video.ended) {
      // Draw current frame
      this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

      // Convert to blob
      const blob = await new Promise<Blob>((resolve, reject) => {
        this.canvas!.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error('Failed to create blob'));
            }
          },
          'image/jpeg',
          this.options.quality
        );
      });

      return {
        blob,
        timestamp: performance.now(),
        frameNumber: this.frameNumber++,
        metadata: {
          mediaTime: this.video.currentTime,
          width: this.canvas.width,
          height: this.canvas.height,
        },
      };
    }

    throw new Error('Video is not playing');
  }

  /**
   * Update capture options
   */
  updateOptions(options: Partial<FrameCaptureOptions>): void {
    this.options = {
      ...this.options,
      ...options,
    };
  }

  /**
   * Check if browser supports requestVideoFrameCallback
   */
  static isSupported(): boolean {
    return 'requestVideoFrameCallback' in HTMLVideoElement.prototype;
  }

  /**
   * Cleanup resources
   */
  dispose(): void {
    this.stopCapture();
    this.video = null;
    this.canvas = null;
    this.ctx = null;
  }
}