from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .docker_client import get_service_status, start_service, stop_service
import logging
import time

logger = logging.getLogger(__name__)

# Allow any for local PoC, restrict in production!
permission_classes = [permissions.AllowAny]

class ServiceStatusView(APIView):
    permission_classes = permission_classes

    def get(self, request, service_name, *args, **kwargs):
        logger.debug(f"Received status request for service: {service_name}")
        if service_name != 'stt': # Simple check for PoC
            logger.warning(f"Status request for unknown service: {service_name}")
            return Response({"error": f"Unknown service: {service_name}"}, status=status.HTTP_404_NOT_FOUND)

        current_status = get_service_status()
        logger.debug(f"Status for service '{service_name}': {current_status}")
        return Response({"service": service_name, "status": current_status})

class ServiceStartView(APIView):
    permission_classes = permission_classes

    def post(self, request, service_name, *args, **kwargs):
        logger.info(f"Received START request for service: {service_name}")
        if service_name != 'stt':
            logger.warning(f"Start request for unknown service: {service_name}")
            return Response({"error": f"Unknown service: {service_name}"}, status=status.HTTP_404_NOT_FOUND)

        success, message = start_service()
        # Fetch status AFTER attempting the action
        current_status = get_service_status() # Refresh status after action attempt
        if success:
            logger.info(f"Start request processed for '{service_name}'. Message: {message}. Current status: {current_status}")
            return Response({"message": message, "status": current_status})
        else:
            logger.error(f"Start request FAILED for '{service_name}'. Message: {message}")
            return Response({"error": message, "status": current_status}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ServiceStopView(APIView):
    permission_classes = permission_classes

    def post(self, request, service_name, *args, **kwargs):
        logger.info(f"Received STOP request for service: {service_name}")
        if service_name != 'stt':
            logger.warning(f"Stop request for unknown service: {service_name}")
            return Response({"error": f"Unknown service: {service_name}"}, status=status.HTTP_404_NOT_FOUND)

        success, message = stop_service()
        # Allow some time for status to potentially update, then fetch
        time.sleep(1.0) # Pause slightly
        current_status = get_service_status() # Refresh status
        if success:
            logger.info(f"Stop request processed for '{service_name}'. Message: {message}. Current status: {current_status}")
            return Response({"message": message, "status": current_status})
        else:
            logger.error(f"Stop request FAILED for '{service_name}'. Message: {message}")
            return Response({"error": message, "status": current_status}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)