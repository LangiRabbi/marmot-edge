import { useState, useEffect } from "react";

interface MarmotTopBarProps {
  activeSection: string;
}

export function MarmotTopBar({ activeSection }: MarmotTopBarProps) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const getSectionTitle = () => {
    switch (activeSection) {
      case 'workstations':
        return { title: 'Production Workstations', subtitle: 'Real-time monitoring and control' };
      case 'alerts':
        return { title: 'System Alerts', subtitle: 'Technical and operational notifications' };
      case 'settings':
        return { title: 'System Configuration', subtitle: 'Team management and system settings' };
      default:
        return { title: 'Marmot Dashboard', subtitle: 'Industrial monitoring system' };
    }
  };

  const { title, subtitle } = getSectionTitle();

  return (
    <div className="h-16 bg-background border-b border-border flex items-center justify-between px-6">
      <div>
        <h1 className="text-xl font-semibold text-foreground">{title}</h1>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </div>

      <div className="flex items-center space-x-4">
        {/* Real-time Clock */}
        <div className="text-right">
          <div className="text-lg font-mono text-primary bg-transparent border-none outline-none">
            {currentTime.toLocaleTimeString('en-US', { hour12: false })}
          </div>
          <div className="text-xs text-muted-foreground">
            {currentTime.toLocaleDateString()}
          </div>
        </div>
      </div>
    </div>
  );
}