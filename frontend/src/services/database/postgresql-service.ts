// PostgreSQL implementation of DatabaseService for on-premise deployment

import {
  DatabaseService,
  WorkstationData,
  WorkstationCreate,
  WorkstationUpdate,
  ZoneData,
  ZoneCreate,
  ZoneUpdate,
  DetectionData,
  DatabaseConfig,
} from './interface';

export class PostgreSQLDataService implements DatabaseService {
  private baseUrl: string;
  private apiVersion: string;
  private headers: Record<string, string>;
  private timeout: number;

  constructor(config: DatabaseConfig) {
    this.baseUrl = config.baseUrl;
    this.apiVersion = config.apiVersion || 'v1';
    this.headers = config.headers || {};
    this.timeout = config.timeout || 10000;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}/api/${this.apiVersion}${endpoint}`;

    const requestOptions: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...this.headers,
        ...options.headers,
      },
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...requestOptions,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  // Workstation operations
  async getWorkstations(skip = 0, limit = 100): Promise<WorkstationData[]> {
    return this.request<WorkstationData[]>(
      `/workstations?skip=${skip}&limit=${limit}`
    );
  }

  async getWorkstation(id: number): Promise<WorkstationData | null> {
    try {
      return await this.request<WorkstationData>(`/workstations/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async createWorkstation(data: WorkstationCreate): Promise<WorkstationData> {
    return this.request<WorkstationData>('/workstations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateWorkstation(
    id: number,
    data: WorkstationUpdate
  ): Promise<WorkstationData | null> {
    try {
      return await this.request<WorkstationData>(`/workstations/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async deleteWorkstation(id: number): Promise<boolean> {
    try {
      await this.request(`/workstations/${id}`, {
        method: 'DELETE',
      });
      return true;
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return false;
      }
      throw error;
    }
  }

  async getWorkstationStatus(id: number): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(`/workstations/${id}/status`);
  }

  // Zone operations
  async getZones(
    workstationId?: number,
    skip = 0,
    limit = 100
  ): Promise<ZoneData[]> {
    let endpoint = `/zones?skip=${skip}&limit=${limit}`;
    if (workstationId) {
      endpoint += `&workstation_id=${workstationId}`;
    }
    return this.request<ZoneData[]>(endpoint);
  }

  async getZone(id: number): Promise<ZoneData | null> {
    try {
      return await this.request<ZoneData>(`/zones/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async createZone(data: ZoneCreate): Promise<ZoneData> {
    return this.request<ZoneData>('/zones', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateZone(id: number, data: ZoneUpdate): Promise<ZoneData | null> {
    try {
      return await this.request<ZoneData>(`/zones/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  }

  async deleteZone(id: number): Promise<boolean> {
    try {
      await this.request(`/zones/${id}`, {
        method: 'DELETE',
      });
      return true;
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return false;
      }
      throw error;
    }
  }

  // Detection operations
  async getDetections(
    workstationId?: number,
    skip = 0,
    limit = 100
  ): Promise<DetectionData[]> {
    let endpoint = `/detections?skip=${skip}&limit=${limit}`;
    if (workstationId) {
      endpoint += `&workstation_id=${workstationId}`;
    }
    return this.request<DetectionData[]>(endpoint);
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.request('/health');
      return true;
    } catch {
      return false;
    }
  }
}