# apps/features/youtube/utils.py
import logging
import os
import shutil
import tempfile
from typing import Optional, Dict, Any

import pysrt
import yt_dlp
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)


def extract_video_info(url: str) -> Dict[str, Any]:
    """
    Extract video information using yt-dlp without downloading.

    Args:
        url: The YouTube video URL.

    Returns:
        A dictionary containing key video metadata.

    Raises:
        DownloadError: If yt-dlp fails to extract information.
    """
    logger.info(f"Extracting video info for URL: {url}")
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"Successfully extracted info for video: {info.get('title', 'Unknown')}")
            return {
                'id': info.get('id', ''),
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', ''),
                'channel': info.get('uploader', ''),
                'channel_url': info.get('channel_url', ''),
            }
    except DownloadError as e:
        logger.error(f"yt-dlp could not process URL '{url}': {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while extracting video info: {e}")
        raise


def get_english_subtitles(url: str, output_format: str = 'txt') -> Optional[str]:
    """
    Check for and download existing English subtitles (human or automatic).

    Args:
        url: The YouTube video URL.
        output_format: The desired format ('srt' for the full file, 'txt' for plain text).

    Returns:
        The subtitles in the requested format as a string, or None if not found.
    """
    logger.info(f"Looking for English subtitles for URL: {url}")
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id')

                requested_subs = info.get('requested_subtitles')
                if not requested_subs or 'en' not in requested_subs:
                    logger.warning(f"No English subtitles found for video ID {video_id}.")
                    return None

                ydl.download([url])

                sub_info = requested_subs['en']
                subtitle_ext = sub_info.get('ext', 'srt')
                subtitle_path = os.path.join(temp_dir, f"{video_id}.en.{subtitle_ext}")

                if not os.path.exists(subtitle_path):
                    logger.warning(f"Subtitle file not found at: {subtitle_path}")
                    return None

                logger.info(f"Successfully downloaded subtitle file: {subtitle_path}")

                subs = pysrt.open(subtitle_path, encoding='utf-8')

                if output_format == 'srt':
                    return str(subs)

                return " ".join(sub.text.replace('\n', ' ') for sub in subs)

        except Exception as e:
            logger.warning(f"Could not retrieve subtitles for {url}: {e}")
            return None


def extract_audio(url: str, debug: bool = False) -> str:
    """
    Extracts audio from a YouTube video and returns the path to the temp mp3 file.

    This function is designed to be highly robust, with fallback mechanisms and
    debugging capabilities.

    Note: The caller is responsible for deleting the returned file after use.

    Args:
        url: The YouTube video URL.
        debug: If True, yt-dlp will print verbose output to the log/console
               for diagnosing issues with specific videos.

    Returns:
        The absolute path to the downloaded and converted .mp3 audio file.

    Raises:
        RuntimeError: If ffmpeg is not installed or not in the system's PATH.
        DownloadError: If yt-dlp fails to download or process the audio.
        FileNotFoundError: If the final audio file is not created.
    """
    if not shutil.which('ffmpeg'):
        msg = "ffmpeg is not installed or not in the system's PATH. It is required for audio extraction."
        logger.critical(msg)
        raise RuntimeError(msg)

    temp_dir = tempfile.mkdtemp(prefix="youtube_audio_")

    ydl_opts = {
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': ['-ar', '16000'],
        'prefer_ffmpeg': True,
        'keepvideo': False,
        'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
        'quiet': not debug,
        'no_warnings': not debug,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Starting audio extraction for {url}...")
            info = ydl.extract_info(url, download=True)
            video_id = info['id']

        final_path = os.path.join(temp_dir, f"{video_id}.mp3")

        if not os.path.exists(final_path):
            mp3_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
            if mp3_files:
                final_path = os.path.join(temp_dir, mp3_files[0])
                logger.warning(f"Expected file not found, using: {final_path}")
            else:
                raise FileNotFoundError(f"yt-dlp did not produce an mp3 file in {temp_dir}")

        logger.info(f"Audio successfully extracted to: {final_path}")
        return final_path

    except DownloadError as e:
        logger.error(f"yt-dlp failed to download or process the video: {e}", exc_info=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during audio extraction: {e}", exc_info=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise