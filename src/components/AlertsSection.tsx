import { Button } from "@/components/ui/button";
import { Clock, X, Search } from "lucide-react";

const alertStats = [
  { label: "Active Alerts", value: "3", color: "text-destructive" },
  { label: "Resolved Today", value: "12", color: "text-success" },
  { label: "Avg Response", value: "4.2min", color: "text-primary" }
];

const technicalAlerts = [
  {
    id: 1,
    title: "Welding Station 2 - Device Offline",
    time: "47min ago",
    actions: ["Dismiss", "Investigate"]
  },
  {
    id: 2,
    title: "Assembly Line 1 - High CPU Usage",
    time: "12min ago",
    actions: ["Dismiss", "View Logs"]
  }
];

const operationalAlerts = [
  {
    id: 3,
    title: "QC Station 3 - No Operator Detected",
    time: "35min ago",
    actions: ["Dismiss", "Notify Supervisor"]
  },
  {
    id: 4,
    title: "Final Inspection - Extended Break",
    time: "18min ago",
    actions: ["Dismiss", "Contact Team"]
  },
  {
    id: 5,
    title: "Paint Booth 1 - Normal Operation Resumed",
    time: "8min ago",
    actions: ["Mark as Read"],
    resolved: true
  }
];

export function AlertsSection() {
  return (
    <div className="p-6 space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {alertStats.map((stat, index) => (
          <div key={index} className="glass-card p-6">
            <div className="text-center">
              <div className={`text-3xl font-bold ${stat.color} mb-2`}>
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground">
                {stat.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Technical Alerts */}
      <div className="glass-card p-6">
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-lg">🔧</span>
          <h2 className="text-lg font-semibold text-foreground">Technical Alerts</h2>
        </div>
        
        <div className="space-y-3">
          {technicalAlerts.map((alert) => (
            <div key={alert.id} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
              <div className="flex items-center space-x-3">
                <div className="status-dot alert" />
                <div>
                  <div className="text-foreground font-medium">{alert.title}</div>
                  <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>{alert.time}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-2">
                {alert.actions.map((action, index) => (
                  <Button
                    key={index}
                    size="sm"
                    variant={index === 0 ? "outline" : "default"}
                    className={index === 0 ? "border-border hover:bg-muted" : "bg-primary text-primary-foreground hover:bg-primary/90"}
                  >
                    {action}
                  </Button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Operational Alerts */}
      <div className="glass-card p-6">
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-lg">👷</span>
          <h2 className="text-lg font-semibold text-foreground">Operational Alerts</h2>
        </div>
        
        <div className="space-y-3">
          {operationalAlerts.map((alert) => (
            <div key={alert.id} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
              <div className="flex items-center space-x-3">
                <div className={`status-dot ${alert.resolved ? 'online' : 'alert'}`} />
                <div>
                  <div className="text-foreground font-medium">{alert.title}</div>
                  <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>{alert.time}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-2">
                {alert.actions.map((action, index) => (
                  <Button
                    key={index}
                    size="sm"
                    variant={action === "Mark as Read" ? "default" : index === 0 ? "outline" : "default"}
                    className={
                      action === "Mark as Read" 
                        ? "bg-success text-success-foreground hover:bg-success/90" 
                        : index === 0 
                          ? "border-border hover:bg-muted" 
                          : "bg-primary text-primary-foreground hover:bg-primary/90"
                    }
                  >
                    {action}
                  </Button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}