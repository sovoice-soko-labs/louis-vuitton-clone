#!/bin/bash
set -euo pipefail
PORT="${1:-8765}"

if lsof -ti ":$PORT" >/dev/null 2>&1; then
  echo "Beende Listener auf Port $PORT …"
  lsof -ti ":$PORT" | xargs kill 2>/dev/null || true
  sleep 1
fi

if curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
  echo "Port $PORT noch belegt — erzwinge Stopp …"
  lsof -ti ":$PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi

echo "Listener gestoppt."
