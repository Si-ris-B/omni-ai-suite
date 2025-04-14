# Stage 1: Use a standard Python base image
FROM python:3.10-slim as python-base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off     PIP_DISABLE_PIP_VERSION_CHECK=on     PIP_DEFAULT_TIMEOUT=100

# Install system dependencies if needed for AI models (e.g., ffmpeg, git)
# RUN apt-get update && apt-get install -y --no-install-recommends #     ffmpeg #     git #     # Add other system deps here
#     && rm -rf /var/lib/apt/lists/*


# Stage 2: Install Python dependencies
FROM python-base as builder-base
WORKDIR /app
RUN pip install --upgrade pip
COPY ai_services/stt_service/requirements.txt .
# Consider installing heavy AI libs like torch separately if needed
# RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu # Example for CPU PyTorch
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 3: Final application image
FROM python-base as production
WORKDIR /app

# Create a non-root user
RUN addgroup --system --gid 1001 nonroot     && adduser --system --uid 1001 --ingroup nonroot nonroot     && chown nonroot:nonroot /app
USER nonroot

# Copy Python dependencies from builder stage
COPY --from=builder-base /app/wheels /wheels
COPY --from=builder-base /app/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt     && rm -rf /wheels

# Copy application code
COPY --chown=nonroot:nonroot ai_services/stt_service/app /app/app

# Expose the port Uvicorn will run on (matches Uvicorn command and .env STT_SERVICE_PORT)
EXPOSE 8001

# Run Uvicorn server
# Use port from environment variable or default
# Use --host 0.0.0.0 to be accessible within Docker network
# Set workers (often 1 is fine for CPU-bound AI unless I/O heavy)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1", "--log-level", "info"]
