import httpx
import json
import logging
from pathlib import Path
from apps.services.models import ExternalService
from .models import STTModelSettings, STTTranscriptionSettings
from apps.features.uploader.models import UploadedFile

logger = logging.getLogger(__name__)


class STTServiceClient:
    """
    A client for communicating with the system's primary, default STT service's API.
    It uses the `service_url` for API calls and provides detailed logging for errors.
    """

    def __init__(self):
        """
        Initializes the client by finding and loading the default STT service.
        """
        try:
            self.service_config = ExternalService.objects.get(
                service_type='stt',
                is_default=True,
                is_enabled=True
            )
        except ExternalService.DoesNotExist:
            raise RuntimeError(
                "Configuration Error: No default STT service is enabled. Please mark one as default in the admin panel.")
        except ExternalService.MultipleObjectsReturned:
            raise RuntimeError(
                "Configuration Error: More than one STT service is marked as default. Please ensure only one is default.")

        try:
            self.model_settings = self.service_config.sttmodelsettings
        except STTModelSettings.DoesNotExist:
            raise RuntimeError(
                f"STT-specific settings for the service linked to container '{self.service_config.container_name}' are not configured.")

        self.transcription_settings = STTTranscriptionSettings.load()

    def _build_url(self, endpoint: str) -> str:
        base_url = self.service_config.service_url.rstrip('/')
        return f"{base_url}/{endpoint.lstrip('/')}"

    def _handle_service_response(self, response: httpx.Response, for_service: str):
        """
        Checks for HTTP errors and logs the full response body for debugging.
        Raises a more informative HTTPStatusError upon failure.
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # This is the crucial part: log the response content that contains the real error
            error_body = e.response.text
            logger.error(
                f"STT service '{for_service}' returned an error: {e.status_code} {e.response.reason_phrase}"
            )
            logger.error(f"--- DOWNSTREAM ERROR TRACEBACK FROM '{for_service}' ---")
            # Log line by line for better readability in most log viewers
            for line in error_body.splitlines():
                logger.error(line)
            logger.error(f"--- END TRACEBACK ---")

            # Re-raise the original exception to let the calling function handle it,
            # but now we have the detailed logs.
            raise e

    def get_status(self):
        url = self._build_url("/status")
        container_id = self.service_config.container_name or "Unknown Container"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                self._handle_service_response(response, for_service=container_id)
                return response.json()
        except httpx.RequestError as e:
            raise ConnectionError(
                f"Could not connect to STT service API for container '{container_id}' at {self.service_config.service_url}: {e}") from e
        except httpx.HTTPStatusError as e:
            # The detailed error is already logged by our helper. Re-raise a simpler one.
            raise ValueError(
                f"STT service API for container '{container_id}' returned an error (see logs for details).") from e

    def get_required_model_config(self) -> dict:
        try:
            indices = [int(i.strip()) for i in self.model_settings.device_index.split(',')]
            device_index_val = indices[0] if len(indices) == 1 else indices
        except (ValueError, AttributeError):
            device_index_val = 0
        return {
            "model_size_or_path": self.model_settings.model_size_or_path,
            "device": self.model_settings.device,
            "compute_type": self.model_settings.compute_type,
            "device_index": device_index_val,
            "cpu_threads": self.model_settings.cpu_threads,
            "num_workers": self.model_settings.num_workers,
        }

    def load_model(self):
        url = self._build_url("/load_model")
        required_config = self.get_required_model_config()
        container_id = self.service_config.container_name or "Unknown Container"

        logger.info(
            f"Requesting to load model on container '{container_id}' with config: {json.dumps(required_config)}")

        try:
            with httpx.Client(timeout=300.0) as client:
                response = client.post(url, json=required_config)
                self._handle_service_response(response, for_service=container_id)
                logger.info(f"Successfully received response from load_model for container '{container_id}'.")
                return response.json()
        except httpx.HTTPStatusError as e:
            # The detailed error is logged by the helper. Re-raise a user-friendly one.
            raise RuntimeError(
                f"Failed to load model for STT container '{container_id}'. The service returned a server error. Check the Django logs for the full traceback from the STT service.") from e
        except Exception as e:
            raise RuntimeError(
                f"An unexpected error occurred while trying to load model for STT container '{container_id}': {e}") from e

    def unload_model(self):
        url = self._build_url("/unload_model")
        container_id = self.service_config.container_name or "Unknown Container"
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url)
                self._handle_service_response(response, for_service=container_id)
                return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to unload model for STT container '{container_id}': {e}") from e

    def ensure_model_loaded(self):
        status = self.get_status()
        required_config = self.get_required_model_config()
        current_config = status.get("loaded_model_config", {})
        if status.get("service_status") == "model_loaded" and current_config == required_config:
            logger.info(f"Model is already loaded correctly on container '{self.service_config.container_name}'.")
            return
        logger.warning(
            f"Model not loaded or configuration mismatch on '{self.service_config.container_name}'. Attempting to load.")
        self.load_model()

    def transcribe_file(self, uploaded_file: UploadedFile):
        self.ensure_model_loaded()
        relative_path = uploaded_file.file.name
        settings = self.transcription_settings
        try:
            temp_list = [float(t.strip()) for t in settings.temperature.split(',')]
        except (ValueError, TypeError):
            temp_list = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

        transcription_params = {
            "language": settings.language or None, "task": settings.task,
            "beam_size": settings.beam_size, "best_of": settings.best_of, "patience": settings.patience,
            "length_penalty": settings.length_penalty, "temperature": temp_list,
            "compression_ratio_threshold": settings.compression_ratio_threshold,
            "log_prob_threshold": settings.log_prob_threshold,
            "no_speech_threshold": settings.no_speech_threshold,
            "condition_on_previous_text": settings.condition_on_previous_text,
            "initial_prompt": settings.initial_prompt or None,
            "word_timestamps": settings.word_timestamps, "vad_filter": settings.vad_filter,
            "repetition_penalty": settings.repetition_penalty, "no_repeat_ngram_size": settings.no_repeat_ngram_size,
        }
        payload = {"file_path": relative_path, "cleanup_file": False, "params": transcription_params}
        url = self._build_url("/transcribe")
        try:
            with httpx.stream("POST", url, json=payload, timeout=1800.0) as response:
                self._handle_service_response(response, for_service=self.service_config.container_name)
                # FIX: Yield the decoded string line directly. iter_lines() already handles decoding.
                for line in response.iter_lines():
                    if line:
                        yield line
        except Exception as e:
            # FIX: Yield the error message as a plain string, matching the new generator contract.
            error_message = json.dumps({"type": "error", "message": str(e)})
            yield error_message