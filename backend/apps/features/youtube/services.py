# apps/features/youtube/services.py
import logging
import os
from .utils import get_english_subtitles, extract_audio, extract_video_info
from apps.features.uploader.services import create_uploaded_file_from_path
from apps.services.stt.services import transcribe_file
from ..uploader.api.serializers import UploadedFileSerializer

logger = logging.getLogger(__name__)


class YouTubeProcessingError(Exception):
    pass


def get_youtube_transcript(url: str, output_format: str = 'srt'):
    """
    Gets a transcript for a YouTube video.
    1. Tries to download existing English subtitles.
    2. If not available, downloads audio, saves it as an UploadedFile,
       and transcribes it using the standard STT service.
    """
    # Step 1: Try to get existing subtitles
    logger.info(f"Attempting to fetch existing subtitles for {url}")
    subtitles = get_english_subtitles(url, output_format)
    if subtitles:
        logger.info("Found and returned existing English subtitles.")
        return subtitles

    # Step 2: If no subtitles, download audio and transcribe
    logger.info("No existing subtitles found. Transcribing audio from scratch.")
    temp_audio_path = None
    try:
        # Get video info to use title as filename
        video_info = extract_video_info(url)
        video_title = video_info.get('title', 'youtube_video')

        # Download audio to a temporary file
        temp_audio_path = extract_audio(url)

        # Create an UploadedFile instance from the downloaded audio
        uploaded_file = create_uploaded_file_from_path(
            file_path=temp_audio_path,
            original_filename=f"{video_title}.mp3",
            file_type='audio'
        )
        logger.info(f"Created UploadedFile (ID: {uploaded_file.id}) from YouTube audio.")

        # Transcribe the new UploadedFile
        transcript = transcribe_file(uploaded_file, output_format)

        return transcript

    except Exception as e:
        logger.error(f"Failed to transcribe YouTube URL {url}: {e}", exc_info=True)
        raise YouTubeProcessingError(f"Failed to process YouTube video. Reason: {str(e)}")
    finally:
        # Clean up the temporary audio file
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logger.info(f"Cleaned up temporary audio file: {temp_audio_path}")

def prepare_audio_from_youtube(url: str):
    """
    Downloads audio from a YouTube URL, creates a persistent UploadedFile,
    and returns its serialized data.
    """
    temp_audio_path = None
    try:
        video_info = extract_video_info(url)
        video_title = video_info.get('title', 'youtube_video')
        temp_audio_path = extract_audio(url)

        # Create a persistent UploadedFile instance
        uploaded_file = create_uploaded_file_from_path(
            file_path=temp_audio_path,
            original_filename=f"{video_title}.mp3",
            file_type='audio'
        )
        logger.info(f"Created UploadedFile (ID: {uploaded_file.id}) from YouTube audio.")

        # Serialize and return the new file's data
        serializer = UploadedFileSerializer(uploaded_file)
        return serializer.data

    finally:
        # Clean up the temporary local audio file
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logger.info(f"Cleaned up temporary audio file: {temp_audio_path}")