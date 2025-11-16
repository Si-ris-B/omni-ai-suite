# FILE: apps/services/stt/services.py (with debugging)

import json
import logging
from .client import STTServiceClient
from .formatters import to_srt, to_txt, to_vtt
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
                segment_data = data.get('data', {})
                segments.append(segment_data)
                logger.debug(f"Received segment: {segment_data}")

            elif data.get('type') == 'final':
                final_message_received = True
                logger.info(f"Transcription complete for file {uploaded_file.id}. "
                            f"Total segments: {len(segments)}. "
                            f"Message: {data.get('message')}")

            elif data.get('type') == 'error':
                error_detail = data.get('message', 'Unknown transcription error from service')
                logger.error(f"Downstream transcription error for file {uploaded_file.id}: {error_detail}")
                raise RuntimeError(error_detail)

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse line from transcription stream: '{line_str}'. Error: {e}")
            continue

    if not final_message_received and not segments:
        raise RuntimeError("Transcription stream ended prematurely with no segments or completion message.")

    logger.info(f"Processing {len(segments)} segments into format: {output_format}")

    # Format the segments
    if output_format == 'txt':
        result = to_txt(segments)
    elif output_format == 'vtt':
        result = to_vtt(segments)
    else:  # Default to SRT
        result = to_srt(segments)

    # Critical debugging - check what we're returning
    logger.info(f"Result type: {type(result)}")
    logger.info(f"Result is string: {isinstance(result, str)}")
    logger.info(f"Result length: {len(result) if result else 0}")
    logger.info(f"First 300 chars of result: {result[:300] if result else 'EMPTY'}")

    # Safety check - ensure we're returning a string
    if not isinstance(result, str):
        logger.error(f"WARNING: Result is {type(result)}, converting to string")
        result = str(result)

    return result