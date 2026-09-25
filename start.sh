#!/bin/bash
set -e

echo "Starting AdsOkay Background Worker Daemon..."
python worker.py &

echo "Starting AdsOkay Media & Image Delivery Web Service on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
