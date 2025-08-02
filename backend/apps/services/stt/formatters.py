# FILE: apps/services/stt/formatters.py

import pysrt
from typing import List, Dict


def to_txt(segments: List[Dict]) -> str:
    """
    Converts a list of transcription segments to a plain text string.
    This logic is adapted from your provided script.
    """
    # Using a list comprehension and join is efficient for creating the string.
    # The strip() ensures there are no leading/trailing spaces on each segment.
    full_text = " ".join(
        seg['text'].strip() for seg in segments if 'text' in seg and seg['text'].strip()
    )
    return full_text


def to_srt(segments: List[Dict]) -> str:
    """
    Converts a list of transcription segments to an SRT formatted string.
    This logic uses the `pysrt` library, adapting the logic from your script.
    """
    subs = pysrt.SubRipFile()
    for i, seg in enumerate(segments, 1):
        # Create a SubRipItem for each segment
        item = pysrt.SubRipItem(
            index=i,
            # pysrt can create timestamps directly from seconds
            start=pysrt.SubRipTime.from_seconds(seg.get('start', 0.0)),
            end=pysrt.SubRipTime.from_seconds(seg.get('end', 0.0)),
            text=seg.get('text', '').strip()
        )
        subs.append(item)

    # The `pysrt` object's __str__ method correctly formats it as a string.
    return str(subs)