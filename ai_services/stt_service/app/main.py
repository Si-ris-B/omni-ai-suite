# main.py
import os
import time
import asyncio
import json
import traceback
import gc
from typing import Optional, List, Union,  Iterable,  Dict
from pathlib import Path

# --- FastAPI and Related Imports ---
from fastapi import (
    FastAPI, HTTPException, Body, status, WebSocket, WebSocketDisconnect
)
# from fastapi.security.api_key import APIKeyHeader # REMOVED
from fastapi.responses import StreamingResponse, JSONResponse

# --- Faster Whisper Imports ---
# REMOVED VadOptions from this import
from faster_whisper import WhisperModel, BatchedInferencePipeline
from faster_whisper.audio import decode_audio
# from faster_whisper.tokenizer import Tokenizer # Needed for suppress_tokens=-1

# --- Pydantic for Validation ---
from pydantic import BaseModel, Field
import numpy as np

# --- Logging Setup ---
from logging_config import setup_logging,  log_websockets # Import necessary items
logger = None # Will be initialized in startup

# --- Global State Variables ---
current_model: Optional[WhisperModel] = None
current_config: Optional[Dict] = None
current_batched_pipeline: Optional[BatchedInferencePipeline] = None
model_lock = asyncio.Lock() # Lock to protect loading/unloading/accessing model state

# --- Configuration Paths (from Environment or Defaults) ---
SHARED_AUDIO_PATH = Path(os.getenv("SHARED_AUDIO_PATH", "/shared_audio"))
MODEL_CACHE_PATH = Path(os.getenv("MODEL_CACHE_PATH", "/models"))

# --- API Key Configuration & Dependency REMOVED ---

# --- Pydantic Models (Unchanged Structurally) ---
class ModelConfigParams(BaseModel):
    model_size_or_path: str = Field(..., description="Model name, HF ID, or local path")
    device: str = Field("cpu")
    compute_type: str = Field("default")
    device_index: Union[int, List[int]] = Field(0)
    cpu_threads: int = Field(0)
    num_workers: int = Field(1)

class VADParams(BaseModel): threshold: Optional[float]=0.5; min_speech_duration_ms: Optional[int]=250; max_speech_duration_s: Optional[float]=float('inf'); min_silence_duration_ms: Optional[int]=2000; window_size_samples: Optional[int]=1024; speech_pad_ms: Optional[int]=400
class BatchedVADParams(VADParams): min_silence_duration_ms: Optional[int]=160; max_speech_duration_s: Optional[float]=None

class StandardTranscriptionParams(BaseModel): language: Optional[str]=None; task: str="transcribe"; beam_size: int=5; best_of: int=5; patience: float=1.0; length_penalty: float=1.0; repetition_penalty: float=1.0; no_repeat_ngram_size: int=0; temperature: Union[float, List[float]]=Field(default=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]); compression_ratio_threshold: Optional[float]=2.4; log_prob_threshold: Optional[float]=-1.0; no_speech_threshold: Optional[float]=0.6; condition_on_previous_text: bool=True; prompt_reset_on_temperature: float=0.5; initial_prompt: Optional[Union[str, Iterable[int]]]=None; prefix: Optional[str]=None; suppress_blank: bool=True; suppress_tokens: Optional[List[int]]=Field(default=[-1]); without_timestamps: bool=False; max_initial_timestamp: float=1.0; word_timestamps: bool=False; prepend_punctuations: str="\"'“¿([{-"; append_punctuations: str="\"'.。,，!！?？:：”)]}、"; vad_filter: bool=False; vad_parameters: Optional[VADParams]=None; max_new_tokens: Optional[int]=None; clip_timestamps: str="0"; hallucination_silence_threshold: Optional[float]=None; hotwords: Optional[str]=None; language_detection_threshold: Optional[float]=0.5; language_detection_segments: int=1
class BatchedTranscriptionParams(BaseModel): language: Optional[str]=None; task: str="transcribe"; beam_size: int=5; patience: float=1.0; length_penalty: float=1.0; repetition_penalty: float=1.0; no_repeat_ngram_size: int=0; temperature: Union[float, List[float]]=Field(default=[0.0]); initial_prompt: Optional[Union[str, Iterable[int]]]=None; suppress_blank: bool=True; suppress_tokens: Optional[List[int]]=Field(default=[-1]); without_timestamps: bool=True; word_timestamps: bool=False; prepend_punctuations: str="\"'“¿([{-"; append_punctuations: str="\"'.。,，!！?？:：”)]}、"; multilingual: bool=False; vad_filter: bool=True; vad_parameters: Optional[BatchedVADParams]=None; max_new_tokens: Optional[int]=None; chunk_length: Optional[int]=None; clip_timestamps: Optional[List[Dict[str, float]]]=None; batch_size: int=8; hotwords: Optional[str]=None; language_detection_threshold: Optional[float]=0.5; language_detection_segments: int=1

class TranscribeRequest(BaseModel): params: StandardTranscriptionParams; file_path: str = Field(...)
class BatchedTranscribeRequest(BaseModel): params: BatchedTranscriptionParams; file_path: str = Field(...)
class DetectLanguageRequest(BaseModel): vad_filter: bool=False; vad_parameters: Optional[VADParams]=None; language_detection_segments: int=1; language_detection_threshold: float=0.5; file_path: str = Field(...)

# --- FastAPI Application Instance ---
app = FastAPI(
    title="Stateful Faster Whisper Service (Local, No API Key)",
    description="API service (no API Key) to dynamically load/unload Whisper models and process audio via shared paths.",
    version="1.2.2" # Version bump for fix
)

# --- Lifespan Events ---
@app.on_event("startup")
async def startup_event():
    global logger
    logger = setup_logging()
    logger.info(f"---- Starting Stateful Whisper Service (PID: {os.getpid()}) ----")
    logger.info(f"Shared audio path: {SHARED_AUDIO_PATH.resolve()}")
    logger.info(f"Model cache path: {MODEL_CACHE_PATH.resolve()}")
    try:
        SHARED_AUDIO_PATH.mkdir(parents=True, exist_ok=True)
        MODEL_CACHE_PATH.mkdir(parents=True, exist_ok=True)
    except Exception as e: logger.error(f"Directory setup error: {e}")
    logger.info("Service started IDLE.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.warning("---- Service Shutting Down ----")
    async with model_lock: await _unload_model_internal()
    logger.info("Service stopped.")

# --- Internal Model Management (Torch references REMOVED) ---
async def _unload_model_internal():
    global current_model, current_config, current_batched_pipeline
    if current_model is not None:
        model_info = f"{current_config.get('model_size_or_path','?')} ({current_config.get('device','?')})"
        logger.warning(f"Unloading model: {model_info}")
        # Explicitly delete references and run garbage collection
        model_ref = current_model
        batch_ref = current_batched_pipeline
        current_model = None
        current_config = None
        current_batched_pipeline = None
        del model_ref
        del batch_ref
        gc.collect() # Suggest garbage collection
        # REMOVED torch.cuda.empty_cache() block
        logger.info(f"Model {model_info} unloaded.")
        await asyncio.sleep(0.1) # Short sleep to allow potential cleanup

async def _load_model_internal(config: ModelConfigParams):
    global current_model, current_config, current_batched_pipeline
    logger.warning(f"Attempting to load model: {config.dict()}")
    start_time = time.time()
    try:
        if not MODEL_CACHE_PATH.exists(): MODEL_CACHE_PATH.mkdir(parents=True, exist_ok=True)
        loaded_model = WhisperModel(**config.dict(), download_root=str(MODEL_CACHE_PATH)) # Pass config directly
        # Create batched pipeline AFTER successful model load
        loaded_batched_pipeline = BatchedInferencePipeline(model=loaded_model)
        current_model = loaded_model
        current_batched_pipeline = loaded_batched_pipeline # Assign batched pipeline here
        current_config = config.dict()
        load_time = time.time() - start_time
        logger.warning(f"Successfully loaded model '{config.model_size_or_path}' and pipeline in {load_time:.2f}s.")
    except Exception as e:
        logger.exception(f"FATAL: Failed to load model '{config.model_size_or_path}': {e}")
        # Reset state if loading failed
        current_model = None; current_config = None; current_batched_pipeline = None
        # Attempt cleanup if load fails midway
        gc.collect()
        # REMOVED torch.cuda.empty_cache() block
        raise # Re-raise the original loading error

# --- Helper Functions (VadOptions type hint FIXED) ---
def sanitize_path(relative_path: str) -> Path:
    if not relative_path:
        raise ValueError("File path cannot be empty.")
    # Normalize path, remove leading slashes/backslashes for consistency
    normalized_path = os.path.normpath(relative_path).lstrip('/\\')
    # Prevent path traversal ('..')
    if ".." in normalized_path.split(os.sep):
        raise ValueError("Relative paths ('..') are forbidden.")
    # Join with the base shared path
    full_path = SHARED_AUDIO_PATH.resolve().joinpath(normalized_path)
    # Robust check: ensure the final resolved path is truly within the shared directory
    if not full_path.is_relative_to(SHARED_AUDIO_PATH.resolve()):
         raise ValueError("Path traversal attempt detected outside designated shared directory.")
    return full_path

def cleanup_audio_source(source_path: Optional[str]):
    # Set to False if Django *guarantees* cleanup, True if FastAPI should attempt it
    SHOULD_FASTAPI_CLEANUP = True # Or False, depending on deployment strategy
    if not SHOULD_FASTAPI_CLEANUP or not source_path:
        return
    try:
        path_obj = Path(source_path)
        if path_obj.is_file():
            logger.info(f"FastAPI attempting to clean up source audio: {source_path}")
            path_obj.unlink()
        # else: logger.debug(f"Cleanup skipped: path not found or not a file: {source_path}")
    except Exception as e:
        # Log error but don't raise, cleanup is best-effort
        logger.error(f"FastAPI cleanup failed for path '{source_path}': {e}")

# --- FIXED TYPE HINT for vad_parameters dictionary ---
def _validate_vad_params(params: Optional[Union[VADParams, BatchedVADParams]]) -> Optional[dict]:
    """Validates VAD parameters Pydantic model and returns a dictionary suitable for faster-whisper."""
    if params is None:
        return None
    # Convert Pydantic model to dict, excluding fields that were not explicitly set
    vad_dict = params.dict(exclude_unset=True)

    # Specific adjustment for BatchedVADParams: remove 'max_speech_duration_s' if it's infinite,
    # as faster-whisper might expect it absent or None in this case.
    if isinstance(params, BatchedVADParams) and 'max_speech_duration_s' in vad_dict and vad_dict['max_speech_duration_s'] == float('inf'):
         del vad_dict['max_speech_duration_s']

    # Could add more validation here if needed (e.g., check ranges)
    # For now, rely on Pydantic and faster-whisper internal validation primarily.

    return vad_dict # Return the validated dictionary

def _parse_clip_timestamps_standard(clip_timestamps_str: str) -> str:
    """Validates the clip_timestamps string format."""
    if clip_timestamps_str == "0":
        return "0"
    try:
        parts = clip_timestamps_str.split(',')
        if not parts or not all(part.strip() for part in parts): # Ensure no empty parts
             raise ValueError("Empty timestamp value found.")
        # Validate that all parts can be converted to float
        [float(ts.strip()) for ts in parts]
        # Return the validated string as is; faster-whisper handles the internal parsing.
        return clip_timestamps_str
    except ValueError as e:
        logger.error(f"Invalid format for clip_timestamps: '{clip_timestamps_str}'. Error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid clip_timestamps format. Expected comma-separated numbers (e.g., '10.5,25') or '0'. Received: '{clip_timestamps_str}'")

# --- API Endpoints (Unchanged logic, relying on corrected helpers) ---

@app.get("/status", summary="Get Service Status")
async def get_status():
    # No auth needed
    async with model_lock:
        # Return a copy to prevent modification of the internal state dict
        status_data = {
            "status": "loaded" if current_model else "idle",
            "config": current_config.copy() if current_config else None
        }
    return status_data

@app.post("/load_model", summary="Load Whisper Model", status_code=status.HTTP_200_OK)
async def api_load_model(config: ModelConfigParams = Body(...)):
    # No auth needed
    request_id = f"load-{time.time_ns()}"
    logger.info(f"[{request_id}] Received request to load model: {config.model_size_or_path} with config: {config.dict()}")
    async with model_lock:
        # Check if the exact same configuration is already loaded
        if current_config and current_config == config.dict():
             logger.warning(f"[{request_id}] Model '{config.model_size_or_path}' with the exact same configuration is already loaded. No action taken.")
             return JSONResponse(
                 status_code=status.HTTP_200_OK, # Indicate success, but note it was already loaded
                 content={"status": "success", "message": "Model with this configuration already loaded.", "config": current_config.copy()}
             )

        # Proceed with loading (unload previous first if necessary)
        logger.info(f"[{request_id}] Acquiring lock to change model state...")
        try:
            if current_model:
                logger.info(f"[{request_id}] Unloading existing model before loading the new one.")
                await _unload_model_internal() # Unload previous if any
            else:
                 logger.info(f"[{request_id}] No model currently loaded, proceeding with load.")

            await _load_model_internal(config)
            logger.info(f"[{request_id}] Successfully completed load request.")
            return {"status": "success", "message": "Model loaded successfully.", "config": current_config.copy()}
        except Exception as e:
            # Error logged within _load_model_internal
            logger.error(f"[{request_id}] Model loading process failed.")
            # Return 500 Internal Server Error
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Model load failed: {str(e)}")

@app.post("/unload_model", summary="Unload Whisper Model")
async def api_unload_model():
    # No auth needed
    request_id = f"unload-{time.time_ns()}"
    logger.info(f"[{request_id}] Received request to unload model.")
    async with model_lock:
        if current_model is None:
             logger.info(f"[{request_id}] No model is currently loaded. Unload request is a no-op.")
             return {"status": "success", "message": "Already idle. No model was loaded."}
        try:
            logger.info(f"[{request_id}] Acquiring lock to unload model.")
            await _unload_model_internal()
            logger.info(f"[{request_id}] Successfully unloaded model.")
            return {"status": "success", "message": "Model unloaded successfully."}
        except Exception as e:
            logger.exception(f"[{request_id}] Failed during model unloading process.")
            raise HTTPException(status_code=500, detail=f"Model unload failed: {str(e)}")

@app.post("/transcribe", summary="Transcribe Audio (Standard)")
async def api_transcribe(request_data: TranscribeRequest = Body(...)):
    # No auth needed
    active_model: Optional[WhisperModel] = None # Hold reference to model used for this request
    source_path_str: Optional[str] = None # Store sanitized path string for reliable cleanup
    params = request_data.params
    request_id = f"txn-{time.time_ns()}" # Simple unique ID for logging this request
    logger.info(f"[{request_id}] Received standard transcribe request for file: '{request_data.file_path}'")

    # --- Acquire Lock and Check Model State ---
    async with model_lock:
        if current_model is None:
            logger.error(f"[{request_id}] Transcription failed: No model loaded.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No model is currently loaded. Use /load_model first.")
        # Keep a reference to the model being used for this request
        active_model = current_model
        active_config = current_config.copy() # Get config at time of request
        logger.debug(f"[{request_id}] Using model: {active_config.get('model_size_or_path', 'unknown')}")
    # --- Lock Released ---

    try:
        # 1. Sanitize and Validate Input File Path
        full_path_obj = sanitize_path(request_data.file_path)
        source_path_str = str(full_path_obj) # Use this string path consistently
        if not full_path_obj.is_file():
            logger.error(f"[{request_id}] Audio file not found at sanitized path: {source_path_str}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audio file not found at specified path: '{request_data.file_path}'")
        logger.debug(f"[{request_id}] Accessing sanitized audio path: {source_path_str}")

        # 2. Decode Audio File
        start_decode = time.time()
        try:
            # Expecting decode_audio to return a numpy array
            audio_input = decode_audio(source_path_str, sampling_rate=16000)
            decode_time = time.time() - start_decode
            logger.info(f"[{request_id}] Decoded audio in {decode_time:.2f}s. Type: {type(audio_input)}, Shape: {getattr(audio_input, 'shape', 'N/A')}")
            if not isinstance(audio_input, np.ndarray):
                 logger.warning(f"[{request_id}] decode_audio did not return a NumPy array (type: {type(audio_input)}). Behavior may be unexpected.")
        except Exception as decode_err:
            logger.exception(f"[{request_id}] Failed to decode audio file: {source_path_str}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to decode audio file: {str(decode_err)}")


        # 3. Prepare Transcription Parameters
        start_prep = time.time()
        # Validate temperature format
        temp_param = params.temperature
        if not isinstance(temp_param, (list, tuple)):
            try: temp_param = [float(temp_param)]
            except ValueError:
                logger.error(f"[{request_id}] Invalid temperature value: {params.temperature}")
                raise HTTPException(status_code=400, detail=f"Invalid temperature value: {params.temperature}")

        # Validate clip timestamps format
        clip_timestamps_param = _parse_clip_timestamps_standard(params.clip_timestamps)

        # Get VAD parameters dictionary
        vad_options_dict = _validate_vad_params(params.vad_parameters)

        # Handle suppress_tokens, including resolving '-1' to non-speech tokens
        _suppress_tokens_processed = params.suppress_tokens
        if -1 in (_suppress_tokens_processed or []):
             try:
                 from faster_whisper.tokenizer import Tokenizer # Import here if not globally needed
                 # Use the tokenizer associated with the *active* model instance
                 tokenizer = Tokenizer(active_model.hf_tokenizer,
                                       active_model.model.is_multilingual,
                                       task=params.task,
                                       language=params.language) # Use specified language if available
                 non_speech_tokens = list(tokenizer.non_speech_tokens) # Convert tuple to list
                 # Combine user's non-negative tokens with non-speech tokens
                 user_tokens = [t for t in params.suppress_tokens if t >= 0]
                 _suppress_tokens_processed = sorted(list(set(user_tokens + non_speech_tokens)))
                 logger.debug(f"[{request_id}] Suppressing tokens (incl. non-speech): {_suppress_tokens_processed}")
             except ImportError:
                 logger.error(f"[{request_id}] Tokenizer import failed. Cannot process suppress_tokens=-1.")
                 raise HTTPException(status_code=500, detail="Internal error: Tokenizer component not available.")
             except Exception as e:
                 logger.exception(f"[{request_id}] Error processing suppress_tokens with Tokenizer: {e}")
                 raise HTTPException(status_code=500, detail=f"Internal error processing suppress_tokens: {e}")
        elif _suppress_tokens_processed is not None:
            # Ensure it's a list of ints if provided but not containing -1
             _suppress_tokens_processed = sorted(list(set(int(t) for t in _suppress_tokens_processed if t>=0)))
             logger.debug(f"[{request_id}] Suppressing user-defined tokens: {_suppress_tokens_processed}")
        else:
             logger.debug(f"[{request_id}] No tokens explicitly suppressed.")
             _suppress_tokens_processed = None # Ensure it's None if empty or originally None

        # Collect final arguments for the transcribe call, excluding handled ones
        transcribe_args = params.dict(
            exclude={'vad_parameters', 'clip_timestamps', 'suppress_tokens', 'temperature'}
        )
        # Add back the processed/validated parameters
        transcribe_args['vad_parameters'] = vad_options_dict
        transcribe_args['clip_timestamps'] = clip_timestamps_param
        transcribe_args['suppress_tokens'] = _suppress_tokens_processed
        transcribe_args['temperature'] = temp_param # Use the validated list/tuple

        prep_time = time.time() - start_prep
        logger.info(f"[{request_id}] Prepared transcription parameters in {prep_time:.2f}s.")
        # Avoid logging potentially sensitive initial_prompt unless debug level is very high
        # logger.debug(f"[{request_id}] Final transcribe args (excluding audio): {transcribe_args}")

        # 4. Define Async Generator for Streaming Response
        async def generate_transcription():
            # Ensure cleanup uses the path string captured before potential errors
            nonlocal source_path_str
            transcribe_start_time = time.time()
            segment_count = 0
            try:
                logger.info(f"[{request_id}] Starting transcription process...")
                # Call the transcribe method on the *active_model* reference
                segments_iterable, info = active_model.transcribe(audio=audio_input, **transcribe_args)

                # Serialize and yield transcription info first
                info_dict = info.__dict__.copy() # Make a copy to avoid modifying the original
                # Convert nested option objects (dataclasses) to dictionaries for JSON serialization
                if hasattr(info, 'transcription_options') and info.transcription_options:
                    info_dict["transcription_options"] = info.transcription_options.__dict__
                if hasattr(info, 'vad_options') and info.vad_options:
                     # vad_options might be a dict or an internal object, handle appropriately
                     info_dict["vad_options"] = info.vad_options if isinstance(info.vad_options, dict) else info.vad_options.__dict__

                yield json.dumps({"type": "info", "data": info_dict}) + "\n"
                logger.debug(f"[{request_id}] Yielded info: Lang={info.language}, Duration={info.duration:.2f}s")

                # Iterate through the segments generator/iterable returned by transcribe
                for segment in segments_iterable:
                    segment_count += 1
                    segment_dict = segment.__dict__.copy()
                    # Convert word timestamps list (if present) to list of dicts
                    if segment.words:
                        segment_dict["words"] = [w.__dict__ for w in segment.words]
                    yield json.dumps({"type": "segment", "data": segment_dict}) + "\n"
                    # Optional small sleep to yield control, test under load if needed
                    # await asyncio.sleep(0.001)

                transcribe_time = time.time() - transcribe_start_time
                logger.info(f"[{request_id}] Transcription finished in {transcribe_time:.2f}s. Yielded {segment_count} segments.")
                yield json.dumps({"type": "final", "message": "Transcription complete."}) + "\n"

            except Exception as e_stream:
                logger.exception(f"[{request_id}] Error during transcription stream generation: {e_stream}")
                # Yield a JSON error message
                yield json.dumps({"type": "error", "message": f"Transcription stream error: {traceback.format_exc()}"}) + "\n"
            finally:
                # Ensure cleanup runs regardless of stream success/failure
                logger.info(f"[{request_id}] Cleaning up audio source (if enabled): {source_path_str}")
                cleanup_audio_source(source_path_str)

        # 5. Return the Streaming Response
        return StreamingResponse(generate_transcription(), media_type="application/x-ndjson")

    # --- Error Handling for Setup Phase (before streaming starts) ---
    except HTTPException as http_exc:
        # Log known HTTP exceptions (like 404, 400, 409) before re-raising
        logger.error(f"[{request_id}] HTTP Exception during setup: {http_exc.status_code} - {http_exc.detail}")
        cleanup_audio_source(source_path_str) # Attempt cleanup on setup errors
        raise http_exc
    except ValueError as val_err: # Catch specific setup errors like path issues
        logger.error(f"[{request_id}] Value Error during setup: {val_err}")
        cleanup_audio_source(source_path_str)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e_setup:
        # Catch unexpected errors during setup (e.g., decoding, param prep)
        logger.exception(f"[{request_id}] Unexpected setup error before transcription: {e_setup}")
        cleanup_audio_source(source_path_str)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during transcription setup: {str(e_setup)}")

@app.post("/transcribe_batched", summary="Transcribe Audio (Batched)")
async def api_transcribe_batched(request_data: BatchedTranscribeRequest = Body(...)):
    # No auth needed
    active_batched_pipeline: Optional[BatchedInferencePipeline] = None
    active_model: Optional[WhisperModel] = None # Need model ref for tokenizer
    source_path_str: Optional[str] = None
    params = request_data.params
    request_id = f"batch-txn-{time.time_ns()}"
    logger.info(f"[{request_id}] Received batched transcribe request for file: '{request_data.file_path}'")

    # --- Acquire Lock and Check Model/Pipeline State ---
    async with model_lock:
        if current_batched_pipeline is None or current_model is None: # Need both pipeline and underlying model
            logger.error(f"[{request_id}] Batched transcription failed: Model or pipeline not loaded.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Batched pipeline requires a loaded model. Use /load_model first.")
        active_batched_pipeline = current_batched_pipeline
        active_model = current_model # Get reference to underlying model
        active_config = current_config.copy()
        logger.debug(f"[{request_id}] Using batched pipeline for model: {active_config.get('model_size_or_path', 'unknown')}")
    # --- Lock Released ---

    try:
        # 1. Sanitize and Validate Input File Path
        full_path_obj = sanitize_path(request_data.file_path)
        source_path_str = str(full_path_obj)
        if not full_path_obj.is_file():
            logger.error(f"[{request_id}] Audio file not found at sanitized path: {source_path_str}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audio file not found: '{request_data.file_path}'")
        logger.debug(f"[{request_id}] Accessing sanitized audio path: {source_path_str}")

        # 2. Decode Audio File
        start_decode = time.time()
        try:
            audio_input = decode_audio(source_path_str, sampling_rate=16000)
            decode_time = time.time() - start_decode
            logger.info(f"[{request_id}] Decoded audio in {decode_time:.2f}s. Type: {type(audio_input)}, Shape: {getattr(audio_input, 'shape', 'N/A')}")
            if not isinstance(audio_input, np.ndarray):
                 logger.warning(f"[{request_id}] decode_audio did not return NumPy array (type: {type(audio_input)}).")
        except Exception as decode_err:
             logger.exception(f"[{request_id}] Failed to decode audio file: {source_path_str}")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to decode audio file: {str(decode_err)}")


        # 3. Prepare Batched Transcription Parameters
        start_prep = time.time()
        # Validate temperature format
        temp_param = params.temperature
        if not isinstance(temp_param, (list, tuple)):
            try: temp_param = [float(temp_param)]
            except ValueError: raise HTTPException(status_code=400, detail=f"Invalid temperature: {params.temperature}")

        # Get VAD parameters dictionary (using BatchedVADParams model)
        vad_options_dict = _validate_vad_params(params.vad_parameters)

        # Handle suppress_tokens (needs tokenizer from the underlying model)
        _suppress_tokens_processed = params.suppress_tokens
        if -1 in (_suppress_tokens_processed or []):
             try:
                 from faster_whisper.tokenizer import Tokenizer
                 # Use tokenizer from the model associated with the *active* pipeline
                 tokenizer = Tokenizer(active_model.hf_tokenizer,
                                       active_model.model.is_multilingual,
                                       task=params.task, language=params.language)
                 non_speech_tokens = list(tokenizer.non_speech_tokens)
                 user_tokens = [t for t in params.suppress_tokens if t >= 0]
                 _suppress_tokens_processed = sorted(list(set(user_tokens + non_speech_tokens)))
                 logger.debug(f"[{request_id}] Suppressing tokens (incl. non-speech): {_suppress_tokens_processed}")
             except ImportError:
                 logger.error(f"[{request_id}] Tokenizer import failed for batched suppression.")
                 raise HTTPException(status_code=500, detail="Internal error: Tokenizer component not available.")
             except Exception as e:
                 logger.exception(f"[{request_id}] Error processing batched suppress_tokens: {e}")
                 raise HTTPException(status_code=500, detail=f"Internal error processing suppress_tokens: {e}")
        elif _suppress_tokens_processed is not None:
             _suppress_tokens_processed = sorted(list(set(int(t) for t in _suppress_tokens_processed if t>=0)))
             logger.debug(f"[{request_id}] Suppressing user-defined tokens: {_suppress_tokens_processed}")
        else:
             logger.debug(f"[{request_id}] No tokens explicitly suppressed for batch.")
             _suppress_tokens_processed = None


        # Collect final arguments for the batched pipeline call
        transcribe_args = params.dict(
            exclude={'vad_parameters', 'suppress_tokens', 'temperature'}
        )
        transcribe_args['vad_parameters'] = vad_options_dict
        transcribe_args['suppress_tokens'] = _suppress_tokens_processed
        transcribe_args['temperature'] = temp_param
        # Note: Batch size is handled by the pipeline itself based on params.batch_size

        prep_time = time.time() - start_prep
        logger.info(f"[{request_id}] Prepared batched transcription parameters in {prep_time:.2f}s.")
        # logger.debug(f"[{request_id}] Final batched transcribe args (excluding audio): {transcribe_args}")

        # 4. Define Async Generator for Streaming Response
        async def generate_transcription_batched():
            nonlocal source_path_str
            transcribe_start_time = time.time()
            segment_count = 0
            try:
                logger.info(f"[{request_id}] Starting batched transcription process...")
                # Call the batched pipeline (which might be synchronous internally)
                # The pipeline likely returns an iterable/list of results directly.
                # Check faster-whisper docs: BatchedInferencePipeline.__call__ returns an iterable of Segment objects.
                segments_iterable = active_batched_pipeline(audio=audio_input, **transcribe_args)

                # Yield a placeholder info message as batched pipeline doesn't return a separate info object
                yield json.dumps({"type": "info", "data": {"message": "Batched processing started.", "params": params.dict(exclude_unset=True)}}) + "\n"

                # Iterate through the results from the batched pipeline
                for segment in segments_iterable:
                    segment_count += 1
                    segment_dict = segment.__dict__.copy()
                    if segment.words:
                        segment_dict["words"] = [w.__dict__ for w in segment.words]
                    yield json.dumps({"type": "segment", "data": segment_dict}) + "\n"
                    # await asyncio.sleep(0.001) # Optional yield point if needed

                transcribe_time = time.time() - transcribe_start_time
                logger.info(f"[{request_id}] Batched transcription finished in {transcribe_time:.2f}s. Processed {segment_count} segments.")
                yield json.dumps({"type": "final", "message": "Batched transcription complete."}) + "\n"

            except Exception as e_stream:
                logger.exception(f"[{request_id}] Error during batched transcription stream: {e_stream}")
                yield json.dumps({"type": "error", "message": f"Batched transcription stream error: {traceback.format_exc()}"}) + "\n"
            finally:
                logger.info(f"[{request_id}] Cleaning up audio source (if enabled): {source_path_str}")
                cleanup_audio_source(source_path_str)

        # 5. Return Streaming Response
        return StreamingResponse(generate_transcription_batched(), media_type="application/x-ndjson")

    # --- Error Handling for Setup Phase ---
    except HTTPException as http_exc:
        logger.error(f"[{request_id}] HTTP Exception during setup: {http_exc.status_code} - {http_exc.detail}")
        cleanup_audio_source(source_path_str)
        raise http_exc
    except ValueError as val_err:
        logger.error(f"[{request_id}] Value Error during setup: {val_err}")
        cleanup_audio_source(source_path_str)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e_setup:
        logger.exception(f"[{request_id}] Unexpected setup error before batched transcription: {e_setup}")
        cleanup_audio_source(source_path_str)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during batched transcription setup: {str(e_setup)}")


@app.post("/detect_language", summary="Detect Audio Language")
async def api_detect_language(request_data: DetectLanguageRequest = Body(...)):
    # No auth needed
    active_model: Optional[WhisperModel] = None
    source_path_str: Optional[str] = None
    params = request_data
    request_id = f"lang-{time.time_ns()}"
    logger.info(f"[{request_id}] Received language detection request for file: '{params.file_path}'")

    # --- Acquire Lock and Check Model State ---
    async with model_lock:
        if current_model is None:
            logger.error(f"[{request_id}] Language detection failed: No model loaded.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No model is currently loaded.")
        # Check if the loaded model is multilingual *before* proceeding
        if not current_model.model.is_multilingual:
            loaded_model_name = current_config.get('model_size_or_path', 'unknown') if current_config else 'unknown'
            logger.warning(f"[{request_id}] Language detection skipped: Loaded model '{loaded_model_name}' is English-only.")
            # Return a consistent JSON response indicating English-only model
            cleanup_audio_source(None) # No file processed, so no cleanup needed here
            return JSONResponse(content={
                "language": "en",
                "language_probability": 1.0,
                "all_language_probs": {"en": 1.0},
                "message": f"Detection skipped: Loaded model ({loaded_model_name}) is English-only."
            })
        active_model = current_model
        logger.debug(f"[{request_id}] Using multilingual model for detection.")
    # --- Lock Released ---

    try:
        # 1. Sanitize and Validate Input File Path
        full_path_obj = sanitize_path(params.file_path)
        source_path_str = str(full_path_obj)
        if not full_path_obj.is_file():
            logger.error(f"[{request_id}] Audio file not found at sanitized path: {source_path_str}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audio file not found: '{params.file_path}'")
        logger.debug(f"[{request_id}] Accessing sanitized audio path: {source_path_str}")

        # 2. Decode Audio File
        start_decode = time.time()
        try:
            audio_input = decode_audio(source_path_str, sampling_rate=16000)
            decode_time = time.time() - start_decode
            logger.info(f"[{request_id}] Decoded audio in {decode_time:.2f}s. Type: {type(audio_input)}, Shape: {getattr(audio_input, 'shape', 'N/A')}")
        except Exception as decode_err:
            logger.exception(f"[{request_id}] Failed to decode audio file: {source_path_str}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to decode audio file: {str(decode_err)}")


        # 3. Prepare Detection Parameters
        vad_options_dict = _validate_vad_params(params.vad_parameters)
        # Collect arguments for detect_language
        detect_args = params.dict(exclude={'file_path', 'vad_parameters'})
        detect_args['vad_parameters'] = vad_options_dict
        logger.debug(f"[{request_id}] Detect language args (excluding audio): {detect_args}")

        # 4. Perform Language Detection
        detect_start_time = time.time()
        try:
            # Call detect_language on the active_model reference
            # Returns tuple: (detected_language, probability, Optional[dict_of_all_probs])
            detection_result = active_model.detect_language(audio=audio_input, **detect_args)
            detect_time = time.time() - detect_start_time

            # Unpack result safely
            lang = detection_result[0] if len(detection_result) > 0 else None
            prob = detection_result[1] if len(detection_result) > 1 else None
            all_probs = detection_result[2] if len(detection_result) > 2 else None

            logger.info(f"[{request_id}] Language detection completed in {detect_time:.2f}s. Detected: {lang} (Prob: {prob:.4f})")

            # 5. Return JSON Response
            return JSONResponse(content={
                "language": lang,
                "language_probability": prob,
                "all_language_probs": all_probs if all_probs is not None else {} # Return empty dict if None
            })
        except Exception as detect_err:
             logger.exception(f"[{request_id}] Error occurred during faster_whisper.detect_language call.")
             raise HTTPException(status_code=500, detail=f"Language detection failed internally: {str(detect_err)}")

    # --- Error Handling for Setup Phase ---
    except HTTPException as http_exc:
        logger.error(f"[{request_id}] HTTP Exception during setup: {http_exc.status_code} - {http_exc.detail}")
        cleanup_audio_source(source_path_str) # Attempt cleanup on setup errors
        raise http_exc
    except ValueError as val_err:
        logger.error(f"[{request_id}] Value Error during setup: {val_err}")
        cleanup_audio_source(source_path_str)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e_setup:
        logger.exception(f"[{request_id}] Unexpected setup error before language detection: {e_setup}")
        cleanup_audio_source(source_path_str)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error during language detection setup: {str(e_setup)}")
    finally:
        # Ensure cleanup runs even if JSONResponse fails (though unlikely)
        # Cleanup is already called within the successful path and error handlers above.
        # Calling it again here is safe due to checks within cleanup_audio_source.
        cleanup_audio_source(source_path_str)


# --- WebSocket Log Endpoint (No Changes Needed Here) ---
@app.websocket("/ws/logs")
async def websocket_log_endpoint(websocket: WebSocket):
    # No auth needed
    await websocket.accept()
    log_websockets.add(websocket)
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown client"
    logger.info(f"Log WebSocket client connected: {client_info}")
    try:
        # Keep connection alive by waiting for messages (client pings or any text)
        while True:
            # This just waits for data/close signal, doesn't process client messages
            await websocket.receive_text()
    except WebSocketDisconnect as e:
        # Log graceful disconnects at INFO level
        logger.info(f"Log WebSocket client disconnected: {client_info}. Code: {e.code}, Reason: {e.reason}")
    except Exception as e:
        # Log unexpected errors during WebSocket communication
        logger.error(f"Log WebSocket error for {client_info}: {e}", exc_info=True)
    finally:
        # Ensure websocket is removed from the active set
        if websocket in log_websockets:
            log_websockets.remove(websocket)
        logger.info(f"Log WebSocket connection closed for {client_info}. Active log clients: {len(log_websockets)}")


# --- Main Execution Block (No Changes Needed Here) ---
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    # Default to 127.0.0.1 for security when API key is removed
    host = os.getenv("HOST", "127.0.0.1")

    # Basic print statements before full logging is configured via startup event
    print(f"---- Preparing to Start Service ----")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Shared Audio Path: {SHARED_AUDIO_PATH.resolve()}")
    print(f"Model Cache Path: {MODEL_CACHE_PATH.resolve()}")
    print(f"------------------------------------")

    # Run Uvicorn server
    uvicorn.run(
        "main:app",         # App location
        host=host,          # Listen address
        port=port,          # Listen port
        workers=1,          # Crucial for stateful model management without IPC
        log_config=None,    # Disable default uvicorn logging to use our custom config
        reload=False        # Disable auto-reload for stability
    )