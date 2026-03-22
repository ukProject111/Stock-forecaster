#!/bin/bash
# start_backend.sh - starts the FastAPI server with the virtual environment
# Run this instead of manually activating venv every time
# Mehmet Tanil Kaplan - T0429362

cd "$(dirname "$0")"
source venv/bin/activate
cd backend
echo "Starting Stock Forecaster API on port 8000..."
echo "API docs available at http://localhost:8000/docs"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
