import json

from django.http import JsonResponse
from rest_framework import views, permissions, status, parsers
from rest_framework.response import Response
from .client import STTServiceClient
# Import new serializer and services
from .serializers import TranscriptionRequestSerializer, ProcessRequestSerializer
from apps.features.uploader.models import UploadedFile
from apps.features.uploader.services import create_uploaded_file_from_request
from apps.features.youtube.services import get_youtube_transcript, YouTubeProcessingError
from apps.services.stt.services import transcribe_file
from apps.services.models import ExternalService
import logging

logger = logging.getLogger(__name__)


class STTServiceBaseView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def handle_exception(self, exc):
        if isinstance(exc, (ConnectionError, RuntimeError, ExternalService.DoesNotExist)):
            logger.error(f"{self.__class__.__name__} configuration or connection error: {exc}")
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        logger.error(f"An unexpected error occurred in {self.__class__.__name__}: {exc}", exc_info=True)
        return Response({"error": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TranscribeView(views.APIView):
    """
    Handles a transcription request by processing the entire stream on the server
    and returning the final formatted text (SRT or TXT).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = TranscriptionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        file_id = validated_data.get('file_id')
        output_format = request.data.get('format', 'srt')

        try:
            uploaded_file = UploadedFile.objects.get(pk=file_id)
            if uploaded_file.file_type not in ['audio', 'video']:
                return JsonResponse({"error": "Only audio and video files can be transcribed."}, status=status.HTTP_400_BAD_REQUEST)

            # This now uses the refactored service logic
            formatted_content = transcribe_file(uploaded_file, output_format)

            return JsonResponse({"content": formatted_content}, status=status.HTTP_200_OK)

        except UploadedFile.DoesNotExist:
            return JsonResponse({"error": f"File with ID {file_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Transcription failed for file {file_id}: {e}", exc_info=True)
            return JsonResponse({"error": f"Transcription failed. Check server logs for details. Reason: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class STTStatusView(STTServiceBaseView):
    """
    Gets the status of the default STT service.
    For admin/debug purposes, a specific service can be checked via its URL.
    """

    def get(self, request, service_name=None, *args, **kwargs):
        try:
            if service_name:
                service_config = ExternalService.objects.get(machine_name=service_name, service_type='stt')
                client = STTServiceClient()  # This needs to be adapted if client accepts config
            else:
                client = STTServiceClient()

            status_data = client.get_status()
            return Response(status_data, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class STTModelControlView(STTServiceBaseView):
    """
    ADMIN/DEBUG: Sends a command (load/unload) to a specific STT service.
    """

    def post(self, request, service_name, action, *args, **kwargs):
        try:
            service_config = ExternalService.objects.get(machine_name=service_name, service_type='stt')
            # This needs to be adapted if client accepts config
            client = STTServiceClient()

            if action == 'load':
                result = client.load_model()
            elif action == 'unload':
                result = client.unload_model()
            else:
                return Response({"error": "Invalid action. Must be 'load' or 'unload'."},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class STTProcessView(views.APIView):
    """
    A unified endpoint to process transcription requests from either
    a file upload or a YouTube URL.
    """
    permission_classes = [permissions.AllowAny]
    # We need multipart parser for file uploads.
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, *args, **kwargs):
        # The serializer validates 'source_type', 'output_format', and 'url' if needed.
        serializer = ProcessRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        source_type = validated_data['source_type']
        output_format = validated_data['output_format']

        try:
            if source_type == 'upload':
                # Handle file upload and transcription
                logger.info("Processing transcription request from file upload.")
                # 1. Create the UploadedFile instance from the request
                uploaded_file = create_uploaded_file_from_request(request)
                logger.info(f"File uploaded successfully. ID: {uploaded_file.id}")

                # 2. Transcribe the file
                content = transcribe_file(uploaded_file, output_format)

                # 3. Return the result
                return JsonResponse({"content": content, "file_id": uploaded_file.id}, status=status.HTTP_200_OK)

            elif source_type == 'youtube':
                # Handle YouTube URL transcription
                url = validated_data['url']
                logger.info(f"Processing transcription request from YouTube URL: {url}")

                # 1. The service handles everything: download, upload, transcribe
                content = get_youtube_transcript(url, output_format)

                # 2. Return the result
                return JsonResponse({"content": content}, status=status.HTTP_200_OK)

        except (ValueError, FileNotFoundError) as e:
            # Catches user errors from uploader service (missing data, etc.)
            logger.warning(f"Bad request during transcription processing: {e}")
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except YouTubeProcessingError as e:
            # Catches specific errors from the YouTube service
            logger.error(f"YouTube processing failed: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # Generic catch-all for other errors (e.g., from STT service)
            logger.error(f"An unexpected error occurred in STTProcessView: {e}", exc_info=True)
            return JsonResponse({"error": "An internal server error occurred. Please check the logs."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)