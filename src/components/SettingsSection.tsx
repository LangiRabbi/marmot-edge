import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Edit, Trash2, Plus, Users, Settings, BarChart3 } from "lucide-react";

const supervisors = [
  { id: 1, name: "Jan Kowalski", email: "jan.k@company.com" },
  { id: 2, name: "Anna Nowak", email: "anna.n@company.com" }
];

const managers = [
  { id: 1, name: "Piotr Wiśniewski", email: "piotr.w@company.com" }
];

const directors = [
  { id: 1, name: "Maria Zielińska", email: "maria.z@company.com" }
];

const upcomingReports = [
  { id: 1, title: "Next Shift Summary", time: "Today 14:15", countdown: "in 2h 23min" },
  { id: 2, title: "Next Weekly Report", time: "Monday 08:00", countdown: "in 3 days" },
  { id: 3, title: "Next Monthly Report", time: "Feb 1st 08:00", countdown: "in 12 days" }
];

export function SettingsSection() {
  const [activeTab, setActiveTab] = useState("team");
  const [systemSettings, setSystemSettings] = useState({
    deviceOfflineAlert: 5,
    noOperatorAlert: 10,
    extendedBreakAlert: 30,
    companyName: "ABC Manufacturing",
    facilityLocation: "Factory Floor A, Building 2"
  });

  const renderTeamSection = (title: string, icon: React.ReactNode, users: any[], description: string) => (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center space-x-2 mb-4">
        {icon}
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        <span className="text-sm text-muted-foreground">({description})</span>
      </div>
      
      <div className="space-y-3">
        {users.map((user) => (
          <div key={user.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border border-border">
            <div>
              <div className="font-medium text-foreground">{user.name}</div>
              <div className="text-sm text-muted-foreground">{user.email}</div>
            </div>
            <div className="flex space-x-2">
              <Button size="sm" variant="outline" className="border-border hover:bg-muted">
                <Edit className="h-3 w-3 mr-1" />
                Edit
              </Button>
              <Button size="sm" variant="outline" className="border-border hover:bg-muted text-destructive">
                <Trash2 className="h-3 w-3 mr-1" />
                Remove
              </Button>
            </div>
          </div>
        ))}
        
        <Button 
          variant="outline" 
          className="w-full border-dashed border-2 border-border hover:border-primary hover:bg-muted"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add {title.split(' ')[0]}
        </Button>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-muted/50">
          <TabsTrigger value="team" className="flex items-center space-x-2">
            <Users className="h-4 w-4" />
            <span>Team & Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center space-x-2">
            <Settings className="h-4 w-4" />
            <span>System Settings</span>
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>Reports Schedule</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="team" className="mt-6">
          {renderTeamSection(
            "Shift Supervisors",
            <span className="text-lg">👷</span>,
            supervisors,
            "Real-time alerts"
          )}
          
          {renderTeamSection(
            "Production Managers",
            <span className="text-lg">👔</span>,
            managers,
            "Daily reports"
          )}
          
          {renderTeamSection(
            "Directors",
            <span className="text-lg">🏢</span>,
            directors,
            "Weekly/Monthly reports"
          )}
        </TabsContent>

        <TabsContent value="system" className="mt-6">
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Alert Thresholds</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="space-y-2">
                <Label htmlFor="deviceOffline" className="text-foreground">
                  Device Offline Alert (minutes)
                </Label>
                <Input
                  id="deviceOffline"
                  type="number"
                  value={systemSettings.deviceOfflineAlert}
                  onChange={(e) => setSystemSettings({
                    ...systemSettings,
                    deviceOfflineAlert: parseInt(e.target.value)
                  })}
                  className="bg-input border-border text-foreground"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="noOperator" className="text-foreground">
                  No Operator Alert (minutes)
                </Label>
                <Input
                  id="noOperator"
                  type="number"
                  value={systemSettings.noOperatorAlert}
                  onChange={(e) => setSystemSettings({
                    ...systemSettings,
                    noOperatorAlert: parseInt(e.target.value)
                  })}
                  className="bg-input border-border text-foreground"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="extendedBreak" className="text-foreground">
                  Extended Break Alert (minutes)
                </Label>
                <Input
                  id="extendedBreak"
                  type="number"
                  value={systemSettings.extendedBreakAlert}
                  onChange={(e) => setSystemSettings({
                    ...systemSettings,
                    extendedBreakAlert: parseInt(e.target.value)
                  })}
                  className="bg-input border-border text-foreground"
                />
              </div>
            </div>

            <h3 className="text-lg font-semibold text-foreground mb-6">Company Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="companyName" className="text-foreground">
                  Company Name
                </Label>
                <Input
                  id="companyName"
                  value={systemSettings.companyName}
                  onChange={(e) => setSystemSettings({
                    ...systemSettings,
                    companyName: e.target.value
                  })}
                  className="bg-input border-border text-foreground"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="facilityLocation" className="text-foreground">
                  Facility Location
                </Label>
                <Input
                  id="facilityLocation"
                  value={systemSettings.facilityLocation}
                  onChange={(e) => setSystemSettings({
                    ...systemSettings,
                    facilityLocation: e.target.value
                  })}
                  className="bg-input border-border text-foreground"
                />
              </div>
            </div>

            <div className="flex justify-end mt-8">
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                Save Settings
              </Button>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="reports" className="mt-6">
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">Upcoming Reports</h3>
            
            <div className="space-y-4">
              {upcomingReports.map((report) => (
                <div key={report.id} className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border border-border">
                  <div>
                    <div className="font-medium text-foreground">{report.title}</div>
                    <div className="text-sm text-muted-foreground">{report.time}</div>
                  </div>
                  <div className="text-sm text-primary font-medium">
                    {report.countdown}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}