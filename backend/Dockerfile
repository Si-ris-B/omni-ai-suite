# --- Stage 1: Python Base ---
# Use a specific Python version on a slim Debian base image
FROM python:3.10-slim AS python-base
# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents python creating .pyc files
ENV PYTHONUNBUFFERED=1
# Prevents python buffering stdout/stderr
ENV PIP_NO_CACHE_DIR=off
# Enable pip cache (within this stage)
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
# Silence pip version check warning
ENV PIP_DEFAULT_TIMEOUT=100
# Increase pip timeout

# Install system dependencies needed for building Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       # Add any other system dependencies your backend might need (e.g., libxml2-dev)
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# --- Stage 2: Dependency Builder ---
# Install Python dependencies in a dedicated stage to leverage Docker cache
FROM python-base AS builder-base
WORKDIR /app

# Install pip wheel tool
RUN pip install --upgrade pip wheel

# Copy only the requirements file first to cache dependencies
COPY requirements.txt .

# Build wheel files for all dependencies
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# --- Stage 3: Final Production Image ---
FROM python-base AS production
WORKDIR /app

# Copy built wheels and requirements file from the builder stage
COPY --from=builder-base /app/wheels /wheels
COPY --from=builder-base /app/requirements.txt .

# Install dependencies from the wheels BEFORE switching to non-root user
# This installs packages globally which non-root users can still access
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Create a non-root user and group for security with proper home directory
RUN addgroup --system --gid 1001 nonroot \
    && adduser --system --uid 1001 --ingroup nonroot --home /home/nonroot nonroot \
    && mkdir -p /home/nonroot \
    && chown -R nonroot:nonroot /home/nonroot \
    && chown -R nonroot:nonroot /app

# Copy the application code into the container
# Use --chown to set the correct owner for the copied files
COPY --chown=nonroot:nonroot ./apps /app/apps
COPY --chown=nonroot:nonroot ./main_backend /app/main_backend
COPY --chown=nonroot:nonroot ./manage.py /app/manage.py

# Switch to the non-root user AFTER installing packages and copying files
USER nonroot

# Set HOME environment variable explicitly
ENV HOME=/home/nonroot

# Expose the port the application will run on
EXPOSE 8000

# Set the command to run the application using Gunicorn
CMD ["gunicorn", "main_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]