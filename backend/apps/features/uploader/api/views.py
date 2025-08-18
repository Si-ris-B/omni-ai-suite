# backend/apps/features/uploader/api/views.py

import logging
from rest_framework import generics, parsers, permissions, status, viewsets
from rest_framework.response import Response
from .serializers import UploadedFileSerializer
from datetime import datetime, timezone
from ..models import UploadedFile

logger = logging.getLogger(__name__)


# This is the existing view for handling the multipart upload itself. It's correct.
class FileUploadView(generics.CreateAPIView):
    """
    A view to handle multipart/form-data file uploads.
    It expects 'file', 'file_type', and 'last_modified_timestamp' in the request.
    """
    serializer_class = UploadedFileSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        logger.info("="*50)
        logger.info(f"FileUploadView: Received a file upload request.")
        logger.info(f"Request FILES: {request.FILES}")
        logger.info(f"Request POST data: {request.POST}")
        logger.info("="*50)

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file was provided.'}, status=status.HTTP_400_BAD_REQUEST)

        file_type = request.data.get('file_type')
        timestamp_ms_str = request.data.get('last_modified_timestamp')

        if not file_type or not timestamp_ms_str:
            return Response({'error': 'Both "file_type" and "last_modified_timestamp" are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            timestamp_ms = int(timestamp_ms_str)
        except (ValueError, TypeError):
            return Response({'error': '"last_modified_timestamp" must be a valid integer (milliseconds).'}, status=status.HTTP_400_BAD_REQUEST)

        original_date = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

        data_for_serializer = {
            'file': file_obj, 'file_type': file_type, 'original_modified_at': original_date,
        }

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


# --- NEW: A ViewSet for managing the list of uploaded files ---
class UploadedFileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A ViewSet for listing and retrieving uploaded files.
    It also provides a custom 'destroy' action.
    """
    queryset = UploadedFile.objects.all().order_by('-created_at')
    serializer_class = UploadedFileSerializer
    permission_classes = [permissions.AllowAny] # Adjust permissions as needed

    # The default 'list' and 'retrieve' methods from ReadOnlyModelViewSet are sufficient.

    # We add a custom destroy method because ReadOnlyModelViewSet doesn't include it.
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Delete the physical file from storage (MEDIA_ROOT)
        instance.file.delete(save=False)
        # Delete the database record
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)