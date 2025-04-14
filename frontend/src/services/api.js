import axios from 'axios';

// Base URL for backend API (proxied by Nginx)
const API_BASE_URL = '/api';

// Create configured Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // Add a reasonable timeout (e.g., 10 seconds)
  headers: {
    'Content-Type': 'application/json',
    // Add Accept header if needed by DRF content negotiation
    Accept: 'application/json',
  },
});

// --- Control API Functions ---
export const getServiceStatus = (serviceName) => {
  console.log(`API Call: GET /control/status/${serviceName}/`);
  return apiClient.get(`/control/status/${serviceName}/`);
};

export const startService = (serviceName) => {
  console.log(`API Call: POST /control/start/${serviceName}/`);
  return apiClient.post(`/control/start/${serviceName}/`);
};

export const stopService = (serviceName) => {
  console.log(`API Call: POST /control/stop/${serviceName}/`);
  return apiClient.post(`/control/stop/${serviceName}/`);
};

// --- STT API Functions (Placeholder for later) ---
export const uploadAudioForSTT = (formData) => {
  console.log('API Call: POST /stt/upload/ with FormData');
  return apiClient.post('/stt/upload/', formData, {
    // Assuming Django URL is /api/stt/upload/
    headers: {
      // Let Axios set Content-Type for FormData automatically
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000, // Longer timeout for potential file uploads
  });
};

// Export the configured instance if needed elsewhere
export default apiClient;
