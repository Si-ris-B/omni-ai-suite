# FILE: apps/services/stt/client.py

import httpx
import json
import logging
from django.shortcuts import get_object_or_404
from apps.services.models import ExternalService
from .models import STTModelSettings, STTTranscriptionSettings
from apps.features.uploader.models import UploadedFile

logger = logging.getLogger(__name__)


class STTServiceClient:
    """
    A client for communicating with a specific STT service's API.
    It can be initialized with a specific service object, or it will fall back
    to the default STT service if none is provided.
    """

    def __init__(self, service: ExternalService = None):
        if service:
            self.service_config = service
        else:
            try:
                self.service_config = ExternalService.objects.get(
                    service_type='stt', is_default=True, is_enabled=True
                )
            except ExternalService.DoesNotExist:
                raise RuntimeError("Configuration Error: No default STT service is enabled.")
            except ExternalService.MultipleObjectsReturned:
                raise RuntimeError("Configuration Error: More than one STT service is marked as default.")

        try:
            self.model_settings = self.service_config.sttmodelsettings
        except STTModelSettings.DoesNotExist:
            logger.warning(f"STTModelSettings not yet created for {self.service_config.machine_name}.")
            self.model_settings = None

        self.transcription_settings = STTTranscriptionSettings.load()

    def _build_url(self, endpoint: str) -> str:
        base_url = self.service_config.service_url.rstrip('/')
        return f"{base_url}/{endpoint.lstrip('/')}"

    def _handle_service_response(self, response: httpx.Response, for_service: str):
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_body = e.response.text
            logger.error(f"STT service '{for_service}' returned an error: {e.response.reason_phrase}\nBody: {error_body}")
            raise e

    def get_status(self):
        url = self._build_url("/status")
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                self._handle_service_response(response, for_service=self.service_config.machine_name)
                return response.json()
        except httpx.RequestError as e:
            logger.warning(f"Could not connect to STT service at {url}. Error: {e}")
            return {"service_status": "unavailable", "error": f"Connection refused to {self.service_config.service_url}."}
        except Exception as e:
            logger.error(f"Unexpected error in get_status: {e}")
            return {"service_status": "error", "error": "An unexpected server error occurred."}

    def get_required_model_config(self) -> dict:
        if not self.model_settings:
            self.model_settings = get_object_or_404(STTModelSettings, service=self.service_config)
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
        with httpx.Client(timeout=300.0) as client:
            response = client.post(url, json=required_config)
            self._handle_service_response(response, for_service=self.service_config.machine_name)
            return response.json()

    def unload_model(self):
        url = self._build_url("/unload_model")
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url)
            self._handle_service_response(response, for_service=self.service_config.machine_name)
            return response.json()

    def ensure_model_loaded(self):
        status = self.get_status()
        if status.get("service_status") == "unavailable":
            raise ConnectionError(f"Cannot ensure model is loaded; service '{self.service_config.machine_name}' is unavailable.")
        required_config = self.get_required_model_config()
        current_config = status.get("loaded_model_config", {})
        if status.get("service_status") == "model_loaded" and current_config.get("model_size_or_path") == required_config.get("model_size_or_path"):
            return
        logger.warning(f"Model not loaded or configuration mismatch on '{self.service_config.machine_name}'. Attempting to load.")
        self.load_model()

    def transcribe_file(self, uploaded_file: UploadedFile):
        self.ensure_model_loaded()
        settings = self.transcription_settings
        transcription_params = {
            "language": settings.language or None, "task": settings.task,
            "beam_size": settings.beam_size, "best_of": settings.best_of, "patience": settings.patience,
            "length_penalty": settings.length_penalty, "temperature": [settings.temperature],
            "compression_ratio_threshold": settings.compression_ratio_threshold,
            "log_prob_threshold": settings.log_prob_threshold,
            "no_speech_threshold": settings.no_speech_threshold,
            "condition_on_previous_text": settings.condition_on_previous_text,
            "initial_prompt": settings.initial_prompt or None,
            "word_timestamps": settings.word_timestamps, "vad_filter": settings.vad_filter,
            "repetition_penalty": settings.repetition_penalty, "no_repeat_ngram_size": settings.no_repeat_ngram_size,
        }
        payload = {"file_path": uploaded_file.file.name, "cleanup_file": False, "params": transcription_params}
        url = self._build_url("/transcribe")
        try:
            with httpx.stream("POST", url, json=payload, timeout=1800.0) as response:
                self._handle_service_response(response, for_service=self.service_config.machine_name)
                for line in response.iter_lines():
                    if line:
                        yield line
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)})