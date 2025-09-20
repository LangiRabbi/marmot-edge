import React, { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Search, Monitor, Camera, Video, Upload } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import type { VideoSourceConfig } from "@/services/workstationService";
import { videoStreamService } from "@/services/videoStreamService";

interface AddWorkstationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddWorkstation: (name: string, ipAddress: string, videoConfig?: VideoSourceConfig) => void;
}

const mockDevices = [
  { name: "Raspberry Pi", ip: "192.168.1.101", type: "edge" },
  { name: "Edge Device", ip: "192.168.1.102", type: "edge" },
  { name: "Industrial Camera", ip: "192.168.1.103", type: "camera" }
];

export function AddWorkstationModal({ open, onOpenChange, onAddWorkstation }: AddWorkstationModalProps) {
  const [formData, setFormData] = useState({
    name: "",
    ipAddress: ""
  });
  const [videoSource, setVideoSource] = useState<'rtsp' | 'usb' | 'file'>('rtsp');
  const [rtspUrl, setRtspUrl] = useState('');
  const [selectedUsbDevice, setSelectedUsbDevice] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [discoveredDevices, setDiscoveredDevices] = useState<typeof mockDevices>([]);
  const [showDevices, setShowDevices] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // USB Camera states
  const [usbCameras, setUsbCameras] = useState<MediaDeviceInfo[]>([]);
  const [isLoadingCameras, setIsLoadingCameras] = useState(false);
  const [previewStream, setPreviewStream] = useState<MediaStream | null>(null);
  const previewVideoRef = useRef<HTMLVideoElement>(null);

  // RTSP testing states
  const [isTestingRtsp, setIsTestingRtsp] = useState(false);
  const [rtspTestResult, setRtspTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Reset file input when modal closes or opens
  useEffect(() => {
    if (!open) {
      // Reset all form data when modal closes
      setFormData({
        name: '',
        ipAddress: ''
      });
      setVideoSource('rtsp');
      setRtspUrl('');
      setSelectedUsbDevice('');
      setUploadedFile(null);
      setShowDevices(false);
      setDiscoveredDevices([]);
      // Reset USB camera states
      setUsbCameras([]);
      stopCameraPreview();
      // Reset RTSP test states
      setIsTestingRtsp(false);
      setRtspTestResult(null);
    }
  }, [open, stopCameraPreview]);

  // Additional cleanup on component unmount
  useEffect(() => {
    const currentFileInput = fileInputRef.current;
    return () => {
      if (currentFileInput) {
        currentFileInput.value = '';
      }
      stopCameraPreview();
    };
  }, [stopCameraPreview]);

  // Load USB cameras when USB source is selected
  useEffect(() => {
    if (videoSource === 'usb' && open) {
      enumerateUsbCameras();
    } else {
      stopCameraPreview();
    }
  }, [videoSource, open, stopCameraPreview, enumerateUsbCameras]);

  // Function to reset file input manually
  const resetFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setUploadedFile(null);
  };

  // USB Camera functions
  const enumerateUsbCameras = useCallback(async () => {
    setIsLoadingCameras(true);
    try {
      // Request permission first
      await navigator.mediaDevices.getUserMedia({ video: true });

      // Get all media devices
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');

      setUsbCameras(videoDevices);
      console.log('Found USB cameras:', videoDevices);
    } catch (error) {
      console.error('Failed to enumerate cameras:', error);
      setUsbCameras([]);
    } finally {
      setIsLoadingCameras(false);
    }
  }, []);

  const startCameraPreview = async (deviceId: string) => {
    try {
      // Stop existing stream
      if (previewStream) {
        previewStream.getTracks().forEach(track => track.stop());
      }

      // Start new stream
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: { exact: deviceId },
          width: { ideal: 320 },
          height: { ideal: 240 }
        }
      });

      setPreviewStream(stream);

      // Attach to video element
      if (previewVideoRef.current) {
        previewVideoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Failed to start camera preview:', error);
    }
  };

  const stopCameraPreview = useCallback(() => {
    if (previewStream) {
      previewStream.getTracks().forEach(track => track.stop());
      setPreviewStream(null);
    }
    if (previewVideoRef.current) {
      previewVideoRef.current.srcObject = null;
    }
  }, [previewStream]);

  // RTSP testing function
  const testRtspConnection = async () => {
    if (!rtspUrl.trim()) {
      setRtspTestResult({ success: false, message: 'Please enter RTSP URL' });
      return;
    }

    setIsTestingRtsp(true);
    setRtspTestResult(null);

    try {
      const result = await videoStreamService.testRtspConnection(rtspUrl);
      setRtspTestResult(result);
    } catch (error) {
      setRtspTestResult({ success: false, message: 'Connection test failed' });
    } finally {
      setIsTestingRtsp(false);
    }
  };


  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate file size (500MB limit)
    if (videoSource === 'file' && uploadedFile && uploadedFile.size > 500 * 1024 * 1024) {
      alert('File size exceeds 500MB limit. Please select a smaller file.');
      return;
    }

    // IP Address is only required for RTSP and USB sources
    const isIpRequired = videoSource === 'rtsp' || videoSource === 'usb';
    const isFormValid = formData.name.trim() && (!isIpRequired || formData.ipAddress.trim());

    if (isFormValid) {
      const videoConfig: VideoSourceConfig = {
        type: videoSource,
        url: videoSource === 'rtsp' ? rtspUrl : undefined,
        usbDeviceId: videoSource === 'usb' ? selectedUsbDevice : undefined,
        fileName: videoSource === 'file' ? uploadedFile?.name : undefined,
        filePath: videoSource === 'file' && uploadedFile ? URL.createObjectURL(uploadedFile) : undefined
      };

      onAddWorkstation(formData.name.trim(), formData.ipAddress.trim(), videoConfig);

      // Reset form
      setFormData({ name: "", ipAddress: "" });
      setVideoSource('rtsp');
      setRtspUrl('');
      resetFileInput();
      setSelectedUsbDevice('');
      setUploadedFile(null);
      setShowDevices(false);
      setDiscoveredDevices([]);
    }
  };

  const handleScanDevices = async () => {
    setIsScanning(true);
    setShowDevices(false);
    
    // Simulate network scan
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setDiscoveredDevices(mockDevices);
    setShowDevices(true);
    setIsScanning(false);
  };

  const handleSelectDevice = (device: typeof mockDevices[0]) => {
    setFormData(prev => ({
      ...prev,
      ipAddress: device.ip,
      name: prev.name || device.name
    }));
    setShowDevices(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-background/95 backdrop-blur-md border border-border/50 shadow-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-foreground">
            Add New Workstation
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Enter the details for the new workstation to add it to your monitoring system.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-foreground font-medium">
              Workstation Name
            </Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Assembly Line 3"
              className="bg-background/50 border-border text-foreground focus:border-primary focus:ring-1 focus:ring-primary/50 h-10 px-3"
              required
            />
          </div>

          {/* IP Address - Only shown for RTSP and USB sources */}
          {(videoSource === 'rtsp' || videoSource === 'usb') && (
            <div className="space-y-2">
              <Label htmlFor="ipAddress" className="text-foreground font-medium">
                Device IP Address
              </Label>

              {/* Device Discovery Section */}
              <div className="space-y-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleScanDevices}
                  disabled={isScanning}
                  className="w-full border-border hover:bg-muted text-foreground"
                >
                  {isScanning ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Scanning for devices...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-4 w-4" />
                      Scan for Devices
                    </>
                  )}
                </Button>

                {/* Discovered Devices List */}
                {showDevices && discoveredDevices.length > 0 && (
                  <div className="space-y-2 p-3 bg-muted/30 rounded-lg border border-border">
                    <p className="text-sm font-medium text-foreground">Discovered Devices:</p>
                    <div className="space-y-1">
                      {discoveredDevices.map((device, index) => (
                        <button
                          key={index}
                          type="button"
                          onClick={() => handleSelectDevice(device)}
                          className="w-full p-2 text-left bg-background/50 hover:bg-background/80 border border-border rounded-md smooth-transition flex items-center space-x-2"
                        >
                          <Monitor className="h-4 w-4 text-primary" />
                          <span className="text-foreground">
                            {device.name} ({device.ip})
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <Input
                id="ipAddress"
                value={formData.ipAddress}
                onChange={(e) => setFormData({ ...formData, ipAddress: e.target.value })}
                placeholder="e.g., 192.168.1.100"
                className="bg-background/50 border-border text-foreground focus:border-primary focus:ring-1 focus:ring-primary/50 h-10 px-3"
                required
              />
            </div>
          )}

          {/* Video Source Selection */}
          <div className="space-y-4">
            <Label className="text-foreground font-medium">Video Source</Label>
            <RadioGroup
              value={videoSource}
              onValueChange={(value) => setVideoSource(value as 'rtsp' | 'usb' | 'file')}
              className="space-y-3"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="rtsp" id="rtsp" />
                <Label htmlFor="rtsp" className="flex items-center space-x-2 cursor-pointer">
                  <Camera className="h-4 w-4 text-primary" />
                  <span>Live Camera (RTSP)</span>
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="usb" id="usb" />
                <Label htmlFor="usb" className="flex items-center space-x-2 cursor-pointer">
                  <Video className="h-4 w-4 text-primary" />
                  <span>USB Camera</span>
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="file" id="file" />
                <Label htmlFor="file" className="flex items-center space-x-2 cursor-pointer">
                  <Upload className="h-4 w-4 text-primary" />
                  <span>Upload Video File</span>
                </Label>
              </div>
            </RadioGroup>

            {/* RTSP Configuration */}
            {videoSource === 'rtsp' && (
              <div className="space-y-3 p-4 bg-muted/30 rounded-lg border border-border">
                <Label htmlFor="rtspUrl" className="text-foreground font-medium">
                  RTSP URL
                </Label>
                <Input
                  id="rtspUrl"
                  value={rtspUrl}
                  onChange={(e) => setRtspUrl(e.target.value)}
                  placeholder="rtsp://192.168.1.100:554/stream"
                  className="bg-background/50 border-border text-foreground focus:border-primary focus:ring-1 focus:ring-primary/50"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={testRtspConnection}
                  disabled={isTestingRtsp || !rtspUrl.trim()}
                  className="border-border hover:bg-muted text-foreground"
                >
                  {isTestingRtsp ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Testing...
                    </>
                  ) : (
                    'Test Connection'
                  )}
                </Button>

                {/* RTSP Test Result */}
                {rtspTestResult && (
                  <div className={`mt-3 p-3 rounded-md text-sm ${
                    rtspTestResult.success
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                  }`}>
                    {rtspTestResult.message}
                  </div>
                )}
              </div>
            )}

            {/* USB Camera Configuration */}
            {videoSource === 'usb' && (
              <div className="space-y-3 p-4 bg-muted/30 rounded-lg border border-border">
                <div className="flex items-center justify-between">
                  <Label className="text-foreground font-medium">USB Camera Device</Label>
                  {isLoadingCameras && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading cameras...
                    </div>
                  )}
                </div>

                <select
                  value={selectedUsbDevice}
                  onChange={(e) => {
                    const deviceId = e.target.value;
                    setSelectedUsbDevice(deviceId);
                    if (deviceId) {
                      startCameraPreview(deviceId);
                    } else {
                      stopCameraPreview();
                    }
                  }}
                  className="w-full p-2 bg-background/50 border border-border rounded-md text-foreground focus:border-primary focus:ring-1 focus:ring-primary/50"
                  disabled={isLoadingCameras}
                >
                  <option value="">
                    {isLoadingCameras ? 'Loading cameras...' : 'Select USB Camera...'}
                  </option>
                  {usbCameras.map((camera, index) => (
                    <option key={camera.deviceId} value={camera.deviceId}>
                      {camera.label || `Camera ${index + 1}`}
                    </option>
                  ))}
                </select>

                {selectedUsbDevice && (
                  <div className="mt-3">
                    <Label className="text-foreground font-medium text-sm">Camera Preview</Label>
                    <div className="mt-2 w-full h-48 bg-black/20 border border-border rounded-md overflow-hidden">
                      <video
                        ref={previewVideoRef}
                        autoPlay
                        muted
                        playsInline
                        className="w-full h-full object-cover"
                        style={{ transform: 'scaleX(-1)' }}
                      />
                    </div>
                  </div>
                )}

                {usbCameras.length === 0 && !isLoadingCameras && (
                  <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded-md">
                    No USB cameras detected. Please connect a camera and refresh.
                  </div>
                )}
              </div>
            )}

            {/* File Upload Configuration */}
            {videoSource === 'file' && (
              <div className="space-y-4 p-4 bg-muted/30 rounded-lg border border-border">
                <Label className="text-foreground font-medium">
                  Video File (MP4, WebM, MOV - Max 500MB)
                </Label>
                <div className="relative">
                  <input
                    id="video-file-upload"
                    ref={fileInputRef}
                    type="file"
                    accept=".mp4,.webm,.mov"
                    onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                    className="sr-only"
                  />
                  <label
                    htmlFor="video-file-upload"
                    className="inline-flex items-center justify-center px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md text-sm font-medium cursor-pointer"
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Add File
                  </label>
                  {!uploadedFile && (
                    <span className="ml-3 text-sm text-muted-foreground">
                      No file selected
                    </span>
                  )}
                </div>
                {uploadedFile && (
                  <div className="text-sm text-muted-foreground bg-background/30 p-2 rounded border">
                    <strong>Selected:</strong> {uploadedFile.name} ({(uploadedFile.size / 1024 / 1024).toFixed(1)} MB)
                    {uploadedFile.size > 500 * 1024 * 1024 && (
                      <div className="text-red-500 mt-1">⚠️ File size exceeds 500MB limit</div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-border hover:bg-muted text-foreground"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Add Workstation
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}