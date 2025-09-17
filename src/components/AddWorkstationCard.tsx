import { Plus } from "lucide-react";

interface AddWorkstationCardProps {
  onClick: () => void;
}

export function AddWorkstationCard({ onClick }: AddWorkstationCardProps) {
  return (
    <button
      onClick={onClick}
      className="glass-card p-6 smooth-transition hover:glow-primary border-dashed border-2 border-border hover:border-primary flex flex-col items-center justify-center min-h-[200px] group"
    >
      <Plus className="h-12 w-12 text-primary bg-transparent border-none outline-none mb-4 smooth-transition opacity-70 group-hover:opacity-100" />
      <span className="text-muted-foreground group-hover:text-primary font-medium smooth-transition">
        Add Workstation
      </span>
    </button>
  );
}