import { useState } from "react";
import { MarmotSidebar } from "./MarmotSidebar";
import { MarmotTopBar } from "./MarmotTopBar";
import { WorkstationsSection } from "./WorkstationsSection";
import { AlertsSection } from "./AlertsSection";
import { SettingsSection } from "./SettingsSection";

export function MarmotDashboard() {
  const [activeSection, setActiveSection] = useState("workstations");

  const renderActiveSection = () => {
    switch (activeSection) {
      case "workstations":
        return <WorkstationsSection />;
      case "alerts":
        return <AlertsSection />;
      case "settings":
        return <SettingsSection />;
      default:
        return <WorkstationsSection />;
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      <MarmotSidebar 
        activeSection={activeSection} 
        onSectionChange={setActiveSection} 
      />
      
      <div className="flex-1 flex flex-col">
        <MarmotTopBar activeSection={activeSection} />
        
        <main className="flex-1 overflow-auto">
          {renderActiveSection()}
        </main>
      </div>
    </div>
  );
}