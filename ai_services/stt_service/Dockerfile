# Dockerfile for the 'stt' service

# --- Stage 1: Python Base ---
FROM python:3.10-slim AS python-base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
# Prevent pip from trying to create .cache directory
ENV PIP_ROOT_USER_ACTION=ignore

# Install system deps needed for backend
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# --- Stage 2: Dependency Builder ---
FROM python-base AS builder-base
WORKDIR /app
RUN pip install --upgrade pip wheel
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Stage 3: Final Production Image ---
FROM python-base AS production
WORKDIR /app

# Create non-root user with proper home directory first
RUN addgroup --system --gid 1001 nonroot \
    && adduser --system --uid 1001 --ingroup nonroot --home /home/nonroot nonroot \
    && mkdir -p /home/nonroot \
    && chown -R nonroot:nonroot /home/nonroot

# Copy wheels and requirements first
COPY --from=builder-base /app/wheels /wheels
COPY --from=builder-base /app/requirements.txt .

# Install Python packages system-wide (as root) with explicit target
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Create and set permissions for app directory
RUN mkdir -p /app \
    && chown -R nonroot:nonroot /app

# Copy application code and set ownership
COPY --chown=nonroot:nonroot ./ /app/

# Switch to the non-root user
USER nonroot

# Set HOME environment variable explicitly
ENV HOME=/home/nonroot

# Expose port
EXPOSE 8000

# Set the CMD
CMD ["gunicorn", "--bind", "0.0.0.0:${BACKEND_SERVICE_PORT:-8000}", "your_project_name.wsgi:application"]