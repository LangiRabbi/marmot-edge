import { useState } from "react";
import { WorkstationCard } from "./WorkstationCard";
import { AddWorkstationCard } from "./AddWorkstationCard";
import { AddWorkstationModal } from "./AddWorkstationModal";
import { useToast } from "@/hooks/use-toast";

const initialWorkstations = [
  {
    id: "1",
    name: "Assembly Line 1",
    status: "online" as const,
    peopleCount: 2,
    efficiency: 86,
    lastActivity: "2 min ago",
    ipAddress: "192.168.1.101"
  },
  {
    id: "2",
    name: "QC Station 3",
    status: "alert" as const,
    peopleCount: 0,
    efficiency: 45,
    lastActivity: "35 min ago",
    ipAddress: "192.168.1.102"
  },
  {
    id: "3",
    name: "Packaging Unit A",
    status: "online" as const,
    peopleCount: 3,
    efficiency: 94,
    lastActivity: "1 min ago",
    ipAddress: "192.168.1.103"
  },
  {
    id: "4",
    name: "Welding Station 2",
    status: "offline" as const,
    peopleCount: 0,
    efficiency: 0,
    lastActivity: "47 min ago",
    ipAddress: "192.168.1.104"
  },
  {
    id: "5",
    name: "Paint Booth 1",
    status: "online" as const,
    peopleCount: 2,
    efficiency: 90,
    lastActivity: "3 min ago",
    ipAddress: "192.168.1.105"
  },
  {
    id: "6",
    name: "Final Inspection",
    status: "alert" as const,
    peopleCount: 2,
    efficiency: 68,
    lastActivity: "18 min ago",
    ipAddress: "192.168.1.106"
  }
];

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
  const [workstations, setWorkstations] = useState<Workstation[]>(initialWorkstations);
  const [showAddModal, setShowAddModal] = useState(false);
  const { toast } = useToast();

  const handleAddWorkstation = (name: string, ipAddress: string) => {
    const newWorkstation: Workstation = {
      id: Date.now().toString(),
      name,
      status: "online",
      peopleCount: 0,
      efficiency: Math.floor(Math.random() * 40) + 60, // Random efficiency between 60-99%
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