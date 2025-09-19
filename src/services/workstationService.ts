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

let mockWorkstations = getMockWorkstations();

class WorkstationService {
  async getWorkstations(): Promise<Workstation[]> {
    try {
      const response = await apiClient.get<Workstation[]>('/workstations/');
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      // Refresh from localStorage in case another tab modified it
      mockWorkstations = getMockWorkstations();
      return mockWorkstations;
    }
  }

  async getWorkstation(id: number): Promise<Workstation> {
    try {
      const response = await apiClient.get<Workstation>(`/workstations/${id}`);
      return response.data;
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