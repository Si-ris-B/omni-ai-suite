# apps/services/container_manager.py
import docker
from docker.errors import NotFound, APIError  # Ensure NotFound is imported
import os
import logging

logger = logging.getLogger(__name__)


class DockerServiceManager:
    """
    Manages Docker services.
    Finds containers using docker-compose labels first, then falls back
    to matching the exact container name.
    """

    def __init__(self):
        try:
            self.client = docker.from_env()
            self.project_name = os.getenv('COMPOSE_PROJECT_NAME', os.path.basename(os.getcwd()))
            logger.info(f"DockerServiceManager initialized for project: {self.project_name}")
        except APIError as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise ConnectionError("Could not connect to the Docker daemon. Is it running?") from e

    def _get_container_for_service(self, service_name: str):
        """
        Finds a container using a two-strategy approach.

        1.  Tries to find a container using standard docker-compose labels.
        2.  If that fails, it tries to find a container by its exact name.
        """
        # --- Strategy 1: Find by docker-compose labels (Preferred method) ---
        try:
            filters = {
                'label': [
                    f'com.docker.compose.project={self.project_name}',
                    f'com.docker.compose.service={service_name}'
                ]
            }
            containers = self.client.containers.list(all=True, filters=filters)

            if containers:
                container = containers[0]
                logger.info(f"Found container '{container.name}' for service '{service_name}' using labels.")
                return container

            logger.warning(
                f"No container found for service '{service_name}' using labels. Attempting fallback strategy.")

        except APIError as e:
            logger.error(f"Docker API error during label search: {e}. Attempting fallback strategy.")

        # --- Strategy 2: Fallback to finding by exact container name ---
        try:
            container = self.client.containers.get(service_name)
            logger.info(f"Found container '{container.name}' by treating '{service_name}' as an exact container name.")
            return container
        except NotFound:
            logger.error(f"Fallback failed: No container with the name '{service_name}' exists.")
            return None
        except APIError as e:
            logger.error(f"Docker API error during name-based fallback search: {e}")
            return None

    def get_service_status(self, service_name: str) -> dict:
        """Gets the status and details of a service's container."""
        container = self._get_container_for_service(service_name)
        if not container:
            return {"service": service_name, "status": "not_found"}

        return {
            "service": service_name,
            "container_id": container.short_id,
            "container_name": container.name,
            "status": container.status,
            "image": str(container.image),
            "labels": container.labels,
        }

    def start_service(self, service_name: str) -> dict:
        """Starts the container for a given service."""
        container = self._get_container_for_service(service_name)
        if not container:
            return {"service": service_name, "status": "error", "message": "Container not found."}

        if container.status == 'running':
            return {"service": service_name, "status": "success", "message": "Service is already running."}

        try:
            container.start()
            logger.info(f"Successfully started container for service: {service_name}")
            return {"service": service_name, "status": "success", "message": "Service started successfully."}
        except APIError as e:
            logger.error(f"Failed to start container for {service_name}: {e}")
            return {"service": service_name, "status": "error", "message": str(e)}

    def stop_service(self, service_name: str) -> dict:
        """Stops the container for a given service."""
        container = self._get_container_for_service(service_name)
        if not container:
            return {"service": service_name, "status": "error", "message": "Container not found."}

        if container.status != 'running':
            return {"service": service_name, "status": "success", "message": "Service was not running."}

        try:
            container.stop(timeout=10)
            logger.info(f"Successfully stopped container for service: {service_name}")
            return {"service": service_name, "status": "success", "message": "Service stopped successfully."}
        except APIError as e:
            logger.error(f"Failed to stop container for {service_name}: {e}")
            return {"service": service_name, "status": "error", "message": str(e)}