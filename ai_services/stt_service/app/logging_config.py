# logging_config.py
import logging
import asyncio
import json
import sys
from typing import Set
from fastapi import WebSocket

# --- WebSocket Log Handler ---
log_websockets: Set[WebSocket] = set() # Global set of connected clients

class WebSocketLogHandler(logging.Handler):
    """A logging handler that sends log records to connected WebSockets."""
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            # If called before event loop is running (e.g., during setup), create one.
            # This might happen less often when setup_logging is called in startup event.
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

    def emit(self, record: logging.LogRecord):
        """Format and queue the log record for broadcasting."""
        try:
            log_entry = self.format(record)
            log_data = {
                "type": "log",
                "level": record.levelname,
                "message": log_entry,
                "logger_name": record.name,
                "timestamp": record.created,
            }
            log_json = json.dumps(log_data) + "\n"

            if self.loop.is_running() and not self.loop.is_closed():
                # Ensure task creation happens within the running loop
                asyncio.run_coroutine_threadsafe(self.broadcast(log_json), self.loop)
            # else: # Optional: handle case where loop isn't ready (might log to stderr)
            #     print(f"Log Loop Not Running! Log: {log_json.strip()}", file=sys.stderr)

        except Exception:
            self.handleError(record)

    async def broadcast(self, message: str):
        """Asynchronously send message to all connected websockets."""
        if not log_websockets: return

        # Use list comprehension for tasks, gather results
        tasks = [client.send_text(message) for client in log_websockets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions (e.g., client disconnected between check and send)
        exceptions = {res for res in results if isinstance(res, Exception)}
        if exceptions:
             # Log errors without crashing the handler
             print(f"Errors broadcasting log messages: {exceptions}", file=sys.stderr)
             # Advanced: You might want to identify and remove specific clients causing errors

# --- Logging Setup Function ---
def setup_logging(log_level=logging.INFO):
    """Configures logging for the application, including WebSocket handler."""
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    websocket_handler = WebSocketLogHandler()
    websocket_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    # Check if handlers are already present to avoid duplicates on reloads (if ever enabled)
    if not any(isinstance(h, (logging.StreamHandler, WebSocketLogHandler)) for h in root_logger.handlers):
        root_logger.setLevel(log_level)
        root_logger.addHandler(stream_handler)
        root_logger.addHandler(websocket_handler)

        faster_whisper_logger = logging.getLogger("faster_whisper")
        faster_whisper_logger.setLevel(log_level)
        faster_whisper_logger.propagate = True

        logging.getLogger("uvicorn.access").propagate = False
        logging.getLogger("uvicorn.error").propagate = False

        app_logger = logging.getLogger(__name__)
        app_logger.info("Logging configured with Stream and WebSocket handlers.")
        return app_logger
    else:
        # Return logger instance if already configured
        return logging.getLogger(__name__)


def get_logger(name: str):
    """Gets a logger instance."""
    return logging.getLogger(name)