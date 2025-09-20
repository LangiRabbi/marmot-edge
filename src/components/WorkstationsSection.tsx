import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { WorkstationCard } from "./WorkstationCard";
import { AddWorkstationCard } from "./AddWorkstationCard";
import { AddWorkstationModal } from "./AddWorkstationModal";
import { useToast } from "@/hooks/use-toast";
import { workstationService } from "@/services/workstationService";
import type { Workstation, VideoSourceConfig } from "@/services/workstationService";

export function WorkstationsSection() {
  const [showAddModal, setShowAddModal] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch workstations using React Query
  const { data: workstations = [], isLoading, error } = useQuery({
    queryKey: ['workstations'],
    queryFn: () => workstationService.getWorkstations(),
  });

  // Create workstation mutation
  const createMutation = useMutation({
    mutationFn: (data: { name: string; location: string; status?: 'online' | 'offline' | 'alert'; video_config?: VideoSourceConfig }) =>
      workstationService.createWorkstation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workstations'] });
      toast({
        title: "Workstation Added",
        description: "Workstation has been successfully added to the system.",
      });
    },
    onError: (error) => {
      setShowAddModal(true);  // Reopen modal only on error
      toast({
        title: "Error",
        description: "Failed to add workstation. Please try again.",
        variant: "destructive",
      });
      console.error('Failed to create workstation:', error);
    }
  });

  // Update workstation mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number; name?: string; location?: string; status?: 'online' | 'offline' | 'alert' }) =>
      workstationService.updateWorkstation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workstations'] });
      toast({
        title: "Workstation Updated",
        description: "Workstation has been successfully updated.",
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: "Failed to update workstation. Please try again.",
        variant: "destructive",
      });
      console.error('Failed to update workstation:', error);
    }
  });

  // Delete workstation mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => workstationService.deleteWorkstation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workstations'] });
      toast({
        title: "Workstation Removed",
        description: "Workstation has been successfully removed from the system.",
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: "Failed to remove workstation. Please try again.",
        variant: "destructive",
      });
      console.error('Failed to delete workstation:', error);
    }
  });

  const handleAddWorkstation = (name: string, ipAddress: string, videoConfig?: VideoSourceConfig) => {
    setShowAddModal(false);  // Close modal IMMEDIATELY
    createMutation.mutate({
      name,
      location: ipAddress || 'N/A', // Use ipAddress as location for now
      status: 'online',
      video_config: videoConfig
    });
  };

  const handleEditWorkstation = (id: string, newName: string) => {
    updateMutation.mutate({
      id: parseInt(id),
      name: newName
    });
  };

  const handleRemoveWorkstation = (id: string) => {
    deleteMutation.mutate(parseInt(id));
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <AddWorkstationCard onClick={() => setShowAddModal(true)} />
          {/* Loading skeleton cards */}
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4 mb-4"></div>
              <div className="h-3 bg-muted rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-muted rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Error loading workstations. Using offline mode.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <AddWorkstationCard onClick={() => setShowAddModal(true)} />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <AddWorkstationCard onClick={() => setShowAddModal(true)} />

        {workstations.map((workstation) => (
          <WorkstationCard
            key={workstation.id}
            id={workstation.id.toString()}
            name={workstation.name}
            status={workstation.status}
            peopleCount={workstation.people_count}
            efficiency={workstation.efficiency}
            lastActivity={workstation.last_activity}
            videoConfig={workstation.video_config}
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