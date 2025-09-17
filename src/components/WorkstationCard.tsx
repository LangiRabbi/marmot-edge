import { Users, Clock, MoreVertical, Edit, Settings, BarChart3, Trash2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { WorkstationDetailsModal } from "./WorkstationDetailsModal";
import { EditWorkstationModal } from "./EditWorkstationModal";
import { useToast } from "@/hooks/use-toast";

interface WorkstationCardProps {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'alert';
  peopleCount: number;
  efficiency: number;
  lastActivity: string;
  onEdit?: (id: string, newName: string) => void;
  onRemove?: (id: string) => void;
}

export function WorkstationCard({ 
  id,
  name, 
  status, 
  peopleCount, 
  efficiency, 
  lastActivity,
  onEdit,
  onRemove
}: WorkstationCardProps) {
  const { toast } = useToast();
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const getStatusColor = () => {
    switch (status) {
      case 'online': return 'text-success';
      case 'offline': return 'text-muted-foreground';
      case 'alert': return 'text-warning';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'online': return 'Online';
      case 'offline': return 'Offline';
      case 'alert': return 'Alert';
    }
  };

  const getProgressColor = () => {
    if (efficiency >= 80) return 'text-success';
    if (efficiency >= 60) return 'text-warning';
    return 'text-destructive';
  };

  const handleViewDetails = () => {
    setShowDetailsModal(true);
  };

  const handleEditName = () => {
    setShowEditModal(true);
  };

  const handleConfigure = () => {
    toast({
      title: "Configuration",
      description: "Configuration coming soon",
    });
  };

  const handleRemove = () => {
    setShowDeleteDialog(true);
  };

  const confirmRemove = () => {
    onRemove?.(id);
    setShowDeleteDialog(false);
    toast({
      title: "Workstation Removed",
      description: `${name} has been removed successfully.`,
    });
  };

  const handleSaveEdit = (newName: string) => {
    onEdit?.(id, newName);
    toast({
      title: "Workstation Updated",
      description: `Workstation renamed to ${newName}.`,
    });
  };

  return (
    <div className="glass-card p-6 smooth-transition cursor-pointer hover:scale-[1.02]" onClick={handleViewDetails}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">{name}</h3>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 hover:bg-muted" 
              onClick={(e) => e.stopPropagation()}
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-popover border-border">
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewDetails(); }} className="hover:bg-muted cursor-pointer">
              <BarChart3 className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleEditName(); }} className="hover:bg-muted cursor-pointer">
              <Edit className="mr-2 h-4 w-4" />
              Edit Name
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleConfigure(); }} className="hover:bg-muted cursor-pointer">
              <Settings className="mr-2 h-4 w-4" />
              Configure
            </DropdownMenuItem>
            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleRemove(); }} className="hover:bg-muted text-destructive cursor-pointer">
              <Trash2 className="mr-2 h-4 w-4" />
              Remove
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Status */}
      <div className="flex items-center space-x-2 mb-3">
        <div className={`status-dot ${status}`} />
        <span className={`text-sm font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>

      {/* People Count */}
      <div className="flex items-center space-x-2 mb-3">
        <Users className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-foreground">{peopleCount} people</span>
      </div>

      {/* Efficiency */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-muted-foreground">Efficiency</span>
          <span className={`text-sm font-medium ${getProgressColor()}`}>
            {efficiency}%
          </span>
        </div>
        <Progress 
          value={efficiency} 
          className={`progress-glow ${getProgressColor()}`}
        />
      </div>

      {/* Last Activity */}
      <div className="flex items-center space-x-2 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" />
        <span>{lastActivity}</span>
      </div>

      {/* Modals */}
      <WorkstationDetailsModal
        open={showDetailsModal}
        onOpenChange={setShowDetailsModal}
        workstation={{ name, status, peopleCount, efficiency, lastActivity }}
      />

      <EditWorkstationModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        currentName={name}
        onSave={handleSaveEdit}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="bg-background border-border">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-foreground">Remove Workstation</AlertDialogTitle>
            <AlertDialogDescription className="text-muted-foreground">
              Are you sure you want to remove "{name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="border-border hover:bg-muted text-foreground">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmRemove}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}