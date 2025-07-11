# Stage 1: Python base (for building wheels, doesn't need CUDA)
FROM python:3.10-slim AS python-builder-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/* # If any wheels need C compilation tools

WORKDIR /app_build
RUN pip install --upgrade pip wheel setuptools
# Assumes requirements.txt is at the root of the build context (stt_service_project/requirements.txt)
COPY requirements.txt .
# Build wheels for all dependencies
RUN pip wheel --no-cache-dir --wheel-dir /app_build/wheels -r requirements.txt


# Stage 2: Final application image using NVIDIA CUDA base
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04 AS production

# Set Python-related ENV VARS again for this stage
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Application-specific ENV VARS (defaults, can be overridden by `docker run -e`)
ENV LOG_LEVEL="INFO" \
    CLEANUP_AUDIO="True" \
    HOST="0.0.0.0" \
    PORT="8001" \
    NVIDIA_VISIBLE_DEVICES="all" \
    NVIDIA_DRIVER_CAPABILITIES="compute,utility"

# Install Python3, pip, and essential tools into the NVIDIA image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Ensure 'python' and 'pip' commands default to python3 versions
RUN if ! command -v python &> /dev/null || ! python --version | grep -q "Python 3"; then \
        update-alternatives --install /usr/bin/python python /usr/bin/python3 1; \
    fi && \
    if ! command -v pip &> /dev/null || ! pip --version | grep -q "pip.*python 3"; then \
        update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1; \
    fi

WORKDIR /app

# Create appgroup and appuser for image build purposes and as a fallback.
# This user will be overridden if `docker run -u <uid>:<gid>` is used.
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser

# Install dependencies from wheels (built in python-builder-base stage)
COPY --from=python-builder-base /app_build/wheels /wheels
# Copy requirements.txt from the build context root again (as it's used by pip install -r)
# This ensures pip can verify the packages against the requirements list, even when using --find-links.
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --no-index --find-links=/wheels -r /app/requirements.txt && \
    pip3 install --no-cache-dir nvidia-cublas-cu12 nvidia-cudnn-cu12 && \
    rm -rf /wheels /app/requirements.txt

# Copy application code from the 'app' subfolder of the build context
COPY --chown=appuser:appgroup app/main.py /app/main.py
COPY --chown=appuser:appgroup app/logging_config.py /app/logging_config.py
COPY --chown=appuser:appgroup app/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

# Create the FIXED internal directories.
# Ownership within the image layer is set to appuser:appgroup.
RUN mkdir -p /stt_app_data/audio_inbox && chown -R appuser:appgroup /stt_app_data/audio_inbox \
    && mkdir -p /stt_app_data/model_cache && chown -R appuser:appgroup /stt_app_data/model_cache

# Set the default user for the image. This will be overridden by `docker run -u <uid>:<gid>`.
USER appuser

EXPOSE ${PORT}
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD []