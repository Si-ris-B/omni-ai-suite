# FILE: apps/services/stt/views.py

import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import views, permissions, status, parsers, generics
from rest_framework.response import Response
from .client import STTServiceClient
from .serializers import (
    TranscriptionRequestSerializer, ProcessRequestSerializer,
    STTModelSettingsSerializer, STTTranscriptionSettingsSerializer
)
from .models import STTModelSettings, STTTranscriptionSettings
from apps.features.uploader.models import UploadedFile
from apps.features.uploader.services import create_uploaded_file_from_request
from apps.features.youtube.services import get_youtube_transcript, YouTubeProcessingError
from apps.services.stt.services import transcribe_file
from apps.services.models import ExternalService
import logging

logger = logging.getLogger(__name__)

# --- Base View for Exception Handling ---
class STTServiceBaseView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def handle_exception(self, exc):
        logger.error(f"An error occurred in {self.__class__.__name__}: {exc}", exc_info=True)
        if isinstance(exc, (ConnectionError, RuntimeError, ExternalService.DoesNotExist)):
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"error": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- CORRECTED AND SEPARATED API VIEWS ---

class STTStatusView(STTServiceBaseView):
    """
    Handles GET requests to check the live status of a specific STT microservice.
    """
    def get(self, request, service_name, *args, **kwargs):
        try:
            service = get_object_or_404(ExternalService, machine_name=service_name, service_type='stt')
            client = STTServiceClient(service=service)
            status_data = client.get_status()
            return Response(status_data, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)


class STTModelControlView(STTServiceBaseView):
    """
    Handles GET and POST requests for model management on a specific STT service.
    GET: Returns current model configuration and status
    POST: Load or unload a model
    """

    def get(self, request, service_name, action=None, *args, **kwargs):
        """
        GET request returns the current model settings and status.
        The 'action' parameter is ignored for GET requests.
        """
        try:
            service = get_object_or_404(ExternalService, machine_name=service_name, service_type='stt')
            client = STTServiceClient(service=service)

            # Get current status
            status_data = client.get_status()

            # Get configured model settings
            try:
                model_config = client.get_required_model_config()
                response_data = {
                    "service_name": service_name,
                    "current_status": status_data,
                    "configured_model": model_config
                }
            except Exception as e:
                response_data = {
                    "service_name": service_name,
                    "current_status": status_data,
                    "error": f"Could not retrieve model configuration: {str(e)}"
                }

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)

    def post(self, request, service_name, action, *args, **kwargs):
        """
        POST request to load or unload a model.
        """
        try:
            service = get_object_or_404(ExternalService, machine_name=service_name, service_type='stt')
            client = STTServiceClient(service=service)

            if action == 'load':
                result = client.load_model()
            elif action == 'unload':
                result = client.unload_model()
            else:
                return Response(
                    {"error": "Invalid action. Must be 'load' or 'unload'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)

# --- Settings Management Views ---

class STTModelSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = STTModelSettingsSerializer
    queryset = STTModelSettings.objects.all()
    lookup_field = 'service__machine_name'
    lookup_url_kwarg = 'service_name'

    def get_object(self):
        service_name = self.kwargs.get(self.lookup_url_kwarg)
        service = get_object_or_404(ExternalService, machine_name=service_name, service_type='stt')
        settings_obj, created = STTModelSettings.objects.get_or_create(service=service)
        return settings_obj

class STTTranscriptionSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = STTTranscriptionSettingsSerializer

    def get_object(self):
        return STTTranscriptionSettings.load()

# --- Business Logic Views ---

class TranscribeView(STTServiceBaseView):
    def post(self, request, *args, **kwargs):
        serializer = TranscriptionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        file_id = serializer.validated_data.get('file_id')
        output_format = request.data.get('format', 'srt')
        try:
            uploaded_file = UploadedFile.objects.get(pk=file_id)
            if uploaded_file.file_type not in ['audio', 'video']:
                return JsonResponse({"error": "Only audio and video files can be transcribed."}, status=status.HTTP_400_BAD_REQUEST)
            formatted_content = transcribe_file(uploaded_file, output_format)
            return JsonResponse({"content": formatted_content}, status=status.HTTP_200_OK)
        except UploadedFile.DoesNotExist:
            return JsonResponse({"error": f"File with ID {file_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return self.handle_exception(e)

class STTProcessView(STTServiceBaseView):
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, *args, **kwargs):
        serializer = ProcessRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated_data = serializer.validated_data
        source_type = validated_data['source_type']
        output_format = validated_data['output_format']
        try:
            if source_type == 'upload':
                uploaded_file = create_uploaded_file_from_request(request)
                content = transcribe_file(uploaded_file, output_format)
                return JsonResponse({"content": content, "file_id": uploaded_file.id}, status=status.HTTP_200_OK)
            elif source_type == 'youtube':
                url = validated_data['url']
                content = get_youtube_transcript(url, output_format)
                return JsonResponse({"content": content}, status=status.HTTP_200_OK)
        except (ValueError, FileNotFoundError) as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except YouTubeProcessingError as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return self.handle_exception(e)


# Add this to your views.py for testing

class DebugSRTView(STTServiceBaseView):
    """
    Debug endpoint to test SRT formatting without transcription.
    POST with sample segments to see the formatted output.
    """

    def post(self, request, *args, **kwargs):
        from .formatters import to_srt, to_txt, to_vtt

        # Sample segments for testing
        test_segments = [
            {
                'start': 15.516,
                'end': 17.559,
                'text': "It won't be long now."
            },
            {
                'start': 17.643,
                'end': 20.020,
                'text': "At least she's comfortable."
            },
            {
                'start': 20.500,
                'end': 23.100,
                'text': "This is a test subtitle."
            }
        ]

        # Use provided segments or default test segments
        segments = request.data.get('segments', test_segments)
        output_format = request.data.get('format', 'srt')

        try:
            if output_format == 'txt':
                result = to_txt(segments)
            elif output_format == 'vtt':
                result = to_vtt(segments)
            else:
                result = to_srt(segments)

            return JsonResponse({
                'content': result,
                'format': output_format,
                'type': str(type(result)),
                'is_string': isinstance(result, str),
                'length': len(result),
                'segments_count': len(segments)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in debug view: {e}", exc_info=True)
            return JsonResponse({
                'error': str(e),
                'traceback': str(e.__traceback__)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):
        """Quick GET test"""
        from .formatters import to_srt

        test_segments = [
            {'start': 0.0, 'end': 2.5, 'text': 'Hello world'},
            {'start': 3.0, 'end': 5.5, 'text': 'This is a test'}
        ]

        result = to_srt(test_segments)

        return JsonResponse({
            'message': 'Debug endpoint working',
            'sample_srt': result,
            'type': str(type(result))
        })

