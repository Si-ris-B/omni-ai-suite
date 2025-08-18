import apiClient from './apiClient.jsx';

const YOUTUBE_API_PATH = '/api/v1/youtube';

const youtubeService = {
  /**
   * Fetches YouTube video information
   */
  getVideoInfo: (url) => {
    return apiClient.post(`${YOUTUBE_API_PATH}/info/`, { url });
  },

  /**
   * Transcribes YouTube video audio
   */
  transcribeVideo: (url, format = 'text') => {
    return apiClient.post(`${YOUTUBE_API_PATH}/transcribe/`, {
      url: url,
      format: format  // 'text' or 'srt'
    }, {
      // Use a longer timeout for transcription, as it's a blocking call
      timeout: 3600000 // 1 hour
    });
  },

  /**
   * Translates transcript to specified language
   */
  translateTranscript: (transcript, targetLanguage) => {
    // This would be implemented when you add translation functionality
    return Promise.reject({
      response: {
        data: {
          error: "Translation feature not implemented."
        }
      }
    });
  },
};

export default youtubeService;