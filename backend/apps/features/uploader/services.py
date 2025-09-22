# apps/features/uploader/services.py
import os
from datetime import datetime, timezone

from django.core.files import File as DjangoFile
from .models import UploadedFile
from .api.serializers import UploadedFileSerializer
from rest_framework.exceptions import ValidationError


def create_uploaded_file_from_request(request):
    """
    Handles file upload logic from a DRF request, creating an UploadedFile instance.
    This encapsulates the logic from the original FileUploadView.
    """
    file_obj = request.FILES.get('file')
    if not file_obj:
        raise ValueError('No file was provided in the request.')

    file_type = request.data.get('file_type')
    timestamp_ms_str = request.data.get('last_modified_timestamp')

    if not file_type or not timestamp_ms_str:
        raise ValueError('Both "file_type" and "last_modified_timestamp" are required.')

    try:
        timestamp_ms = int(timestamp_ms_str)
    except (ValueError, TypeError):
        raise ValueError('"last_modified_timestamp" must be a valid integer (milliseconds).')

    original_date = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

    data_for_serializer = {
        'file': file_obj,
        'file_type': file_type,
        'original_modified_at': original_date,
    }

    serializer = UploadedFileSerializer(data=data_for_serializer)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    return instance


def create_uploaded_file_from_path(file_path: str, original_filename: str, file_type: str = 'audio'):
    """
    Creates an UploadedFile instance from a local file path.
    Useful for processing files generated on the server (e.g., YouTube downloads).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at path: {file_path}")

    # Use the file's modification time for the timestamp
    modified_timestamp = os.path.getmtime(file_path)
    original_date = datetime.fromtimestamp(modified_timestamp, tz=timezone.utc)

    with open(file_path, 'rb') as f:
        django_file = DjangoFile(f, name=original_filename)

        data_for_serializer = {
            'file': django_file,
            'file_type': file_type,
            'original_modified_at': original_date,
        }

        serializer = UploadedFileSerializer(data=data_for_serializer)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return instance