// src/services/uploadService.js

// Import the configured client, NOT the raw axios library
import apiClient from './apiClient';

// Define the correct, versioned API path for the uploader feature
const UPLOADER_API_PATH = '/api/v1/uploader';

const uploadService = {
    /**
     * Uploads a file.
     * @param {FormData} formData - The FormData object containing the file and metadata.
     * Required keys in FormData: 'file' (the file blob), 'file_type' ('audio', 'video', etc.).
     * Optional key: 'delete_after_days' (an integer like 7).
     */
    uploadFile: (formData) => {
        // Use the apiClient instance and the correct endpoint path
        // We still need to override the Content-Type header just for this request
        return apiClient.post(`${UPLOADER_API_PATH}/upload/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // --- OTHER POTENTIAL FUNCTIONS ---
    // The functions below are examples. They won't work until you build the
    // corresponding endpoints in your Django backend.

    // A function to get a list of all uploaded files would require a new 'ListAPIView' in Django.
    getFiles: () => {
        // The Django endpoint might be GET /api/v1/uploader/files/
        console.warn("getFiles feature not yet implemented on backend.");
        return Promise.reject("Not implemented");
        // return apiClient.get(`${UPLOADER_API_PATH}/files/`);
    },

    // Deleting a file would require a new 'DestroyAPIView' in Django.
    deleteFile: (id) => {
        // The Django endpoint might be DELETE /api/v1/uploader/files/{id}/
        console.warn("deleteFile feature not yet implemented on backend.");
        return Promise.reject("Not implemented");
        // return apiClient.delete(`${UPLOADER_API_PATH}/files/${id}/`);
    },
};

export default uploadService;