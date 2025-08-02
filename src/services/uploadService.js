import apiClient from './apiClient.jsx';

const UPLOADER_API_PATH = '/api/v1/uploader';
const STT_API_PATH = '/api/v1/stt';

const uploadService = {
    /**
     * Uploads a file with its metadata.
     */
    uploadFile: (formData) => {
        return apiClient.post(`${UPLOADER_API_PATH}/upload/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    /**
     * Fetches a list of all uploaded files from the library.
     */
    getFiles: () => {
        return apiClient.get(`${UPLOADER_API_PATH}/files/`);
    },

    /**
     * Deletes a file from the library by its ID.
     */
    deleteFile: (id) => {
        return apiClient.delete(`${UPLOADER_API_PATH}/files/${id}/`);
    },

    /**
     * Requests transcription for a file and waits for the complete result.
     * This is now a simple, non-streaming POST request.
     */
    transcribeFile: (fileId, format) => {
        return apiClient.post(`${STT_API_PATH}/transcribe/`, {
            file_id: fileId,
            format: format,
        }, {
            // Use a longer timeout for transcription, as it's a blocking call
            timeout: 3600000 // 1 hour
        });
    },

    // Mocked functions remain
    translateFile: (fileId, format) => Promise.reject({ response: { data: { error: "Translation feature not implemented." } } }),
    addYoutubeLink: (url) => Promise.reject({ response: { data: { error: "Adding YouTube links is not implemented." } } }),
};

export default uploadService;