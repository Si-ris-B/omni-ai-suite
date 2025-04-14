import axios from 'axios';

// Base URL for our backend API, proxied by Nginx in production/docker
const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // Add other default headers if needed
  },
});

// Function to get service status
export const getServiceStatus = (serviceName) => {
  return apiClient.get(`/control/status/${serviceName}/`);
};

// Function to start a service
export const startService = (serviceName) => {
  // POST request, even if no body is needed for this specific action
  return apiClient.post(`/control/start/${serviceName}/`);
};

// Function to stop a service
export const stopService = (serviceName) => {
  return apiClient.post(`/control/stop/${serviceName}/`);
};

// Add other API functions here later (e.g., for STT uploads)
// export const uploadAudioForSTT = (formData) => {
//   return apiClient.post('/stt/upload/', formData, {
//     headers: { 'Content-Type': 'multipart/form-data' },
//   });
// };

export default apiClient; // Export configured instance if needed elsewhere
