import { Factory, Bell, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

interface MarmotSidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

export function MarmotSidebar({ activeSection, onSectionChange }: MarmotSidebarProps) {
  const navItems = [
    { id: 'workstations', label: 'Workstations', icon: Factory },
    { id: 'alerts', label: 'Alerts', icon: Bell },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="w-64 h-screen bg-sidebar border-r border-sidebar-border flex flex-col">
      {/* Logo */}
      <div className="p-6">
        <div className="flex items-center space-x-3">
          <span className="text-2xl leading-none bg-transparent border-none outline-none">🐿️</span>
          <span className="text-xl font-bold text-primary bg-transparent border-none outline-none">Marmot</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            const Icon = item.icon;
            
            return (
              <button
                key={item.id}
                onClick={() => onSectionChange(item.id)}
                className={cn(
                  "w-full flex items-center space-x-3 px-4 py-3 rounded-lg smooth-transition text-left",
                  isActive
                    ? "nav-active"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}