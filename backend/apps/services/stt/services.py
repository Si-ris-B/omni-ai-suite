# apps/services/stt/services.py
import json
import logging
from .client import STTServiceClient
from .formatters import to_srt, to_txt
from apps.features.uploader.models import UploadedFile

logger = logging.getLogger(__name__)


def transcribe_file(uploaded_file: UploadedFile, output_format: str = 'srt'):
    """
    Takes an UploadedFile object, transcribes it, and returns the formatted result.
    Encapsulates the logic from the original TranscribeView.
    """
    if uploaded_file.file_type not in ['audio', 'video']:
        raise ValueError("Only audio and video files can be transcribed.")

    client = STTServiceClient()
    stream_generator = client.transcribe_file(uploaded_file)

    segments = []
    final_message_received = False

    for line_str in stream_generator:
        try:
            data = json.loads(line_str)
            if data.get('type') == 'segment':
                segments.append(data.get('data', {}))
            elif data.get('type') == 'final':
                final_message_received = True
                logger.info(f"Transcription complete for file {uploaded_file.id}. Message: {data.get('message')}")
            elif data.get('type') == 'error':
                error_detail = data.get('message', 'Unknown transcription error from service')
                logger.error(f"Downstream transcription error for file {uploaded_file.id}: {error_detail}")
                raise RuntimeError(error_detail)
        except (json.JSONDecodeError, KeyError):
            logger.warning(f"Could not parse line from transcription stream: '{line_str}'")
            continue

    if not final_message_received and not segments:
        raise RuntimeError("Transcription stream ended prematurely with no segments or completion message.")

    if output_format == 'txt':
        return to_txt(segments)
    else:  # Default to SRT
        return to_srt(segments)