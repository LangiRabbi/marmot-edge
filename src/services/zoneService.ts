import { apiClient } from './api';

export interface Zone {
  id: number;
  name: string;
  workstation_id: number;
  coordinates: {
    points?: number[][];
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
  is_active: boolean;
  color: string;
  person_count: number;
  status: 'work' | 'idle' | 'other';
  created_at: string;
  updated_at?: string;
}

// Frontend-specific zone interface for canvas overlay
export interface CanvasZone {
  id: number;
  name: string;
  x: number; // percentage 0-100
  y: number; // percentage 0-100
  width: number; // percentage 0-100
  height: number; // percentage 0-100
  color: string;
  status: 'Work' | 'Idle' | 'Other';
}

export interface CreateZoneRequest {
  name: string;
  workstation_id: number;
  coordinates: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  is_active?: boolean;
  color: string;
}

export interface UpdateZoneRequest {
  name?: string;
  coordinates?: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
  is_active?: boolean;
  color?: string;
}

// Mock data for development when backend is not available
const mockZones: Zone[] = [
  {
    id: 1,
    name: 'Assembly Area',
    workstation_id: 1,
    coordinates: { x: 20, y: 20, width: 30, height: 25 },
    is_active: true,
    color: '#3B82F6',
    status: 'work',
    person_count: 2,
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:49:00Z'
  },
  {
    id: 2,
    name: 'Quality Control',
    workstation_id: 1,
    coordinates: { x: 55, y: 20, width: 25, height: 20 },
    is_active: true,
    color: '#10B981',
    status: 'idle',
    person_count: 0,
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:14:00Z'
  },
  {
    id: 3,
    name: 'Packaging Station',
    workstation_id: 1,
    coordinates: { x: 20, y: 50, width: 28, height: 30 },
    is_active: true,
    color: '#F59E0B',
    status: 'other',
    person_count: 3,
    created_at: '2025-09-17T10:00:00Z',
    updated_at: '2025-09-18T20:48:00Z'
  },
  {
    id: 4,
    name: 'Final Inspection',
    workstation_id: 2,
    coordinates: { x: 30, y: 30, width: 25, height: 25 },
    is_active: true,
    color: '#8B5CF6',
    status: 'work',
    person_count: 1,
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
        coordinates: data.coordinates,
        is_active: data.is_active ?? true,
        color: data.color,
        status: 'idle',
        person_count: 0,
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
        coordinates: data.coordinates ? { ...mockZones[index].coordinates, ...data.coordinates } : mockZones[index].coordinates,
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

  // Utility methods for converting between backend and frontend formats
  convertToCanvasZone(zone: Zone): CanvasZone {
    const coords = zone.coordinates;
    return {
      id: zone.id,
      name: zone.name,
      x: coords.x || 0,
      y: coords.y || 0,
      width: coords.width || 10,
      height: coords.height || 10,
      color: zone.color,
      status: this.mapStatusToCanvas(zone.status)
    };
  }

  convertFromCanvasZone(canvasZone: CanvasZone, workstationId: number): CreateZoneRequest {
    return {
      name: canvasZone.name,
      workstation_id: workstationId,
      coordinates: {
        x: canvasZone.x,
        y: canvasZone.y,
        width: canvasZone.width,
        height: canvasZone.height
      },
      color: canvasZone.color,
      is_active: true
    };
  }

  convertFromCanvasZoneUpdate(canvasZone: CanvasZone): UpdateZoneRequest {
    return {
      name: canvasZone.name,
      coordinates: {
        x: canvasZone.x,
        y: canvasZone.y,
        width: canvasZone.width,
        height: canvasZone.height
      },
      color: canvasZone.color
    };
  }

  private mapStatusToCanvas(status: 'work' | 'idle' | 'other'): 'Work' | 'Idle' | 'Other' {
    switch (status) {
      case 'work': return 'Work';
      case 'idle': return 'Idle';
      case 'other': return 'Other';
      default: return 'Idle';
    }
  }

  private mapStatusFromCanvas(status: 'Work' | 'Idle' | 'Other'): 'work' | 'idle' | 'other' {
    switch (status) {
      case 'Work': return 'work';
      case 'Idle': return 'idle';
      case 'Other': return 'other';
      default: return 'idle';
    }
  }
}

export const zoneService = new ZoneService();