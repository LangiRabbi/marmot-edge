import { useState, useMemo } from "react";
import { WorkstationCard } from "./WorkstationCard";
import { AddWorkstationCard } from "./AddWorkstationCard";
import { AddWorkstationModal } from "./AddWorkstationModal";
import { useToast } from "@/hooks/use-toast";
import { getConfig } from "@/config/environment";

// Get initial workstations from config
const getInitialWorkstations = () => {
  const config = getConfig();
  const statusOptions: Array<"online" | "offline" | "alert"> = ["online", "offline", "alert"];
  
  return config.workstations.defaultIPs.map((ws) => ({
    id: ws.id,
    name: ws.name,
    status: statusOptions[Math.floor(Math.random() * statusOptions.length)],
    peopleCount: Math.floor(Math.random() * 5),
    efficiency: ws.name.includes("Welding") ? 0 : Math.floor(Math.random() * 40) + 60,
    lastActivity: `${Math.floor(Math.random() * 60)} min ago`,
    ipAddress: ws.ip
  }));
};

interface Workstation {
  id: string;
  name: string;
  status: "online" | "offline" | "alert";
  peopleCount: number;
  efficiency: number;
  lastActivity: string;
  ipAddress: string;
}

export function WorkstationsSection() {
  // Use memoized initial state to avoid recreating on every render
  const initialWorkstations = useMemo(() => getInitialWorkstations(), []);
  const [workstations, setWorkstations] = useState<Workstation[]>(initialWorkstations);
  const [showAddModal, setShowAddModal] = useState(false);
  const { toast } = useToast();

  const handleAddWorkstation = (name: string, ipAddress: string) => {
    const newWorkstation: Workstation = {
      id: Date.now().toString(),
      name,
      status: "online",
      peopleCount: 0,
      efficiency: 75, // Fixed initial efficiency to avoid hydration mismatch
      lastActivity: "Just added",
      ipAddress
    };

    setWorkstations(prev => [...prev, newWorkstation]);
    setShowAddModal(false);
    
    toast({
      title: "Workstation Added",
      description: `${name} has been successfully added to the system.`,
    });
  };

  const handleEditWorkstation = (id: string, newName: string) => {
    setWorkstations(prev => 
      prev.map(workstation => 
        workstation.id === id 
          ? { ...workstation, name: newName }
          : workstation
      )
    );
  };

  const handleRemoveWorkstation = (id: string) => {
    setWorkstations(prev => prev.filter(workstation => workstation.id !== id));
  };

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <AddWorkstationCard onClick={() => setShowAddModal(true)} />
        
        {workstations.map((workstation) => (
          <WorkstationCard
            key={workstation.id}
            id={workstation.id}
            name={workstation.name}
            status={workstation.status}
            peopleCount={workstation.peopleCount}
            efficiency={workstation.efficiency}
            lastActivity={workstation.lastActivity}
            onEdit={handleEditWorkstation}
            onRemove={handleRemoveWorkstation}
          />
        ))}
      </div>

      <AddWorkstationModal 
        open={showAddModal} 
        onOpenChange={setShowAddModal}
        onAddWorkstation={handleAddWorkstation}
      />
    </div>
  );
}