# stt_service_project/app/main.py
import os
import time
import asyncio
import json
import traceback
import gc
from typing import Optional, List, Union, Iterable, Dict, Tuple
from pathlib import Path

# --- FastAPI and Related Imports ---
from fastapi import (
    FastAPI, HTTPException, Body, status, WebSocket, WebSocketDisconnect
)
from fastapi.responses import StreamingResponse, JSONResponse

# --- Faster Whisper Imports ---
from faster_whisper import WhisperModel, BatchedInferencePipeline
from faster_whisper.audio import decode_audio
# from faster_whisper.tokenizer import Tokenizer # Conditionally imported

# --- Pydantic for Validation ---
from pydantic import BaseModel, Field
import numpy as np

# --- Logging Setup ---
APP_LOGGER_NAME = "stt_service.main"  # Define before importing logging_config
from logging_config import setup_logging, log_websockets

logger = None  # Will be initialized in startup

# --- Global State Variables ---
current_model: Optional[WhisperModel] = None
current_config: Optional[Dict] = None  # Store the dict version of ModelConfigParams
current_batched_pipeline: Optional[BatchedInferencePipeline] = None
model_lock = asyncio.Lock()

# --- FIXED INTERNAL Configuration Paths ---
# These are fixed from the application's perspective INSIDE the container.
# Dynamism comes from what HOST directories are mounted TO these locations via `docker run -v`.
SHARED_AUDIO_PATH = Path("/stt_app_data/audio_inbox")
MODEL_CACHE_PATH = Path("/stt_app_data/model_cache")

# --- Environment Variables for other settings ---
ENV_LOG_LEVEL = "LOG_LEVEL"
ENV_CLEANUP_AUDIO = "CLEANUP_AUDIO"
ENV_APP_PORT = "PORT"  # For Uvicorn, matches Dockerfile and run commands
ENV_APP_HOST = "HOST"  # For Uvicorn

LOG_LEVEL = os.getenv(ENV_LOG_LEVEL, "INFO")
SHOULD_CLEANUP_AUDIO = os.getenv(ENV_CLEANUP_AUDIO, "True").lower() == "true"
APP_PORT = int(os.getenv(ENV_APP_PORT, "8001"))  # Default internal port
APP_HOST = os.getenv(ENV_APP_HOST, "0.0.0.0")


# --- Pydantic Models ---
class ModelConfigParams(BaseModel):
    model_size_or_path: str = Field(...,
                                    description="Model name (e.g., 'base.en'), HuggingFace ID, or path to a converted model directory (can be relative to STT_MODEL_CACHE_PATH or absolute inside container).")
    device: str = Field("auto", description="Device: 'cpu', 'cuda', 'auto'.")
    compute_type: str = Field("default", description="Compute type: e.g., 'int8', 'float16', 'default'.")
    device_index: Union[int, List[int]] = Field(0, description="GPU device index/indices.")
    cpu_threads: int = Field(0, description="Number of CPU threads (0 for auto).")
    num_workers: int = Field(1,
                             description="Number of workers for WhisperModel (not BatchedInferencePipeline's batch_size).")


class VADParams(BaseModel):
    threshold: Optional[float] = 0.5;
    min_speech_duration_ms: Optional[int] = 250
    max_speech_duration_s: Optional[float] = float('inf');
    min_silence_duration_ms: Optional[int] = 2000
    window_size_samples: Optional[int] = 1024;
    speech_pad_ms: Optional[int] = 400


class BatchedVADParams(VADParams):
    min_silence_duration_ms: Optional[int] = 160
    max_speech_duration_s: Optional[float] = None


class StandardTranscriptionParams(BaseModel):
    language: Optional[str] = Field(None, description="Language code (e.g., 'en'). None for auto-detect.");
    task: str = Field("transcribe", description="'transcribe' or 'translate'")
    beam_size: int = Field(5);
    best_of: int = Field(5);
    patience: float = Field(1.0);
    length_penalty: float = Field(1.0)
    repetition_penalty: float = Field(1.0);
    no_repeat_ngram_size: int = Field(0)
    temperature: Union[float, List[float]] = Field(default=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    compression_ratio_threshold: Optional[float] = Field(2.4);
    log_prob_threshold: Optional[float] = Field(-1.0)
    no_speech_threshold: Optional[float] = Field(0.6);
    condition_on_previous_text: bool = Field(True)
    prompt_reset_on_temperature: float = Field(0.5);
    initial_prompt: Optional[Union[str, Iterable[int]]] = Field(None)
    prefix: Optional[str] = Field(None);
    suppress_blank: bool = Field(True)
    suppress_tokens: Optional[List[int]] = Field(default=[-1], description="List of token IDs. -1 for non-speech.");
    without_timestamps: bool = Field(False)
    max_initial_timestamp: float = Field(1.0);
    word_timestamps: bool = Field(False, description="Enable word timestamps.")
    prepend_punctuations: str = Field("\"'“¿([{-");
    append_punctuations: str = Field("\"'.。,，!！?？:：”)]}、")
    vad_filter: bool = Field(False, description="Enable VAD filter.");
    vad_parameters: Optional[VADParams] = Field(None, description="VAD parameters.")
    max_new_tokens: Optional[int] = Field(None);
    clip_timestamps: str = Field("0", description="Timestamps to clip audio.")
    hallucination_silence_threshold: Optional[float] = Field(None);
    hotwords: Optional[str] = Field(None, description="Boost these words.")
    language_detection_threshold: Optional[float] = Field(0.5);
    language_detection_segments: int = Field(1)


class BatchedTranscriptionParams(BaseModel):
    language: Optional[str] = None;
    task: str = "transcribe";
    beam_size: int = Field(1, description="Usually 1 for batched pipeline.")
    patience: float = 1.0;
    length_penalty: float = 1.0;
    repetition_penalty: float = 1.0;
    no_repeat_ngram_size: int = 0
    temperature: Union[float, List[float]] = Field(default=[0.0]);
    initial_prompt: Optional[Union[str, Iterable[int]]] = None
    suppress_blank: bool = True;
    suppress_tokens: Optional[List[int]] = Field(default=[-1]);
    without_timestamps: bool = True
    word_timestamps: bool = False;
    prepend_punctuations: str = "\"'“¿([{-";
    append_punctuations: str = "\"'.。,，!！?？:：”)]}、"
    vad_filter: bool = True;
    vad_parameters: Optional[BatchedVADParams] = None
    max_new_tokens: Optional[int] = None;
    chunk_length: Optional[int] = Field(None, description="Audio chunk length for pipeline.")
    clip_timestamps: Optional[Union[str, List[Dict[str, float]]]] = Field(None)
    batch_size: int = Field(8, description="Inference batch size for pipeline.");
    hotwords: Optional[str] = None
    language_detection_threshold: Optional[float] = 0.5;
    language_detection_segments: int = 1


class TranscribeRequest(BaseModel):
    params: StandardTranscriptionParams
    file_path: str = Field(..., description="Filename relative to the service's internal shared audio path.")


class BatchedTranscribeRequest(BaseModel):
    params: BatchedTranscriptionParams
    file_path: str = Field(..., description="Filename relative to the service's internal shared audio path.")


class DetectLanguageRequest(BaseModel):
    vad_filter: bool = False;
    vad_parameters: Optional[VADParams] = None
    language_detection_segments: int = 1;
    language_detection_threshold: float = 0.5
    file_path: str = Field(..., description="Filename relative to the service's internal shared audio path.")


# --- FastAPI Application Instance ---
app = FastAPI(
    title="On-Demand STT Service",
    description="Dynamically load/unload Whisper models. Processes audio from a shared space defined by volume mounts. Uses fixed internal paths.",
    version="2.1.0"  # Version bump for clarity
)


# --- Lifespan Events ---
@app.on_event("startup")
async def startup_event():
    global logger
    logger = setup_logging(LOG_LEVEL)  # logger will be named APP_LOGGER_NAME by setup_logging
    logger.info(f"---- STT Service Starting (PID: {os.getpid()}) ----")
    logger.info(f"LOG_LEVEL set to: {LOG_LEVEL}")
    logger.info(f"Internal Shared Audio Path (fixed): {SHARED_AUDIO_PATH.resolve()}")
    logger.info(f"Internal Model Cache Path (fixed): {MODEL_CACHE_PATH.resolve()}")
    try:
        SHARED_AUDIO_PATH.mkdir(parents=True, exist_ok=True)
        MODEL_CACHE_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Internal directory ensured: {SHARED_AUDIO_PATH.resolve()}")
        logger.info(f"Internal directory ensured: {MODEL_CACHE_PATH.resolve()}")
    except Exception as e:
        logger.error(
            f"CRITICAL: Failed to create/access fixed internal directories. Check Dockerfile 'mkdir' and permissions if this occurs.",
            exc_info=True)
    logger.info("STT Service initialized IDLE (no model loaded).")


@app.on_event("shutdown")
async def shutdown_event():
    log_msg_prefix = f"[{APP_LOGGER_NAME}] " if logger else ""  # Handle if logger failed to init
    print(f"{log_msg_prefix}---- STT Service Shutting Down ----")  # Print ensures visibility if logging is broken
    if logger: logger.warning("Service Shutting Down (called via shutdown_event)")
    async with model_lock:
        await _unload_model_internal()
    if logger:
        logger.info("Service stopped.")
    else:
        print(f"{log_msg_prefix}Service stopped.")


# --- Internal Model Management ---
async def _unload_model_internal():
    global current_model, current_config, current_batched_pipeline
    if current_model is not None:
        model_info = f"{current_config.get('model_size_or_path', '?')} ({current_config.get('device', '?')})"
        log_msg = f"Unloading model: {model_info}"
        if logger:
            logger.warning(log_msg)
        else:
            print(f"[{APP_LOGGER_NAME}] {log_msg}")
        model_ref = current_model;
        batch_ref = current_batched_pipeline
        current_model = None;
        current_config = None;
        current_batched_pipeline = None
        del model_ref;
        del batch_ref;
        gc.collect()
        log_msg = f"Model {model_info} unloaded."
        if logger:
            logger.info(log_msg)
        else:
            print(f"[{APP_LOGGER_NAME}] {log_msg}")
        await asyncio.sleep(0.1)


async def _load_model_internal(config: ModelConfigParams):
    global current_model, current_config, current_batched_pipeline
    logger.info(f"Attempting to load model: {config.model_size_or_path} with config: {config.dict(exclude_none=True)}")
    start_time = time.time()
    try:
        if not MODEL_CACHE_PATH.is_dir():
            logger.warning(
                f"Internal model cache path {MODEL_CACHE_PATH} is not a directory or doesn't exist. Attempting to create.")
            MODEL_CACHE_PATH.mkdir(parents=True, exist_ok=True)

        model_source = config.model_size_or_path
        candidate_path = Path(model_source)
        effective_model_source = model_source  # Default to what user provided

        if not candidate_path.is_absolute():  # If it's not an absolute path like /other_mounted_models/my_model
            # Check if it's a directory relative to our MODEL_CACHE_PATH
            potential_local_path = MODEL_CACHE_PATH / model_source
            if potential_local_path.is_dir():
                effective_model_source = str(potential_local_path)
                logger.info(f"Found local model directory in cache: {effective_model_source}")
            else:
                logger.info(
                    f"Assuming '{model_source}' is a HuggingFace ID or downloadable path (not found as local dir in cache).")
        else:  # User provided an absolute path (inside container)
            logger.info(
                f"Using provided absolute model path: {effective_model_source}. Ensure this path is accessible in the container.")

        loaded_model = WhisperModel(effective_model_source,
                                    device=config.device, device_index=config.device_index,
                                    compute_type=config.compute_type, cpu_threads=config.cpu_threads,
                                    num_workers=config.num_workers, download_root=str(MODEL_CACHE_PATH))
        loaded_batched_pipeline = BatchedInferencePipeline(model=loaded_model)
        current_model = loaded_model
        current_batched_pipeline = loaded_batched_pipeline
        current_config = config.dict()
        load_time = time.time() - start_time
        logger.info(
            f"Successfully loaded model '{config.model_size_or_path}' (resolved to '{effective_model_source}') and batched pipeline in {load_time:.2f}s.")
    except Exception as e:
        logger.error(f"FATAL: Failed to load model '{config.model_size_or_path}': {e}", exc_info=True)
        current_model = None;
        current_config = None;
        current_batched_pipeline = None
        gc.collect();
        raise


# --- Helper Functions ---
def sanitize_path(client_relative_path: str) -> Path:
    if not client_relative_path:
        raise ValueError("File path from client cannot be empty.")
    normalized_client_path_str = os.path.normpath(client_relative_path).lstrip('/\\')
    if ".." in normalized_client_path_str.split(os.sep):
        logger.error(f"Forbidden '..' in client path component: '{client_relative_path}'")
        raise ValueError("Path component '..' is forbidden in the provided file path.")
    # SHARED_AUDIO_PATH is already an absolute internal path. We resolve it once more
    # during comparison for utmost robustness, but it's fixed for the app's lifetime.
    base_path_for_val = SHARED_AUDIO_PATH.resolve()
    prospective_full_path = (base_path_for_val / normalized_client_path_str).resolve()
    if not prospective_full_path.is_relative_to(base_path_for_val):
        logger.error(
            f"Path traversal attempt. Client path '{client_relative_path}' -> '{prospective_full_path}' is outside '{base_path_for_val}'.")
        raise ValueError("Path resolves outside designated shared audio directory.")
    return prospective_full_path


def cleanup_audio_source(source_path_str: Optional[str]):
    if not SHOULD_CLEANUP_AUDIO or not source_path_str: return
    try:
        path_obj = Path(source_path_str)
        if path_obj.is_file(): logger.info(f"Attempting to clean up source audio: {source_path_str}"); path_obj.unlink(
            missing_ok=True)
    except Exception as e:
        logger.error(f"Cleanup failed for '{source_path_str}': {e}")


def _validate_vad_params(params: Optional[Union[VADParams, BatchedVADParams]]) -> Optional[dict]:  # Unchanged
    if params is None: return None
    vad_dict = params.dict(exclude_unset=True)
    if isinstance(params, BatchedVADParams) and 'max_speech_duration_s' in vad_dict and vad_dict[
        'max_speech_duration_s'] == float('inf'):
        del vad_dict['max_speech_duration_s']
    return vad_dict


def _parse_clip_timestamps_standard(clip_timestamps_str: str) -> str:  # Unchanged
    if clip_timestamps_str == "0": return "0"
    try:
        parts = clip_timestamps_str.split(',');
        if not parts or not all(part.strip() for part in parts): raise ValueError("Empty timestamp value found.")
        [float(ts.strip()) for ts in parts]
        return clip_timestamps_str
    except ValueError as e:
        logger.error(f"Invalid clip_timestamps: '{clip_timestamps_str}'. {e}"); raise HTTPException(status_code=400,
                                                                                                    detail=f"Invalid clip_timestamps: '{clip_timestamps_str}'")


# --- API Endpoints (Identical logic to the previous "final" set, just re-pasted for completeness) ---
@app.get("/status", summary="Get current STT service status", response_model=Dict)
async def get_stt_status_api():
    async with model_lock:
        status_data = {
            "service_status": "model_loaded" if current_model else "idle_no_model",
            "loaded_model_config": current_config,
            "internal_shared_audio_path": str(SHARED_AUDIO_PATH.resolve()),  # Show resolved path
            "internal_model_cache_path": str(MODEL_CACHE_PATH.resolve()),  # Show resolved path
            "log_level": LOG_LEVEL,
            "audio_cleanup_enabled": SHOULD_CLEANUP_AUDIO
        }
    return status_data


@app.post("/load_model", summary="Load a specific Whisper model configuration", status_code=status.HTTP_200_OK,
          response_model=Dict)
async def api_load_model(config: ModelConfigParams = Body(...)):
    request_id = f"load-{time.time_ns()}"
    logger.info(
        f"[{request_id}] API: Load model req: {config.model_size_or_path}, Config: {config.dict(exclude_none=True)}")
    async with model_lock:
        if current_config and current_config == config.dict():
            logger.info(f"[{request_id}] API: Model '{config.model_size_or_path}' already loaded with this config.")
            return JSONResponse(status_code=status.HTTP_200_OK,
                                content={"status": "success", "message": "Model already loaded.",
                                         "config": current_config})
        try:
            if current_model:
                prev_model_name = current_config.get('model_size_or_path') if current_config else "N/A"
                logger.info(f"[{request_id}] API: Unloading existing model ('{prev_model_name}') first.")
                await _unload_model_internal()
            await _load_model_internal(config)
            logger.info(f"[{request_id}] API: Successfully loaded model '{config.model_size_or_path}'.")
            return {"status": "success", "message": "Model loaded successfully.", "config": current_config}
        except Exception as e:
            logger.error(f"[{request_id}] API: Model loading failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Model load failed: {str(e)}")


@app.post("/unload_model", summary="Unload the currently active Whisper model", response_model=Dict)
async def api_unload_model():
    request_id = f"unload-{time.time_ns()}"
    logger.info(f"[{request_id}] API: Unload model req.")
    async with model_lock:
        if current_model is None:
            logger.info(f"[{request_id}] API: No model loaded. Unload is a no-op.")
            return {"status": "success", "message": "Already idle. No model was loaded."}
        try:
            await _unload_model_internal()
            logger.info(f"[{request_id}] API: Successfully unloaded model.")
            return {"status": "success", "message": "Model unloaded successfully."}
        except Exception as e:
            logger.error(f"[{request_id}] API: Model unloading failed.", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Model unload failed: {str(e)}")


@app.post("/transcribe", summary="Transcribe audio using the currently loaded model")
async def api_transcribe(request_data: TranscribeRequest = Body(...)):
    active_model_ref: Optional[WhisperModel] = None
    source_path_abs_str: Optional[str] = None
    params = request_data.params
    request_id = f"txn-{time.time_ns()}"
    logger.info(f"[{request_id}] API: Transcribe req for client file: '{request_data.file_path}'")

    async with model_lock:
        if current_model is None:
            logger.error(f"[{request_id}] API: No model loaded for transcription.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No model loaded. Use /load_model first.")
        active_model_ref = current_model
        model_name_for_log = current_config.get('model_size_or_path', 'unknown') if current_config else 'unknown'
        logger.debug(f"[{request_id}] API: Using loaded model: '{model_name_for_log}'")

    try:
        full_path_obj = sanitize_path(request_data.file_path)
        source_path_abs_str = str(full_path_obj)
        if not full_path_obj.is_file():
            logger.error(
                f"[{request_id}] API: Audio file not found: {source_path_abs_str} (from '{request_data.file_path}')")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Audio file not found from '{request_data.file_path}'")
        logger.debug(f"[{request_id}] API: Accessing audio: {source_path_abs_str}")

        start_decode = time.time()
        try:
            audio_input = decode_audio(source_path_abs_str, sampling_rate=16000)
            logger.info(f"[{request_id}] Decoded audio in {time.time() - start_decode:.2f}s.")
        except Exception as de:
            logger.error(f"[{request_id}] Failed to decode: {source_path_abs_str}", exc_info=True); raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Decode failed: {str(de)}")

        temp_param = params.temperature
        if not isinstance(temp_param, (list, tuple)): temp_param = [float(temp_param)]
        clip_timestamps_param = _parse_clip_timestamps_standard(params.clip_timestamps)
        vad_options_dict = _validate_vad_params(params.vad_parameters)
        _suppress_tokens_processed = params.suppress_tokens
        if _suppress_tokens_processed and -1 in _suppress_tokens_processed:
            try:
                from faster_whisper.tokenizer import Tokenizer
                tokenizer = Tokenizer(active_model_ref.hf_tokenizer, active_model_ref.model.is_multilingual,
                                      task=params.task, language=params.language)
                non_speech = list(tokenizer.non_speech_tokens);
                user_set = [t for t in _suppress_tokens_processed if t >= 0 and isinstance(t, int)]
                _suppress_tokens_processed = sorted(list(set(user_set + non_speech)))
                logger.debug(f"[{request_id}] Suppressing (incl. non-speech): {_suppress_tokens_processed or 'None'}")
            except Exception as e_tok:
                logger.error(f"[{request_id}] Error suppress_tokens: {e_tok}", exc_info=True); raise HTTPException(
                    status_code=500, detail="Internal error on suppress_tokens.")
        elif _suppress_tokens_processed:
            _suppress_tokens_processed = sorted(list(set(int(t) for t in _suppress_tokens_processed if
                                                         t >= 0 and isinstance(t,
                                                                               int))));_suppress_tokens_processed = _suppress_tokens_processed or None
        else:
            _suppress_tokens_processed = None

        transcribe_args = params.dict(exclude={'vad_parameters', 'clip_timestamps', 'suppress_tokens', 'temperature'})
        transcribe_args.update({'vad_parameters': vad_options_dict, 'clip_timestamps': clip_timestamps_param,
                                'suppress_tokens': _suppress_tokens_processed, 'temperature': temp_param})
        logger.debug(f"[{request_id}] Prepared transcribe params.")

        async def generate_transcription_stream():
            nonlocal source_path_abs_str;
            tx_start = time.time();
            seg_count = 0
            try:
                logger.info(f"[{request_id}] Starting stream for {source_path_abs_str}...")
                segments_iter, info_obj = active_model_ref.transcribe(audio=audio_input, **transcribe_args)
                info_data = info_obj.__dict__.copy()  # Make a copy
                if hasattr(info_obj, 'transcription_options') and info_obj.transcription_options: info_data[
                    "transcription_options"] = info_obj.transcription_options.__dict__
                if hasattr(info_obj, 'vad_options') and info_obj.vad_options: info_data[
                    "vad_options"] = info_obj.vad_options if isinstance(info_obj.vad_options,
                                                                        dict) else info_obj.vad_options.__dict__
                yield json.dumps({"type": "info", "data": info_data}) + "\n"
                for segment in segments_iter:
                    seg_count += 1;
                    seg_data = segment.__dict__.copy()
                    if segment.words: seg_data["words"] = [w.__dict__ for w in segment.words]
                    yield json.dumps({"type": "segment", "data": seg_data}) + "\n"
                logger.info(f"[{request_id}] Stream finished in {time.time() - tx_start:.2f}s. Segments: {seg_count}.")
                yield json.dumps({"type": "final", "message": "Transcription complete."}) + "\n"
            except Exception as e_stream:
                logger.error(f"[{request_id}] Stream error for {source_path_abs_str}: {e_stream}",
                             exc_info=True); yield json.dumps(
                    {"type": "error", "message": f"Stream error: {traceback.format_exc()}"}) + "\n"
            finally:
                cleanup_audio_source(source_path_abs_str)

        return StreamingResponse(generate_transcription_stream(), media_type="application/x-ndjson")
    except HTTPException:
        cleanup_audio_source(source_path_abs_str); raise
    except ValueError as ve:
        logger.error(f"[{request_id}] Input error: {ve}", exc_info=True); cleanup_audio_source(
            source_path_abs_str); raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e_gen:
        logger.error(f"[{request_id}] General error: {e_gen}", exc_info=True); cleanup_audio_source(
            source_path_abs_str); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                      detail=f"Unexpected error: {str(e_gen)}")


@app.post("/transcribe_batched", summary="Transcribe audio using the currently loaded model's batched pipeline")
async def api_transcribe_batched(request_data: BatchedTranscribeRequest = Body(...)):
    active_pipeline_ref: Optional[BatchedInferencePipeline] = None
    active_model_for_tokenizer_ref: Optional[WhisperModel] = None
    source_path_abs_str: Optional[str] = None
    params = request_data.params;
    request_id = f"batch-txn-{time.time_ns()}"
    logger.info(f"[{request_id}] API: Batched transcribe req for client file: '{request_data.file_path}'")

    async with model_lock:
        if not (current_batched_pipeline and current_model):
            logger.error(f"[{request_id}] API: Batched tx failed - No model/pipeline loaded.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="No model/pipeline. Use /load_model first.")
        active_pipeline_ref = current_batched_pipeline
        active_model_for_tokenizer_ref = current_model
        model_name = current_config.get('model_size_or_path', 'unknown') if current_config else 'unknown'
        logger.debug(f"[{request_id}] API: Using loaded batched pipeline for model: '{model_name}'")
    try:
        full_path_obj = sanitize_path(request_data.file_path)
        source_path_abs_str = str(full_path_obj)
        if not full_path_obj.is_file(): logger.error(
            f"[{request_id}] API: Audio file not found: {source_path_abs_str} (from '{request_data.file_path}')"); raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Audio file not found from '{request_data.file_path}'")
        logger.debug(f"[{request_id}] API: Accessing audio: {source_path_abs_str}")
        start_decode = time.time()
        try:
            audio_input = decode_audio(source_path_abs_str, sampling_rate=16000); logger.info(
                f"[{request_id}] Decoded audio in {time.time() - start_decode:.2f}s.")
        except Exception as de:
            logger.error(f"[{request_id}] Failed to decode: {source_path_abs_str}", exc_info=True); raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Decode failed: {str(de)}")

        temp_param = params.temperature
        if not isinstance(temp_param, (list, tuple)): temp_param = [float(temp_param)]
        vad_options_dict = _validate_vad_params(params.vad_parameters)
        _suppress_tokens_processed = params.suppress_tokens
        if _suppress_tokens_processed and -1 in _suppress_tokens_processed:
            try:
                from faster_whisper.tokenizer import Tokenizer
                tokenizer = Tokenizer(active_model_for_tokenizer_ref.hf_tokenizer,
                                      active_model_for_tokenizer_ref.model.is_multilingual, task=params.task,
                                      language=params.language)
                non_speech = list(tokenizer.non_speech_tokens);
                user_set = [t for t in _suppress_tokens_processed if t >= 0 and isinstance(t, int)]
                _suppress_tokens_processed = sorted(list(set(user_set + non_speech)))
            except Exception as e_tok_b:
                logger.error(f"[{request_id}] Error suppress_tokens_batched: {e_tok_b}",
                             exc_info=True); raise HTTPException(status_code=500,
                                                                 detail="Internal error on suppress_tokens.")
        elif _suppress_tokens_processed:
            _suppress_tokens_processed = sorted(list(set(int(t) for t in _suppress_tokens_processed if
                                                         t >= 0 and isinstance(t,
                                                                               int)))); _suppress_tokens_processed = _suppress_tokens_processed or None
        else:
            _suppress_tokens_processed = None

        pipeline_call_args = {k: v for k, v in params.dict(exclude_none=True).items() if
                              k not in ['vad_parameters', 'temperature', 'suppress_tokens']}
        pipeline_call_args.update({'vad_parameters': vad_options_dict, 'temperature': temp_param,
                                   'suppress_tokens': _suppress_tokens_processed})
        logger.debug(f"[{request_id}] Prepared batched transcribe params. Batch size: {params.batch_size}")

        async def generate_batched_stream():
            nonlocal source_path_abs_str;
            tx_start = time.time();
            seg_count = 0
            try:
                logger.info(f"[{request_id}] Starting batched stream for {source_path_abs_str}...")
                segments_iter = active_pipeline_ref(audio=audio_input, **pipeline_call_args)
                yield json.dumps({"type": "info", "data": {"message": "Batched processing started.",
                                                           "parameters_used": {k: v for k, v in
                                                                               pipeline_call_args.items() if
                                                                               k != 'vad_parameters' or v is not None}}}) + "\n"  # Avoid logging large VAD params unless needed
                for segment in segments_iter:
                    seg_count += 1;
                    seg_data = segment.__dict__.copy()
                    if segment.words: seg_data["words"] = [w.__dict__ for w in segment.words]
                    yield json.dumps({"type": "segment", "data": seg_data}) + "\n"
                logger.info(
                    f"[{request_id}] Batched stream finished in {time.time() - tx_start:.2f}s. Segments: {seg_count}.")
                yield json.dumps({"type": "final", "message": "Batched transcription complete."}) + "\n"
            except Exception as e_stream_b:
                logger.error(f"[{request_id}] Batched stream error for {source_path_abs_str}: {e_stream_b}",
                             exc_info=True); yield json.dumps(
                    {"type": "error", "message": f"Batched stream error: {traceback.format_exc()}"}) + "\n"
            finally:
                cleanup_audio_source(source_path_abs_str)

        return StreamingResponse(generate_batched_stream(), media_type="application/x-ndjson")
    except HTTPException:
        cleanup_audio_source(source_path_abs_str); raise
    except ValueError as ve_b:
        logger.error(f"[{request_id}] Input error: {ve_b}", exc_info=True); cleanup_audio_source(
            source_path_abs_str); raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve_b))
    except Exception as e_gen_b:
        logger.error(f"[{request_id}] General error: {e_gen_b}", exc_info=True); cleanup_audio_source(
            source_path_abs_str); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                      detail=f"Unexpected error: {str(e_gen_b)}")


@app.post("/detect_language", summary="Detect language using the currently loaded model", response_model=Dict)
async def api_detect_language(request_data: DetectLanguageRequest = Body(...)):
    active_model_ref: Optional[WhisperModel] = None
    source_path_abs_str: Optional[str] = None
    params = request_data;
    request_id = f"lang-{time.time_ns()}"
    logger.info(f"[{request_id}] API: Lang detect req for client file: '{params.file_path}'")

    async with model_lock:
        if current_model is None: logger.error(
            f"[{request_id}] API: Lang detect failed - No model loaded."); raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="No model loaded.")
        active_model_ref = current_model
        if not active_model_ref.model.is_multilingual:
            model_name = current_config.get('model_size_or_path', 'unknown') if current_config else 'unknown'
            logger.warning(f"[{request_id}] API: Lang detect skipped: Model '{model_name}' is English-only.")
            return JSONResponse(
                content={"language": "en", "language_probability": 1.0, "all_language_probs": {"en": 1.0},
                         "message": f"Model ({model_name}) is English-only."})
        logger.debug(f"[{request_id}] API: Using multilingual model for detection.")
    try:
        full_path_obj = sanitize_path(params.file_path)
        source_path_abs_str = str(full_path_obj)
        if not full_path_obj.is_file(): logger.error(
            f"[{request_id}] API: Audio file not found: {source_path_abs_str} (from '{params.file_path}')"); raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Audio file not found from '{params.file_path}'")
        logger.debug(f"[{request_id}] API: Accessing audio: {source_path_abs_str}")
        start_decode = time.time()
        try:
            audio_input = decode_audio(source_path_abs_str, sampling_rate=16000); logger.info(
                f"[{request_id}] Decoded audio in {time.time() - start_decode:.2f}s.")
        except Exception as de_l:
            logger.error(f"[{request_id}] Failed to decode: {source_path_abs_str}", exc_info=True); raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Decode failed: {str(de_l)}")

        vad_options_dict = _validate_vad_params(params.vad_parameters)
        detect_args = params.dict(exclude={'file_path', 'vad_parameters'})
        detect_args['vad_parameters'] = vad_options_dict
        detect_args = {k: v for k, v in detect_args.items() if v is not None}  # Ensure no None values for kwargs
        logger.debug(f"[{request_id}] Detect language args: {detect_args}")
        detect_start_time = time.time()
        try:
            detection_result_tuple = active_model_ref.detect_language(audio=audio_input, **detect_args)
            lang, prob = detection_result_tuple[0:2] if detection_result_tuple and len(
                detection_result_tuple) >= 2 else (None, None)
            all_probs = detection_result_tuple[2] if detection_result_tuple and len(
                detection_result_tuple) > 2 else None
            logger.info(
                f"[{request_id}] Lang detect completed in {time.time() - detect_start_time:.2f}s. Detected: {lang} (Prob: {prob:.4f if prob is not None else 'N/A'})")
            return JSONResponse(content={"language": lang, "language_probability": prob,
                                         "all_language_probs": all_probs if all_probs is not None else {}})
        except Exception as detect_err:
            logger.error(f"[{request_id}] Error in detect_language for {source_path_abs_str}.",
                         exc_info=True); raise HTTPException(status_code=500,
                                                             detail=f"Language detection failed: {str(detect_err)}")
    except HTTPException:
        cleanup_audio_source(source_path_abs_str); raise
    except ValueError as ve_l:
        logger.error(f"[{request_id}] Input error: {ve_l}", exc_info=True); cleanup_audio_source(
            source_path_abs_str); raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve_l))
    except Exception as e_gen_l:
        logger.error(f"[{request_id}] General error: {e_gen_l}", exc_info=True); cleanup_audio_source(
            source_path_abs_str); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                      detail=f"Unexpected error: {str(e_gen_l)}")


@app.websocket("/ws/logs")
async def websocket_log_endpoint(websocket: WebSocket):
    await websocket.accept()
    log_websockets.add(websocket)
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown client"
    # Use logger if available, otherwise print
    log_func = logger.info if logger else lambda msg: print(f"[{APP_LOGGER_NAME}] {msg}")
    log_func(f"Log WebSocket client connected: {client_info}")
    try:
        while True: await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect as e:
        log_func(f"Log WebSocket client disconnected: {client_info}. Code: {e.code}, Reason: {e.reason or 'N/A'}")
    except Exception as e_ws:
        if logger:
            logger.error(f"Log WebSocket error for {client_info}: {e_ws}", exc_info=True)
        else:
            print(f"[{APP_LOGGER_NAME}] Log WebSocket error for {client_info}: {e_ws}\n{traceback.format_exc()}")
    finally:
        if websocket in log_websockets: log_websockets.remove(websocket)
        log_func(f"Log WebSocket connection closed for {client_info}. Active: {len(log_websockets)}")


# --- Main Execution Block (for Uvicorn run from CMD in Dockerfile) ---
if __name__ == "__main__":
    import uvicorn

    print(f"---- STT Service: Preparing to Start (via __main__, usually for local dev testing) ----")
    print(f"ENV HOST: {APP_HOST} (Uvicorn will bind here)")
    print(f"ENV PORT: {APP_PORT} (Uvicorn will bind here)")
    print(f"ENV LOG_LEVEL: {LOG_LEVEL}")
    print(f"FIXED Internal Shared Audio Path: {SHARED_AUDIO_PATH}")
    print(f"FIXED Internal Model Cache Path: {MODEL_CACHE_PATH}")
    print(f"Audio Cleanup Enabled (from ENV '{ENV_CLEANUP_AUDIO}'): {SHOULD_CLEANUP_AUDIO}")
    print(f"---------------------------------------------------------------------------------")

    uvicorn.run(
        "main:app",  # app instance in main.py
        host=APP_HOST,
        port=APP_PORT,
        workers=1,  # Crucial for stateful model management
        log_config=None,  # Our logging_config.py handles it
        reload=False,  # Should be False for this on-demand container model
        log_level=LOG_LEVEL.lower()  # Pass log level to Uvicorn as well
    )