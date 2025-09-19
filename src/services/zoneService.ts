import { apiClient } from './api';

export interface Zone {
  id: number;
  name: string;
  workstation_id: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  status: 'work' | 'idle' | 'other';
  people_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateZoneRequest {
  name: string;
  workstation_id: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface UpdateZoneRequest {
  name?: string;
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
}

// Mock data for development when backend is not available
const mockZones: Zone[] = [
  {
    id: 1,
    name: 'Assembly Area',
    workstation_id: 1,
    x1: 100,
    y1: 100,
    x2: 400,
    y2: 300,
    status: 'work',
    people_count: 2,
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:49:00Z'
  },
  {
    id: 2,
    name: 'Quality Check Zone',
    workstation_id: 2,
    x1: 50,
    y1: 50,
    x2: 350,
    y2: 250,
    status: 'idle',
    people_count: 0,
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:14:00Z'
  },
  {
    id: 3,
    name: 'Packaging Zone A',
    workstation_id: 3,
    x1: 75,
    y1: 75,
    x2: 375,
    y2: 275,
    status: 'other',
    people_count: 3,
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:48:00Z'
  }
];

class ZoneService {
  async getZones(workstationId?: number): Promise<Zone[]> {
    try {
      const url = workstationId
        ? `/zones/?workstation_id=${workstationId}`
        : '/zones/';
      const response = await apiClient.get<Zone[]>(url);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      return workstationId
        ? mockZones.filter(z => z.workstation_id === workstationId)
        : mockZones;
    }
  }

  async getZone(id: number): Promise<Zone> {
    try {
      const response = await apiClient.get<Zone>(`/zones/${id}`);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock data:', error);
      const zone = mockZones.find(z => z.id === id);
      if (!zone) {
        throw new Error(`Zone with id ${id} not found`);
      }
      return zone;
    }
  }

  async createZone(data: CreateZoneRequest): Promise<Zone> {
    try {
      const response = await apiClient.post<Zone>('/zones/', data);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const newZone: Zone = {
        id: Math.max(...mockZones.map(z => z.id)) + 1,
        name: data.name,
        workstation_id: data.workstation_id,
        x1: data.x1,
        y1: data.y1,
        x2: data.x2,
        y2: data.y2,
        status: 'idle',
        people_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      mockZones.push(newZone);
      return newZone;
    }
  }

  async updateZone(id: number, data: UpdateZoneRequest): Promise<Zone> {
    try {
      const response = await apiClient.put<Zone>(`/zones/${id}`, data);
      return response.data;
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const index = mockZones.findIndex(z => z.id === id);
      if (index === -1) {
        throw new Error(`Zone with id ${id} not found`);
      }

      mockZones[index] = {
        ...mockZones[index],
        ...data,
        updated_at: new Date().toISOString()
      };
      return mockZones[index];
    }
  }

  async deleteZone(id: number): Promise<void> {
    try {
      await apiClient.delete(`/zones/${id}`);
    } catch (error) {
      console.warn('Backend not available, using mock response:', error);
      const index = mockZones.findIndex(z => z.id === id);
      if (index === -1) {
        throw new Error(`Zone with id ${id} not found`);
      }
      mockZones.splice(index, 1);
    }
  }

  async getZonesByWorkstation(workstationId: number): Promise<Zone[]> {
    return this.getZones(workstationId);
  }
}

export const zoneService = new ZoneService();