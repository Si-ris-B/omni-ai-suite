# backend/apps/features/uploader/api/views.py

import logging
from rest_framework import generics, parsers, permissions, status
from rest_framework.response import Response
from .serializers import UploadedFileSerializer
from datetime import datetime, timezone  # <--- 1. IMPORT timezone from datetime

logger = logging.getLogger(__name__)


class FileUploadView(generics.CreateAPIView):
    """
    A view to handle multipart/form-data file uploads.
    It expects 'file', 'file_type', and 'last_modified_timestamp' in the request.
    """
    serializer_class = UploadedFileSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        # ... (all your logging can stay) ...
        logger.info("="*50)
        logger.info(f"FileUploadView: Received a file upload request.")
        logger.info(f"Request FILES: {request.FILES}")
        logger.info(f"Request POST data: {request.POST}")
        logger.info("="*50)

        # ... (no changes to the file/metadata extraction) ...
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file was provided.'}, status=status.HTTP_400_BAD_REQUEST)

        file_type = request.data.get('file_type')
        timestamp_ms_str = request.data.get('last_modified_timestamp')

        # 2. Validate required metadata
        if not file_type or not timestamp_ms_str:
            return Response(
                {'error': 'Both "file_type" and "last_modified_timestamp" are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            timestamp_ms = int(timestamp_ms_str)
        except (ValueError, TypeError):
            return Response(
                {'error': '"last_modified_timestamp" must be a valid integer (milliseconds).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Prepare data for the serializer
        # Convert the millisecond timestamp to a timezone-aware datetime object
        original_date = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

        # This dictionary will be passed to the serializer.
        data_for_serializer = {
            'file': file_obj,
            'file_type': file_type,
            'original_modified_at': original_date,
        }

        # 4. Use the standard serializer validation and creation process
        serializer = self.get_serializer(data=data_for_serializer)
        try:
            serializer.is_valid(raise_exception=True)
            logger.info("FileUploadView: Serializer data is valid.")
        except Exception as e:
            logger.error(f"FileUploadView: Serializer validation failed! Errors: {serializer.errors}", exc_info=True)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        logger.info(f"FileUploadView: Successfully created file object with ID: {serializer.instance.id}")

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)