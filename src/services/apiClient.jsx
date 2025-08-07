// FILE: src/services/apiClient.jsx

import axios from 'axios';
// --- CHANGED: Import toast and ToastContainer from react-toastify ---
import { toast, ToastContainer, Zoom } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css'; // Import the default CSS
import React from 'react'; // Ensure React is imported if needed elsewhere or for JSX

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const extractErrorMessage = (error) => {
  if (error.response?.data) {
    const data = error.response.data;
    // Handle Django REST Framework validation errors (e.g., {'field': ['message']})
    if (typeof data === 'object' && !Array.isArray(data)) {
        const firstKey = Object.keys(data)[0];
        if (Array.isArray(data[firstKey])) {
            return `${firstKey}: ${data[firstKey][0]}`;
        }
        // Handle simple error objects (e.g., {'error': 'message'})
        if (data.error) { return data.error; }
        if (data.detail) { return data.detail; }
    }
    // Fallback for other object types or simple strings
    return typeof data === 'string' ? data : JSON.stringify(data);
  }
  return error.message || 'An unexpected error occurred.';
};

// --- RESPONSE INTERCEPTOR ---
apiClient.interceptors.response.use(
  (response) => {
    // --- CHANGED: Using react-toastify for SUCCESS messages ---
    const method = response.config.method.toLowerCase();
    if (method === 'post' || method === 'put' || method === 'patch' || method === 'delete') {
      const responseDataString = JSON.stringify(response.data, null, 2);

      // Use toast.success for success messages
      // You can customize appearance using options
      toast.success(
        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          {responseDataString}
        </pre>,
        {
          position: "top-center",
          autoClose: 5000,
          hideProgressBar: false,
          closeOnClick: false,
          pauseOnHover: true,
          draggable: true,
          transition: Zoom,}
      );
    }
    // --- END OF CHANGE for SUCCESS ---

    return response;
  },
  (error) => {
    // --- CHANGED: Using react-toastify for ERROR messages ---
    const errorMessage = extractErrorMessage(error);

    // Use toast.error for error messages
    toast.error(errorMessage, {
      position: "top-center",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: false,
      pauseOnHover: true,
      draggable: true,
      transition: Zoom,
       // Style adjustments can be made via CSS classes or ToastContainer
    });
    // --- END OF CHANGE for ERROR ---

    return Promise.reject(error);
  }
);

// --- IMPORTANT: Export ToastContainer ---
// You need to render this component in your app's root (e.g., App.jsx)
export { ToastContainer };
export default apiClient;
