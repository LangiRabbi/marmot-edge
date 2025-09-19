import { apiClient } from './api';

export interface VideoSourceConfig {
  type: 'rtsp' | 'usb' | 'file';
  url?: string;
  usbDeviceId?: string;
  fileName?: string;
  filePath?: string; // For storing file uploads
}

export interface Workstation {
  id: number;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'alert';
  people_count: number;
  efficiency: number;
  last_activity: string;
  created_at: string;
  updated_at: string;
  video_config?: VideoSourceConfig;
}

export interface CreateWorkstationRequest {
  name: string;
  location: string;
  status?: 'online' | 'offline' | 'alert';
  video_config?: VideoSourceConfig;
}

export interface UpdateWorkstationRequest {
  name?: string;
  location?: string;
  status?: 'online' | 'offline' | 'alert';
  video_config?: VideoSourceConfig;
}

// Mock data for development when backend is not available
const initialMockWorkstations: Workstation[] = [
  {
    id: 1,
    name: 'Assembly Line 1',
    location: 'Production Floor A',
    status: 'online',
    people_count: 2,
    efficiency: 86,
    last_activity: '2 min ago',
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:49:00Z'
  },
  {
    id: 2,
    name: 'QC Station 3',
    location: 'Quality Control',
    status: 'alert',
    people_count: 0,
    efficiency: 45,
    last_activity: '35 min ago',
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:14:00Z'
  },
  {
    id: 3,
    name: 'Packaging Unit A',
    location: 'Packaging Department',
    status: 'online',
    people_count: 3,
    efficiency: 94,
    last_activity: '1 min ago',
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:48:00Z'
  }
];

// Get mock workstations from localStorage or use initial data
const getMockWorkstations = (): Workstation[] => {
  if (typeof window === 'undefined') return initialMockWorkstations;

  const stored = localStorage.getItem('mockWorkstations');
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.warn('Failed to parse stored workstations, using initial data');
    }
  }
  return [...initialMockWorkstations];
};

// Save mock workstations to localStorage
const saveMockWorkstations = (workstations: Workstation[]) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('mockWorkstations', JSON.stringify(workstations));
  }
};

interface BackendWorkstation {
  id: number;
  name: string;
  description?: string;
  current_status: string;
  video_source_config?: Record<string, unknown>;
  [key: string]: unknown;
}

interface BackendZone {
  id: number;
  person_count?: number;
  status?: string;
  [key: string]: unknown;
}

let mockWorkstations = getMockWorkstations();

class WorkstationService {
  async getWorkstations(): Promise<Workstation[]> {
    try {
      const response = await apiClient.get<BackendWorkstation[]>('/workstations/');

      // Transform backend data to frontend interface
      const transformedData = response.data.map((backendWorkstation) => ({
        id: backendWorkstation.id,
        name: backendWorkstation.name,
        location: backendWorkstation.description || 'No description',
        status: this.mapBackendStatusToFrontend(backendWorkstation.current_status),
        people_count: this.calculatePeopleCount(backendWorkstation.zones || []),
        efficiency: this.calculateEfficiency(backendWorkstation.zones || []),
        last_activity: backendWorkstation.last_detection_at || 'No recent activity',
        created_at: backendWorkstation.created_at,
        updated_at: backendWorkstation.updated_at,
        video_config: backendWorkstation.video_config
      }));

      return transformedData;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      // Refresh from localStorage in case another tab modified it
      mockWorkstations = getMockWorkstations();
      return mockWorkstations;
    }
  }

  private mapBackendStatusToFrontend(backendStatus: string): 'online' | 'offline' | 'alert' {
    switch (backendStatus) {
      case 'work':
      case 'active':
        return 'online';
      case 'idle':
        return 'alert';
      case 'offline':
      case 'inactive':
        return 'offline';
      default:
        return 'offline';
    }
  }

  private calculatePeopleCount(zones: BackendZone[]): number {
    return zones.reduce((total, zone) => total + (zone.person_count || 0), 0);
  }

  private calculateEfficiency(zones: BackendZone[]): number {
    const workingZones = zones.filter(zone => zone.status === 'work');
    const totalZones = zones.length;
    if (totalZones === 0) return 0;
    return Math.round((workingZones.length / totalZones) * 100);
  }

  async getWorkstation(id: number): Promise<Workstation> {
    try {
      const response = await apiClient.get<BackendWorkstation>(`/workstations/${id}`);

      // Transform backend data to frontend interface
      const backendWorkstation = response.data;
      return {
        id: backendWorkstation.id,
        name: backendWorkstation.name,
        location: backendWorkstation.description || 'No description',
        status: this.mapBackendStatusToFrontend(backendWorkstation.current_status),
        people_count: this.calculatePeopleCount(backendWorkstation.zones || []),
        efficiency: this.calculateEfficiency(backendWorkstation.zones || []),
        last_activity: backendWorkstation.last_detection_at || 'No recent activity',
        created_at: backendWorkstation.created_at,
        updated_at: backendWorkstation.updated_at,
        video_config: backendWorkstation.video_config
      };
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      const workstation = mockWorkstations.find(w => w.id === id);
      if (!workstation) {
        throw new Error(`Workstation with id ${id} not found`);
      }
      return workstation;
    }
  }

  async createWorkstation(data: CreateWorkstationRequest): Promise<Workstation> {
    try {
      const response = await apiClient.post<Workstation>('/workstations/', data);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const newWorkstation: Workstation = {
        id: Math.max(...mockWorkstations.map(w => w.id)) + 1,
        name: data.name,
        location: data.location,
        status: data.status || 'offline',
        people_count: 0,
        efficiency: 0,
        last_activity: 'just now',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        video_config: data.video_config
      };
      mockWorkstations.push(newWorkstation);
      saveMockWorkstations(mockWorkstations);
      return newWorkstation;
    }
  }

  async updateWorkstation(id: number, data: UpdateWorkstationRequest): Promise<Workstation> {
    try {
      const response = await apiClient.put<Workstation>(`/workstations/${id}`, data);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const index = mockWorkstations.findIndex(w => w.id === id);
      if (index === -1) {
        throw new Error(`Workstation with id ${id} not found`);
      }

      mockWorkstations[index] = {
        ...mockWorkstations[index],
        ...data,
        updated_at: new Date().toISOString()
      };
      saveMockWorkstations(mockWorkstations);
      return mockWorkstations[index];
    }
  }

  async deleteWorkstation(id: number): Promise<void> {
    try {
      await apiClient.delete(`/workstations/${id}`);
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const index = mockWorkstations.findIndex(w => w.id === id);
      if (index === -1) {
        throw new Error(`Workstation with id ${id} not found`);
      }
      mockWorkstations.splice(index, 1);
      saveMockWorkstations(mockWorkstations);
    }
  }
}

export const workstationService = new WorkstationService();