// src/services/uploadService.js
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/uploads';

const uploadService = {
    getFiles: () => {
        return axios.get(`${API_BASE_URL}/`);
    },

    uploadFiles: (formData) => {
        return axios.post(`${API_BASE_URL}/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    addYoutubeLink: (url) => {
        return axios.post(`${API_BASE_URL}/youtube/`, { url });
    },

    deleteFile: (id) => {
        return axios.delete(`${API_BASE_URL}/${id}/`);
    },
};

export default uploadService;
