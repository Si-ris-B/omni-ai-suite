// File: frontend/src/services/api.js
import axios from 'axios';

// Base URL for backend API (proxied by Nginx)
const API_BASE_URL = '/api';

// Create configured Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // Increased timeout slightly for actions
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// --- Control API Functions ---
export const getServiceStatus = (serviceName) => {
  console.log(`[API] GET /control/status/${serviceName}/`);
  return apiClient.get(`/control/status/${serviceName}/`);
};

export const startService = (serviceName) => {
  console.log(`[API] POST /control/start/${serviceName}/`);
  // POST even without body for control actions
  return apiClient.post(`/control/start/${serviceName}/`);
};

export const stopService = (serviceName) => {
  console.log(`[API] POST /control/stop/${serviceName}/`);
  return apiClient.post(`/control/stop/${serviceName}/`);
};

// --- STT API Functions (Placeholder for later) ---
// export const uploadAudioForSTT = (formData) => {
//   console.log('[API] POST /stt/upload/ with FormData');
//   return apiClient.post('/stt/upload/', formData, { // Ensure Django URL is correct
//     headers: {
//       'Content-Type': 'multipart/form-data',
//     },
//     timeout: 60000, // Longer timeout for uploads
//   });
// };

// Export the configured instance if needed elsewhere
export default apiClient;