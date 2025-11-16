# FILE: apps/services/stt/formatters.py (CORRECTED)

import pysrt
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def to_txt(segments: List[Dict]) -> str:
    """
    Converts a list of transcription segments to a plain text string.
    """
    full_text = " ".join(
        seg['text'].strip() for seg in segments if 'text' in seg and seg['text'].strip()
    )
    return full_text


def to_srt(segments: List[Dict]) -> str:
    """
    Converts a list of transcription segments to an SRT formatted string.

    Expected segment format:
    {
        'start': 15.516,  # float seconds
        'end': 17.559,    # float seconds
        'text': 'It won\'t be long now.'
    }

    Returns properly formatted SRT string like:
    1
    00:00:15,516 --> 00:00:17,559
    It won't be long now.

    2
    00:00:17,643 --> 00:00:20,020
    At least she's comfortable.
    """
    # Build SRT manually - this is more reliable than pysrt's str() method
    srt_lines = []

    for i, seg in enumerate(segments, 1):
        # Get text, start, and end from segment
        text = seg.get('text', '').strip()
        start_seconds = seg.get('start', 0.0)
        end_seconds = seg.get('end', 0.0)

        if not text:
            continue

        # Format timestamps
        start_time = _format_srt_timestamp(start_seconds)
        end_time = _format_srt_timestamp(end_seconds)

        # Add subtitle entry (index, timestamp, text, blank line)
        srt_lines.append(str(i))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between entries

    result = "\n".join(srt_lines)

    # Debug logging
    logger.debug(f"Generated SRT with {len(segments)} segments")
    logger.debug(f"SRT type: {type(result)}")
    logger.debug(f"SRT preview (first 200 chars): {result[:200] if result else 'EMPTY'}")

    return result


def to_srt_with_pysrt(segments: List[Dict]) -> str:
    """
    Alternative implementation using pysrt library.
    Use the manual version above if this doesn't work properly.
    """
    subs = pysrt.SubRipFile()

    for i, seg in enumerate(segments, 1):
        text = seg.get('text', '').strip()
        start_seconds = seg.get('start', 0.0)
        end_seconds = seg.get('end', 0.0)

        if not text:
            continue

        # Create SubRipItem
        item = pysrt.SubRipItem(index=i, text=text)
        item.start.seconds = start_seconds
        item.end.seconds = end_seconds

        subs.append(item)

    # CRITICAL FIX: Use the write-to-string method
    # Don't use str(subs) - it gives object representation
    # Instead, format each item manually
    srt_content = []
    for item in subs:
        srt_content.append(str(item.index))
        srt_content.append(f"{item.start} --> {item.end}")
        srt_content.append(item.text)
        srt_content.append("")

    return "\n".join(srt_content)


def _format_srt_timestamp(seconds: float) -> str:
    """
    Helper to format seconds as HH:MM:SS,mmm for SRT format.
    Note: SRT uses comma for milliseconds, not period.

    Examples:
        15.516 -> 00:00:15,516
        336.04 -> 00:05:36,040
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def to_vtt(segments: List[Dict]) -> str:
    """
    Converts a list of transcription segments to WebVTT format.
    """
    vtt_lines = ["WEBVTT", ""]

    for seg in segments:
        start = seg.get('start', 0.0)
        end = seg.get('end', 0.0)
        text = seg.get('text', '').strip()

        if not text:
            continue

        # Format timestamps as HH:MM:SS.mmm (note: VTT uses period, not comma)
        start_time = _format_vtt_timestamp(start)
        end_time = _format_vtt_timestamp(end)

        vtt_lines.append(f"{start_time} --> {end_time}")
        vtt_lines.append(text)
        vtt_lines.append("")

    return "\n".join(vtt_lines)


def _format_vtt_timestamp(seconds: float) -> str:
    """
    Helper to format seconds as HH:MM:SS.mmm for WebVTT.
    VTT uses period for milliseconds (unlike SRT which uses comma).
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"