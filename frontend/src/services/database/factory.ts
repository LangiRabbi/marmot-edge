// Database service factory for different deployment scenarios

import {
  DatabaseService,
  DatabaseConfig,
  DeploymentType,
} from './interface';
import { PostgreSQLDataService } from './postgresql-service';

export class DatabaseServiceFactory {
  private static instances: Map<string, DatabaseService> = new Map();

  static createDatabaseService(config: DatabaseConfig): DatabaseService {
    const key = `${config.deploymentType}-${config.baseUrl}`;

    if (this.instances.has(key)) {
      return this.instances.get(key)!;
    }

    let service: DatabaseService;

    switch (config.deploymentType) {
      case DeploymentType.OnPremise:
        service = new PostgreSQLDataService(config);
        break;

      case DeploymentType.Cloud:
        // Future: implement SupabaseDataService or similar
        service = new PostgreSQLDataService(config);
        break;

      case DeploymentType.Edge:
        // Future: implement EdgeDataService with local caching
        service = new PostgreSQLDataService(config);
        break;

      default:
        throw new Error(`Unsupported deployment type: ${config.deploymentType}`);
    }

    this.instances.set(key, service);
    return service;
  }

  static createFromEnvironment(): DatabaseService {
    const deploymentType = (import.meta.env.VITE_DEPLOYMENT_TYPE || 'onpremise') as DeploymentType;
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
    const apiVersion = import.meta.env.VITE_API_VERSION || 'v1';

    const config: DatabaseConfig = {
      deploymentType,
      baseUrl,
      apiVersion,
      timeout: 10000,
    };

    return this.createDatabaseService(config);
  }

  static clearInstances() {
    this.instances.clear();
  }
}

// Global instance for use throughout the application
let globalDatabaseService: DatabaseService | null = null;

export function getDatabaseService(): DatabaseService {
  if (!globalDatabaseService) {
    globalDatabaseService = DatabaseServiceFactory.createFromEnvironment();
  }
  return globalDatabaseService;
}

export function resetDatabaseService() {
  globalDatabaseService = null;
  DatabaseServiceFactory.clearInstances();
}

// Convenience functions
export async function getWorkstations() {
  const service = getDatabaseService();
  return service.getWorkstations();
}

export async function getWorkstation(id: number) {
  const service = getDatabaseService();
  return service.getWorkstation(id);
}

export async function createWorkstation(data: WorkstationCreate) {
  const service = getDatabaseService();
  return service.createWorkstation(data);
}

export async function updateWorkstation(id: number, data: WorkstationUpdate) {
  const service = getDatabaseService();
  return service.updateWorkstation(id, data);
}

export async function deleteWorkstation(id: number) {
  const service = getDatabaseService();
  return service.deleteWorkstation(id);
}

export async function getZones(workstationId?: number) {
  const service = getDatabaseService();
  return service.getZones(workstationId);
}

export async function createZone(data: ZoneCreate) {
  const service = getDatabaseService();
  return service.createZone(data);
}

export async function updateZone(id: number, data: ZoneUpdate) {
  const service = getDatabaseService();
  return service.updateZone(id, data);
}

export async function deleteZone(id: number) {
  const service = getDatabaseService();
  return service.deleteZone(id);
}