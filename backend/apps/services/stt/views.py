import json

from django.http import StreamingHttpResponse, JsonResponse
from rest_framework import views, permissions, status
from rest_framework.response import Response
from .client import STTServiceClient
from .formatters import to_srt, to_txt
from .serializers import TranscriptionRequestSerializer
from apps.features.uploader.models import UploadedFile
from apps.services.models import ExternalService
import logging

logger = logging.getLogger(__name__)


# The dynamic factory is no longer needed for the primary user workflow.

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
        # NOTE: The front-end needs to send `format` in the request body
        # e.g. { "file_id": 123, "format": "srt" }
        serializer = TranscriptionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Use DRF's default error response
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        file_id = validated_data.get('file_id')
        # This will require a 'format' field in your TranscriptionRequestSerializer.
        # If it's not there, you can get it from request.data.get('format', 'srt')
        # For now, let's assume it's in the request data but not the serializer for simplicity.
        output_format = request.data.get('format', 'srt')


        try:
            uploaded_file = UploadedFile.objects.get(pk=file_id)
            if uploaded_file.file_type != 'audio':
                return JsonResponse({"error": "Only audio files can be transcribed."}, status=status.HTTP_400_BAD_REQUEST)

            client = STTServiceClient()
            stream_generator = client.transcribe_file(uploaded_file)

            segments = []
            final_message_received = False
            # FIX: The generator now yields strings, so we can iterate directly.
            for line_str in stream_generator:
                try:
                    # Now we can safely parse the string.
                    data = json.loads(line_str)
                    if data.get('type') == 'segment':
                        segments.append(data.get('data', {}))
                    elif data.get('type') == 'final':
                        final_message_received = True
                        logger.info(f"Transcription complete for file {file_id}. Message: {data.get('message')}")
                    elif data.get('type') == 'error':
                        # The error from the downstream service is now handled cleanly.
                        error_detail = data.get('message', 'Unknown transcription error from service')
                        logger.error(f"Downstream transcription error for file {file_id}: {error_detail}")
                        raise RuntimeError(error_detail)
                except (json.JSONDecodeError, KeyError):
                    logger.warning(f"Could not parse line from transcription stream: '{line_str}'")
                    continue

            if not final_message_received and not segments:
                raise RuntimeError("Transcription stream ended prematurely with no segments or completion message.")

            if output_format == 'txt':
                formatted_content = to_txt(segments)
            else:
                formatted_content = to_srt(segments)

            return JsonResponse({"content": formatted_content}, status=status.HTTP_200_OK)

        except UploadedFile.DoesNotExist:
            return JsonResponse({"error": f"File with ID {file_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Transcription failed for file {file_id}: {e}", exc_info=True)
            return JsonResponse({"error": f"Transcription failed. Check server logs for details. Reason: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# The administrative views below are for direct management and debugging.
# It is appropriate for them to require a specific machine_name.


# The administrative views below are for direct management and debugging.
# It is appropriate for them to require a specific machine_name.

class STTStatusView(STTServiceBaseView):
    """
    Gets the status of the default STT service.
    For admin/debug purposes, a specific service can be checked via its URL.
    """

    def get(self, request, service_name=None, *args, **kwargs):
        try:
            # Re-implementing a simple factory here for admin purposes.
            if service_name:
                service_config = ExternalService.objects.get(machine_name=service_name, service_type='stt')
                client = STTServiceClient(service_config)  # Temporarily override default
            else:
                client = STTServiceClient()  # Use default

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
            client = STTServiceClient(service_config)  # Override default

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