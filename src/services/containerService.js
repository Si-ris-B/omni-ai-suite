import apiClient from './apiClient.jsx';

// Define the API path for the generic container management feature
const CONTAINER_API_PATH = '/api/v1/containers';

const containerService = {
  /**
   * Fetches the status of a specific container by its name.
   * @param {string} containerName - The exact name of the container.
   */
  getContainerStatus: (containerName) => {
    return apiClient.get(`${CONTAINER_API_PATH}/${containerName}/status/`);
  },

  /**
   * Sends a command to start or stop a container.
   * @param {string} containerName - The exact name of the container.
   * @param {'start' | 'stop'} action - The action to perform.
   */
  controlContainer: (containerName, action) => {
    // The backend endpoint is generic and expects the name in the payload
    return apiClient.post(`${CONTAINER_API_PATH}/control/`, {
      service_name: containerName, // The backend serializer field is 'service_name'
      action: action,
    });
  },

  /**
   * (Advanced) Creates an EventSource for real-time status updates.
   * This connects to the StreamingHttpResponse endpoint on the backend.
   * @param {string} containerName - The exact name of the container.
   * @returns {EventSource} A configured EventSource instance.
   */
  getStatusStream: (containerName) => {
    // Note: We construct the URL with the apiClient's baseURL, but EventSource is a browser API, not an axios call.
    const baseURL = apiClient.defaults.baseURL || '';
    const streamUrl = `${baseURL}${CONTAINER_API_PATH}/${containerName}/status-stream/`;

    console.log(`[SSE] Connecting to status stream: ${streamUrl}`);
    return new EventSource(streamUrl);
  },
};

export default containerService;