#!/bin/bash
# HTTP Playground - Start Script
# Activates venv and starts Gunicorn with gevent workers

DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/venv/bin/activate"

exec gunicorn app:app \
    --bind 0.0.0.0:5050 \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 500 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload
