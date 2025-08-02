// FILE: src/services/apiClient.jsx

import axios from 'axios';
import { message } from 'antd';
import React from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.1.17:8000';

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
// This function runs for every successful API response (status 2xx)
apiClient.interceptors.response.use(
  (response) => {
    // --- THIS IS THE FIX for SUCCESS messages ---

    // Only show a toast for methods that modify data.
    // GET requests shouldn't pop up a success message every time.
    const method = response.config.method.toLowerCase();
    if (method === 'post' || method === 'put' || method === 'patch' || method === 'delete') {

      const responseDataString = JSON.stringify(response.data, null, 2);

      const content = (
        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          {responseDataString}
        </pre>
      );

      message.success({
        content: content,
        duration: 5, // Display for 5 seconds
        closable: true, // IMPORTANT: This adds the close button
        style: {
          marginTop: '20vh',
          maxWidth: '80vw',
        },
      });
    }
    // --- END OF FIX ---

    return response;
  },
  (error) => {
    // --- THIS IS THE FIX for ERROR messages ---
    const errorMessage = extractErrorMessage(error);

    message.error({
      content: errorMessage,
      duration: 10, // Errors can stay a bit longer
      closable: true, // IMPORTANT: This adds the close button
      style: {
        marginTop: '20vh',
      },
    });
    // --- END OF FIX ---

    return Promise.reject(error);
  }
);

export default apiClient;