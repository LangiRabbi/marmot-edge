import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Search, Monitor } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AddWorkstationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAddWorkstation: (name: string, ipAddress: string) => void;
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
  const [isScanning, setIsScanning] = useState(false);
  const [discoveredDevices, setDiscoveredDevices] = useState<typeof mockDevices>([]);
  const [showDevices, setShowDevices] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name.trim() && formData.ipAddress.trim()) {
      onAddWorkstation(formData.name.trim(), formData.ipAddress.trim());
      setFormData({ name: "", ipAddress: "" });
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
      <DialogContent className="glass-card border-border max-w-md mx-auto fixed">
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