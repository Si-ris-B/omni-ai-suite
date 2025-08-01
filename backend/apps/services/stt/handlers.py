# apps/services/stt/handlers.py
from ..container_manager import DockerServiceManager
import logging

logger = logging.getLogger(__name__)


class STTServiceHandler:
    """
    Provides a high-level, business-logic interface for managing the STT service.

    This class encapsulates the specific knowledge that our STT functionality
    is provided by a docker-compose service named "stt-service".

    It USES the generic DockerServiceManager to perform the actual work.
    """
    # This specific knowledge is now isolated in one place.
    SERVICE_NAME = "stt-service"

    def __init__(self):
        try:
            self.manager = DockerServiceManager()
        except ConnectionError as e:
            logger.error(f"STTServiceHandler could not connect to Docker: {e}")
            # Re-raise so the calling code knows there's a critical infrastructure issue.
            raise

    def get_status(self):
        """Checks the status of the STT service container."""
        logger.info(f"Checking status for the specific service: {self.SERVICE_NAME}")
        return self.manager.get_service_status(self.SERVICE_NAME)

    def ensure_running(self):
        """
        Checks if the STT service is running and starts it if it's not.
        This is an example of higher-level business logic.
        """
        status_info = self.get_status()
        if status_info.get('status') != 'running':
            logger.warning(
                f"STT service is not running (current status: {status_info.get('status')}). Attempting to start...")
            return self.manager.start_service(self.SERVICE_NAME)

        logger.info("STT service is already running.")
        return {"service": self.SERVICE_NAME, "status": "success", "message": "Service is already running."}

    def stop(self):
        """Stops the STT service container."""
        logger.info(f"Requesting to stop the specific service: {self.SERVICE_NAME}")
        return self.manager.stop_service(self.SERVICE_NAME)