#!/usr/bin/env bash
# Installs backend dependencies and runs the NER Sentinel server, which
# serves both the API (/api/*) and the dashboard frontend from one port.
set -e
cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "Starting NER Sentinel on http://localhost:8000"
echo "Press Ctrl+C to stop."
echo ""
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
