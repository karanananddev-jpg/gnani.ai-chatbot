#!/usr/bin/env bash
set -e

echo "========================================================="
echo "Starting Gnani.ai Enterprise Chatbot with Guardrails..."
echo "========================================================="

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Starting server at http://localhost:8000 ..."
python -m uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload

