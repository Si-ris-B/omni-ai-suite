// src/services/apiClient.js
import axios from 'axios';

// 1. CREATE THE AXIOS INSTANCE
const apiClient = axios.create({
  // Use the environment variable for the base URL.
  // This makes your code portable between development and production.
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 2. OPTIONAL: USE A RESPONSE INTERCEPTOR FOR GLOBAL ERROR HANDLING
// Even without auth, this is useful for logging errors or showing a generic error message.
apiClient.interceptors.response.use(
  (response) => {
    // If the request was successful, just return the response
    return response;
  },
  (error) => {
    // This block will run for any non-2xx response (e.g., 404 Not Found, 500 Server Error)

    // Log the error for debugging purposes
    console.error("API Error:", error.response || error.message);

    // You could also trigger a global notification to the user, e.g.,
    // showToast("An unexpected error occurred. Please try again later.");

    // It's important to still reject the promise so the component that
    // made the call knows the request failed.
    return Promise.reject(error);
  }
);

export default apiClient;