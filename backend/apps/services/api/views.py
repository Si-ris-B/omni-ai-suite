# apps/services/api/views.py
from rest_framework import views, permissions, status
from rest_framework.response import Response
from .serializers import ContainerControlSerializer
from ..container_manager import DockerServiceManager
import logging

# Add these imports at the top
from django.http import StreamingHttpResponse
import time
import json

logger = logging.getLogger(__name__)


class ContainerControlView(views.APIView):
    """
    API endpoint to start or stop a Docker container service.
    Requires admin user permissions.

    POST /api/v1/containers/control/
    {
        "service_name": "stt-service",
        "action": "start"
    }
    """
    # CRITICAL: Only allow admin users to access this view.
    permission_classes = [permissions.AllowAny] # <-- CHANGE THIS LINE

    def post(self, request, *args, **kwargs):
        serializer = ContainerControlSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service_name = serializer.validated_data['service_name']
        action = serializer.validated_data['action']

        try:
            manager = DockerServiceManager()
        except ConnectionError as e:
            logger.error(f"ContainerControlView: {e}")
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if action == 'start':
            result = manager.start_service(service_name)
        elif action == 'stop':
            result = manager.stop_service(service_name)
        else:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        if result.get('status') == 'error':
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(result, status=status.HTTP_200_OK)


class ContainerStatusView(views.APIView):
    """
    API endpoint to get the status of a specific Docker container service.
    Requires admin user permissions.

    GET /api/v1/containers/stt-service/status/
    """
    # permission_classes = [permissions.IsAdminUser]
    permission_classes = [permissions.AllowAny] # <-- CHANGE THIS LINE


    def get(self, request, service_name, *args, **kwargs):
        try:
            manager = DockerServiceManager()
        except ConnectionError as e:
            logger.error(f"ContainerStatusView: {e}")
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        status_data = manager.get_service_status(service_name)

        if status_data.get('status') == 'not_found':
            return Response(status_data, status=status.HTTP_404_NOT_FOUND)

        return Response(status_data, status=status.HTTP_200_OK)


class ContainerStatusStreamView(views.APIView):
    """
    Streams the status of a specific container using Server-Sent Events (SSE).
    This provides real-time updates to a connected client.
    """
    # Use the same permission class as your other endpoints.
    # AllowAny for testing, IsAdminUser for production.
    permission_classes = [permissions.AllowAny]

    def get(self, request, service_name, *args, **kwargs):

        def event_stream_generator():
            """
            This is the generator function. It will run in a loop, check for
            status changes, and yield messages in the SSE format.
            """
            logger.info(f"SSE STREAM: Client connected for service: {service_name}")
            last_known_status = None
            manager = DockerServiceManager()

            try:
                while True:
                    # 1. Get the current status using our existing manager
                    current_status_data = manager.get_service_status(service_name)
                    current_status = current_status_data.get('status')

                    # 2. Check if the status has actually changed since the last check
                    if current_status != last_known_status:
                        logger.info(
                            f"SSE STREAM: Status change for '{service_name}' detected: '{last_known_status}' -> '{current_status}'. Sending update.")

                        # 3. Format the data as a JSON string for the event
                        message = json.dumps(current_status_data)

                        # 4. Yield the message in the SSE format: "data: <message>\n\n"
                        # The double newline is crucial.
                        yield f"data: {message}\n\n"

                        # 5. Update the last known status
                        last_known_status = current_status

                    # 6. Wait for 2 seconds before checking again.
                    # This is the server's check interval, NOT a client poll.
                    time.sleep(2)

            except GeneratorExit:
                # This code block executes when the client disconnects.
                logger.info(f"SSE STREAM: Client disconnected for service: {service_name}. Closing stream.")
                # The generator is automatically cleaned up.

        # Create the StreamingHttpResponse, passing it our generator function
        response = StreamingHttpResponse(event_stream_generator(), content_type='text/event-stream')

        # These headers are important to prevent proxies or browsers from
        # buffering the response, which would break the real-time stream.
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Specifically for Nginx proxies

        return response