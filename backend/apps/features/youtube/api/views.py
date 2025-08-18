import json
import logging
import os
import tempfile
import pysrt
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import yt_dlp

logger = logging.getLogger(__name__)


class YoutubeVideoInfoView(views.APIView):
    """
    API endpoint to get YouTube video information using yt-dlp
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            url = request.data.get('url')

            if not url:
                return Response(
                    {'error': 'URL is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            video_info = self.extract_video_info(url)

            # Format duration as MM:SS or HH:MM:SS
            minutes, seconds = divmod(video_info['duration'], 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_formatted = f"{minutes:02d}:{seconds:02d}"

            # Format upload date
            upload_date = video_info['upload_date']
            if len(upload_date) == 8:  # YYYYMMDD
                formatted_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
            else:
                formatted_date = upload_date

            # Format view count
            views = video_info['view_count']
            if views >= 1000000:
                views_formatted = f"{views / 1000000:.1f}M views"
            elif views >= 1000:
                views_formatted = f"{views / 1000:.1f}K views"
            else:
                views_formatted = f"{views} views"

            response_data = {
                'title': video_info['title'],
                'description': video_info['description'],
                'duration': duration_formatted,
                'views': views_formatted,
                'date': formatted_date,
                'thumbnail': video_info['thumbnail'],
                'channel': video_info['channel'],
                'channelLogo': video_info['channel_logo'] or '',
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return Response(
                {'error': f'Failed to process video: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def extract_video_info(self, url):
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
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'duration': info.get('duration', 0),  # in seconds
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', ''),  # YYYYMMDD format
                    'thumbnail': info.get('thumbnail', ''),
                    'channel': info.get('uploader', ''),
                    'channel_logo': info.get('uploader_avatar', ''),
                }
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            raise


class YoutubeTranscribeView(views.APIView):
    """
    API endpoint to transcribe YouTube video using yt-dlp and Whisper
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            url = request.data.get('url')
            output_format = request.data.get('format', 'text')  # 'text' or 'srt'

            logger.info(f"Transcribe request received - URL: {url}, Format: {output_format}")

            if not url:
                logger.warning("No URL provided in transcribe request")
                return Response(
                    {'error': 'URL is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # First, try to get existing English subtitles
            logger.info("Checking for existing English subtitles...")
            transcript_data = self.get_english_subtitles(url, output_format)

            # If no subtitles found, extract audio and transcribe
            if transcript_data is None:
                logger.info("No subtitles found, falling back to audio transcription")
                transcript_data = self.transcribe_from_audio(url, output_format)
            else:
                logger.info("Successfully retrieved existing subtitles")

            return Response({
                'transcript': transcript_data,
                'message': 'Processing completed successfully'
            })

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to process video: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_english_subtitles(self, url, output_format):
        """Check for and download existing English subtitles"""
        try:
            logger.info(f"Looking for English subtitles for URL: {url}")

            # Create a temporary directory for subtitle files
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Using temporary directory: {temp_dir}")

                ydl_opts = {
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': False,  # Only get human-made subtitles
                    'subtitleslangs': ['en'],
                    'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # First, just get info to check what subtitles are available
                    logger.info("Extracting info to check available subtitles")
                    info = ydl.extract_info(url, download=False)

                    # Log all available subtitles
                    all_subtitles = info.get('subtitles', {})
                    logger.info(f"All available subtitles: {list(all_subtitles.keys())}")

                    # Check if English subtitles are available
                    if 'en' not in all_subtitles:
                        logger.info("No English subtitles found in video")
                        # Also check for 'en-US' or other English variants
                        english_keys = [key for key in all_subtitles.keys() if key.startswith('en')]
                        if english_keys:
                            logger.info(f"Found English variant subtitles: {english_keys}")
                            # Use the first English variant
                            ydl_opts['subtitleslangs'] = [english_keys[0]]
                        else:
                            return None

                    logger.info("Downloading English subtitles")
                    # Now download the subtitles
                    ydl.download([url])

                    # Find the downloaded subtitle file
                    subtitle_files = [f for f in os.listdir(temp_dir) if f.endswith('.en.srt') or '.en.' in f]
                    logger.info(f"Found subtitle files: {subtitle_files}")

                    if not subtitle_files:
                        logger.info("No subtitle files found after download")
                        return None

                    subtitle_path = os.path.join(temp_dir, subtitle_files[0])
                    logger.info(f"Using subtitle file: {subtitle_path}")

                    # Process based on requested format
                    if output_format == 'srt':
                        # Return SRT content directly
                        with open(subtitle_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            logger.info("Returning SRT content")
                            return content
                    else:
                        # For plain text, return just the text content without timestamps
                        subs = pysrt.open(subtitle_path)
                        text_segments = [sub.text for sub in subs]
                        plain_text = " ".join(text_segments)
                        logger.info(f"Returning plain text with {len(text_segments)} segments")
                        return plain_text

        except Exception as e:
            logger.warning(f"Could not retrieve existing subtitles: {str(e)}", exc_info=True)
            return None

    def transcribe_from_audio(self, url, output_format):
        """Extract audio and transcribe using Whisper"""
        try:
            logger.info("Extracting audio for transcription")
            # Extract audio using yt-dlp
            audio_path = self.extract_audio(url)

            # Process with Whisper (placeholder)
            transcript_segments = self.process_with_whisper(audio_path)

            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)

            # Return in requested format
            if output_format == 'srt':
                return self.convert_to_srt(transcript_segments)
            else:
                # For plain text, return just the text content without timestamps
                text_segments = [segment['text'] for segment in transcript_segments]
                plain_text = " ".join(text_segments)
                logger.info(f"Returning plain text with {len(text_segments)} segments")
                return plain_text

        except Exception as e:
            logger.error(f"Error transcribing from audio: {str(e)}", exc_info=True)
            raise

    def extract_audio(self, url):
        """Extract audio from YouTube video"""
        # Create a temporary file for audio
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, "temp_audio.mp3")

        logger.info(f"Extracting audio to: {audio_path}")

        ydl_opts = {
            'format': 'bestaudio/best',
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
            'outtmpl': audio_path.replace('.mp3', ''),  # yt-dlp will add extension
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Return the actual path with extension
            final_path = audio_path.replace('.mp3', '') + '.mp3'
            logger.info(f"Audio extracted to: {final_path}")
            return final_path
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}", exc_info=True)
            raise

    def process_with_whisper(self, audio_path):
        """Process audio with Whisper (placeholder implementation)"""
        logger.info("Processing audio with Whisper (placeholder)")
        # This is a placeholder - you would integrate with OpenAI Whisper API
        # or a local Whisper model here

        # For demonstration, returning sample data
        segments = [
            {"time": "00:00",
             "text": "Welcome to Tech Insights. Today we're discussing how AI is changing the future of work."},
            {"time": "00:15",
             "text": "Artificial intelligence is rapidly transforming industries across the globe at an unprecedented pace."},
            {"time": "00:30",
             "text": "From healthcare diagnostics to financial forecasting, AI is automating routine tasks and creating new opportunities for innovation."},
            {"time": "00:45", "text": "Let's examine three key areas where AI is making the biggest impact..."},
        ]
        logger.info(f"Generated {len(segments)} transcript segments")
        return segments

    def convert_to_srt(self, transcript_segments):
        """Convert transcript segments to SRT format"""
        logger.info("Converting transcript to SRT format")
        srt_lines = []
        for i, segment in enumerate(transcript_segments, 1):
            # For this example, we'll use the time as both start and end
            # In a real implementation, you'd have proper timestamps
            time_str = segment['time']
            srt_lines.append(str(i))
            srt_lines.append(f"{time_str.replace(':', ',')} --> {time_str.replace(':', ',')}")
            srt_lines.append(segment['text'])
            srt_lines.append("")  # Empty line between entries
        content = "\n".join(srt_lines)
        logger.info(f"Generated SRT content with {len(srt_lines)} lines")
        return content