import docker
from docker.errors import NotFound, APIError
import os
import logging

logger = logging.getLogger(__name__)

# --- Docker Client Initialization ---
try:
    client = docker.from_env()
    client.ping()
    logger.info("Successfully connected to Docker daemon via socket.")
except Exception as e:
    logger.error(f"ERROR: Failed to connect to Docker daemon: {e}")
    client = None

# --- Configuration ---
STT_CONTAINER_NAME = os.getenv('STT_CONTAINER_NAME', 'omnicore_stt_service_container')

# --- Helper Functions ---
def get_container(container_name=STT_CONTAINER_NAME):
    """Gets the container object by name. Returns None if not found or error."""
    if not client:
        logger.error("Docker client not available.")
        return None
    try:
        container = client.containers.get(container_name)
        return container
    except NotFound:
        logger.warning(f"Container '{container_name}' not found.")
        return None
    except APIError as e:
        logger.error(f"APIError getting container '{container_name}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting container '{container_name}': {e}")
        return None

def get_service_status(container_name=STT_CONTAINER_NAME):
    """Checks the status of the container. Returns status string or 'error'/'not_found'."""
    container = get_container(container_name)
    if container:
        try:
            # Refresh state before checking status
            container.reload()
            return container.status
        except Exception as e:
             logger.error(f"Error getting status for container '{container_name}': {e}")
             return "error"
    elif client is None:
        return "error"
    else:
        return "not_found"

def start_service(container_name=STT_CONTAINER_NAME):
    """Starts the container by name. Returns (bool success, str message)."""
    container = get_container(container_name)
    if not container:
        return False, f"Container '{container_name}' not found or Docker client error."

    current_status = get_service_status(container_name) # Check current status first
    if current_status == 'running':
        return True, f"Container '{container_name}' is already running."
    if current_status not in ['created', 'exited']:
        return False, f"Container '{container_name}' cannot be started from status '{current_status}'."

    try:
        logger.info(f"Attempting to start container: {container_name}")
        container.start()
        import time; time.sleep(1.5) # Give it a moment to start
        container.reload()
        if container.status == 'running':
            logger.info(f"Container '{container_name}' started successfully.")
            return True, f"Container '{container_name}' started successfully."
        else:
             logger.warning(f"Container '{container_name}' status is '{container.status}' after start attempt.")
             return False, f"Container '{container_name}' failed to reach 'running' state. Current status: {container.status}"
    except APIError as e:
        logger.error(f"APIError starting container '{container_name}': {e}")
        return False, f"Error starting container: {e}"
    except Exception as e:
         logger.error(f"Unexpected error starting container '{container_name}': {e}")
         return False, f"Unexpected error starting container: {e}"

def stop_service(container_name=STT_CONTAINER_NAME):
    """Stops the container gracefully by name. Returns (bool success, str message)."""
    container = get_container(container_name)
    if not container:
        return False, f"Container '{container_name}' not found or Docker client error."

    current_status = get_service_status(container_name) # Check current status first
    if current_status != 'running':
        return True, f"Container '{container_name}' is not running (status: {current_status})."

    try:
        stop_timeout = container.attrs.get('HostConfig', {}).get('StopTimeout', 10) # Get timeout from config or default
        logger.info(f"Attempting to stop container: {container_name} (grace period: {stop_timeout}s)")
        container.stop(timeout=stop_timeout) # Use timeout from config
        logger.info(f"Stop signal sent to container '{container_name}'.")
        return True, f"Stop signal sent to container '{container_name}'."
    except APIError as e:
        logger.error(f"APIError stopping container '{container_name}': {e}")
        return False, f"Error stopping container: {e}"
    except Exception as e:
        logger.error(f"Unexpected error stopping container '{container_name}': {e}")
        return False, f"Unexpected error stopping container: {e}"