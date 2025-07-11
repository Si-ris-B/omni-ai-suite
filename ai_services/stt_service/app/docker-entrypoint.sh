#!/bin/sh
# stt_service_project/app/docker-entrypoint.sh
set -e

APP_HOST="${HOST:-0.0.0.0}"
APP_PORT="${PORT:-8001}"
APP_LOG_LEVEL_INPUT="${LOG_LEVEL:-INFO}"
APP_LOG_LEVEL_LOWERCASE=$(echo "${APP_LOG_LEVEL_INPUT}" | tr '[:upper:]' '[:lower:]')

# Dynamically construct LD_LIBRARY_PATH to include pip-installed NVIDIA libs
PYTHON_EXEC="python3"
SITE_PACKAGES_LD_PATH=$(${PYTHON_EXEC} -c 'import os, sys; sys.path = [p for p in sys.path if p]; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))' 2>/dev/null || echo "")

if [ -n "${SITE_PACKAGES_LD_PATH}" ]; then
  if [ -n "${LD_LIBRARY_PATH}" ]; then
    export LD_LIBRARY_PATH="${SITE_PACKAGES_LD_PATH}:${LD_LIBRARY_PATH}"
  else
    export LD_LIBRARY_PATH="${SITE_PACKAGES_LD_PATH}"
  fi
  echo "[$(date)] Entrypoint: Updated LD_LIBRARY_PATH to include pip NVIDIA libs: ${LD_LIBRARY_PATH}"
else
  echo "[$(date)] Entrypoint: nvidia-cublas-cu12/nvidia-cudnn-cu12 not found by pip. Relying on system LD_LIBRARY_PATH."
fi

if [ -d "/usr/local/cuda/lib64" ]; then
    export LD_LIBRARY_PATH="/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
fi
if [ -d "/usr/lib/x86_64-linux-gnu" ]; then
    export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
fi

echo "[$(date)] Entrypoint: Final LD_LIBRARY_PATH: ${LD_LIBRARY_PATH}"
echo "[$(date)] Entrypoint: Starting Uvicorn as current user (from docker run -u)..."
echo "[$(date)] Entrypoint:   Host: ${APP_HOST}"
echo "[$(date)] Entrypoint:   Port: ${APP_PORT}"
echo "[$(date)] Entrypoint:   Log Level (Uvicorn): ${APP_LOG_LEVEL_LOWERCASE}"

# The process will run as the user specified by `docker run -u`
exec uvicorn main:app \
    --host "${APP_HOST}" \
    --port "${APP_PORT}" \
    --workers 1 \
    --log-level "${APP_LOG_LEVEL_LOWERCASE}"