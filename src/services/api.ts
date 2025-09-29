import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.VITE_DEBUG) {
      console.log('API Request:', config.method?.toUpperCase(), config.url);
    }

    // Handle FormData - remove Content-Type to let browser set it with boundary
    if (config.data instanceof FormData) {
      console.log('📦 FormData Request:', config.url);
      // Delete Content-Type header to let browser set multipart/form-data with boundary
      delete config.headers['Content-Type'];
      console.log('  - Content-Type: (auto - browser will set with boundary)');
      console.log('  - Data type:', config.data.constructor.name);
      // Log FormData entries
      for (const [key, value] of config.data.entries()) {
        if (value instanceof Blob) {
          console.log(`  - ${key}: Blob (${value.size} bytes, type: ${value.type})`);
        } else {
          console.log(`  - ${key}: ${value}`);
        }
      }
    }

    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.VITE_DEBUG) {
      console.log('API Response:', response.status, response.config.url);
    }
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

export default apiClient;