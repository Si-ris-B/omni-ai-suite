from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio
import signal
import os
import time
import logging # Use proper logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Simulate a resource (like a loaded model) ---
class SimulatedModel:
    def __init__(self):
        self.loaded = False
        logger.info("SimulatedModel: Initialized.")

    def load(self):
        logger.info("SimulatedModel: Loading resource (e.g., model)...")
        time.sleep(2) # Simulate loading time
        self.loaded = True
        logger.info("SimulatedModel: Resource loaded.")

    def unload(self):
        logger.info("SimulatedModel: Unloading resource gracefully...")
        time.sleep(1) # Simulate cleanup time
        self.loaded = False
        logger.info("SimulatedModel: Resource unloaded.")

    def process(self, data):
        if not self.loaded:
            logger.error("SimulatedModel: Process called but model not loaded!")
            raise RuntimeError("Model not loaded!")
        logger.info(f"SimulatedModel: Processing '{data}'...")
        time.sleep(0.5)
        return f"Processed: {data}"

# --- Global state / Resource Holder ---
# Using a simple dictionary to hold app state, including the model
app_state = {"model": SimulatedModel(), "shutdown_event": asyncio.Event()}

# --- Lifespan Context Manager (Handles Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # === Startup ===
    logger.info("STT Service: Startup sequence initiating...")
    model = app_state["model"]
    shutdown_event = app_state["shutdown_event"]

    # Add signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    stop_signals = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)

    # Define the handler within lifespan to capture the shutdown_event easily
    async def shutdown_handler(sig: signal.Signals):
        logger.warning(f"Received exit signal {sig.name}... Starting graceful shutdown.")
        if model.loaded:
            model.unload()
        await asyncio.sleep(0.5) # Brief pause
        logger.warning("Graceful shutdown finished.")
        shutdown_event.set() # Signal completion

    for sig in stop_signals:
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown_handler(s)))

    # Load the model during startup
    model.load()
    logger.info("STT Service: Startup complete.")

    yield # Application runs here

    # === Shutdown ===
    # This part runs AFTER the shutdown signal handler has completed (or on normal exit)
    logger.info("STT Service: Lifespan shutdown sequence initiating...")
    # Wait for the explicit signal from the handler
    await shutdown_event.wait()
    logger.info("STT Service: Lifespan shutdown complete.")


# --- FastAPI App Initialization ---
app = FastAPI(
    title="OmniCore STT Service (Control PoC)",
    description="Provides STT functionality and demonstrates graceful shutdown.",
    version="0.1.0",
    lifespan=lifespan # Register the lifespan context manager
)

# --- Pydantic Models ---
class STTResponse(BaseModel):
    filename: str | None = None # Make filename optional
    transcription: str
    processing_time: float | None = None

class SimpleProcessRequest(BaseModel):
    data: str = "sample input"

class SimpleProcessResponse(BaseModel):
    input: str
    result: str

# --- API Endpoints ---
@app.get("/", tags=["Health"])
async def root():
    """Basic health check, indicates if model resource is loaded."""
    model_status = app_state["model"].loaded
    return {"message": "OmniCore STT Service is running", "model_loaded": model_status}

@app.get("/ping", tags=["Health"])
async def ping():
     """Simple endpoint to check if service is responsive."""
     return {"status": "alive"}

@app.post("/api/v1/stt", response_model=STTResponse, tags=["STT"])
async def process_speech_to_text(
    audio_file: UploadFile = File(..., description="Audio file to transcribe")
    ):
    """
    (PoC Stub) Receives audio file, returns placeholder transcription.
    In a real implementation, this would save the file, call the model's
    processing method, and return the actual result.
    """
    start_time = time.time()
    model = app_state["model"]
    if not model.loaded:
        logger.error("STT request received but model is not loaded.")
        raise HTTPException(status_code=503, detail="Service Unavailable: Model not ready")

    logger.info(f"Received file: {audio_file.filename}, Content-Type: {audio_file.content_type}")

    # Placeholder logic:
    # try:
    #     # content = await audio_file.read() # Read if needed
    #     # result = model.process(content) # Process with real model
    #     placeholder_transcription = f"Actual transcription for {audio_file.filename} would go here."
    # except Exception as e:
    #      logger.error(f"Error during STT processing: {e}")
    #      raise HTTPException(status_code=500, detail=f"STT processing error: {e}")
    # finally:
    #      await audio_file.close() # Ensure file handle is closed

    placeholder_transcription = f"Placeholder transcription for {audio_file.filename}"
    processing_time = time.time() - start_time

    return STTResponse(
        filename=audio_file.filename,
        transcription=placeholder_transcription,
        processing_time=round(processing_time, 3)
    )

# Example endpoint using the simulated model process method
@app.post("/api/v1/process", response_model=SimpleProcessResponse, tags=["Processing"])
async def simulate_processing(request: SimpleProcessRequest):
    """Simulates processing data using the loaded resource."""
    model = app_state["model"]
    if not model.loaded:
        logger.error("Process request received but model is not loaded.")
        raise HTTPException(status_code=503, detail="Service Unavailable: Model not loaded")
    try:
        result = model.process(request.data)
        return SimpleProcessResponse(input=request.data, result=result)
    except Exception as e:
         logger.error(f"Error during simulated processing: {e}")
         raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")