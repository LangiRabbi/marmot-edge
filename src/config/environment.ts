// Environment configuration
// Move sensitive data to environment variables in production

export const config = {
  // API Configuration
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:3000',
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  
  // Workstation Default IPs - Should be fetched from backend in production
  workstations: {
    defaultIPs: [
      { id: '1', ip: import.meta.env.VITE_WS1_IP || '192.168.1.101', name: 'Assembly Line 1' },
      { id: '2', ip: import.meta.env.VITE_WS2_IP || '192.168.1.102', name: 'QC Station 3' },
      { id: '3', ip: import.meta.env.VITE_WS3_IP || '192.168.1.103', name: 'Packaging Unit A' },
      { id: '4', ip: import.meta.env.VITE_WS4_IP || '192.168.1.104', name: 'Welding Station 2' },
      { id: '5', ip: import.meta.env.VITE_WS5_IP || '192.168.1.105', name: 'Paint Booth 1' },
      { id: '6', ip: import.meta.env.VITE_WS6_IP || '192.168.1.106', name: 'Final Inspection' },
    ],
  },
  
  // Feature Flags
  features: {
    enableConfiguration: import.meta.env.VITE_ENABLE_CONFIG === 'true' || false,
    enableAdvancedMetrics: import.meta.env.VITE_ENABLE_ADVANCED_METRICS === 'true' || false,
    enableExport: import.meta.env.VITE_ENABLE_EXPORT === 'true' || false,
  },
  
  // Application Settings
  app: {
    refreshInterval: parseInt(import.meta.env.VITE_REFRESH_INTERVAL || '5000'),
    maxAlerts: parseInt(import.meta.env.VITE_MAX_ALERTS || '100'),
    environment: import.meta.env.MODE || 'development',
  },
  
  // Logging
  logging: {
    enabled: import.meta.env.VITE_LOGGING_ENABLED === 'true' || false,
    level: import.meta.env.VITE_LOG_LEVEL || 'info',
  },
};

// Type-safe configuration getter
export const getConfig = () => config;