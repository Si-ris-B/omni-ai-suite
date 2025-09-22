# apps/features/youtube/utils.py
import logging
import os
import tempfile
import pysrt
import yt_dlp

logger = logging.getLogger(__name__)


def extract_video_info(url):
    """Extract video information using yt-dlp without downloading"""
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
                'channel_logo': info.get('uploader_avatar', ''),
            }
    except Exception as e:
        logger.error(f"Error extracting video info: {str(e)}")
        raise


def get_english_subtitles(url, output_format):
    """Check for and download existing English subtitles (human or automatic)."""
    try:
        logger.info(f"Looking for English subtitles for URL: {url}")
        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                # --- THIS IS THE KEY CHANGE ---
                'writeautomaticsub': True,  # Allow fallback to auto-generated subs
                # --- END OF CHANGE ---
                'subtitleslangs': ['en', 'en-US', 'en-GB'],  # Look for common English variants
                'outtmpl': os.path.join(temp_dir, '%(id)s'),  # Let yt-dlp handle extension
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Check if any subtitles were found in the metadata
                if not info.get('subtitles') and not info.get('automatic_captions'):
                    logger.info("No subtitle metadata found at all for this video.")
                    return None

                # Let yt-dlp attempt the download
                ydl.download([url])

                # Robustly find the downloaded subtitle file
                subtitle_file = None
                for f in os.listdir(temp_dir):
                    if f.endswith(('.srt', '.vtt')):
                        subtitle_file = f
                        break

                if not subtitle_file:
                    logger.warning("Download attempted, but no subtitle file (.srt, .vtt) was found in temp dir.")
                    return None

                subtitle_path = os.path.join(temp_dir, subtitle_file)
                logger.info(f"Successfully found subtitle file: {subtitle_path}")

                # Process based on requested format
                if outputFormat == 'srt':
                    subs = pysrt.open(subtitle_path)
                    return str(subs)  # pysrt will clean and format it
                else:
                    subs = pysrt.open(subtitle_path)
                    return " ".join([sub.text for sub in subs])
    except Exception as e:
        logger.warning(f"Could not retrieve existing subtitles: {str(e)}",
                       exc_info=False)  # exc_info=False to reduce log noise
        return None

def extract_audio(url):
    """Extract audio from YouTube video and return the path to the temp file"""
    temp_dir = tempfile.gettempdir()
    info = yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}).extract_info(url, download=False)
    temp_audio_base = os.path.join(temp_dir, f"youtube_audio_{info['id']}")

    ydl_opts = {
        # --- THIS IS THE LINE TO CHANGE ---
        'format': 'm4a/bestaudio/best', # More robust format selector
        # --- END OF CHANGE ---
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': [
            '-ar', '16000'
        ],
        'prefer_ffmpeg': True,
        'keepvideo': False,
        'outtmpl': temp_audio_base,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        final_path = temp_audio_base + '.mp3'
        if not os.path.exists(final_path):
            raise FileNotFoundError(f"yt-dlp did not produce the expected file: {final_path}")
        logger.info(f"Audio extracted to: {final_path}")
        return final_path
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}", exc_info=True)
        raise